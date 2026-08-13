#!/usr/bin/env python3
"""Apply a ChatGPT-generated update bundle to this Memory only.

Bundle format:
{
  "updates": [
    {"path": "CURRENT_STATE.md", "mode": "replace", "content": "..."},
    {"path": "findings/OPEN.md", "mode": "append", "content": "..."}
  ]
}

No Git commands are executed. After update, validator is run. On validation
failure, original files are restored.
"""
from pathlib import Path
import json, sys, shutil, subprocess, tempfile

ROOT = Path(__file__).resolve().parents[1]
if len(sys.argv) != 2:
    print("usage: apply_update.py <bundle.json>", file=sys.stderr)
    sys.exit(2)

bundle = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
updates = bundle.get("updates", [])
if not isinstance(updates, list):
    raise SystemExit("updates must be a list")

backup_dir = Path(tempfile.mkdtemp(prefix="sportsbrain-memory-backup-"))
changed = []
try:
    for u in updates:
        rel = u["path"]
        mode = u.get("mode","replace")
        content = u.get("content","")
        target = (ROOT/rel).resolve()
        if ROOT.resolve() not in target.parents:
            raise ValueError(f"path escapes memory root: {rel}")
        if target.exists():
            bp = backup_dir/rel
            bp.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(target,bp)
        target.parent.mkdir(parents=True, exist_ok=True)
        if mode == "replace":
            target.write_text(content.rstrip()+"\n", encoding="utf-8")
        elif mode == "append":
            with target.open("a",encoding="utf-8") as f:
                f.write("\n"+content.rstrip()+"\n")
        else:
            raise ValueError(f"unsupported mode {mode}")
        changed.append((target, rel))
    r = subprocess.run([sys.executable, str(ROOT/"tools/validate_memory.py")], cwd=ROOT)
    if r.returncode != 0:
        raise RuntimeError("memory validation failed")
    print(f"Applied {len(changed)} update(s); Git was not touched.")
except Exception:
    for target, rel in reversed(changed):
        bp = backup_dir/rel
        if bp.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(bp,target)
        elif target.exists():
            target.unlink()
    raise
finally:
    shutil.rmtree(backup_dir, ignore_errors=True)
