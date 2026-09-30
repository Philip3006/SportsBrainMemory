#!/usr/bin/env python3
"""Small deterministic quality check for the operational Memory surface.

The existing V1/V2 validator checks schema and governed records. This tool
checks the human navigation layer: wikilinks, canonical IDs, required
frontmatter, current-state cardinality, stale current references, and obvious
secret-like material. It never edits the vault.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
SHA = re.compile(r"\b[0-9a-f]{40}\b")
SECRET = (
    re.compile(r"\b(?:sk|pk)_(?:live|test)_[A-Za-z0-9]{16,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._-]{24,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
)
REQUIRED_META_DIRS = {"domains", "runbooks", "templates", "operations"}
EXCLUDED_PARTS = {".git", ".memory-backups", ".pytest_cache", "__pycache__", "_live"}
CURRENT_FILES = {
    "00_HOME.md",
    "CURRENT_STATE.md",
    "CURRENT_PRIORITIES.md",
    "CURRENT_BLOCKERS.md",
    "architecture/OPERATIONAL_KNOWLEDGE_BASE.md",
    "domains/PRODUCTION_OPERATIONS.md",
    "domains/BUILDERS.md",
}
ALLOWED_STATUSES = {
    "active", "current", "open", "closed", "complete", "completed",
    "completed_ceo_approved", "completed_disabled", "draft", "planned",
    "planned_ready", "active_preparation", "technically_complete_soak_deferred",
    "superseded", "branch_candidate", "resolved", "resolved_production",
    "resolved_branch_candidate", "accepted_risk", "unverified", "unsupported",
    "observed", "verified", "target", "retired", "pending", "reconciled",
    "reconciled_for_operational_kb_review", "ready_for_ceo_review", "stale",
    "passed", "approved_target", "complete_with_external_gates", "recompute_required",
}


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}
    meta: dict[str, str] = {}
    for line in text[4:end].splitlines():
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            meta[match.group(1)] = match.group(2).strip().strip('"\'')
    return meta


def markdown_files(root: Path) -> list[Path]:
    return [
        path for path in sorted(root.rglob("*.md"))
        if not any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts)
    ]


def resolve_link(root: Path, raw: str) -> Path | None:
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    if not target or target.startswith(("http://", "https://", "mailto:", "#")):
        return None
    target = target.lstrip("/")
    # _live is an intentionally ignored/generated layer. Its links are
    # valid only when the user-level live synchronizer has rendered them.
    if target.startswith("_live/"):
        return None
    candidate = root / target
    if candidate.suffix == "":
        candidate = candidate.with_suffix(".md")
    return candidate


def add_issue(issues: list[dict[str, str]], severity: str, code: str, message: str, path: str = "") -> None:
    issues.append({"severity": severity, "code": code, "message": message, "path": path})


def validate(root: Path) -> dict[str, object]:
    issues: list[dict[str, str]] = []
    files = markdown_files(root)
    incoming: dict[str, int] = {}
    ids: dict[str, str] = {}
    current_states = []
    manifest_path = root / "_meta" / "MEMORY_V2.json"
    manifest: dict[str, object] = {}
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            add_issue(issues, "ERROR", "MANIFEST_JSON", str(exc), "_meta/MEMORY_V2.json")
    else:
        add_issue(issues, "ERROR", "MANIFEST_MISSING", "_meta/MEMORY_V2.json is missing")

    for path in files:
        rel = path.relative_to(root).as_posix()
        meta = parse_frontmatter(path)
        if meta.get("id"):
            if meta["id"] in ids:
                add_issue(issues, "ERROR", "DUPLICATE_CANONICAL_ID", f"also declared at {ids[meta['id']]}", rel)
            else:
                ids[meta["id"]] = rel
        if meta.get("status") == "current" and meta.get("type") == "project-state":
            current_states.append(rel)
        if any(rel == directory or rel.startswith(directory + "/") for directory in REQUIRED_META_DIRS):
            if "type" not in meta or "status" not in meta:
                add_issue(issues, "ERROR", "MISSING_REQUIRED_FRONTMATTER", "type and status are required", rel)
        if "status" in meta and meta["status"] not in ALLOWED_STATUSES:
            add_issue(issues, "WARNING", "UNKNOWN_STATUS", f"status={meta['status']!r}", rel)

        text = path.read_text(encoding="utf-8", errors="replace")
        for match in WIKILINK.finditer(text):
            target = resolve_link(root, match.group(1))
            if target is None:
                continue
            target_rel = target.relative_to(root).as_posix() if target.is_relative_to(root) else str(target)
            incoming[target_rel] = incoming.get(target_rel, 0) + 1
            if not target.exists():
                severity = "ERROR" if rel in CURRENT_FILES or rel.startswith("runbooks/") else "WARNING"
                add_issue(issues, severity, "BROKEN_WIKILINK", f"target does not exist: {match.group(1)}", rel)
        if rel in CURRENT_FILES and any(pattern.search(text) for pattern in SECRET):
            add_issue(issues, "ERROR", "SECRET_LIKE_MATERIAL", "possible secret-like text in current note", rel)

    if len(current_states) != 1:
        add_issue(issues, "ERROR", "CURRENT_STATE_CARDINALITY", f"expected one current project-state, got {len(current_states)}")

    source_main = str(manifest.get("source_main_sha", ""))
    if not re.fullmatch(r"[0-9a-f]{40}", source_main):
        add_issue(issues, "ERROR", "SOURCE_MAIN_SHA", "manifest source_main_sha is not a 40-character SHA", "_meta/MEMORY_V2.json")
    else:
        for rel in ("CURRENT_STATE.md", "00_HOME.md"):
            text = (root / rel).read_text(encoding="utf-8", errors="replace") if (root / rel).exists() else ""
            if source_main not in text:
                add_issue(issues, "ERROR", "CURRENT_SHA_MISSING", f"{source_main} is absent", rel)

    stale_sha = {
        "6493f14093aa08e457e610c2961da1e77b80bc76",
        "8de9472644057656c50d900380a843909ff5a46b",
        "010ee71559fef2a25d0e77c2ef82413c99ce127f",
    }
    for rel in CURRENT_FILES:
        path = root / rel
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            for old in stale_sha:
                if old in text:
                    add_issue(issues, "ERROR", "STALE_CURRENT_SHA", f"obsolete source/runtime SHA {old}", rel)

    ignored_orphans = {"README.md", "00_HOME.md", "CURRENT_STATE.md", "CURRENT_PRIORITIES.md", "CURRENT_BLOCKERS.md", "CURRENT_TASK.md", "VALIDATION_REPORT.md"}
    orphan_count = 0
    for path in files:
        rel = path.relative_to(root).as_posix()
        if rel in ignored_orphans or rel.startswith(("history/", "templates/", "runbooks/")):
            continue
        if rel not in incoming and not rel.startswith(("_meta/", "events/records/")):
            orphan_count += 1
            add_issue(issues, "WARNING", "ORPHAN_NOTE", "no inbound wikilink found", rel)

    for path in root.rglob("*"):
        if not path.is_file() or any(part in EXCLUDED_PARTS for part in path.relative_to(root).parts):
            continue
        # The existing unit tests intentionally contain a synthetic bearer
        # string to prove the V2 secret detector rejects it. It is not vault
        # credential material.
        if "tests" in path.relative_to(root).parts:
            continue
        if path.suffix not in {".md", ".json", ".py"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(pattern.search(text) for pattern in SECRET):
            add_issue(issues, "ERROR", "SECRET_LIKE_MATERIAL", "possible secret-like text detected", path.relative_to(root).as_posix())

    errors = sum(issue["severity"] == "ERROR" for issue in issues)
    warnings = sum(issue["severity"] == "WARNING" for issue in issues)
    return {
        "root": str(root),
        "files": len(files),
        "canonical_ids": len(ids),
        "current_states": current_states,
        "orphan_count": orphan_count,
        "errors": errors,
        "warnings": warnings,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = validate(args.root.resolve())
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(f"Operational Memory: {result['files']} Markdown files, {result['canonical_ids']} IDs")
        print(f"Errors: {result['errors']}  Warnings: {result['warnings']}  Orphans: {result['orphan_count']}")
        for issue in result["issues"]:
            print(f"{issue['severity']}: {issue['code']} [{issue['path']}] {issue['message']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
