#!/usr/bin/env python3
"""Graph-quality validation entry point for the operational Memory."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from graph_health import analyze, quality_issues  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = analyze(args.root)
    issues = quality_issues(result)
    print(f"Graph quality: {result['notes']} notes, {result['canonical_notes']} canonical, {result['unique_edges']} unique edges")
    print(f"Components: {result['connected_components']}; largest operational-canonical coverage: {result['largest_component_canonical_operational_pct']}%")
    print(f"Isolates: {result['isolated_node_count']} total / {result['isolated_canonical_count']} operational canonical")
    print(f"Degree-1 canonical: {result['degree_one_canonical_count']}; MOC-only canonical: {result['moc_only_canonical_count']}; broken links: {result['broken_link_count']}")
    for issue in issues:
        print(f"{issue['severity']}: {issue['code']} {issue['message']}")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
