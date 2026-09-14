#!/usr/bin/env python3
"""Fail-closed canonical Memory V2 update engine."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from memorylib.dashboard import render_all
from memorylib.validate import validate
from memorylib.v2 import ingest_events


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a structured Memory V2 event payload")
    parser.add_argument("payload", type=Path)
    parser.add_argument("--commit", action="store_true")
    parser.add_argument("--commit-message", default="memory: apply canonical V2 update")
    args = parser.parse_args()
    data = json.loads(args.payload.read_text(encoding="utf-8"))
    results = ingest_events(ROOT, data.get("events", []), canonical_records=data.get("canonical_records", []), validate_after=False)
    render_all(ROOT)
    report = validate(ROOT, "v1")
    if report.errors:
        raise SystemExit(f"Validation failed closed: {report.errors} error(s)")
    if args.commit:
        paths = ["00_HOME.md", "CURRENT_STATE.md", "CURRENT_PRIORITIES.md", "CURRENT_BLOCKERS.md", "CURRENT_TASK.md", "findings/OPEN.md", "findings/RESOLVED.md", "views", "mocs", "builder/CURRENT_CONTEXT_PACKET.md", "builder/context", "events", "decisions/records", "workstreams", "tasks/records", "findings/records", "state/records", "architecture", "_meta"]
        subprocess.run(["git", "-C", str(ROOT), "add", "--", *paths], check=True)
        staged = subprocess.run(["git", "-C", str(ROOT), "diff", "--cached", "--name-only"], capture_output=True, text=True, check=True).stdout.strip()
        if staged:
            subprocess.run(["git", "-C", str(ROOT), "commit", "-m", args.commit_message], check=True)
    print(json.dumps({"results": [r.__dict__ for r in results], "committed": args.commit, "errors": report.errors, "warnings": report.warnings}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
