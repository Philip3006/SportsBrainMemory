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

from memorylib import builder_bootstrap, context_compiler, observer, semantic_graph  # noqa: E402
from memorylib.consistency_auditor import audit_consistency, write_audit_report  # noqa: E402
from memorylib.observer import parse_builder_handoff  # noqa: E402


def write_text(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(root: Path, relative: str, payload: object) -> None:
    write_text(root, relative, json.dumps(payload, indent=2, sort_keys=True) + "\n")


class ConsistencyAuditorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp(prefix="sbmem-consistency-root-"))
        self.vault = Path(tempfile.mkdtemp(prefix="sbmem-consistency-vault-"))
        write_json(self.root, "_meta/MEMORY_V2.json", {"memory_version": 2, "source_main_sha": "1" * 40})
        write_text(self.root, "workstreams/TOP5-PRODUCTION.md", """---
id: WS-TOP5-PRODUCTION
type: workstream
status: active
---
# Top-5 Production
NO-BET; no live activation is permitted. 2425 and 2526 remain SEALED.
Closing odds remain a benchmark/CLV artifact only.
This layer does not grant CEO authorization, merge, deploy, or production authority.
""")
        write_text(self.root, "invariants/SAFETY.md", """---
id: INV-SAFETY
type: invariant
status: active
---
# Safety
NO-BET, no-live-activation, and sealed 2425/2526 are mandatory.
Execution authorization: NOT PROVIDED.
""")
        write_text(self.root, "architecture/BUILDER_BOOTSTRAP_V4.md", """# Builder Bootstrap V4
Builder 1–5 are governed. Builder 5 is Autonomous Development / Night Shift Dispatcher Owner.
It does not grant CEO authorization, merge, deploy, or production authority.
""")
        write_text(self.root, "architecture/CONTEXT_COMPILER_V3.md", "# Context Compiler V3\nConsumers are CEO and BUILDER_1 through BUILDER_5.\n")
        write_text(self.root, "architecture/SOURCE_OBSERVER.md", "# Source Observer\nHandoffs require BUILDER: 1 through BUILDER: 5.\n")
        write_text(self.root, "architecture/SEMANTIC_GRAPH_V2.md", "# Semantic Graph V2\nThe graph seeds Builder 1–5 only.\n")
        write_text(self.root, "README.md", "# SportsBrainMemory\nCurrent bootstrap governance supports Builders 1–5.\n")

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.vault, ignore_errors=True)

    def test_clean_governed_roster(self):
        report = audit_consistency(self.root, reference_time="2026-09-16T12:00:00Z")
        statuses = {(item["domain"], item["status"]) for item in report.findings}
        self.assertNotIn(("governance", "GOVERNANCE_DRIFT"), statuses)
        self.assertNotIn(("context_compiler", "GOVERNANCE_DRIFT"), statuses)
        self.assertNotIn(("semantic_graph", "GOVERNANCE_DRIFT"), statuses)

    def test_context_observer_bootstrap_graph_roster_drift_is_visible(self):
        with patch.object(context_compiler, "CONSUMER_TYPES", {"CEO", "BUILDER_1", "BUILDER_6"}), \
             patch.object(observer, "BUILDER_NUMBER_SET", frozenset({1, 2, 3, 4, 5, 6})), \
             patch.object(builder_bootstrap, "BUILDER_NUMBERS", (1, 2, 3, 4, 5, 6)), \
             patch.object(semantic_graph, "BUILDER_NUMBERS", (1, 2, 3, 4, 5, 6)):
            report = audit_consistency(self.root, reference_time="2026-09-16T12:00:00Z")
        drift = [item for item in report.findings if item["status"] == "GOVERNANCE_DRIFT"]
        self.assertTrue(drift)
        self.assertTrue(any("Builder 6" in json.dumps(item) or "BUILDER_6" in json.dumps(item) for item in drift))

    def test_unsupported_builder_runtime_is_rejected(self):
        write_json(self.vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "candidates": [{
            "candidate_type": "CANDIDATE_OPERATIONAL_EVIDENCE", "builder": "Builder 6", "builder_number": 6,
            "canonical": False, "promotion_required": True, "observed_at": "2026-09-16T11:00:00Z",
        }]})
        report = audit_consistency(self.root, vault=self.vault, reference_time="2026-09-16T12:00:00Z")
        self.assertTrue(any(item["status"] == "GOVERNANCE_DRIFT" and "Builder 6" in item["summary"] for item in report.findings))

    def test_stale_and_unknown_builder_state_are_explicit(self):
        report = audit_consistency(self.root, vault=self.vault, reference_time="2026-09-17T12:00:00Z")
        self.assertTrue(any(item["status"] == "UNKNOWN" and "Builder 1" in item["summary"] for item in report.findings))
        handoff = parse_builder_handoff("BUILDER: 4\nROLE: Provider\nFinal status: READY\n", observed_at="2026-09-15T00:00:00Z")
        write_json(self.vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "candidates": [handoff]})
        report = audit_consistency(self.root, vault=self.vault, reference_time="2026-09-17T12:00:00Z")
        self.assertTrue(any(item["status"] == "STALE" and "Builder 4" in item["summary"] for item in report.findings))

    def test_candidate_cannot_satisfy_authoritative_dependency(self):
        write_json(self.vault, "_live/builder-bootstrap/BOOT.json", {
            "bootstrap_id": "BOOT", "execution_authorization": "NOT_PROVIDED", "safety_decision": "NOT_EVALUATED",
            "required_dependency_status": [{"dependency": "EVD-CAND", "status": "SATISFIED_AUTHORITATIVE"}],
            "context_pack": {"included_entities": [{"entity_id": "EVD-CAND", "stable_id": "EVD-CAND", "authority_class": "CANDIDATE", "canonical": False}]},
        })
        report = audit_consistency(self.root, vault=self.vault, reference_time="2026-09-16T12:00:00Z")
        self.assertTrue(any(item["status"] == "NONAUTHORITATIVE_ONLY" for item in report.findings))

    def test_branch_head_pr_blocker_mismatch_is_conflict(self):
        handoff = parse_builder_handoff("""BUILDER: 1
ROLE: Research
Local branch: feat/one
Exact head: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
PR #59
Final status: READY
Hard Blocker: quota exhausted
""", observed_at="2026-09-16T11:00:00Z")
        write_json(self.vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "candidates": [handoff]})
        write_json(self.vault, "_live/graph/GRAPH_MANIFEST.json", {"schema": 2, "entities": [{
            "namespace": "BUILDER", "stable_id": "BUILDER-1", "metadata": {"current_evidence": {
                "branch": "feat/other", "head_sha": "b" * 40, "source_pr": 59, "status": "READY", "blockers": [],
            }}
        }]})
        report = audit_consistency(self.root, vault=self.vault, reference_time="2026-09-16T12:00:00Z")
        self.assertTrue(any(item["status"] == "CONFLICT" and item["domain"] == "builder_status" for item in report.findings))

    def test_canonical_verified_conflict_and_safety_missing(self):
        write_json(self.root, "events/records/EVT-1.json", {"event_id": "EVT-1", "canonical": True, "source_repository": "repo", "source_pr": 1, "status": "OPEN"})
        write_text(self.root, "verifications/records/VER-1.md", """---
id: VER-1
type: verification
source_repository: repo
source_pr: 1
status: VERIFIED
---
# Verification
""")
        safety = self.root / "invariants/SAFETY.md"
        safety.write_text(safety.read_text().replace("NO-BET", "BET"), encoding="utf-8")
        production = self.root / "workstreams/TOP5-PRODUCTION.md"
        production.write_text(production.read_text().replace("NO-BET", "BET"), encoding="utf-8")
        report = audit_consistency(self.root, reference_time="2026-09-16T12:00:00Z")
        self.assertTrue(any(item["status"] == "CONFLICT" and item["domain"] == "authority" for item in report.findings))
        self.assertTrue(any(item["status"] == "SAFETY_INVARIANT_MISSING" for item in report.findings))

    def test_authorization_claim_and_external_symlink_are_failed_closed(self):
        live = self.vault / "_live"
        live.mkdir(parents=True, exist_ok=True)
        (live / "context").symlink_to(self.root, target_is_directory=True)
        write_json(self.vault, "_live/SOURCE_OBSERVER.json", {"schema": 1, "candidates": [{"candidate_type": "SOURCE_CANDIDATE_EVENT", "canonical": True, "promotion_required": False, "candidate_id": "x"}]})
        write_json(self.vault, "_live/builder-bootstrap/BOOT.json", {"execution_authorization": "AUTHORIZED", "safety_decision": "NOT_EVALUATED"})
        report = audit_consistency(self.root, vault=self.vault, reference_time="2026-09-16T12:00:00Z")
        self.assertTrue(any(item["domain"] == "external_output" and item["status"] == "FAILED_CLOSED" for item in report.findings))
        self.assertTrue(any(item["domain"] == "authority" and item["status"] == "FAILED_CLOSED" for item in report.findings))

    def test_deterministic_findings_and_external_output_guard(self):
        first = audit_consistency(self.root, reference_time="2026-09-16T12:00:00Z")
        second = audit_consistency(self.root, reference_time="2026-09-16T12:00:00Z")
        self.assertEqual(first.findings, second.findings)
        self.assertEqual(first.semantic_digest, second.semantic_digest)
        output = Path(tempfile.mkdtemp(prefix="sbmem-audit-output-"))
        try:
            written = write_audit_report(first, output, root=self.root)
            self.assertTrue(Path(written["json"]).is_file())
            self.assertTrue(Path(written["markdown"]).is_file())
            with self.assertRaises(ValueError):
                write_audit_report(first, self.root / "report.json", root=self.root)
        finally:
            shutil.rmtree(output, ignore_errors=True)

    def test_audit_does_not_mutate_canonical_or_runtime_inputs(self):
        handoff = parse_builder_handoff("BUILDER: 5\nROLE: Dispatcher\nFinal status: READY\n", observed_at="2026-09-16T11:00:00Z")
        write_json(self.vault, "_live/BUILDER_HANDOFFS.json", {"schema": 1, "candidates": [handoff]})
        before_root = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        before_vault = {path.relative_to(self.vault): path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}
        audit_consistency(self.root, vault=self.vault, reference_time="2026-09-16T12:00:00Z")
        after_root = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        after_vault = {path.relative_to(self.vault): path.read_bytes() for path in self.vault.rglob("*") if path.is_file()}
        self.assertEqual(before_root, after_root)
        self.assertEqual(before_vault, after_vault)


if __name__ == "__main__":
    unittest.main()
