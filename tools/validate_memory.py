#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from memorylib.validate import validate
ROOT=Path(__file__).resolve().parents[1]
r=validate(ROOT,"v0-compatible")
print(f"Errors: {r.errors}")
for i in r.issues:
    if i.severity in {"FATAL","ERROR"}: print(f"{i.severity}: {i.code}{' ['+i.path+']' if i.path else ''}: {i.message}")
print(f"Warnings: {r.warnings}")
for i in r.issues:
    if i.severity=="WARNING": print(f"WARN: {i.code}{' ['+i.path+']' if i.path else ''}: {i.message}")
raise SystemExit(1 if r.errors else 0)
