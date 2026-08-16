#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from memorylib.changeset import load_changeset,apply
from memorylib.validate import validate
ROOT=Path(__file__).resolve().parents[1]
if len(sys.argv)!=2: print("usage: apply_update.py <bundle.json>",file=sys.stderr); raise SystemExit(2)
r=apply(ROOT,load_changeset(Path(sys.argv[1])),dry_run=False,validator=lambda rr:validate(rr))
print(f"Applied {len(r.changed)} update(s) transactionally; Git was not touched.")
