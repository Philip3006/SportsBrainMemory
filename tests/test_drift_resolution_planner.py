import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from memorylib import drift_resolution_planner as planner  # noqa: E402


REFERENCE = "2026-09-16T12:00:00Z"
SOURCE_SHA = "a" * 40


def finding(
    finding_id: str,
    *,
    status: str = "WARNING",
    domain: str = "documentation",
    severity: str = "WARNING",
    summary: str = "review this evidence",
    paths: list[str] | None = None,
    authorities: list[str] | None = None,
    entities: list[str] | None = None,
    action: str = "",
) -> dict:
    return {
        "finding_id": finding_id,
        "status": status,
        "domain": domain,
        "severity": severity,
        "summary": summary,
        "affected_entities": entities or [finding_id],
        "evidence": [{"authority_class": value} for value in (authorities or ["VERIFIED"])],
        "authority_classes": authorities or ["VERIFIED"],
        "source_paths": paths or ["CURRENT_STATE.md"],
        "recommended_human_action": action,
    }


def audit(findings: list[dict] | None = None, *, source_sha: str = SOURCE_SHA) -> dict:
    values = findings or []
    semantic = {
        "schema_version": 5,
        "source_memory_sha": source_sha,
        "reference_time": REFERENCE,
        "overall_status": "CONSISTENT" if not values else values[0]["status"],
        "runtime_available": False,
        "findings": values,
    }
    return {
        **semantic,
        "audit_version": "memory-consistency-auditor-v5.0",
        "read_only": True,
        "generated_at": REFERENCE,
        "semantic_digest": planner._v5_audit_semantic_digest(semantic),
        "summary": {"finding_count": len(values)},
    }


def fake_envelope(*, classification: str = "CONTEXT_READY", source_sha: str = SOURCE_SHA) -> dict:
    return {"classification": classification, "source_memory_sha": source_sha}


class DriftResolutionPlannerTests(unittest.TestCase):
    def compile(self, findings: list[dict] | None = None, *, source_sha: str = SOURCE_SHA, envelope=None):
        with patch.object(planner, "_read_envelope", return_value=envelope):
            return planner.plan_drift_resolution(
                ROOT,
                audit=audit(findings, source_sha=source_sha),
                envelope=envelope,
                reference_time=REFERENCE,
            )

    def test_clean_memory_requires_no_remediation(self):
        compiled = self.compile()
        self.assertEqual(compiled.plan["planner_status"], "REMEDIATION_NOT_REQUIRED")
        self.assertEqual(compiled.plan["summary"]["finding_count"], 0)
        self.assertIn("V6_ENVELOPE_UNAVAILABLE", compiled.plan["review_flags"])

    def test_priority_and_remediation_classes_are_deterministic(self):
        values = [
            finding("F-WARN", domain="metrics", paths=["architecture/README.md"]),
            finding("F-CAND", status="NONAUTHORITATIVE_ONLY", domain="builder_status", authorities=["CANDIDATE"]),
            finding("F-STALE", status="STALE", domain="current_view", paths=["CURRENT_STATE.md"]),
            finding("F-GOV", status="GOVERNANCE_DRIFT", domain="governance", summary="unsupported Builder 8"),
            finding("F-SAFE", status="SAFETY_INVARIANT_MISSING", domain="safety", severity="ERROR", summary="NO-BET boundary missing"),
        ]
        compiled = self.compile(values, envelope=fake_envelope())
        items = compiled.plan["findings"]
        self.assertEqual([item["finding_id"] for item in items], ["F-SAFE", "F-GOV", "F-STALE", "F-CAND", "F-WARN"])
        self.assertEqual(items[0]["remediation_class"], "SAFETY_REVIEW_REQUIRED")
        self.assertEqual(items[1]["remediation_class"], "REMOVE_UNSUPPORTED_RUNTIME_REFERENCE")
        self.assertEqual(items[2]["remediation_class"], "REFRESH_CURRENT_VIEW")
        self.assertEqual(items[3]["remediation_class"], "PROMOTION_REVIEW_REQUIRED")
        self.assertEqual(items[4]["remediation_class"], "NO_ACTION")
        for item in items:
            for key in (
                "finding_id", "source_finding_status", "domain", "severity", "affected_entities",
                "authoritative_source_classes", "conflicting_source_classes", "non_authoritative_source_classes",
                "affected_canonical_current_view_paths", "affected_runtime_paths", "dispatcher_impact",
                "remediation_class", "proposed_human_action", "canonical_mutation_required",
                "runtime_only_cleanup_required", "evidence_promotion_required", "prerequisite_evidence",
                "unresolved_ceo_decision", "fail_closed_reason", "provenance", "remediation_digest",
            ):
                self.assertIn(key, item)

    def test_dependency_conflict_unknown_and_runtime_drift_are_classified(self):
        values = [
            finding("F-DEP", status="MISSING", domain="dependencies", severity="ERROR", paths=["architecture/CONTEXT_COMPILER_V3.md"]),
            finding("F-CONFLICT", status="CONFLICT", domain="semantic_graph", authorities=["CANONICAL", "RUNTIME_DERIVED"], paths=["_live/graph/GRAPH_MANIFEST.json"]),
            finding("F-UNKNOWN", status="UNKNOWN", domain="builder_status", paths=["_live/BUILDER_HANDOFFS.json"]),
        ]
        plan = self.compile(values, envelope=fake_envelope(classification="CONTEXT_CONFLICT")).plan
        by_id = {item["finding_id"]: item for item in plan["findings"]}
        self.assertEqual(by_id["F-DEP"]["remediation_class"], "INSUFFICIENT_EVIDENCE")
        self.assertEqual(by_id["F-CONFLICT"]["remediation_class"], "REGENERATE_DERIVED_VIEW")
        self.assertEqual(by_id["F-CONFLICT"]["affected_canonical_current_view_paths"], [])
        self.assertEqual(by_id["F-CONFLICT"]["affected_runtime_paths"], ["_live/graph/GRAPH_MANIFEST.json"])
        self.assertEqual(by_id["F-UNKNOWN"]["dispatcher_impact"], "CONTEXT_BLOCKING")
        self.assertEqual(plan["planner_status"], "REMEDIATION_FAILED_CLOSED")

    def test_v6_stale_and_failed_closed_context_remains_visible(self):
        stale = self.compile(envelope=fake_envelope(source_sha="b" * 40))
        self.assertIn("V6_SOURCE_SHA_STALE", stale.plan["review_flags"])
        self.assertEqual(stale.plan["planner_status"], "REMEDIATION_REVIEW_REQUIRED")
        conflict = self.compile(envelope=fake_envelope(classification="CONTEXT_CONFLICT"))
        self.assertEqual(conflict.plan["planner_status"], "REMEDIATION_FAILED_CLOSED")
        with patch.object(planner, "_read_envelope", return_value={"classification": "CONTEXT_FAILED_CLOSED", "source_memory_sha": SOURCE_SHA}):
            failed = planner.plan_drift_resolution(ROOT, audit=audit([finding("F-1")]), envelope=object(), reference_time=REFERENCE)
        self.assertIn("V6_CONTEXT_FAILED_CLOSED", failed.plan["review_flags"])
        self.assertEqual(failed.plan["planner_status"], "REMEDIATION_FAILED_CLOSED")

    def test_candidate_runtime_remediation_never_changes_safety_flags(self):
        values = [finding("F-CAND", status="NONAUTHORITATIVE_ONLY", domain="builder_status", authorities=["CANDIDATE_OPERATIONAL_EVIDENCE"], paths=["_live/SOURCE_CANDIDATES.json"])]
        plan = self.compile(values).plan
        item = plan["findings"][0]
        self.assertTrue(item["evidence_promotion_required"])
        self.assertFalse(plan["automatic_repair"])
        self.assertFalse(plan["candidate_promotion"])
        self.assertFalse(plan["authorization_created"])
        self.assertTrue(plan["actions_are_proposals_only"])
        self.assertIn("NO-BET", json.dumps(plan["safety_invariants"]))
        self.assertIn("SEALED 2425/2526", json.dumps(plan["safety_invariants"]))

    def test_semantic_plan_is_stable_for_same_inputs_and_changes_with_source_sha(self):
        first = self.compile([finding("F-1")], envelope=fake_envelope())
        second = self.compile([finding("F-1")], envelope=fake_envelope())
        self.assertEqual(first.plan["semantic_plan_digest"], second.plan["semantic_plan_digest"])
        self.assertEqual(first.plan["planner_id"], second.plan["planner_id"])
        changed = self.compile([finding("F-1")], source_sha="c" * 40, envelope=fake_envelope(source_sha="c" * 40))
        self.assertNotEqual(first.plan["semantic_plan_digest"], changed.plan["semantic_plan_digest"])

    def test_validator_rederives_v5_digest_and_plan_digest(self):
        compiled = self.compile([finding("F-1")])
        with tempfile.TemporaryDirectory(prefix="sbmem-v7-validator-") as directory:
            path = Path(directory) / "plan.json"
            path.write_text(json.dumps(compiled.plan), encoding="utf-8")
            planner.validate_drift_resolution_plan(path)
            tampered = copy.deepcopy(compiled.plan)
            tampered["consistency_audit"]["findings"][0]["summary"] = "tampered"
            path.write_text(json.dumps(tampered), encoding="utf-8")
            with self.assertRaises(planner.DriftPlannerValidationError):
                planner.validate_drift_resolution_plan(path)

    def test_secret_evidence_is_rejected(self):
        secret = finding("F-SECRET", summary="access_token=ghp_" + "x" * 30)
        with self.assertRaises(planner.DriftPlannerError):
            self.compile([secret])

    def test_output_guard_rejects_canonical_and_vault_paths_without_mutation(self):
        compiled = self.compile([finding("F-1")])
        with tempfile.TemporaryDirectory(prefix="sbmem-v7-output-") as directory:
            root = Path(directory) / "memory"
            vault = Path(directory) / "vault"
            root.mkdir()
            vault.mkdir()
            for forbidden in (root / "plan.json", vault / "plan.json"):
                with self.assertRaises(planner.DriftPlannerError):
                    planner.write_drift_resolution_plan(compiled, forbidden, root=root, vault=vault)
                self.assertFalse(forbidden.exists())
            output = Path(directory) / "external" / "plan.json"
            result = planner.write_drift_resolution_plan(compiled, output, root=root, vault=vault)
            self.assertTrue(Path(result["json"]).exists())
            self.assertTrue(Path(result["markdown"]).exists())
            self.assertEqual(list(root.iterdir()), [])
            self.assertEqual(list(vault.iterdir()), [])

    def test_markdown_is_human_readable_and_does_not_claim_execution(self):
        compiled = self.compile([finding("F-1")])
        self.assertIn("# SportsBrain Memory Drift Resolution Plan V7", compiled.markdown)
        self.assertIn("Read-only: **true**", compiled.markdown)
        self.assertIn("No file, runtime projection", compiled.markdown)
        self.assertNotIn("AUTHORIZED", compiled.markdown)


if __name__ == "__main__":
    unittest.main()
