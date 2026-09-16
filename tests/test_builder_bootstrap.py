from __future__ import annotations

import json
import copy
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from memorylib.builder_bootstrap import (  # noqa: E402
    BOOTSTRAP_VERSION,
    BUILDER_ROLES,
    BuilderBootstrapError,
    BuilderBootstrapRequest,
    BuilderBootstrapValidationError,
    _bootstrap_digest,
    build_builder_bootstrap_atomic,
    compile_builder_bootstrap,
    inspect_builder_bootstrap,
    validate_builder_bootstrap,
)
from memorylib.context_compiler import ContextCompilerError  # noqa: E402
from memorylib.observer import FixtureGitHubClient, handoff_evidence_id, ingest_handoff, observe_sources, parse_builder_handoff  # noqa: E402
from memorylib.semantic_graph import build_semantic_graph_atomic  # noqa: E402


def write_text(root: Path, relative: str, value: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_json(root: Path, relative: str, value: object) -> None:
    write_text(root, relative, json.dumps(value, indent=2, sort_keys=True) + "\n")


def write_record(root: Path, relative: str, object_id: str, object_type: str, status: str = "active", **fields: object) -> None:
    lines = ["---", f"id: {object_id}", f"type: {object_type}", f"status: {status}"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"{key}: {value}")
    lines.extend(["---", f"# {object_id}", "", f"{object_id} authored context."])
    write_text(root, relative, "\n".join(lines) + "\n")


class BuilderBootstrapTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="sbmem-bootstrap-root-"))
        self.vault = Path(tempfile.mkdtemp(prefix="sbmem-bootstrap-vault-"))
        write_json(self.root, "_meta/MEMORY_V2.json", {
            "memory_version": 2,
            "canonical_updated_at": "2026-09-16T00:00:00Z",
            "source_latest_meaningful_at": "2026-09-16T00:00:00Z",
            "frozen_research_sha": "6eaabbec7d0182103d815c72fae4976e261b40aa",
        })
        write_record(self.root, "workstreams/ONE.md", "WS-ONE", "workstream", builder="Builder 1", builder_number=1, depends_on=["WS-DEP"], invariants=["INV-SAFETY"])
        write_record(self.root, "workstreams/DEP.md", "WS-DEP", "workstream", builder="Builder 2", builder_number=2)
        write_record(self.root, "workstreams/CONTRACT.md", "WS-CONTRACT", "workstream", builder="Builder 2", builder_number=2, summary="Builder contract verification interface")
        write_record(self.root, "invariants/SAFETY.md", "INV-SAFETY", "invariant", summary="NO-BET, no live activation, and sealed 2425/2526 remain enforced")
        write_record(self.root, "decisions/records/CEO.md", "DEC-CEO", "decision", "active", summary="CEO decision required for the release boundary")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.vault, ignore_errors=True)

    def request(self, number: int, **overrides: object) -> BuilderBootstrapRequest:
        value = {
            "bootstrap_id": f"BOOT-B{number}",
            "builder_number": number,
            "task_id": f"TASK-B{number}",
            "task": "deterministic bootstrap validation",
            "workstream": "Memory Context Delivery",
            "token_budget": 12000,
            "max_entity_count": 80,
            "generated_at": "2026-09-16T12:00:00Z",
        }
        value.update(overrides)
        return BuilderBootstrapRequest.from_mapping(value)

    def handoff(self, number: int, observed_at: str, role: str | None = None, blocker: str | None = None) -> dict:
        blocker_line = f"Hard Blocker: {blocker}\n" if blocker else "Blockers: none\n"
        return parse_builder_handoff(
            f"""BUILDER: {number}
ROLE: {role or BUILDER_ROLES[number]}
Branch: feat/builder-{number}
Head SHA: {'a' * 40}
PR #{50 + number}
Final status: READY FOR CEO REVIEW
Tests: 58 passed
CI: green
{blocker_line}Observed at: {observed_at}
""",
            observed_at=observed_at,
        )

    def write_handoffs(self, *handoffs: dict) -> None:
        write_json(self.vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "candidates": list(handoffs)})

    def test_builders_one_to_seven_and_invalid_identity(self) -> None:
        for number in range(1, 8):
            pack = compile_builder_bootstrap(self.root, self.request(number)).pack
            self.assertEqual(pack["builder"]["number"], number)
            self.assertEqual(pack["builder"]["role_baseline"], BUILDER_ROLES[number])
            self.assertEqual(pack["context_pack"]["consumer"], f"BUILDER_{number}")
        for invalid in (0, 8, "four", "1/4", "BUILDER: 1/4"):
            with self.assertRaises(BuilderBootstrapError):
                BuilderBootstrapRequest.from_mapping({"builder": invalid, "task_id": "TASK-BAD"})
        self.assertEqual(parse_builder_handoff("BUILDER: 4\nROLE: Provider\nStatus: ready")["builder_number"], 4)
        self.assertEqual(parse_builder_handoff("BUILDER: 7\nROLE: Reliability\nStatus: ready")["builder_number"], 7)

    def test_metadata_scope_prohibited_and_verification_contract(self) -> None:
        pack = compile_builder_bootstrap(self.root, self.request(
            5,
            task_metadata={"requested_domains": ["pwa"], "entity_seeds": ["WS-ONE"]},
            repository_scope=["Philip3006/SportsBrainMemory"],
            path_scope=["tools/memorylib"],
            required_dependencies=["WS-DEP"],
            prohibited_operations=["change external production"],
            verification_requirements=["verify no generated canonical changes"],
        )).pack
        self.assertEqual(pack["allowed_scope"], {"repositories": ["Philip3006/SportsBrainMemory"], "paths": ["tools/memorylib"]})
        self.assertIn("change external production", pack["prohibited_operations"])
        self.assertIn("verify no generated canonical changes", pack["verification_requirements"])
        self.assertEqual(pack["task_identity"]["metadata"]["requested_domains"], ["pwa"])

    def test_missing_dependency_is_explicit(self) -> None:
        pack = compile_builder_bootstrap(self.root, self.request(6, required_dependencies=["WS-NOT-PRESENT"])).pack
        self.assertEqual(pack["required_dependency_status"][0]["status"], "MISSING")
        self.assertEqual(pack["missing_dependencies"], [{"dependency": "WS-NOT-PRESENT", "required": True, "status": "MISSING"}])
        self.assertIn("MISSING_DEPENDENCY", pack["review_flags"])

    def test_dependency_authority_statuses_are_distinct(self) -> None:
        verified_path = "verifications/records/VER-BOOTSTRAP.md"
        write_record(self.root, verified_path, "VER-BOOTSTRAP", "verification", "verified", summary="Verified dependency")
        canonical = compile_builder_bootstrap(self.root, self.request(1, required_dependencies=["WS-DEP"])).pack
        verified = compile_builder_bootstrap(self.root, self.request(1, required_dependencies=["VER-BOOTSTRAP"])).pack
        self.write_handoffs(self.handoff(1, "2026-09-16T11:00:00Z"))
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        candidate_id = json.loads(json.dumps(self.handoff(1, "2026-09-16T11:00:00Z")))["candidate_id"]
        # Reuse the exact handoff identity written into the runtime graph.
        candidate = json.loads((self.vault / "_live/BUILDER_HANDOFFS.json").read_text(encoding="utf-8"))["candidates"][0]
        self.assertEqual(candidate_id, candidate["candidate_id"])
        candidate_only = compile_builder_bootstrap(self.root, self.request(1, required_dependencies=[candidate_id], include_runtime=True), vault=self.vault).pack
        self.assertEqual(canonical["required_dependency_status"][0]["status"], "SATISFIED_AUTHORITATIVE")
        self.assertEqual(verified["required_dependency_status"][0]["status"], "SATISFIED_AUTHORITATIVE")
        self.assertEqual(candidate_only["required_dependency_status"][0]["status"], "PRESENT_NONAUTHORITATIVE")
        self.assertIn("DEPENDENCY_AUTHORITY_MISSING", candidate_only["review_flags"])
        self.assertFalse(candidate_only["authoritative_dependencies"] and any(entry.get("entity_id") == f"EVIDENCE:{candidate_id}" for entry in candidate_only["authoritative_dependencies"]))

        runtime_id = "BLK-BOOTSTRAP-RUNTIME"
        write_json(self.vault, "_live/BLOCKERS.json", {"schema": 1, "blockers": [{
            "blocker_id": runtime_id, "classification": "EXTERNAL", "status": "OPEN",
            "summary": "runtime-only dependency", "auto_resolve": False,
        }]})
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        runtime_only = compile_builder_bootstrap(self.root, self.request(1, required_dependencies=[f"BLOCKER:{runtime_id}"], include_runtime=True), vault=self.vault).pack
        self.assertEqual(runtime_only["required_dependency_status"][0]["status"], "PRESENT_NONAUTHORITATIVE")
        self.assertIn("DEPENDENCY_AUTHORITY_MISSING", runtime_only["review_flags"])

    def test_dependency_status_and_digest_ordering_are_deterministic(self) -> None:
        first = compile_builder_bootstrap(self.root, self.request(2, required_dependencies=["WS-DEP", "WS-MISSING"])).pack
        second = compile_builder_bootstrap(self.root, self.request(2, required_dependencies=["WS-MISSING", "WS-DEP"])).pack
        self.assertEqual(first["required_dependency_status"], second["required_dependency_status"])
        self.assertEqual(first["missing_dependencies"], second["missing_dependencies"])
        self.assertEqual(first["bootstrap_digest"], second["bootstrap_digest"])

    def test_runtime_unavailable_is_explicit_and_candidates_never_canonical(self) -> None:
        self.write_handoffs(self.handoff(7, "2026-09-16T11:00:00Z", blocker="provider outage"))
        pack = compile_builder_bootstrap(self.root, self.request(7, include_runtime=True), vault=self.vault).pack
        self.assertFalse(pack["context_pack"]["graph_available"])
        self.assertEqual(pack["context_pack"]["runtime_count"], 0)
        self.assertIn("RUNTIME_GRAPH_UNAVAILABLE", pack["review_flags"])
        self.assertFalse(any(item.get("candidate_type") in {"CANDIDATE_OPERATIONAL_EVIDENCE", "SOURCE_CANDIDATE_EVENT"} for item in pack["context_pack"]["included_entities"]))

    def test_stale_and_conflicting_context_are_visible(self) -> None:
        self.write_handoffs(self.handoff(7, "2026-09-14T00:00:00Z"))
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        write_json(self.vault, "_live/SOURCE_OBSERVER.json", {"schema": 1, "conflicts": [{"type": "STATUS_CONFLICT", "severity": "CEO_DECISION_REQUIRED"}], "candidates": []})
        pack = compile_builder_bootstrap(self.root, self.request(7, include_runtime=True), vault=self.vault).pack
        self.assertIn("STALE_EVIDENCE", pack["review_flags"])
        self.assertIn("CONTEXT_CONFLICT", pack["review_flags"])
        self.assertTrue(pack["stale_evidence"])
        self.assertTrue(pack["conflicting_evidence"])

    def test_mandatory_conflict_fails_closed(self) -> None:
        self.write_handoffs(self.handoff(7, "2026-09-16T11:00:00Z"))
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        write_json(self.vault, "_live/SOURCE_OBSERVER.json", {"schema": 1, "conflicts": [{"mandatory": True, "type": "BLOCKER_CONFLICT", "severity": "CEO_DECISION_REQUIRED"}], "candidates": []})
        with self.assertRaisesRegex(BuilderBootstrapError, "mandatory context conflict"):
            compile_builder_bootstrap(self.root, self.request(7, include_runtime=True), vault=self.vault)

    def test_semantic_determinism_and_source_sha_change(self) -> None:
        first = compile_builder_bootstrap(self.root, self.request(3, generated_at="2026-09-16T10:00:00Z")).pack
        second = compile_builder_bootstrap(self.root, self.request(3, generated_at="2026-09-16T11:00:00Z")).pack
        self.assertEqual(first["semantic_digest"], second["semantic_digest"])
        self.assertEqual(first["bootstrap_digest"], second["bootstrap_digest"])
        self.assertNotEqual(first["context_pack"]["cache_key"], second["context_pack"]["cache_key"])
        write_text(self.root, "workstreams/ONE.md", (self.root / "workstreams/ONE.md").read_text(encoding="utf-8").replace("WS-ONE authored context", "WS-ONE changed source context"))
        changed = compile_builder_bootstrap(self.root, self.request(3)).pack
        self.assertNotEqual(first["source_memory_sha"], changed["source_memory_sha"])
        self.assertNotEqual(first["bootstrap_digest"], changed["bootstrap_digest"])

    def test_secret_rejection(self) -> None:
        with self.assertRaises(ContextCompilerError):
            self.request(1, task_metadata={"api_key": "not permitted"})
        write_json(self.vault, "_live/SOURCE_OBSERVER.json", {"authorization": "Bearer " + "x" * 30})
        with self.assertRaises(ContextCompilerError):
            compile_builder_bootstrap(self.root, self.request(3, include_runtime=True), vault=self.vault)

    def test_external_atomic_output_and_canonical_history_safety(self) -> None:
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        result = build_builder_bootstrap_atomic(self.root, self.request(4), vault=self.vault)
        json_path = Path(result["json"])
        last_good = json_path.read_bytes()
        self.assertTrue(json_path.resolve().is_relative_to(self.vault.resolve()))
        self.assertEqual(validate_builder_bootstrap(json_path)["bootstrap_digest"], result["bootstrap_digest"])
        after = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(before, after)
        with self.assertRaisesRegex(ContextCompilerError, "outside the canonical Memory checkout"):
            build_builder_bootstrap_atomic(self.root, self.request(4), vault=self.root / "vault")
        self.assertFalse(list(self.vault.glob(".builder-bootstrap-*")))

        linked_vault = Path(tempfile.mkdtemp(prefix="sbmem-bootstrap-linked-vault-"))
        try:
            (linked_vault / "_live").mkdir(parents=True)
            (linked_vault / "_live" / "builder-bootstrap").symlink_to(self.root, target_is_directory=True)
            with self.assertRaisesRegex(ContextCompilerError, "Builder Bootstrap output must be outside"):
                build_builder_bootstrap_atomic(self.root, self.request(4), vault=linked_vault)
            self.assertEqual(json_path.read_bytes(), last_good)
        finally:
            shutil.rmtree(linked_vault, ignore_errors=True)

    def test_validate_inspect_and_human_readable_output(self) -> None:
        result = build_builder_bootstrap_atomic(self.root, self.request(2), vault=self.vault)
        payload = validate_builder_bootstrap(Path(result["json"]))
        report = inspect_builder_bootstrap(Path(result["json"]))
        markdown = Path(result["markdown"]).read_text(encoding="utf-8")
        self.assertEqual(payload["bootstrap_version"], BOOTSTRAP_VERSION)
        self.assertEqual(report["builder"]["number"], 2)
        self.assertIn("Builder Bootstrap Pack V4", markdown)
        self.assertIn("PROHIBITED OPERATIONS", markdown)
        self.assertIn("NOT PROVIDED", markdown)

    def test_dependencies_blockers_contracts_invariants_and_ceo_decision_are_separated(self) -> None:
        self.write_handoffs(self.handoff(1, "2026-09-16T11:00:00Z", blocker="provider unavailable"))
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        pack = compile_builder_bootstrap(self.root, self.request(1, task_metadata={"entity_seeds": ["WS-ONE", "DEC-CEO"]}, required_dependencies=["WS-DEP"], include_runtime=True), vault=self.vault).pack
        self.assertTrue(any(item.get("target") == "WORKSTREAM:WS-DEP" or item.get("entity_id") == "WORKSTREAM:WS-DEP" for item in pack["authoritative_dependencies"]))
        self.assertTrue(pack["active_blockers"])
        self.assertTrue(pack["safety_invariants"])
        self.assertTrue(pack["unresolved_ceo_decisions"])

    def test_validator_rejects_tampered_derived_sections_even_with_recomputed_digest(self) -> None:
        self.write_handoffs(self.handoff(7, "2026-09-16T11:00:00Z", blocker="provider unavailable"))
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        pack = compile_builder_bootstrap(
            self.root,
            self.request(7, task_metadata={"entity_seeds": ["DEC-CEO"]}, required_dependencies=["WS-NOT-PRESENT"], repository_scope=["memory"], path_scope=["tools/memorylib"], include_runtime=True),
            vault=self.vault,
        ).pack
        pack_path = self.vault / "tamper.json"

        mutations = {
            "active blocker removal": lambda value: value["active_blockers"].clear(),
            "missing dependency removal": lambda value: value["missing_dependencies"].clear(),
            "review flag change": lambda value: value["review_flags"].append("UNDECLARED"),
            "current evidence change": lambda value: value["builder"]["current_evidence"].update({"status": "TAMPERED"}),
            "allowed scope change": lambda value: value["allowed_scope"]["paths"].append("outside-scope"),
            "CEO decision removal": lambda value: value["unresolved_ceo_decisions"].clear(),
        }
        for label, mutate in mutations.items():
            tampered = copy.deepcopy(pack)
            mutate(tampered)
            tampered["bootstrap_digest"] = _bootstrap_digest(tampered)
            write_json(self.vault, "tamper.json", tampered)
            with self.assertRaisesRegex(BuilderBootstrapValidationError, "derived field|Builder current evidence|allowed_scope"):
                validate_builder_bootstrap(pack_path)

    def test_builder_four_to_seven_latest_evidence_is_independent(self) -> None:
        handoffs = [self.handoff(number, f"2026-09-16T0{number}:00:00Z") for number in range(4, 8)]
        self.write_handoffs(*handoffs)
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        for number in range(4, 8):
            pack = compile_builder_bootstrap(self.root, self.request(number, include_runtime=True), vault=self.vault).pack
            current = pack["builder"]["current_evidence"]
            self.assertEqual(current["status"], "READY FOR CEO REVIEW")
            self.assertEqual(current["freshness"], "FRESH" if 12 - number <= 6 else "AGING")
            self.assertEqual(current["branch"], f"feat/builder-{number}")
            self.assertEqual(current["head_sha"], "a" * 40)
            self.assertEqual(current["source_pr"], 50 + number)
            self.assertEqual(current["tests_passed"], 58)
            self.assertEqual(current["ci"], "green")
            self.assertEqual(current["blocker_state"], "NONE REPORTED")

    def test_builder_four_identity_dedupe_and_blocker_transition(self) -> None:
        old = self.handoff(4, "2026-09-16T09:00:00Z", blocker="quota exhausted")
        duplicate = self.handoff(4, "2026-09-16T10:00:00Z", blocker="quota exhausted")
        changed = self.handoff(4, "2026-09-16T11:00:00Z", blocker="credential invalid")
        self.assertEqual(handoff_evidence_id(old), handoff_evidence_id(duplicate))
        self.assertNotEqual(handoff_evidence_id(old), handoff_evidence_id(changed))
        store = self.vault / "_live/BUILDER_HANDOFFS.json"
        ingest_handoff(store, old)
        ingest_handoff(store, duplicate)
        ingest_handoff(store, changed)
        stored = json.loads(store.read_text(encoding="utf-8"))["candidates"]
        self.assertEqual(len(stored), 2)
        old_stored = next(item for item in stored if item["candidate_id"] == old["candidate_id"])
        self.assertEqual(old_stored["observation_count"], 2)
        self.assertIn(changed["candidate_id"], {item["candidate_id"] for item in stored})
        transition = observe_sources(
            self.root,
            FixtureGitHubClient({
                "Philip3006/sportsbrain": {"main_sha": "1" * 40, "pull_requests": []},
                "Philip3006/SportsBrainMemory": {"main_sha": "2" * 40, "pull_requests": []},
            }),
            previous={"builder_handoffs": [old, changed]},
            observed_at="2026-09-16T12:00:00Z",
        )
        self.assertIn("BLOCKER_STATE_CHANGE_REQUIRES_CEO_REVIEW", {item["type"] for item in transition["conflicts"]})

    def test_builder_four_stale_and_absent_runtime_states_are_explicit(self) -> None:
        stale = self.handoff(4, "2026-09-14T00:00:00Z")
        self.write_handoffs(stale)
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        stale_pack = compile_builder_bootstrap(self.root, self.request(4, include_runtime=True), vault=self.vault).pack
        self.assertEqual(stale_pack["builder"]["current_evidence"]["freshness"], "STALE")
        self.assertIn("STALE_EVIDENCE", stale_pack["review_flags"])
        shutil.rmtree(self.vault / "_live/graph")
        unknown_pack = compile_builder_bootstrap(self.root, self.request(4, include_runtime=True), vault=self.vault).pack
        self.assertEqual(unknown_pack["builder"]["current_evidence"]["state"], "UNKNOWN")
        self.assertIn("UNKNOWN_EVIDENCE", unknown_pack["review_flags"])


if __name__ == "__main__":
    unittest.main()
