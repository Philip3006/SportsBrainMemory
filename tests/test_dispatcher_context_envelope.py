from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "tools"))

from memorylib import dispatcher_context_envelope as envelope  # noqa: E402
from memorylib.consistency_auditor import ConsistencyAudit  # noqa: E402
from memorylib.context_compiler import _digest, _git_head  # noqa: E402
from memorylib.observer import parse_builder_handoff  # noqa: E402
from memorylib.semantic_graph import build_semantic_graph_atomic  # noqa: E402


def write_text(root: Path, relative: str, value: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8")


def write_record(root: Path, relative: str, object_id: str, object_type: str, **fields: object) -> None:
    lines = ["---", f"id: {object_id}", f"type: {object_type}", "status: active"]
    for key, value in fields.items():
        if isinstance(value, list):
            lines.append(f"{key}:")
            lines.extend(f"  - {item}" for item in value)
        else:
            lines.append(f"{key}: {value}")
    lines.extend(["---", f"# {object_id}", "", f"{object_id} evidence."])
    write_text(root, relative, "\n".join(lines) + "\n")


class DispatcherContextEnvelopeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="sbmem-v6-root-"))
        self.vault = Path(tempfile.mkdtemp(prefix="sbmem-v6-vault-"))
        write_text(self.root, "_meta/MEMORY_V2.json", json.dumps({
            "memory_version": 2,
            "canonical_updated_at": "2026-09-16T00:00:00Z",
        }) + "\n")
        write_record(self.root, "workstreams/ONE.md", "WS-ONE", "workstream", builder="Builder 1", builder_number=1, depends_on=["WS-DEP"], invariants=["NO-BET"])
        write_record(self.root, "workstreams/DEP.md", "WS-DEP", "workstream", builder="Builder 2", builder_number=2)

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.vault, ignore_errors=True)

    def _audit(self, status: str = "CONSISTENT", findings: list[dict] | None = None) -> ConsistencyAudit:
        findings = [
            {
                "severity": item.get("severity", "WARNING"),
                "domain": item.get("domain", "runtime"),
                "status": item.get("status", "WARNING"),
                "summary": item.get("summary", "test finding"),
                "affected_entities": item.get("affected_entities", []),
                "evidence": item.get("evidence", []),
                "authority_classes": item.get("authority_classes", []),
                "source_paths": item.get("source_paths", []),
                "recommended_human_action": item.get("recommended_human_action", "Review manually."),
                "finding_id": item.get("finding_id", "TEST-FINDING"),
            }
            for item in (findings or [])
        ]
        semantic = {
            "schema_version": 5,
            "source_memory_sha": _git_head(self.root),
            "reference_time": "2026-09-16T12:00:00Z",
            "overall_status": status,
            "runtime_available": False,
            "findings": findings,
        }
        return ConsistencyAudit(
            source_memory_sha=_git_head(self.root),
            reference_time="2026-09-16T12:00:00Z",
            overall_status=status,
            findings=findings,
            semantic_digest=_digest(semantic),
            generated_at="2026-09-16T12:00:00Z",
            runtime_available=False,
        )

    def _request(self, number: int = 1, **overrides: object) -> envelope.DispatcherContextEnvelopeRequest:
        value: dict[str, object] = {
            "envelope_id": f"ENV-B{number}-TEST",
            "builder_number": number,
            "task_id": f"TASK-B{number}-TEST",
            "task": "bounded context delivery",
            "workstream": "Context Delivery",
            "repository": "Philip3006/SportsBrainMemory",
            "allowed_paths": ["tools/memorylib/"],
            "prohibited_paths": ["SportsBrain production"],
            "reference_time": "2026-09-16T12:00:00Z",
            "generated_at": "2026-09-16T12:00:00Z",
        }
        value.update(overrides)
        return envelope.DispatcherContextEnvelopeRequest.from_mapping(value)

    def _compile(self, request: envelope.DispatcherContextEnvelopeRequest | None = None, *, audit: ConsistencyAudit | None = None):
        request = request or self._request()
        audit = audit or self._audit()
        with patch.object(envelope, "audit_consistency", return_value=audit):
            return envelope.compile_dispatcher_context_envelope(self.root, request, vault=self.vault)

    def test_builders_one_to_four_are_valid_worker_envelopes(self) -> None:
        for number in range(1, 5):
            compiled = self._compile(self._request(number))
            pack = compiled.envelope
            self.assertEqual(pack["builder_number"], number)
            self.assertEqual(pack["governed_role"], envelope.BUILDER_ROLES[number])
            self.assertIn(pack["classification"], envelope.CLASSIFICATIONS)
            path = self.vault / f"envelope-{number}.json"
            path.write_text(json.dumps(pack), encoding="utf-8")
            self.assertEqual(envelope.validate_dispatcher_context_envelope(path)["envelope_id"], pack["envelope_id"])

    def test_builder_five_is_not_a_worker_and_future_builders_fail_closed(self) -> None:
        for number in (5, 6, 7, 8):
            with self.assertRaises(envelope.DispatcherEnvelopeError):
                self._request(number)
        with self.assertRaises(envelope.DispatcherEnvelopeError):
            self._request("1/4")  # type: ignore[arg-type]

    def test_governed_role_is_dispatcher_owner_only_in_v4_not_worker_envelope(self) -> None:
        self.assertEqual(envelope.BUILDER_ROLES[5], "Autonomous Development / Night Shift Dispatcher Owner")
        with self.assertRaises(envelope.DispatcherEnvelopeError):
            envelope.DispatcherContextEnvelopeRequest.from_mapping({"builder": 5, "task_id": "TASK"})

    def test_memory_v4_bootstrap_provider_is_a_validated_read_only_seam(self) -> None:
        provider = envelope.MemoryV4BootstrapProvider(self.root, vault=self.vault)
        with patch.object(envelope, "audit_consistency", return_value=self._audit()):
            pack = provider.request(
                builder=1,
                task_metadata={"task_id": "TASK-PROVIDER", "task": "provider context request"},
                repository="Philip3006/SportsBrainMemory",
                allowed_paths=["tools/memorylib/"],
                declared_dependencies=["WS-DEP"],
                reference_time="2026-09-16T12:00:00Z",
            )
        self.assertEqual(pack["builder_number"], 1)
        self.assertEqual(pack["execution_authorization"], "NOT_PROVIDED")
        self.assertEqual(pack["safety_decision"], "NOT_EVALUATED")

    def test_authoritative_dependency_is_preserved(self) -> None:
        compiled = self._compile(self._request(declared_dependencies=["WS-DEP"], entity_seeds=["WS-ONE"]))
        self.assertTrue(any(item["dependency"] == "WS-DEP" and item["status"] == "SATISFIED_AUTHORITATIVE" for item in compiled.envelope["required_dependency_states"]))
        self.assertIn(compiled.envelope["classification"], {"CONTEXT_READY", "CONTEXT_UNKNOWN"})

    def test_missing_dependency_fails_closed(self) -> None:
        compiled = self._compile(self._request(declared_dependencies=["DOES-NOT-EXIST"]))
        self.assertEqual(compiled.envelope["classification"], "CONTEXT_FAILED_CLOSED")
        self.assertTrue(any(item["status"] == "MISSING" for item in compiled.envelope["required_dependency_states"]))

    def test_candidate_only_dependency_is_non_authoritative(self) -> None:
        handoff = parse_builder_handoff(
            "BUILDER: 1\nROLE: Research\nBranch: feat/research\nHead SHA: " + "a" * 40 +
            "\nPR #59\nFinal status: CANDIDATE\nObserved at: 2026-09-16T11:00:00Z\n",
            observed_at="2026-09-16T11:00:00Z",
        )
        live = self.vault / "_live"
        live.mkdir(parents=True, exist_ok=True)
        (live / "BUILDER_HANDOFFS.json").write_text(json.dumps({"schema": 1, "candidates": [handoff]}), encoding="utf-8")
        build_semantic_graph_atomic(self.root, self.vault, reference_time="2026-09-16T12:00:00Z")
        compiled = self._compile(self._request(
            include_runtime=True,
            declared_dependencies=[handoff["candidate_id"]],
            entity_seeds=[handoff["candidate_id"]],
        ))
        self.assertEqual(compiled.envelope["classification"], "CONTEXT_FAILED_CLOSED")
        self.assertTrue(any(item["status"] == "PRESENT_NONAUTHORITATIVE" for item in compiled.envelope["required_dependency_states"]))
        candidate = json.dumps(compiled.envelope["non_authoritative_evidence"])
        self.assertIn(handoff["candidate_id"], candidate)
        self.assertIn("canonical", candidate)

    def test_stale_unknown_conflict_governance_and_safety_mapping(self) -> None:
        cases = (
            ({"status": "STALE", "domain": "builder_status", "summary": "old handoff"}, "CONTEXT_STALE"),
            ({"status": "UNKNOWN", "domain": "runtime", "summary": "unknown runtime"}, "CONTEXT_UNKNOWN"),
            ({"status": "CONFLICT", "domain": "builder_status", "summary": "current-view conflict"}, "CONTEXT_CONFLICT"),
            ({"status": "GOVERNANCE_DRIFT", "domain": "governance", "summary": "drift"}, "CONTEXT_FAILED_CLOSED"),
            ({"status": "SAFETY_INVARIANT_MISSING", "domain": "safety", "summary": "missing safety"}, "CONTEXT_FAILED_CLOSED"),
            ({"status": "CEO_DECISION_REQUIRED", "domain": "decision", "summary": "review needed"}, "CONTEXT_WARNING"),
        )
        for finding, expected in cases:
            compiled = self._compile(audit=self._audit(findings=[finding]))
            self.assertEqual(compiled.envelope["classification"], expected, finding)
        compiled = self._compile(self._request(include_runtime=True))
        self.assertEqual(compiled.envelope["classification"], "CONTEXT_UNKNOWN")
        self.assertIn("RUNTIME_GRAPH_UNAVAILABLE", compiled.envelope["review_flags"])
        self.assertEqual(self._compile(audit=self._audit(status="GOVERNANCE_DRIFT")).envelope["classification"], "CONTEXT_FAILED_CLOSED")

    def test_candidate_evidence_remains_non_authoritative_and_runtime_boundary_visible(self) -> None:
        compiled = self._compile()
        for marker in ("NO-BET", "NO-LIVE-ACTIVATION", "SEALED 2425/2526", "Closing odds benchmark-only"):
            self.assertIn(marker.upper(), json.dumps(compiled.envelope["safety_invariants"], ensure_ascii=False).upper())
        self.assertIn("NO-BET", compiled.markdown)
        self.assertIn("NO-LIVE-ACTIVATION", compiled.markdown)

    def test_deterministic_digest_and_ordering_ignore_generated_time(self) -> None:
        first = self._compile(self._request(declared_dependencies=["WS-DEP"], entity_seeds=["WS-ONE"]))
        second = self._compile(self._request(declared_dependencies=["WS-DEP"], entity_seeds=["WS-ONE"]))
        self.assertEqual(first.envelope["semantic_envelope_digest"], second.envelope["semantic_envelope_digest"])
        self.assertEqual(first.envelope["context_pack_digest"], second.envelope["context_pack_digest"])
        self.assertEqual(first.envelope["review_flags"], sorted(first.envelope["review_flags"]))
        self.assertEqual(first.envelope["source_provenance"], sorted(first.envelope["source_provenance"]))
        later = self._compile(self._request(declared_dependencies=["WS-DEP"], entity_seeds=["WS-ONE"], generated_at="2026-09-16T13:00:00Z"))
        self.assertEqual(first.envelope["semantic_envelope_digest"], later.envelope["semantic_envelope_digest"])

    def test_source_sha_change_changes_context_and_envelope(self) -> None:
        first = self._compile()
        write_text(self.root, "workstreams/NEW.md", "---\nid: WS-NEW\ntype: workstream\nstatus: active\n---\n# New\n")
        second = self._compile()
        self.assertNotEqual(first.envelope["source_memory_sha"], second.envelope["source_memory_sha"])
        self.assertNotEqual(first.envelope["semantic_envelope_digest"], second.envelope["semantic_envelope_digest"])

    def test_immutable_authorizations_and_secret_rejection(self) -> None:
        compiled = self._compile()
        path = self.vault / "immutable.json"
        path.write_text(json.dumps(compiled.envelope), encoding="utf-8")
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["execution_authorization"] = "AUTHORIZED"
        path.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaises(envelope.DispatcherEnvelopeValidationError):
            envelope.validate_dispatcher_context_envelope(path)
        with self.assertRaises(envelope.DispatcherEnvelopeError):
            self._request(task_metadata={"api_key": "secret-value"})

    def test_external_output_guard_rejects_memory_vault_and_symlink_back(self) -> None:
        compiled = self._compile()
        with self.assertRaises(envelope.DispatcherEnvelopeError):
            envelope.write_dispatcher_context_envelope(compiled, self.root / "envelope.json", root=self.root, vault=self.vault)
        with self.assertRaises(envelope.DispatcherEnvelopeError):
            envelope.write_dispatcher_context_envelope(compiled, self.vault / "envelope.json", root=self.root, vault=self.vault)
        external = Path(tempfile.mkdtemp(prefix="sbmem-v6-output-"))
        try:
            back = external / "back"
            back.symlink_to(self.root, target_is_directory=True)
            with self.assertRaises(envelope.DispatcherEnvelopeError):
                envelope.write_dispatcher_context_envelope(compiled, back / "envelope.json", root=self.root, vault=self.vault)
            result = envelope.write_dispatcher_context_envelope(compiled, external / "ok", root=self.root, vault=self.vault)
            self.assertTrue(Path(result["json"]).is_file())
            self.assertTrue(Path(result["markdown"]).is_file())
            self.assertIn(envelope.inspect_dispatcher_context_envelope(Path(result["json"]))["classification"], envelope.CLASSIFICATIONS)
        finally:
            shutil.rmtree(external, ignore_errors=True)

    def test_compile_does_not_mutate_canonical_or_vault(self) -> None:
        before_root = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        before_vault = {path.relative_to(self.vault): path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}
        self._compile()
        after_root = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        after_vault = {path.relative_to(self.vault): path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}
        self.assertEqual(before_root, after_root)
        self.assertEqual(before_vault, after_vault)


if __name__ == "__main__":
    unittest.main()
