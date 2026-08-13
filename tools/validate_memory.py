#!/usr/bin/env python3
"""Validate SportsBrain Shared Memory integrity. Stdlib only."""
from pathlib import Path
import re, json, sys

ROOT = Path(__file__).resolve().parents[1]
errors, warnings = [], []

# Required files
required = [
    "README.md","CLAUDE.md","BOOTSTRAP.md","CURRENT_STATE.md","CURRENT_TASK.md",
    "CURRENT_BLOCKERS.md","CURRENT_PRIORITIES.md","_meta/memory_manifest.json",
    "invariants/INDEX.md","findings/OPEN.md","decisions/INDEX.md",
    "builder/CURRENT_CONTEXT_PACKET.md"
]
for rel in required:
    if not (ROOT/rel).exists():
        errors.append(f"missing required file: {rel}")

# Unique IDs across finding/decision/task declarations
patterns = {
    "finding": re.compile(r'\bFND-\d{8}-\d{3}\b'),
    "decision": re.compile(r'\bDEC-\d{4}\b'),
}
for kind, pat in patterns.items():
    record_dir = ROOT / ("findings/records" if kind=="finding" else "decisions/records")
    ids = []
    if record_dir.exists():
        for p in record_dir.glob("*.md"):
            found = set(pat.findall(p.read_text(encoding="utf-8")))
            own = p.stem
            if own not in found:
                errors.append(f"{kind} file {p.relative_to(ROOT)} does not contain own id")
            ids.append(own)
    if len(ids) != len(set(ids)):
        errors.append(f"duplicate {kind} record IDs")

# Invariant IDs globally unique by definition headings.
inv_ids = []
for p in (ROOT/"invariants").glob("*.md"):
    inv_ids += re.findall(r'^##\s+([A-Z]+-\d{3})\s*$', p.read_text(encoding="utf-8"), re.M)
if len(inv_ids) != len(set(inv_ids)):
    errors.append("duplicate invariant IDs across domain files")
if len(set(inv_ids)) != 159:
    errors.append(f"expected 159 invariant IDs, found {len(set(inv_ids))}")

# Finding invariant references must exist
inv_set = set(inv_ids)
for p in (ROOT/"findings/records").glob("*.md"):
    for iid in re.findall(r'\b[A-Z]+-\d{3}\b', p.read_text(encoding="utf-8")):
        if iid.startswith(("FND","DEC","INC","AUD","TASK")):
            continue
        if iid not in inv_set:
            errors.append(f"{p.relative_to(ROOT)} references unknown invariant {iid}")

# Obsidian wikilinks resolve to .md where path-like.
for p in ROOT.rglob("*.md"):
    text = p.read_text(encoding="utf-8")
    for target in re.findall(r'\[\[([^\]|#]+)(?:#[^\]|]+)?(?:\|[^\]]+)?\]\]', text):
        target = target.strip()
        candidates = [ROOT/(target+".md"), ROOT/target]
        if "/" not in target:
            candidates += list(ROOT.rglob(target+".md"))
        if not any(c.exists() for c in candidates):
            errors.append(f"broken wikilink in {p.relative_to(ROOT)}: [[{target}]]")

# Sensitive-data heuristic: actual obvious secret values, not documentation words.
secret_patterns = [
    re.compile(r'(?i)(api[_-]?key|secret|token)\s*[:=]\s*["\']?[A-Za-z0-9_\-]{24,}["\']?'),
    re.compile(r'\bsk-[A-Za-z0-9]{20,}\b'),
    re.compile(r'\bghp_[A-Za-z0-9]{20,}\b'),
]
for p in ROOT.rglob("*"):
    if not p.is_file() or p.suffix.lower() not in {".md",".json",".py"}:
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for sp in secret_patterns:
        for m in sp.finditer(text):
            # Ignore explicit placeholder/demo language.
            snippet = text[max(0,m.start()-80):m.end()+80].lower()
            if any(x in snippet for x in ["example","placeholder","never store","pattern"]):
                continue
            warnings.append(f"possible secret-like text in {p.relative_to(ROOT)}")

# Current task exactly one and packet budget
task_text = (ROOT/"CURRENT_TASK.md").read_text(encoding="utf-8") if (ROOT/"CURRENT_TASK.md").exists() else ""
if 'status: "current"' not in task_text:
    errors.append("CURRENT_TASK frontmatter is not status=current")
packet = ROOT/"builder/CURRENT_CONTEXT_PACKET.md"
if packet.exists():
    m = re.search(r'estimated_tokens=(\d+)', packet.read_text(encoding="utf-8"))
    if not m:
        errors.append("context packet missing token estimate")
    elif int(m.group(1)) > 8000:
        errors.append(f"context packet exceeds 8000 token soft limit: {m.group(1)}")

# Manifest
manifest = ROOT/"_meta/memory_manifest.json"
if manifest.exists():
    try:
        obj = json.loads(manifest.read_text(encoding="utf-8"))
        if not isinstance(obj.get("files"), list):
            errors.append("manifest files missing/not list")
    except Exception as e:
        errors.append(f"manifest invalid JSON: {e}")

print(f"Errors: {len(errors)}")
for e in errors: print("ERROR:", e)
print(f"Warnings: {len(warnings)}")
for w in warnings[:20]: print("WARN:", w)
sys.exit(1 if errors else 0)
