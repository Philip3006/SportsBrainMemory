#!/usr/bin/env python3
"""Explicit post-review, user-level installer. Never invoked by CI or importer."""
import argparse
import os
from pathlib import Path
import plistlib
import subprocess
import sys

LABEL = "com.sportsbrain.memory-sync"


def plist_payload(memory, vault, source, python, logs):
    return {
        "Label": LABEL,
        "ProgramArguments": [str(python), str(memory / "tools/sync_memory.py"),
                             "--memory-repo", str(memory), "--vault", str(vault),
                             "--source-repo", str(source), "--branch", "main"],
        "RunAtLoad": True, "StartInterval": 300,
        "StandardOutPath": str(logs / "memory-sync.log"),
        "StandardErrorPath": str(logs / "memory-sync-error.log"),
        "ProcessType": "Background",
    }


def install(args, *, run=subprocess.run):
    home = args.home.resolve()
    target = home / "Library/LaunchAgents" / f"{LABEL}.plist"
    domain = f"gui/{os.getuid()}"
    job = f"{domain}/{LABEL}"
    probe = run(["launchctl", "print", job], capture_output=True, check=False)
    if args.status:
        return {"installed": target.exists(), "loaded": probe.returncode == 0}
    if args.uninstall:
        if probe.returncode == 0:
            run(["launchctl", "bootout", job], check=True)
        target.unlink(missing_ok=True)
        return {"installed": False, "loaded": False}
    for path in (args.memory_repo, args.vault, args.source_repo):
        if not path.is_absolute() or not path.is_dir():
            raise ValueError("Canonical directories must exist and be absolute")
    if not (args.memory_repo / ".git").exists() or not (args.source_repo / ".git").exists():
        raise ValueError("Canonical clones must be Git repositories")
    if not (args.memory_repo / "tools/sync_memory.py").is_file():
        raise ValueError("Missing sync script")
    if not args.python.is_file() or not os.access(args.python, os.X_OK):
        raise ValueError("Python interpreter must be executable")
    # --seed is deliberately absent: a missing/conflicting manifest fails closed.
    logs = home / "Library/Logs/SportsBrain"
    payload = plistlib.dumps(plist_payload(args.memory_repo, args.vault, args.source_repo, args.python, logs), sort_keys=True)
    unchanged = target.exists() and target.read_bytes() == payload
    if unchanged and probe.returncode == 0:
        return {"installed": True, "loaded": True, "changed": False}
    if probe.returncode == 0:
        run(["launchctl", "bootout", job], check=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(payload)
    temporary.replace(target)
    run(["launchctl", "bootstrap", domain, str(target)], check=True)
    run(["launchctl", "kickstart", job], check=True)
    return {"installed": True, "loaded": True, "changed": not unchanged}


def main():
    import json
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument("--status", action="store_true")
    modes.add_argument("--uninstall", action="store_true")
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--memory-repo", type=Path, default=Path("/Users/philiprassillier/SportsBrain-Memory"))
    parser.add_argument("--vault", type=Path, default=Path("/Users/philiprassillier/Downloads/SportsBrain-Memory"))
    parser.add_argument("--source-repo", type=Path, default=Path("/Users/philiprassillier/sportsbrain"))
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    args = parser.parse_args()
    try:
        print(json.dumps(install(args), sort_keys=True))
    except (ValueError, OSError, subprocess.CalledProcessError):
        print("Memory LaunchAgent operation failed; inspect canonical paths and launchctl status.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
