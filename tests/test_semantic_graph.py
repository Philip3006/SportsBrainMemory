from __future__ import annotations

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from memorylib.observer import parse_builder_handoff
from memorylib.semantic_graph import (
    build_semantic_graph,
    build_semantic_graph_atomic,
    render_semantic_graph,
    validate_semantic_graph,
)


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
        result = build_semantic_graph(self.temp, vault=vault, include_runtime=True, reference_time="2026-09-16T02:00:00Z")
        manifest = json.loads((vault / "_live/graph/GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        by_key = {item["entity_key"]: item for item in manifest["entities"]}
        self.assertFalse(by_key["EVIDENCE:SRC-CAND-TEST-001"]["canonical"])
        self.assertEqual(by_key["EVIDENCE:SRC-CAND-TEST-001"]["metadata"]["promotion_required"], True)
        self.assertIn("BUILDER:BUILDER-4", by_key)
        self.assertIn("BLOCKER:BLK-TEST-001", by_key)
        self.assertTrue(manifest["runtime_included"])
        self.assertGreater(result["edge_count"], 0)
        self.assertEqual(manifest["generated_location"], "_live/graph")
        self.assertEqual(validate_semantic_graph(self.temp, vault=vault).errors, 0)
        self.assertFalse((self.temp / "views/graph").exists())

    def test_canonical_only_projection_contains_no_runtime_snapshot(self):
        output = self.temp / "canonical-projection"
        result = build_semantic_graph(self.temp, output_root=output)
        manifest = json.loads((output / "GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertFalse(manifest["runtime_included"])
        self.assertEqual(result["output"], str(output.resolve()))
        self.assertFalse(any(item.get("provenance") == "RUNTIME_DERIVED" for item in manifest["entities"]))
        self.assertEqual(validate_semantic_graph(self.temp, output).errors, 0)

    def test_arbitrary_output_root_writes_all_files_and_links_resolve_there(self):
        output = self.temp / "arbitrary" / "graph"
        build_semantic_graph(self.temp, output_root=output)
        files = {path.relative_to(output).as_posix() for path in output.rglob("*") if path.is_file()}
        self.assertIn("GRAPH_MANIFEST.json", files)
        self.assertIn("00_GRAPH_HOME.md", files)
        self.assertTrue(any(path.startswith("entities/") for path in files))
        manifest = json.loads((output / "GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["generated_location"], "arbitrary/graph")
        self.assertTrue(all(item["target"].startswith("arbitrary/graph/") for item in manifest["entities"]))
        self.assertEqual(validate_semantic_graph(self.temp, output).errors, 0)

    def test_runtime_refresh_is_current_and_atomic(self):
        vault = self.temp / "vault"
        live = vault / "_live"
        first = build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-16T01:00:00Z")
        self.assertEqual(first["validation"]["errors"], 0)
        builder_moc = (live / "graph/MOC-BUILDERS.md").read_text(encoding="utf-8")
        self.assertIn("Builder 4", builder_moc)
        self.assertIn("UNKNOWN / NO CURRENT HANDOFF EVIDENCE", builder_moc)

        handoff_a = parse_builder_handoff(
            """BUILDER: 4
ROLE: Top-5 Multi-Provider Cascade / Odds Reliability Owner
Branch: feat/provider-cascade
Head SHA: 4aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
PR: #59
Final status: BLOCKED
Hard Blocker: quota exhausted
""",
            observed_at="2026-09-16T01:00:00Z",
        )
        handoff_b = parse_builder_handoff(
            """BUILDER: 4
ROLE: Top-5 Multi-Provider Cascade / Odds Reliability Owner
Branch: feat/provider-cascade
Head SHA: 4aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
PR: #59
Final status: BLOCKED
Hard Blocker: credential invalid
""",
            observed_at="2026-09-16T02:00:00Z",
        )
        write_json(live, "BUILDER_HANDOFFS.json", {"schema": 1, "candidates": [handoff_a, handoff_b]})
        write_json(live, "SOURCE_CANDIDATES.json", {"schema": 1, "candidates": [{
            "candidate_id": "SRC-CAND-TEST-002",
            "candidate_type": "SOURCE_CANDIDATE_EVENT",
            "canonical": False,
            "promotion_required": True,
            "observed_at": "2026-09-16T02:00:00Z",
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
        current = build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-16T03:00:00Z")
        manifest = json.loads((live / "graph/GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        by_key = {item["entity_key"]: item for item in manifest["entities"]}
        self.assertEqual(by_key["BUILDER:BUILDER-4"]["metadata"]["current_evidence"]["status"], "BLOCKED")
        self.assertEqual(by_key["BUILDER:BUILDER-4"]["metadata"]["current_evidence"]["freshness"], "FRESH")
        self.assertIn("EVIDENCE:" + handoff_b["candidate_id"], by_key)
        self.assertIn("EVIDENCE:" + handoff_a["candidate_id"], by_key)
        self.assertFalse(by_key["EVIDENCE:SRC-CAND-TEST-002"]["canonical"])
        self.assertTrue(by_key["EVIDENCE:SRC-CAND-TEST-002"]["metadata"]["promotion_required"])
        self.assertEqual(validate_semantic_graph(self.temp, vault=vault).errors, 0)
        self.assertGreater(current["edge_count"], 0)

        stale = build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-17T03:00:00Z")
        stale_manifest = json.loads((live / "graph/GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        stale_builder = {item["entity_key"]: item for item in stale_manifest["entities"]}["BUILDER:BUILDER-4"]
        self.assertEqual(stale_builder["metadata"]["current_evidence"]["freshness"], "STALE")
        self.assertNotEqual(current["graph_digest"], stale["graph_digest"])

    def test_failed_runtime_generation_preserves_last_good_graph_and_no_partial_graph(self):
        vault = self.temp / "vault"
        build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-16T01:00:00Z")
        sentinel = vault / "_live/graph/LAST_GOOD_SENTINEL"
        sentinel.write_text("last good", encoding="utf-8")
        original = render_semantic_graph

        def broken(graph, output_root=None):
            result = original(graph, output_root)
            (Path(result["output"]) / "GRAPH_MANIFEST.json").write_text("{invalid", encoding="utf-8")
            return result

        with patch("memorylib.semantic_graph.render_semantic_graph", side_effect=broken):
            with self.assertRaises(Exception):
                build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-16T02:00:00Z")
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "last good")
        self.assertEqual(json.loads((vault / "_live/SEMANTIC_GRAPH_STATUS.json").read_text(encoding="utf-8"))["status"], "DEGRADED")
        self.assertFalse(list((vault / "_live").glob(".graph-build-*")))
        self.assertEqual(validate_semantic_graph(self.temp, vault=vault).errors, 0)

    def test_canonical_change_requires_rebuild_then_validates(self):
        output = self.temp / "canonical-projection"
        first = build_semantic_graph(self.temp, output_root=output)
        event_path = self.temp / "events/records/EVT-20260916-001.json"
        payload = json.loads(event_path.read_text(encoding="utf-8"))
        payload["summary"] = "Canonical graph update"
        event_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assertGreater(validate_semantic_graph(self.temp, output).errors, 0)
        second = build_semantic_graph(self.temp, output_root=output)
        self.assertNotEqual(first["graph_digest"], second["graph_digest"])
        self.assertEqual(validate_semantic_graph(self.temp, output).errors, 0)

    def test_runtime_rerun_is_digest_and_byte_stable_for_identical_inputs(self):
        vault = self.temp / "vault"
        first = build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-16T02:00:00Z")
        first_bytes = {path.relative_to(vault / "_live/graph"): path.read_bytes() for path in (vault / "_live/graph").rglob("*") if path.is_file()}
        second = build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-16T02:00:00Z")
        second_bytes = {path.relative_to(vault / "_live/graph"): path.read_bytes() for path in (vault / "_live/graph").rglob("*") if path.is_file()}
        self.assertEqual(first["graph_digest"], second["graph_digest"])
        self.assertEqual(first_bytes, second_bytes)

    def test_runtime_builder_one_to_four_are_selected_independently(self):
        vault = self.temp / "vault"
        handoffs = []
        for number in range(1, 5):
            handoffs.append(parse_builder_handoff(
                f"""BUILDER: {number}
ROLE: Runtime Builder {number}
Branch: feat/builder-{number}
Head SHA: {str(number) * 40}
PR: #{50 + number}
Final status: BUILDER {number} CURRENT
""",
                observed_at=f"2026-09-16T0{number}:00:00Z",
            ))
        write_json(vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "candidates": handoffs})
        build_semantic_graph_atomic(self.temp, vault, reference_time="2026-09-16T05:00:00Z")
        manifest = json.loads((vault / "_live/graph/GRAPH_MANIFEST.json").read_text(encoding="utf-8"))
        by_key = {item["entity_key"]: item for item in manifest["entities"]}
        for number in range(1, 5):
            current = by_key[f"BUILDER:BUILDER-{number}"]["metadata"]["current_evidence"]
            self.assertEqual(current["status"], f"BUILDER {number} CURRENT")
            self.assertEqual(current["branch"], f"feat/builder-{number}")
            self.assertEqual(current["freshness"], "FRESH")
        self.assertEqual(validate_semantic_graph(self.temp, vault=vault).errors, 0)

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
