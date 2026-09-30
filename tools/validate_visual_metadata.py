#!/usr/bin/env python3
"""Validate the small semantic metadata contract used by Obsidian Graph.

The validator is deliberately separate from graph topology. Domains provide
color-group identity; roles provide importance/context. It never edits notes
and it does not require historical, template, archive, or support leaves to
carry visual metadata.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from graph_health import _is_operational_canonical  # noqa: E402
from validate_operational_memory import markdown_files, parse_frontmatter  # noqa: E402


SCHEMA = "sportsbrain-memory-visual-metadata-v1"
DOMAINS = (
    "top5",
    "nations-league",
    "tennis",
    "production",
    "providers-data",
    "model-research",
    "governance",
    "observability",
    "product",
    "memory",
)
ROLES = ("core", "operational", "evidence", "support", "historical")


def _value(meta: dict[str, str], key: str) -> str:
    value = meta.get(key, "")
    return value if isinstance(value, str) else ""


def analyze(root: Path) -> dict[str, object]:
    root = root.resolve()
    files = markdown_files(root)
    entries: list[tuple[str, dict[str, str], bool]] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        meta = parse_frontmatter(path)
        entries.append((rel, meta, _is_operational_canonical(rel, meta)))

    invalid_domains = [
        {"path": rel, "value": _value(meta, "graph_domain")}
        for rel, meta, _ in entries
        if _value(meta, "graph_domain") and _value(meta, "graph_domain") not in DOMAINS
    ]
    invalid_roles = [
        {"path": rel, "value": _value(meta, "graph_role")}
        for rel, meta, _ in entries
        if _value(meta, "graph_role") and _value(meta, "graph_role") not in ROLES
    ]
    operational = [(rel, meta) for rel, meta, is_operational in entries if is_operational]
    missing = [
        {
            "path": rel,
            "missing": [key for key in ("graph_domain", "graph_role") if not _value(meta, key)],
        }
        for rel, meta in operational
        if not _value(meta, "graph_domain") or not _value(meta, "graph_role")
    ]
    issues: list[dict[str, str]] = []
    issues.extend(
        {"code": "INVALID_GRAPH_DOMAIN", "path": item["path"], "value": item["value"]}
        for item in invalid_domains
    )
    issues.extend(
        {"code": "INVALID_GRAPH_ROLE", "path": item["path"], "value": item["value"]}
        for item in invalid_roles
    )
    for item in missing:
        for key in item["missing"]:
            issues.append({"code": f"MISSING_{key.upper()}", "path": item["path"], "value": ""})

    domain_counts = Counter(_value(meta, "graph_domain") for _, meta, _ in entries if _value(meta, "graph_domain"))
    role_counts = Counter(_value(meta, "graph_role") for _, meta, _ in entries if _value(meta, "graph_role"))
    operational_domain_count = sum(bool(_value(meta, "graph_domain")) for _, meta in operational)
    operational_role_count = sum(bool(_value(meta, "graph_role")) for _, meta in operational)
    return {
        "schema": SCHEMA,
        "allowed_graph_domains": list(DOMAINS),
        "allowed_graph_roles": list(ROLES),
        "notes": len(entries),
        "notes_with_graph_domain": sum(bool(_value(meta, "graph_domain")) for _, meta, _ in entries),
        "notes_with_graph_role": sum(bool(_value(meta, "graph_role")) for _, meta, _ in entries),
        "canonical_operational_notes": len(operational),
        "canonical_operational_with_graph_domain": operational_domain_count,
        "canonical_operational_with_graph_role": operational_role_count,
        "canonical_operational_missing_visual_metadata": missing,
        "graph_domain_counts": dict(sorted(domain_counts.items())),
        "graph_role_counts": dict(sorted(role_counts.items())),
        "invalid_graph_domains": invalid_domains,
        "invalid_graph_roles": invalid_roles,
        "quality": {"ok": not issues, "error_count": len(issues), "issues": issues},
    }


def _write_report(path: Path, result: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--json", action="store_true", help="print the machine-readable result")
    parser.add_argument("--write-report", type=Path, help="write the deterministic report to this path")
    parser.add_argument("--check-report", type=Path, help="fail if this report differs from the current result")
    args = parser.parse_args()
    result = analyze(args.root)
    if args.write_report:
        _write_report(args.write_report, result)
    if args.check_report:
        try:
            existing = json.loads(args.check_report.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            result["quality"]["issues"].append({"code": "REPORT_UNREADABLE", "path": str(args.check_report), "value": str(exc)})
            result["quality"]["error_count"] += 1
            result["quality"]["ok"] = False
        else:
            if existing != result:
                result["quality"]["issues"].append({"code": "REPORT_DRIFT", "path": str(args.check_report), "value": "report differs from current metadata"})
                result["quality"]["error_count"] += 1
                result["quality"]["ok"] = False
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(
            f"Visual metadata: {result['canonical_operational_with_graph_domain']}/"
            f"{result['canonical_operational_notes']} operational canonical domains, "
            f"{result['canonical_operational_with_graph_role']}/"
            f"{result['canonical_operational_notes']} roles"
        )
        if result["quality"]["issues"]:
            for issue in result["quality"]["issues"]:
                print(f"ERROR {issue['code']} {issue['path']}: {issue['value']}", file=sys.stderr)
    return 0 if result["quality"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
