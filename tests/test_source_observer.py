from __future__ import annotations

import json
from pathlib import Path
import shutil
import tempfile
import unittest

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from memorylib.observer import (  # noqa: E402
    CandidateValidationError,
    FixtureGitHubClient,
    ObserverError,
    candidate_id,
    ingest_handoff,
    observe_sources,
    parse_builder_handoff,
    validate_blocker,
    validate_candidate,
    validate_candidate_store,
    write_runtime_outputs,
)
from memorylib.validate import validate_runtime_payload  # noqa: E402


SPORTS = "Philip3006/sportsbrain"
MEMORY = "Philip3006/SportsBrainMemory"
HEAD_59 = "a" * 40
MERGE_59 = "b" * 40
HEAD_OPEN = "c" * 40


def pr(number: int, state: str, head_sha: str, merge_sha: str | None = None, title: str = "fixture") -> dict:
    return {
        "number": number,
        "state": state,
        "head_sha": head_sha,
        "merge_sha": merge_sha,
        "title": title,
        "merged_at": "2026-09-15T08:00:00+00:00" if state == "MERGED" else None,
    }


def snapshot(main_sha: str, pull_requests: list[dict]) -> dict:
    return {"main_sha": main_sha, "pull_requests": pull_requests, "ci": {"status": "AVAILABLE", "workflow_count": 1, "successful": 1}}


class SourceObserverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = Path(tempfile.mkdtemp(prefix="sbmem-observer-test-"))
        self.memory = self.temp / "memory"
        self.vault = self.temp / "vault"
        (self.memory / "events/records").mkdir(parents=True)
        (self.vault / "_live").mkdir(parents=True)

    def tearDown(self) -> None:
        shutil.rmtree(self.temp, ignore_errors=True)

    def test_merged_pr_59_is_detected_as_noncanonical_candidate(self):
        client = FixtureGitHubClient({
            SPORTS: snapshot("1" * 40, [
                pr(59, "MERGED", HEAD_59, MERGE_59, "add disabled shadow integration"),
                pr(60, "OPEN", HEAD_OPEN, title="open work"),
                pr(61, "CLOSED", "d" * 40, title="closed without merge"),
            ]),
            MEMORY: snapshot("2" * 40, []),
        })
        payload = observe_sources(self.memory, client, observed_at="2026-09-15T08:01:00+00:00")
        self.assertEqual(payload["status"], "ONLINE")
        self.assertTrue(payload["pr_59"]["detected"])
        candidate = next(item for item in payload["candidates"] if item["source_pr"] == 59)
        self.assertFalse(candidate["canonical"])
        self.assertTrue(candidate["promotion_required"])
        self.assertEqual(candidate["candidate_id"], candidate_id(SPORTS, 59, HEAD_59, MERGE_59))
        self.assertEqual(len(payload["repositories"][SPORTS]["open_prs"]), 1)
        self.assertEqual(len(payload["repositories"][SPORTS]["closed_unmerged_prs"]), 1)

    def test_repeated_observation_is_deduplicated(self):
        client = FixtureGitHubClient({SPORTS: snapshot("1" * 40, [pr(59, "MERGED", HEAD_59, MERGE_59)]), MEMORY: snapshot("2" * 40, [])})
        first = observe_sources(self.memory, client, observed_at="2026-09-15T08:01:00+00:00")
        second = observe_sources(self.memory, client, previous=first, observed_at="2026-09-15T08:02:00+00:00")
        self.assertEqual(len(first["candidates"]), len(second["candidates"]))
        self.assertEqual(second["candidates"][0]["observation_count"], 2)
        self.assertEqual(second["candidates"][0]["first_observed_at"], "2026-09-15T08:01:00+00:00")

    def test_moving_main_creates_source_drift(self):
        before = observe_sources(self.memory, FixtureGitHubClient({SPORTS: snapshot("1" * 40, []), MEMORY: snapshot("2" * 40, [])}), observed_at="2026-09-15T08:01:00+00:00")
        after = observe_sources(self.memory, FixtureGitHubClient({SPORTS: snapshot("3" * 40, []), MEMORY: snapshot("2" * 40, [])}), previous=before, observed_at="2026-09-15T08:02:00+00:00")
        self.assertEqual(after["source_drift"][0]["previous_main_sha"], "1" * 40)
        self.assertEqual(after["source_drift"][0]["current_main_sha"], "3" * 40)

    def test_outage_preserves_last_known_state_and_candidates(self):
        previous = observe_sources(self.memory, FixtureGitHubClient({SPORTS: snapshot("1" * 40, [pr(59, "MERGED", HEAD_59, MERGE_59)]), MEMORY: snapshot("2" * 40, [])}), observed_at="2026-09-15T08:01:00+00:00")
        outage = FixtureGitHubClient({SPORTS: ObserverError("GitHub unavailable"), MEMORY: ObserverError("GitHub unavailable")})
        current = observe_sources(self.memory, outage, previous=previous, observed_at="2026-09-15T08:02:00+00:00")
        self.assertEqual(current["status"], "DEGRADED")
        self.assertEqual(current["repositories"], previous["repositories"])
        self.assertEqual(current["candidates"], previous["candidates"])
        self.assertEqual(len(current["errors"]), 2)

    def test_malformed_response_is_degraded_not_canonical(self):
        malformed = FixtureGitHubClient({SPORTS: {"main_sha": "not-a-sha", "pull_requests": []}, MEMORY: snapshot("2" * 40, [])})
        payload = observe_sources(self.memory, malformed)
        self.assertEqual(payload["status"], "DEGRADED")
        self.assertTrue(any(item["type"] == "SOURCE_UNAVAILABLE" for item in payload["errors"]))
        self.assertEqual(list((self.memory / "events/records").glob("*.json")), [])

    def test_canonical_source_mismatch_is_visible(self):
        event = {
            "event_id": "EVT-20260915-001",
            "type": "PR_MERGED",
            "source_repository": SPORTS,
            "source_pr": 59,
            "source_sha": "e" * 40,
            "evidence": [f"merge commit {'f' * 40}"],
        }
        (self.memory / "events/records/EVT-20260915-001.json").write_text(json.dumps(event), encoding="utf-8")
        payload = observe_sources(self.memory, FixtureGitHubClient({SPORTS: snapshot("1" * 40, [pr(59, "OPEN", HEAD_59)]), MEMORY: snapshot("2" * 40, [])}))
        kinds = {item["type"] for item in payload["conflicts"]}
        self.assertIn("PR_STATE_MISMATCH", kinds)
        self.assertIn("SOURCE_HEAD_MISMATCH", kinds)

    def test_safety_conflicts_are_visible_without_self_correction(self):
        (self.memory / "_meta").mkdir()
        (self.memory / "_meta/MEMORY_V2.json").write_text(json.dumps({"frozen_research_sha": "bad"}), encoding="utf-8")
        (self.memory / "workstreams").mkdir()
        (self.memory / "workstreams/TOP5-RESEARCH.md").write_text("2425 only\n", encoding="utf-8")
        payload = observe_sources(self.memory, FixtureGitHubClient({SPORTS: snapshot("1" * 40, []), MEMORY: snapshot("2" * 40, [])}))
        kinds = {item["type"] for item in payload["conflicts"]}
        self.assertIn("RESEARCH_SHA_MISMATCH", kinds)
        self.assertIn("SEALED_STATE_CONFLICT", kinds)
        self.assertIn("NO_BET_STATE_CONFLICT", kinds)
        self.assertEqual(list((self.memory / "events/records").glob("*.json")), [])

    def test_builder_handoff_requires_explicit_identity_and_stays_operational(self):
        handoff = """BUILDER: 1
ROLE: Top-5 Shadow Integration
Local branch: feat/shadow
Exact head: aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
PR #59
Status: active
Tests: 58 passed
CI: green
Blocker: The Odds API quota is exhausted
Safety: no production mutation and no live activation
"""
        evidence = parse_builder_handoff(handoff, observed_at="2026-09-15T08:00:00+00:00")
        self.assertEqual(evidence["builder_number"], 1)
        self.assertEqual(evidence["tests_passed"], 58)
        self.assertFalse(evidence["canonical"])
        store = self.vault / "_live/BUILDER_HANDOFFS.json"
        ingest_handoff(store, evidence)
        ingest_handoff(store, evidence)
        stored = json.loads(store.read_text(encoding="utf-8"))
        self.assertEqual(len(stored["candidates"]), 1)
        self.assertEqual(validate_runtime_payload(store), [])
        with self.assertRaises(CandidateValidationError):
            parse_builder_handoff("BUILDER: 1/2\nROLE: ambiguous")

    def test_blocker_classification_is_fail_closed(self):
        validate_blocker({"blocker_id": "x", "classification": "EXTERNAL", "status": "OPEN", "summary": "quota", "auto_resolve": False})
        with self.assertRaises(CandidateValidationError):
            validate_blocker({"blocker_id": "x", "classification": "UNKNOWN", "status": "OPEN", "summary": "bad", "auto_resolve": False})
        with self.assertRaises(CandidateValidationError):
            validate_blocker({"blocker_id": "x", "classification": "EXTERNAL", "status": "RESOLVED", "summary": "bad", "auto_resolve": True})

    def test_runtime_outputs_are_separate_from_canonical_history(self):
        client = FixtureGitHubClient({SPORTS: snapshot("1" * 40, [pr(59, "MERGED", HEAD_59, MERGE_59)]), MEMORY: snapshot("2" * 40, [])})
        payload = observe_sources(self.memory, client)
        write_runtime_outputs(self.vault, payload)
        self.assertTrue((self.vault / "_live/SOURCE_OBSERVER.json").exists())
        self.assertTrue((self.vault / "_live/CEO_CONTROL_PLANE.md").exists())
        self.assertEqual(list((self.memory / "events/records").glob("*.json")), [])
        self.assertEqual(validate_candidate_store(json.loads((self.vault / "_live/SOURCE_CANDIDATES.json").read_text())), [])


if __name__ == "__main__":
    unittest.main()
