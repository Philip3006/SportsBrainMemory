from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, shutil, tempfile

SUPPORTED_OPS={"create","replace","append","delete","move"}

@dataclass
class ChangeResult:
    changed:list[str]
    dry_run:bool

def load_changeset(path:Path):
    obj=json.loads(path.read_text(encoding="utf-8"))
    ops=obj.get("operations",obj.get("updates"))
    if not isinstance(ops,list): raise ValueError("changeset must contain operations[] (or legacy updates[])")
    return {"metadata":obj.get("metadata",{}),"operations":ops}

def _safe(root,rel):
    target=(root/rel).resolve(); rr=root.resolve()
    if target!=rr and rr not in target.parents: raise ValueError(f"path escapes memory root: {rel}")
    return target

def check(root,changeset):
    planned=[]
    for raw in changeset["operations"]:
        op=raw.get("op") or raw.get("mode","replace")
        if op not in SUPPORTED_OPS: raise ValueError(f"unsupported operation {op!r}")
        rel=raw.get("path")
        if not isinstance(rel,str) or not rel: raise ValueError("operation path is required")
        target=_safe(root,rel)
        if op=="create" and target.exists(): raise ValueError(f"create target already exists: {rel}")
        if op in {"append","delete"} and not target.exists(): raise ValueError(f"{op} target does not exist: {rel}")
        if op=="move":
            dest=raw.get("to")
            if not isinstance(dest,str) or not dest: raise ValueError("move operation requires 'to'")
            _safe(root,dest)
        planned.append(f"{op}:{rel}")
    return planned

def apply(root,changeset,dry_run=True,validator=None):
    planned=check(root,changeset)
    if dry_run: return ChangeResult(planned,True)
    backup=Path(tempfile.mkdtemp(prefix="sportsbrain-memory-changeset-"))
    created=[]; touched={}
    try:
        for raw in changeset["operations"]:
            op=raw.get("op") or raw.get("mode","replace")
            rel=raw["path"]; target=_safe(root,rel)
            if target.exists() and target not in touched:
                bp=backup/rel; bp.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(target,bp); touched[target]=bp
            if op in {"create","replace"}:
                existed_before = target.exists()
                target.parent.mkdir(parents=True,exist_ok=True)
                target.write_text(str(raw.get("content","")).rstrip()+"\n",encoding="utf-8")
                if not existed_before:
                    created.append(target)
            elif op=="append":
                with target.open("a",encoding="utf-8") as f: f.write("\n"+str(raw.get("content","")).rstrip()+"\n")
            elif op=="delete": target.unlink()
            elif op=="move":
                dest=_safe(root,raw["to"])
                if dest.exists(): raise ValueError(f"move destination exists: {raw['to']}")
                dest.parent.mkdir(parents=True,exist_ok=True); shutil.move(str(target),str(dest)); created.append(dest)
        if validator is not None:
            report=validator(root)
            if report.errors: raise RuntimeError(f"post-change validation failed with {report.errors} error(s)")
        return ChangeResult(planned,False)
    except Exception:
        for p in reversed(created):
            if p.exists(): p.unlink()
        for target,bp in reversed(list(touched.items())):
            target.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(bp,target)
        raise
    finally:
        shutil.rmtree(backup,ignore_errors=True)
