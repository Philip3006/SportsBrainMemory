from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from memorylib.context_compiler import (  # noqa: E402
    ContextCompilerError,
    ContextRequest,
    build_context_atomic,
    compile_context,
    validate_context_pack,
)
from memorylib.observer import parse_builder_handoff  # noqa: E402
from memorylib.semantic_graph import build_semantic_graph_atomic  # noqa: E402


def write_text(root: Path, relative: str, value: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(root: Path, relative: str, value: dict) -> None:
    write_text(root, relative, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_record(root: Path, relative: str, object_id: str, object_type: str, status: str = "active", **fields: object) -> None:
    frontmatter = ["---", f"id: {object_id}", f"type: {object_type}", f"status: {status}"]
    for key, value in fields.items():
        if isinstance(value, list):
            frontmatter.append(f"{key}:")
            frontmatter.extend(f"  - {item}" for item in value)
        else:
            frontmatter.append(f"{key}: {value}")
    frontmatter.extend(["---", f"# {object_id}", "", f"{object_id} authored context."])
    write_text(root, relative, "\n".join(frontmatter) + "\n")


def request(consumer: str, **overrides: object) -> ContextRequest:
    value = {
        "request_id": overrides.pop("request_id", f"TEST-{consumer}"),
        "consumer_type": consumer,
        "task": overrides.pop("task", "focused task"),
        "token_budget": overrides.pop("token_budget", 6000),
        "max_entity_count": overrides.pop("max_entity_count", 80),
        "generated_at": overrides.pop("generated_at", "2026-09-16T12:00:00Z"),
    }
    value.update(overrides)
    return ContextRequest.from_mapping(value)


class ContextCompilerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="sbmem-context-root-"))
        write_json(self.root, "_meta/MEMORY_V2.json", {"memory_version": 2, "canonical_updated_at": "2026-09-16T00:00:00Z"})
        write_record(self.root, "workstreams/ONE.md", "WS-ONE", "workstream", builder="Builder 1", builder_number=1, invariants=["NO-BET"], depends_on=["WS-DEP"])
        write_record(self.root, "workstreams/DEP.md", "WS-DEP", "workstream", builder="Builder 2", builder_number=2)
        write_record(self.root, "workstreams/UNRELATED.md", "WS-UNRELATED", "workstream", builder="Builder 4", builder_number=4)
        write_record(self.root, "decisions/records/DEC-NEW.md", "DEC-NEW", "decision", "active", supersedes=["DEC-OLD"])
        write_record(self.root, "decisions/records/DEC-OLD.md", "DEC-OLD", "decision", "active")
        write_record(self.root, "models/UNRELATED.md", "MOD-UNRELATED", "model", "active", builder="Builder 4", builder_number=4)
        self.vault = Path(tempfile.mkdtemp(prefix="sbmem-context-vault-"))

    def tearDown(self) -> None:
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.vault, ignore_errors=True)

    def _handoff(self, number: int, observed_at: str, status: str = "CURRENT", blocker: str | None = None) -> dict:
        text = f"""BUILDER: {number}
ROLE: Builder {number} operational evidence
Branch: feat/builder-{number}
Head SHA: {'a' * 40}
PR #{50 + number}
Final status: {status}
Tests: 10 passed
CI: green
Observed at: {observed_at}
"""
        if blocker:
            text += f"Hard Blocker: {blocker}\n"
        return parse_builder_handoff(text, observed_at=observed_at)

    def _write_handoffs(self, *handoffs: dict) -> None:
        write_json(self.vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "generated_at": "2026-09-16T12:00:00Z", "candidates": list(handoffs)})

    def test_all_consumer_profiles_and_invalid_builder_fail_closed(self) -> None:
        for consumer in ("CEO", "BUILDER_1", "BUILDER_2", "BUILDER_3", "BUILDER_4", "BUILDER_5", "BUILDER_6", "BUILDER_7", "GENERIC_REVIEW"):
            compiled = compile_context(self.root, request(consumer))
            self.assertEqual(compiled.pack["consumer"], consumer)
            self.assertLessEqual(compiled.pack["estimated_tokens"], 6000)
        with self.assertRaises(ContextCompilerError):
            request("BUILDER_8")
        with self.assertRaises(ContextCompilerError):
            ContextRequest.from_mapping({"request_id": "bad", "consumer_type": "BUILDER_4", "builder_number": 1})

    def test_explicit_seed_direct_dependency_and_unrelated_branch_excluded(self) -> None:
        compiled = compile_context(self.root, request("BUILDER_1", entity_seeds=["WS-ONE"], task="", workstream=""))
        ids = {item["entity_id"] for item in compiled.pack["included_entities"]}
        self.assertIn("WORKSTREAM:WS-ONE", ids)
        self.assertIn("WORKSTREAM:WS-DEP", ids)
        self.assertNotIn("WORKSTREAM:WS-UNRELATED", ids)
        self.assertTrue(any(edge["target"] == "WORKSTREAM:WS-DEP" for edge in compiled.pack["included_edges"]))

    def test_builder1_cross_builder_contract_and_builder4_boundary(self) -> None:
        write_record(self.root, "workstreams/B2-CONTRACT.md", "WS-B2-CONTRACT", "workstream", builder="Builder 2", builder_number=2)
        write_text(self.root / "workstreams", "B2-CONTRACT.md", "---\nid: WS-B2-CONTRACT\ntype: workstream\nstatus: active\nbuilder: Builder 2\nbuilder_number: 2\n---\n# Provider validation interface contract\n")
        compiled = compile_context(self.root, request("BUILDER_1", entity_seeds=["WS-ONE"], token_budget=12000))
        ids = {item["entity_id"] for item in compiled.pack["included_entities"]}
        self.assertIn("BUILDER:BUILDER-2", ids)
        self.assertIn("BUILDER:BUILDER-4", ids)
        self.assertNotIn("MODEL:MOD-UNRELATED", ids)

    def test_runtime_current_candidate_unknown_stale_and_conflicting(self) -> None:
        current = self._handoff(4, "2026-09-16T11:00:00Z", "RELIABILITY READY", "provider credential unavailable")
        self._write_handoffs(current)
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        compiled = compile_context(self.root, request("BUILDER_4", include_runtime=True), vault=self.vault)
        self.assertTrue(compiled.pack["graph_available"])
        self.assertGreater(compiled.pack["runtime_count"], 0)
        handoff_items = [item for item in compiled.pack["included_entities"] if item["entity_id"].startswith("EVIDENCE:")]
        self.assertTrue(handoff_items)
        self.assertTrue(all(item["canonical"] is False and item["promotion_required"] is True for item in handoff_items))
        self.assertEqual(compiled.pack["freshness_state"], "FRESH")
        stale = compile_context(self.root, request("BUILDER_4", include_runtime=True, generated_at="2026-09-17T12:00:00Z"), vault=self.vault)
        self.assertEqual(stale.pack["freshness_state"], "STALE")
        self.assertTrue(any("STALE" in warning for warning in stale.pack["warnings"]))
        self.assertNotEqual(compiled.pack["context_digest"], stale.pack["context_digest"])
        self.assertNotEqual(compiled.pack["cache_key"], stale.pack["cache_key"])
        write_json(self.vault, "_live/SOURCE_OBSERVER.json", {"schema": 1, "conflicts": [{"type": "STATUS_CONFLICT", "severity": "CEO_DECISION_REQUIRED"}], "candidates": []})
        conflict = compile_context(self.root, request("BUILDER_4", include_runtime=True), vault=self.vault)
        self.assertEqual(conflict.pack["freshness_state"], "CONFLICTING")
        self.assertIn("CONFLICTING EVIDENCE", conflict.markdown)

    def test_runtime_graph_unavailable_falls_back_explicitly(self) -> None:
        self._write_handoffs(self._handoff(4, "2026-09-16T11:00:00Z"))
        compiled = compile_context(self.root, request("BUILDER_4", include_runtime=True), vault=self.vault)
        self.assertFalse(compiled.pack["graph_available"])
        self.assertEqual(compiled.pack["runtime_count"], 0)
        self.assertIsNone(compiled.pack["runtime_digest"])
        self.assertTrue(any("runtime context withheld" in warning for warning in compiled.pack["warnings"]))
        self.assertFalse(any(item.get("candidate_type") in {"SOURCE_CANDIDATE_EVENT", "CANDIDATE_OPERATIONAL_EVIDENCE"} for item in compiled.pack["included_entities"]))
        write_json(self.vault, "_live/graph/GRAPH_MANIFEST.json", {"schema": 2, "noncanonical_view": True})
        invalid_graph = compile_context(self.root, request("BUILDER_4", include_runtime=True), vault=self.vault)
        self.assertFalse(invalid_graph.pack["graph_available"])
        self.assertEqual(invalid_graph.pack["runtime_count"], 0)

    def test_missing_runtime_builder_is_explicit_unknown(self) -> None:
        compiled = compile_context(self.root, request("BUILDER_4", include_runtime=True), vault=self.vault)
        builders = [item for item in compiled.pack["included_entities"] if item["entity_id"] == "BUILDER:BUILDER-4"]
        self.assertEqual(len(builders), 1)
        self.assertEqual(builders[0]["runtime_status"]["state"], "UNKNOWN")
        self.assertIn("UNKNOWN / NO CURRENT HANDOFF EVIDENCE", compiled.markdown)

    def test_latest_runtime_evidence_is_independent_for_builders_one_to_four(self) -> None:
        handoffs = [self._handoff(number, f"2026-09-16T0{number}:00:00Z", f"BUILDER {number} CURRENT") for number in range(1, 5)]
        self._write_handoffs(*handoffs)
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        compiled = compile_context(self.root, request("CEO", include_runtime=True), vault=self.vault)
        status = {item["entity_id"]: item.get("runtime_status") for item in compiled.pack["included_entities"] if item["entity_id"].startswith("BUILDER:")}
        for number in range(1, 5):
            self.assertIn(f"BUILDER:BUILDER-{number}", status)
            self.assertEqual(status[f"BUILDER:BUILDER-{number}"]["status"], f"BUILDER {number} CURRENT")

    def test_repository_scope_and_current_corpus_performance(self) -> None:
        write_record(self.root, "workstreams/REPO-A.md", "WS-REPO-A", "workstream", source_repository="repo-a")
        write_record(self.root, "workstreams/REPO-B.md", "WS-REPO-B", "workstream", source_repository="repo-b")
        scoped = compile_context(self.root, request("GENERIC_REVIEW", entity_seeds=["WS-REPO-A"], repository_scope=["repo-a"]))
        ids = {item["entity_id"] for item in scoped.pack["included_entities"]}
        self.assertIn("WORKSTREAM:WS-REPO-A", ids)
        self.assertNotIn("WORKSTREAM:WS-REPO-B", ids)
        started = time.perf_counter()
        current = compile_context(ROOT, request("BUILDER_3", task="Memory graph context", token_budget=12000, max_entity_count=140))
        self.assertLess(time.perf_counter() - started, 8.0)
        self.assertLessEqual(current.pack["estimated_tokens"], 12000)

    def test_larger_synthetic_corpus_is_indexed_without_pairwise_scan(self) -> None:
        for index in range(500):
            write_record(self.root, f"workstreams/SYN-{index:04d}.md", f"WS-SYN-{index:04d}", "workstream", source_repository="synthetic")
        started = time.perf_counter()
        compiled = compile_context(self.root, request("GENERIC_REVIEW", entity_seeds=["WS-SYN-0001"], token_budget=6000, max_entity_count=40))
        self.assertLess(time.perf_counter() - started, 8.0)
        self.assertIn("WORKSTREAM:WS-SYN-0001", {item["entity_id"] for item in compiled.pack["included_entities"]})

    def test_authority_supersession_and_safety_survive_budget_truncation(self) -> None:
        compiled = compile_context(self.root, request("BUILDER_1", entity_seeds=["DEC-NEW"], token_budget=900, max_entity_count=4))
        self.assertTrue(compiled.pack["truncated"])
        self.assertLessEqual(compiled.pack["estimated_tokens"], 900)
        ids = {item["entity_id"] for item in compiled.pack["included_entities"]}
        self.assertIn("DECISION:DEC-NEW", ids)
        self.assertTrue(any(item["namespace"] == "INVARIANT" for item in compiled.pack["included_entities"]))

    def test_semantic_digest_ignores_generated_at_but_changes_selected_source(self) -> None:
        first = compile_context(self.root, request("BUILDER_1", entity_seeds=["WS-ONE"], generated_at="2026-09-16T10:00:00Z"))
        second = compile_context(self.root, request("BUILDER_1", entity_seeds=["WS-ONE"], generated_at="2026-09-16T11:00:00Z"))
        self.assertEqual(first.pack["context_digest"], second.pack["context_digest"])
        self.assertNotEqual(first.pack["cache_key"], second.pack["cache_key"])
        write_text(self.root, "workstreams/ONE.md", (self.root / "workstreams/ONE.md").read_text(encoding="utf-8").replace("WS-ONE authored context", "WS-ONE changed verified context"))
        third = compile_context(self.root, request("BUILDER_1", entity_seeds=["WS-ONE"], generated_at="2026-09-16T11:00:00Z"))
        self.assertNotEqual(first.pack["context_digest"], third.pack["context_digest"])

    def test_mandatory_safety_blockers_and_decision_priority(self) -> None:
        write_record(self.root, "invariants/INV-SAFETY.md", "INV-SAFETY", "invariant", "active", summary="NO-BET and sealed 2425/2526 remain enforced")
        write_record(self.root, "findings/records/BLK-CANON.md", "BLK-CANON", "blocker", "active", classification="HARD", summary="canonical release gate remains open")
        write_record(self.root, "decisions/records/DEC-GOV.md", "DEC-GOV", "decision", "active", summary="CEO decision governs the release boundary")
        self._write_handoffs(self._handoff(4, "2026-09-16T11:00:00Z", "CURRENT", "provider credential unavailable"))
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        compiled = compile_context(
            self.root,
            request("BUILDER_4", include_runtime=True, max_entity_count=4, token_budget=12000),
            vault=self.vault,
        )
        included = compiled.pack["included_entities"]
        ids = {item["entity_id"] for item in included}
        self.assertIn("INVARIANT:INV-SAFETY", ids)
        self.assertIn("FINDING:BLK-CANON", ids)
        self.assertTrue(any(item["entity_id"] == "FINDING:BLK-CANON" and item["namespace"] == "BLOCKER" and item["authority_class"] == "CANONICAL" for item in included))
        self.assertTrue(any(item["namespace"] == "BLOCKER" and item["authority_class"] == "RUNTIME_DERIVED" for item in included))
        self.assertLessEqual(compiled.pack["included_entity_count"], 4)
        self.assertTrue(compiled.pack["truncated"])

        focused = compile_context(
            self.root,
            request("BUILDER_4", include_runtime=True, entity_seeds=["DEC-NEW"], max_entity_count=5, token_budget=12000),
            vault=self.vault,
        )
        focused_ids = {item["entity_id"] for item in focused.pack["included_entities"]}
        self.assertIn("DECISION:DEC-NEW", focused_ids)
        self.assertNotIn("DECISION:DEC-OLD", focused_ids)
        self.assertGreater(focused.pack["candidate_entity_count"], focused.pack["included_entity_count"])

        ceo = compile_context(self.root, request("CEO", include_runtime=True, max_entity_count=20, token_budget=12000), vault=self.vault)
        self.assertIn("DECISION:DEC-GOV", {item["entity_id"] for item in ceo.pack["included_entities"]})

    def test_impossible_mandatory_budget_fails_closed(self) -> None:
        write_record(self.root, "invariants/INV-SAFETY.md", "INV-SAFETY", "invariant", "active", summary="NO-BET and sealed 2425/2526 remain enforced")
        write_record(self.root, "findings/records/BLK-CANON.md", "BLK-CANON", "blocker", "active", classification="HARD", summary="canonical release gate remains open")
        self._write_handoffs(self._handoff(4, "2026-09-16T11:00:00Z", "CURRENT", "provider credential unavailable"))
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        with self.assertRaisesRegex(ContextCompilerError, "mandatory"):
            compile_context(
                self.root,
                request("BUILDER_4", include_runtime=True, max_entity_count=2, token_budget=12000),
                vault=self.vault,
            )

    def test_external_output_guard_rejects_checkout_paths_and_preserves_last_good(self) -> None:
        result = build_context_atomic(self.root, request("BUILDER_3", request_id="CTX-GUARD"), vault=self.vault)
        output = Path(result["json"])
        before = output.read_bytes()
        invalid_paths = [self.root, self.root / "nested-vault"]
        alias = self.root.parent / f"{self.root.name}-alias"
        alias.symlink_to(self.root, target_is_directory=True)
        invalid_paths.append(alias)
        try:
            for invalid in invalid_paths:
                with self.assertRaisesRegex(ContextCompilerError, "outside the canonical Memory checkout"):
                    build_context_atomic(self.root, request("BUILDER_3", request_id="CTX-GUARD"), vault=invalid)
                self.assertEqual(output.read_bytes(), before)
        finally:
            alias.unlink(missing_ok=True)

    def test_atomic_output_validation_and_last_good_preservation(self) -> None:
        req = request("BUILDER_3", entity_seeds=["WS-ONE"], request_id="CTX-ATOMIC")
        result = build_context_atomic(self.root, req, vault=self.vault)
        json_path = Path(result["json"])
        before = json_path.read_bytes()
        write_json(self.vault, "_live/SOURCE_OBSERVER.json", {"api_key": "ghp_" + "x" * 30})
        with self.assertRaises(ContextCompilerError):
            build_context_atomic(self.root, request("BUILDER_3", entity_seeds=["WS-ONE"], request_id="CTX-ATOMIC", include_runtime=True), vault=self.vault)
        self.assertEqual(json_path.read_bytes(), before)
        self.assertEqual(validate_context_pack(json_path)["context_digest"], result["context_digest"])
        self.assertFalse(list(self.vault.glob(".context-build-*")))

    def test_secret_scanning_rejects_context_fields(self) -> None:
        # The rejection is exercised by runtime payloads to avoid mutating
        # canonical source in this regression.
        write_json(self.vault, "_live/SOURCE_OBSERVER.json", {"authorization": "Bearer " + "x" * 30})
        with self.assertRaises(ContextCompilerError):
            compile_context(self.root, request("CEO", include_runtime=True), vault=self.vault)

    def test_pack_validate_and_no_canonical_mutation(self) -> None:
        before = {path.relative_to(self.root): path.read_bytes() for path in (self.root / "events").rglob("*") if path.is_file()} if (self.root / "events").exists() else {}
        result = build_context_atomic(self.root, request("CEO", request_id="CTX-VALIDATE"), vault=self.vault)
        validate_context_pack(Path(result["json"]))
        after = {path.relative_to(self.root): path.read_bytes() for path in (self.root / "events").rglob("*") if path.is_file()} if (self.root / "events").exists() else {}
        self.assertEqual(before, after)
        self.assertTrue((self.vault / "_live/context/CTX-VALIDATE.md").exists())


if __name__ == "__main__":
    unittest.main()
