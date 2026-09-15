from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from memorylib.observer import parse_builder_handoff
from memorylib.semantic_graph import build_semantic_graph, validate_semantic_graph


def write_text(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(root: Path, relative: str, value: dict) -> None:
    write_text(root, relative, json.dumps(value, indent=2, sort_keys=True) + "\n")


class SemanticGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = Path(tempfile.mkdtemp(prefix="sbmem-semantic-graph-"))
        write_json(self.temp, "_meta/MEMORY_V2.json", {
            "memory_version": 2,
            "canonical_updated_at": "2026-09-16T00:00:00Z",
            "source_main_sha": "1" * 40,
        })
        write_text(self.temp, "workstreams/TOP5-SHADOW.md", """---
id: WS-TOP5-SHADOW
type: workstream
status: active
workstream: TOP5-SHADOW
---
# Top-5 Shadow
""")
        write_text(self.temp, "evidence/records/EVD-TEST-001.md", """---
id: EVD-TEST-001
type: evidence
status: current
canonical: true
workstream: TOP5-SHADOW
---
# Evidence
""")
        write_json(self.temp, "events/records/EVT-20260916-001.json", {
            "event_id": "EVT-20260916-001",
            "timestamp": "2026-09-16T00:00:00Z",
            "type": "PR_MERGED",
            "domain": "research/top5",
            "summary": "Explicit structured graph fixture",
            "source_repository": "Philip3006/sportsbrain",
            "source_pr": 59,
            "source_sha": "2" * 40,
            "builder": "Builder 4",
            "builder_number": 4,
            "affected_workstreams": ["TOP5-SHADOW"],
            "findings": [],
            "invariants": ["NO-BET"],
            "supersedes": [],
            "evidence": ["EVD-TEST-001", "GitHub PR #59", "sportsbrain commit " + "3" * 40],
            "ceo_gate_state": "review_required",
            "verification_state": "merged_source",
            "canonical": True,
        })

    def tearDown(self):
        shutil.rmtree(self.temp, ignore_errors=True)

    def test_structured_entities_relations_and_health(self):
        result = build_semantic_graph(self.temp)
        manifest = json.loads((self.temp / "views/graph/GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        entities = {item["entity_key"] for item in manifest["entities"]}
        edges = {(item["source"], item["relation"], item["target"]) for item in manifest["edges"]}
        self.assertIn("EVENT:EVT-20260916-001", entities)
        self.assertIn("PR:philip3006/sportsbrain#59", entities)
        self.assertIn("COMMIT:" + "2" * 40, entities)
        self.assertIn("BUILDER:BUILDER-4", entities)
        self.assertTrue(any(source == "EVENT:EVT-20260916-001" and relation == "source_pr" for source, relation, _ in edges))
        self.assertTrue(any(source == "EVENT:EVT-20260916-001" and relation == "affected_workstream" for source, relation, _ in edges))
        self.assertEqual(result["health"]["baseline"]["edge_count"], 0)
        self.assertGreater(result["health"]["after"]["edge_count"], 0)
        self.assertEqual(validate_semantic_graph(self.temp).errors, 0)

    def test_runtime_candidates_are_noncanonical_and_builder_four_is_independent(self):
        vault = self.temp / "vault"
        handoff = parse_builder_handoff(
            """BUILDER: 4
ROLE: Top-5 Multi-Provider Cascade / Odds Reliability Owner
Branch: feat/builder-four
Head SHA: 4aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
PR: #59
Final status: implementation_complete
Hard Blocker: EXTERNAL provider unavailable
""",
            observed_at="2026-09-16T01:00:00Z",
        )
        write_json(vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "candidates": [handoff]})
        write_json(vault, "_live/SOURCE_CANDIDATES.json", {"schema": 1, "candidates": [{
            "candidate_id": "SRC-CAND-TEST-001",
            "candidate_type": "SOURCE_CANDIDATE_EVENT",
            "canonical": False,
            "promotion_required": True,
            "observed_at": "2026-09-16T01:00:00Z",
            "source_repository": "Philip3006/sportsbrain",
            "source_pr": 59,
            "source_state": "OPEN",
            "source_sha": "5" * 40,
            "source_merge_sha": None,
            "summary": "Candidate PR #59",
            "builder": "SYSTEM",
            "builder_number": "SYSTEM",
            "ceo_gate_state": "candidate_pending_ceo_review",
            "verification_state": "observed_source",
            "affected_workstreams": ["SOURCE-OBSERVER"],
            "findings": [],
            "invariants": ["NO-AUTOMATIC-CANONICAL-PROMOTION"],
            "supersedes": [],
            "evidence": ["GitHub observation of PR #59"],
            "dedupe_key": {"repository": "Philip3006/sportsbrain", "pr": 59, "head_sha": "5" * 40, "merge_sha": None},
        }]})
        write_json(vault, "_live/BLOCKERS.json", {"schema": 1, "blockers": [{
            "blocker_id": "BLK-TEST-001",
            "classification": "EXTERNAL",
            "status": "PRESERVED_UNVERIFIED",
            "summary": "Provider evidence unavailable",
            "auto_resolve": False,
            "source_candidate_id": "SRC-CAND-TEST-001",
        }]})
        result = build_semantic_graph(self.temp, vault=vault, include_runtime=True)
        manifest = json.loads((self.temp / "views/graph/GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        by_key = {item["entity_key"]: item for item in manifest["entities"]}
        self.assertFalse(by_key["EVIDENCE:SRC-CAND-TEST-001"]["canonical"])
        self.assertEqual(by_key["EVIDENCE:SRC-CAND-TEST-001"]["metadata"]["promotion_required"], True)
        self.assertIn("BUILDER:BUILDER-4", by_key)
        self.assertIn("BLOCKER:BLK-TEST-001", by_key)
        self.assertTrue(manifest["runtime_included"])
        self.assertGreater(result["edge_count"], 0)
        self.assertEqual(validate_semantic_graph(self.temp).errors, 0)

    def test_unresolved_reference_is_reported_without_broken_link(self):
        event_path = self.temp / "events/records/EVT-20260916-001.json"
        payload = json.loads(event_path.read_text(encoding="utf-8"))
        payload["verified_by"] = ["VER-MISSING-001"]
        event_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        result = build_semantic_graph(self.temp)
        self.assertGreater(result["unresolved_count"], 0)
        unresolved = json.loads((self.temp / "views/graph/UNRESOLVED_REFERENCES.json").read_text(encoding="utf-8"))["references"]
        self.assertTrue(any(item["raw_target"] == "VER-MISSING-001" for item in unresolved))
        self.assertEqual(validate_semantic_graph(self.temp).errors, 0)

    def test_rebuild_is_byte_stable_and_canonical_event_bytes_are_preserved(self):
        event_path = self.temp / "events/records/EVT-20260916-001.json"
        before = event_path.read_bytes()
        first = build_semantic_graph(self.temp)
        first_bytes = {path.relative_to(self.temp): path.read_bytes() for path in (self.temp / "views/graph").rglob("*") if path.is_file()}
        second = build_semantic_graph(self.temp)
        second_bytes = {path.relative_to(self.temp): path.read_bytes() for path in (self.temp / "views/graph").rglob("*") if path.is_file()}
        self.assertEqual(first["graph_digest"], second["graph_digest"])
        self.assertEqual(first_bytes, second_bytes)
        self.assertEqual(before, event_path.read_bytes())


if __name__ == "__main__":
    unittest.main()
