#!/usr/bin/env python3
"""Transactional installer for SportsBrainMemory V1.

Default is dry-run. No Git mutation commands are executed.
"""
from __future__ import annotations
from pathlib import Path
import argparse, datetime, shutil, subprocess, sys, json, hashlib

PACKAGE=Path(__file__).resolve().parents[1]
EXPECTED_BASELINE='67444780f8ed0a1340a935934638a7cbd3dfe83b'
SKIP_PARTS={'.git','.memory-build','__pycache__','.memory-backups','.claude','.obsidian'}
SKIP_FILES={'.DS_Store'}

def package_files():
    out=[]
    for p in PACKAGE.rglob('*'):
        if not p.is_file():
            continue
        rel=p.relative_to(PACKAGE)
        if any(x in SKIP_PARTS for x in rel.parts) or p.suffix=='.pyc' or rel.as_posix() in SKIP_FILES:
            continue
        out.append(rel)
    return sorted(out)


def _sha256(path:Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def _content_fingerprint(root:Path):
    h=hashlib.sha256()
    excludes={'.memory-build','__pycache__','.git','.memory-backups','.claude','.obsidian'}
    metadata_excludes={'_meta/ACCEPTANCE_REPORT.json','_meta/PACKAGE_MANIFEST.json','.DS_Store'}
    for p in sorted(root.rglob('*')):
        rel=p.relative_to(root)
        if (not p.is_file() or any(x in excludes for x in rel.parts)
                or p.suffix=='.pyc' or rel.as_posix() in metadata_excludes):
            continue
        h.update(rel.as_posix().encode()); h.update(b'\0')
        h.update(p.read_bytes()); h.update(b'\0')
    return h.hexdigest()

def verify_package_manifest():
    manifest_path=PACKAGE/'_meta'/'PACKAGE_MANIFEST.json'
    if not manifest_path.exists():
        raise SystemExit('STOP: package manifest is missing')
    try:
        manifest=json.loads(manifest_path.read_text(encoding='utf-8'))
    except Exception as exc:
        raise SystemExit(f'STOP: package manifest is unreadable: {exc}')
    declared=manifest.get('files')
    if not isinstance(declared,list):
        raise SystemExit('STOP: package manifest files[] is invalid')
    expected={x['path']:x for x in declared if isinstance(x,dict) and x.get('path')}
    manifest_rel='_meta/PACKAGE_MANIFEST.json'
    actual={rel.as_posix() for rel in package_files()}
    expected_files=set(expected) | {manifest_rel}
    if expected_files!=actual:
        missing_from_package=sorted(expected_files-actual)[:10]
        unexpected_in_package=sorted(actual-expected_files)[:10]
        raise SystemExit(f'STOP: package manifest file-set mismatch missing_from_package={missing_from_package} unexpected_in_package={unexpected_in_package}')
    for rel,meta in expected.items():
        path=PACKAGE/rel
        if _sha256(path)!=meta.get('sha256') or path.stat().st_size!=meta.get('bytes'):
            raise SystemExit(f'STOP: package integrity mismatch: {rel}')
    fp=_content_fingerprint(PACKAGE)
    if fp!=manifest.get('content_fingerprint'):
        raise SystemExit(f'STOP: package content fingerprint mismatch {fp} != {manifest.get("content_fingerprint")}')
    return manifest

def git_read(repo:Path,args:list[str]):
    try:
        return subprocess.run(['git','-C',str(repo),*args],text=True,capture_output=True,check=True).stdout.strip()
    except Exception:
        return ''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--repo',required=True)
    ap.add_argument('--apply',action='store_true')
    ap.add_argument('--allow-head-mismatch',action='store_true')
    ap.add_argument('--allow-dirty',action='store_true')
    a=ap.parse_args()
    verify_package_manifest()
    repo=Path(a.repo).expanduser().resolve()
    if not (repo/'README.md').exists() or not (repo/'tools').exists():
        raise SystemExit(f'{repo} does not look like SportsBrainMemory')

    head=git_read(repo,['rev-parse','HEAD'])
    dirty=git_read(repo,['status','--porcelain'])
    if head and head!=EXPECTED_BASELINE and not a.allow_head_mismatch:
        raise SystemExit(f'STOP: Memory HEAD {head} != expected {EXPECTED_BASELINE}')
    if dirty and not a.allow_dirty:
        raise SystemExit('STOP: target Memory worktree is dirty; preserve/reconcile user changes first')

    files=package_files()
    plan=[]
    for rel in files:
        dst=repo/rel
        plan.append({'path':rel.as_posix(),'action':'replace' if dst.exists() else 'create'})
    print(json.dumps({
        'mode':'APPLY' if a.apply else 'DRY-RUN',
        'target':str(repo),'head':head or 'UNKNOWN','dirty':bool(dirty),
        'files':len(files),'replace':sum(x['action']=='replace' for x in plan),
        'create':sum(x['action']=='create' for x in plan),
    },indent=2))
    if not a.apply:
        print('Dry-run complete. No files changed.')
        return 0

    stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    backup=repo/'.memory-backups'/f'v1-{stamp}'
    backup.mkdir(parents=True,exist_ok=False)
    created=[]
    replaced=[]
    try:
        for rel in files:
            src=PACKAGE/rel
            dst=repo/rel
            if dst.exists():
                bp=backup/rel
                bp.parent.mkdir(parents=True,exist_ok=True)
                shutil.copy2(dst,bp)
                replaced.append((dst,bp))
            else:
                created.append(dst)
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(src,dst)

        # Acceptance on the installed tree. These commands do not mutate Git history.
        commands=[
            [sys.executable,'-m','compileall','-q','.'],
            [sys.executable,'-m','unittest','discover','-s','tests','-v'],
            [sys.executable,'tools/memory.py','acceptance'],
        ]
        for cmd in commands:
            r=subprocess.run(cmd,cwd=repo,text=True,capture_output=True)
            print(r.stdout,end='')
            print(r.stderr,end='',file=sys.stderr)
            if r.returncode!=0:
                raise RuntimeError(f'acceptance command failed: {cmd}')
        print(f'V1 installed and accepted. Backup: {backup}')
        print('Git history/refs were not modified.')
        return 0
    except Exception:
        for dst in reversed(created):
            if dst.exists():
                dst.unlink()
        for dst,bp in reversed(replaced):
            dst.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(bp,dst)
        print(f'INSTALL FAILED — restored files from {backup}',file=sys.stderr)
        raise

if __name__=='__main__':
    raise SystemExit(main())
