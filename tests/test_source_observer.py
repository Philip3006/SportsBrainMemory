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
    handoff_evidence_id,
    ingest_handoff,
    observe_and_write,
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
        repeated = parse_builder_handoff(handoff, observed_at="2026-09-15T09:00:00+00:00")
        self.assertEqual(evidence["builder_number"], 1)
        self.assertEqual(evidence["tests_passed"], 58)
        self.assertFalse(evidence["canonical"])
        self.assertEqual(evidence["candidate_id"], repeated["candidate_id"])
        self.assertEqual(evidence["candidate_id"], handoff_evidence_id(evidence))
        store = self.vault / "_live/BUILDER_HANDOFFS.json"
        ingest_handoff(store, evidence)
        ingest_handoff(store, repeated)
        stored = json.loads(store.read_text(encoding="utf-8"))
        self.assertEqual(len(stored["candidates"]), 1)
        self.assertEqual(stored["candidates"][0]["observation_count"], 2)
        self.assertEqual(stored["candidates"][0]["first_observed_at"], "2026-09-15T08:00:00+00:00")
        self.assertEqual(stored["candidates"][0]["last_observed_at"], "2026-09-15T09:00:00+00:00")
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
        control_plane = (self.vault / "_live/CEO_CONTROL_PLANE.md").read_text(encoding="utf-8")
        self.assertIn("Unresolved CEO Decisions", control_plane)
        self.assertIn("PR #59", control_plane)
        self.assertEqual(list((self.memory / "events/records").glob("*.json")), [])
        self.assertEqual(validate_candidate_store(json.loads((self.vault / "_live/SOURCE_CANDIDATES.json").read_text())), [])

    def _handoff(self, builder_number: int, observed_at: str, status: str, branch: str, head: str, blocker: str | None = None, blocker_classification: str | None = None, blocker_status: str | None = None) -> dict:
        blocker_line = f"Hard Blocker: {blocker}\n" if blocker else ""
        classification_line = f"Blocker classification: {blocker_classification}\n" if blocker_classification else ""
        status_line = f"Blocker status: {blocker_status}\n" if blocker_status else ""
        text = f"""BUILDER: {builder_number}
ROLE: Builder {builder_number} evidence
Local branch: {branch}
Exact head: {head}
PR #{builder_number + 50}
Final status: {status}
Tests: 58 passed
CI: green
{blocker_line}{classification_line}{status_line}Safety: no production mutation and no live activation
"""
        return parse_builder_handoff(text, observed_at=observed_at)

    def test_newer_builder_one_handoff_replaces_older_rendered_state(self):
        older = self._handoff(1, "2026-09-15T08:00:00+00:00", "OLD STATUS", "feat/old", "1" * 40)
        newer = self._handoff(1, "2026-09-15T09:00:00+00:00", "NEW STATUS", "feat/new", "2" * 40)
        payload = observe_sources(
            self.memory,
            FixtureGitHubClient({SPORTS: snapshot("1" * 40, []), MEMORY: snapshot("2" * 40, [])}),
            previous={"builder_handoffs": [older, newer]},
            observed_at="2026-09-15T10:00:00+00:00",
        )
        control_plane = write_and_render(payload)
        self.assertIn("NEW STATUS", control_plane)
        self.assertIn("feat/new", control_plane)
        self.assertNotIn("OLD STATUS", control_plane)
        self.assertNotIn("feat/old", control_plane)

    def test_builder_two_and_three_are_selected_independently(self):
        handoffs = [
            self._handoff(2, "2026-09-15T09:00:00+00:00", "BUILDER TWO", "feat/two", "2" * 40),
            self._handoff(3, "2026-09-15T09:00:00+00:00", "BUILDER THREE", "feat/three", "3" * 40),
        ]
        control_plane = write_and_render({"observed_at": "2026-09-15T10:00:00+00:00", "builder_handoffs": handoffs})
        self.assertIn("BUILDER TWO", control_plane)
        self.assertIn("feat/two", control_plane)
        self.assertIn("BUILDER THREE", control_plane)
        self.assertIn("feat/three", control_plane)

    def test_absent_builder_evidence_is_unknown(self):
        control_plane = write_and_render({"observed_at": "2026-09-15T10:00:00+00:00", "builder_handoffs": []})
        for builder_number in (1, 2, 3):
            self.assertIn(f"Builder {builder_number} — **UNKNOWN / NO CURRENT HANDOFF EVIDENCE**", control_plane)

    def test_stale_builder_handoff_is_visibly_stale(self):
        stale = self._handoff(1, "2026-09-13T08:00:00+00:00", "OLD", "feat/stale", "1" * 40)
        control_plane = write_and_render({"observed_at": "2026-09-15T10:00:00+00:00", "builder_handoffs": [stale]})
        self.assertIn("freshness: **STALE**", control_plane)
        self.assertIn("not unquestionably current", control_plane)

    def test_final_status_and_final_recommendation_are_parsed(self):
        final_status = self._handoff(1, "2026-09-15T09:00:00+00:00", "FINAL STATUS COMPLETE", "feat/status", "1" * 40)
        recommendation = parse_builder_handoff(
            """BUILDER: 2
ROLE: readiness
Local branch: feat/recommendation
Exact head: bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb
Final recommendation: READY FOR CEO REVIEW
""",
            observed_at="2026-09-15T09:00:00+00:00",
        )
        self.assertEqual(final_status["status"], "FINAL STATUS COMPLETE")
        self.assertEqual(recommendation["status"], "READY FOR CEO REVIEW")

    def test_hard_blocker_section_is_parsed(self):
        evidence = self._handoff(1, "2026-09-15T09:00:00+00:00", "BLOCKED", "feat/blocker", "1" * 40, "provider authentication is unavailable")
        self.assertEqual(len(evidence["blockers"]), 1)
        self.assertEqual(evidence["blockers"][0]["classification"], "EXTERNAL")
        self.assertEqual(evidence["blockers"][0]["status"], "REPORTED_OPEN")

    def test_quota_blocker_is_not_fabricated_without_evidence(self):
        payload = observe_sources(
            self.memory,
            FixtureGitHubClient({SPORTS: snapshot("1" * 40, []), MEMORY: snapshot("2" * 40, [])}),
            observed_at="2026-09-15T10:00:00+00:00",
        )
        self.assertFalse(any("QUOTA" in item["blocker_id"] for item in payload["blockers"]))

    def test_old_blocker_is_preserved_unverified_and_not_auto_resolved(self):
        older = self._handoff(1, "2026-09-15T08:00:00+00:00", "BLOCKED", "feat/old", "1" * 40, "quota is exhausted")
        newer = self._handoff(1, "2026-09-15T09:00:00+00:00", "CONDITION CHANGED", "feat/new", "2" * 40)
        payload = observe_sources(
            self.memory,
            FixtureGitHubClient({SPORTS: snapshot("1" * 40, []), MEMORY: snapshot("2" * 40, [])}),
            previous={"observed_at": "2026-09-15T09:00:00+00:00", "builder_handoffs": [older, newer], "blockers": older["blockers"]},
            observed_at="2026-09-15T10:00:00+00:00",
        )
        preserved = next(item for item in payload["blockers"] if item["blocker_id"] == older["blockers"][0]["blocker_id"])
        self.assertEqual(preserved["status"], "PRESERVED_UNVERIFIED")
        self.assertTrue(preserved["needs_ceo_review"])
        self.assertIn("BLOCKER_STATE_CHANGE_REQUIRES_CEO_REVIEW", {item["type"] for item in payload["conflicts"]})

    def test_control_plane_has_no_static_builder_workstream_truth(self):
        control_plane = write_and_render({"observed_at": "2026-09-15T10:00:00+00:00", "builder_handoffs": []})
        self.assertNotIn("Real NO-BET Shadow Execution active", control_plane)
        self.assertNotIn("Independent Shadow Validation Gate merged", control_plane)
        self.assertNotIn("Memory Source Observer / CEO Control Plane active", control_plane)

    def test_handoff_identity_separates_blocker_state_transitions(self):
        common = (1, "2026-09-15T09:00:00+00:00", "SAME OVERALL STATUS", "feat/same", "1" * 40)
        quota = self._handoff(*common, blocker="quota exhausted")
        credential = self._handoff(*common, blocker="credential invalid")
        no_blocker = self._handoff(*common)
        classification_changed = self._handoff(*common, blocker="quota exhausted", blocker_classification="CEO_DECISION_REQUIRED")
        status_changed = self._handoff(*common, blocker="quota exhausted", blocker_status="REPORTED_CHANGED")
        evidence = [quota, credential, no_blocker, classification_changed, status_changed]
        self.assertEqual(len({item["candidate_id"] for item in evidence}), 5)
        self.assertEqual(len({handoff_evidence_id(item) for item in evidence}), 5)

        store = self.vault / "_live/BUILDER_HANDOFFS.json"
        for item in evidence:
            ingest_handoff(store, item)
        stored = json.loads(store.read_text(encoding="utf-8"))["candidates"]
        self.assertEqual(len(stored), 5)
        self.assertIn(quota["candidate_id"], {item["candidate_id"] for item in stored})
        self.assertIn(credential["candidate_id"], {item["candidate_id"] for item in stored})

        for previous, latest in ((quota, credential), (quota, no_blocker), (quota, classification_changed), (quota, status_changed)):
            transition = observe_sources(
                self.memory,
                FixtureGitHubClient({SPORTS: snapshot("1" * 40, []), MEMORY: snapshot("2" * 40, [])}),
                previous={"builder_handoffs": [previous, latest]},
                observed_at="2026-09-15T10:00:00+00:00",
            )
            self.assertIn("BLOCKER_STATE_CHANGE_REQUIRES_CEO_REVIEW", {item["type"] for item in transition["conflicts"]})
            self.assertEqual(transition["builder_handoffs"], [previous, latest])

    def test_observer_loads_persisted_handoff_evidence_for_live_rendering(self):
        evidence = self._handoff(2, "2026-09-15T09:00:00+00:00", "INGESTED STATUS", "feat/ingested", "2" * 40)
        ingest_handoff(self.vault / "_live/BUILDER_HANDOFFS.json", evidence)
        payload = observe_and_write(
            self.memory,
            self.vault,
            client=FixtureGitHubClient({SPORTS: snapshot("1" * 40, []), MEMORY: snapshot("2" * 40, [])}),
        )
        self.assertEqual(payload["builder_handoffs"][0]["candidate_id"], evidence["candidate_id"])
        control_plane = (self.vault / "_live/CEO_CONTROL_PLANE.md").read_text(encoding="utf-8")
        self.assertIn("INGESTED STATUS", control_plane)
        self.assertIn("UNKNOWN / NO CURRENT HANDOFF EVIDENCE", control_plane)


def write_and_render(payload: dict) -> str:
    from memorylib.observer import render_control_plane

    return render_control_plane(payload)


if __name__ == "__main__":
    unittest.main()
