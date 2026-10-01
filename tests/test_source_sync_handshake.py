import json
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_source_sync_head import BRANCH, GateBlocked, validate_and_merge


class HandshakeTests(unittest.TestCase):
    def run_gate(self, **changes):
        pr_head = changes.pop("pr_head", "a" * 40)
        protected = changes.pop("protected", "true")
        evidence = dict(databaseId=123, workflowName="Memory validation", headBranch=BRANCH,
                        headSha="a" * 40, event="workflow_dispatch", status="completed", conclusion="success")
        evidence.update(changes)
        def respond(*args):
            if args[1:3] == ("workflow", "run"):
                return "https://github.com/Philip3006/SportsBrainMemory/actions/runs/123"
            if args[1:3] == ("run", "view"):
                return json.dumps(evidence)
            if args[1] == "api":
                return protected
            if args[1:3] == ("pr", "view"):
                return pr_head
            return ""
        self.command = Mock(side_effect=respond)
        self.clock = Mock(side_effect=[0, 0, 0, 601])
        return validate_and_merge("Philip3006/SportsBrainMemory", "15", "a" * 40,
                                  run=self.command, clock=self.clock, sleep=lambda _: None)

    def assert_no_merge(self):
        self.assertFalse(any(call.args[1:3] == ("pr", "merge") for call in self.command.call_args_list))

    def test_success_before_merge(self):
        self.assertEqual(self.run_gate(), "123")
        calls = [call.args[1:3] for call in self.command.call_args_list]
        self.assertLess(calls.index(("run", "view")), calls.index(("pr", "merge")))

    def test_wrong_sha_branch_workflow_event_or_id_blocks(self):
        for field, value in (("headSha", "b" * 40), ("headBranch", "main"),
                             ("workflowName", "Other"), ("event", "push"), ("databaseId", 456)):
            with self.subTest(field=field), self.assertRaises(GateBlocked):
                self.run_gate(**{field: value})
            self.assert_no_merge()

    def test_failure_and_cancellation_block(self):
        for conclusion in ("failure", "cancelled", "timed_out", "skipped"):
            with self.subTest(conclusion=conclusion), self.assertRaisesRegex(GateBlocked, "VALIDATION_FAILED"):
                self.run_gate(conclusion=conclusion)
            self.assert_no_merge()

    def test_timeout_blocks(self):
        with self.assertRaisesRegex(GateBlocked, "VALIDATION_TIMEOUT"):
            self.run_gate(status="in_progress", conclusion="")
        self.assert_no_merge()

    def test_missing_dispatch_run_blocks(self):
        with self.assertRaisesRegex(GateBlocked, "VALIDATION_RUN_MISSING"):
            validate_and_merge("Philip3006/SportsBrainMemory", "15", "a" * 40, run=lambda *args: "")

    def test_pr_head_change_or_unprotected_repo_blocks(self):
        for changes in ({"pr_head": "b" * 40}, {"protected": "false"}):
            with self.subTest(changes=changes), self.assertRaises(GateBlocked):
                self.run_gate(**changes)
            self.assert_no_merge()

    def test_api_error_blocks(self):
        with self.assertRaises(GateBlocked):
            validate_and_merge("Philip3006/SportsBrainMemory", "15", "a" * 40,
                               run=Mock(side_effect=GateBlocked("VALIDATION_API_ERROR")))

    def test_workflow_branch_diff_and_existing_pr_contract(self):
        workflow = (ROOT / ".github/workflows/sportsbrain-source-sync.yml").read_text()
        self.assertNotIn("protection/required_status_checks", workflow)
        self.assertIn("git diff --quiet origin/main...HEAD && exit 0", workflow)
        self.assertLess(workflow.index("git diff --quiet"), workflow.index("git push"))
        self.assertIn('if test -z "$pr"; then', workflow)
        self.assertIn("--head automation/sportsbrain-source-sync --state open", workflow)
        self.assertIn("check_source_sync_branch.py", workflow)
        self.assertNotIn('test -n "$(git status --porcelain)" || exit 0', workflow)
