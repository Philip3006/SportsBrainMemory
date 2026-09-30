from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "tools"))
from memorylib.dashboard import render_all
from memorylib.live import render_live_status
from memorylib.validate import validate
from memorylib.v2 import MemoryV2Error, build_context_packets, freshness_state, ingest_events
from sync_memory import refresh_runtime_graph, seed_vault, sync_repo, sync_vault


def event(event_id: str, *, canonical: bool = True, state: str = "ceo_approved"):
    return {
        "event_id": event_id,
        "timestamp": "2026-09-13T23:00:00+02:00",
        "type": "CEO_DECISION",
        "domain": "test",
        "summary": "Test event",
        "source_repository": "test",
        "builder": "CEO",
        "builder_number": "CEO",
        "ceo_gate_state": "approved",
        "affected_workstreams": [],
        "findings": [],
        "invariants": [],
        "supersedes": [],
        "evidence": ["test evidence"],
        "verification_state": state,
        "canonical": canonical,
    }


class MemoryV2Tests(unittest.TestCase):
    def test_canonical_event_is_idempotent_and_conflicts_fail(self):
        td = Path(tempfile.mkdtemp(prefix="sbmem-v2-event-"))
        try:
            first = ingest_events(td, [event("EVT-20260913-901")], validate_after=False)
            second = ingest_events(td, [event("EVT-20260913-901")], validate_after=False)
            self.assertTrue(first[0].changed)
            self.assertFalse(second[0].changed)
            changed = event("EVT-20260913-901")
            changed["summary"] = "different"
            with self.assertRaises(MemoryV2Error):
                ingest_events(td, [changed], validate_after=False)
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_builder_evidence_stays_pending(self):
        td = Path(tempfile.mkdtemp(prefix="sbmem-v2-pending-"))
        try:
            result = ingest_events(td, [event("EVT-20260913-902", canonical=False, state="builder_report")], validate_after=False)
            self.assertEqual(result[0].destination, "events/pending/EVT-20260913-902.json")
            payload = json.loads((td / result[0].destination).read_text())
            self.assertFalse(payload["canonical"])
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_secret_like_event_is_rejected(self):
        payload = event("EVT-20260913-903")
        payload["summary"] = "bearer abcdefghijklmnopqrstuvwxyz123456"
        with self.assertRaises(MemoryV2Error):
            ingest_events(Path(tempfile.mkdtemp(prefix="sbmem-v2-secret-")), [payload], validate_after=False)

    def test_freshness_thresholds(self):
        self.assertEqual(freshness_state("2026-09-13T23:00:00+02:00", "2026-09-13T23:01:00+02:00"), "FRESH")
        self.assertEqual(freshness_state("2026-09-13T10:00:00+02:00", "2026-09-13T17:00:01+02:00"), "AGING")
        self.assertEqual(freshness_state("2026-09-12T10:00:00+02:00", "2026-09-13T11:00:01+02:00"), "STALE")

    def test_role_packets_are_bounded_and_deterministic(self):
        first = build_context_packets(ROOT)
        contents = {p.name: p.read_bytes() for p in (ROOT / "builder/context").glob("*.md")}
        second = build_context_packets(ROOT)
        self.assertEqual(first, second)
        self.assertEqual(contents, {p.name: p.read_bytes() for p in (ROOT / "builder/context").glob("*.md")})
        self.assertIn("BUILDER: 3", (ROOT / "builder/context/BUILDER_3_MEMORY.md").read_text())

    def test_builder_number_is_required_and_matches_identity(self):
        payload = event("EVT-20260913-904")
        del payload["builder_number"]
        with self.assertRaises(MemoryV2Error):
            ingest_events(Path(tempfile.mkdtemp(prefix="sbmem-v2-builder-required-")), [payload], validate_after=False)
        payload = event("EVT-20260913-905")
        payload["builder"] = "Builder 1"
        payload["builder_number"] = 2
        with self.assertRaises(MemoryV2Error):
            ingest_events(Path(tempfile.mkdtemp(prefix="sbmem-v2-builder-mismatch-")), [payload], validate_after=False)

    def test_current_governance_uses_numbered_builders_and_approved_research(self):
        render_all(ROOT)
        report = validate(ROOT, "v1")
        self.assertEqual((report.errors, report.warnings), (0, 0))
        current = "\n".join((ROOT / name).read_text() for name in ("00_HOME.md", "CURRENT_STATE.md", "CURRENT_PRIORITIES.md", "CURRENT_BLOCKERS.md"))
        self.assertIn("Builder 1", current)
        self.assertIn("Builder 2", current)
        self.assertIn("Builder 3", current)
        self.assertNotRegex(current, r"\bBuilder [ABC]\b")
        self.assertIn("6eaabbec7d0182103d815c72fae4976e261b40aa", current)
        self.assertIn("EVT-20260913-010", current)
        self.assertIn("NOT APPROVED", current)

    def test_seed_creates_recoverable_snapshot_and_conflict_blocks(self):
        td = Path(tempfile.mkdtemp(prefix="sbmem-v2-sync-"))
        try:
            memory = td / "memory"
            vault = td / "vault"
            memory.mkdir()
            vault.mkdir()
            (memory / "canonical.md").write_text("canonical\n")
            (vault / "legacy.md").write_text("keep me\n")
            _, detail = seed_vault(memory, vault)
            self.assertIn("pre-sync snapshot", detail)
            self.assertTrue((vault / ".memory-backups").exists())
            (vault / "canonical.md").write_text("local edit\n")
            ok, detail, _ = sync_vault(memory, vault)
            self.assertFalse(ok)
            self.assertIn("local edits/conflicts", detail)
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_sync_removes_only_unchanged_retired_packet_files(self):
        td = Path(tempfile.mkdtemp(prefix="sbmem-v2-retire-"))
        try:
            memory = td / "memory"
            vault = td / "vault"
            memory.mkdir()
            vault.mkdir()
            retired = memory / "builder/context/BUILDER_A_RESEARCH.md"
            retired.parent.mkdir(parents=True)
            retired.write_text("retired\n")
            (memory / "current.md").write_text("current\n")
            seed_vault(memory, vault)
            retired.unlink()
            ok, detail, _ = sync_vault(memory, vault)
            self.assertTrue(ok)
            self.assertIn("BUILDER_A_RESEARCH.md", detail)
            self.assertFalse((vault / "builder/context/BUILDER_A_RESEARCH.md").exists())
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_live_projection_writes_status_files_without_canonical_mutation(self):
        td = Path(tempfile.mkdtemp(prefix="sbmem-v2-live-"))
        try:
            memory = td / "memory"
            source = td / "source"
            vault = td / "vault"
            for repo in (memory, source):
                subprocess.run(["git", "init", str(repo)], check=True, capture_output=True)
                subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.invalid"], check=True)
                subprocess.run(["git", "-C", str(repo), "config", "user.name", "Memory Test"], check=True)
            (memory / "canonical.md").write_text("canonical\n")
            (memory / "_meta").mkdir()
            (memory / "_meta/MEMORY_V2.json").write_text(
                '{"memory_version":2,"canonical_updated_at":"2026-09-13T23:00:00+02:00"}\n'
            )
            (source / "docs/data").mkdir(parents=True)
            (source / "docs/data/health.json").write_text('{"overall":"ok","generated_at":"2026-09-13T23:00:00Z","jobs":[]}\n')
            subprocess.run(["git", "-C", str(memory), "add", "canonical.md", "_meta/MEMORY_V2.json"], check=True)
            subprocess.run(["git", "-C", str(memory), "commit", "-m", "memory"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(source), "add", "docs/data/health.json"], check=True)
            subprocess.run(["git", "-C", str(source), "commit", "-m", "source"], check=True, capture_output=True)
            payload = render_live_status(memory, vault, source, sync_state="ONLINE")
            self.assertIn(payload["status"], {"ONLINE", "STALE"})
            self.assertTrue((vault / "_live/LIVE_STATUS.md").exists())
            self.assertTrue((vault / "_live/STATUS.json").exists())
            self.assertEqual((memory / "canonical.md").read_text(), "canonical\n")
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_runtime_graph_refresh_stays_out_of_memory_checkout_and_sync_manifest(self):
        td = Path(tempfile.mkdtemp(prefix="sbmem-v2-runtime-graph-"))
        try:
            memory = td / "memory"
            vault = td / "vault"
            memory.mkdir()
            vault.mkdir()
            subprocess.run(["git", "init", str(memory)], check=True, capture_output=True)
            for args in (("user.email", "test@example.invalid"), ("user.name", "Memory Test")):
                subprocess.run(["git", "-C", str(memory), "config", *args], check=True)
            (memory / "_meta").mkdir()
            (memory / "_meta/MEMORY_V2.json").write_text('{"memory_version":2,"canonical_updated_at":"2026-09-16T00:00:00Z"}\n')
            (memory / "canonical.md").write_text("canonical\n")
            subprocess.run(["git", "-C", str(memory), "add", "."], check=True)
            subprocess.run(["git", "-C", str(memory), "commit", "-m", "memory"], check=True, capture_output=True)
            seed_vault(memory, vault)
            before = subprocess.run(["git", "-C", str(memory), "status", "--porcelain"], check=True, capture_output=True, text=True).stdout

            status, detail = refresh_runtime_graph(memory, vault)

            after = subprocess.run(["git", "-C", str(memory), "status", "--porcelain"], check=True, capture_output=True, text=True).stdout
            self.assertEqual(before, after)
            self.assertEqual(status["status"], "ONLINE")
            self.assertIn("refreshed and validated", detail)
            self.assertTrue((vault / "_live/graph/GRAPH_MANIFEST.json").exists())
            self.assertFalse((memory / "views/graph").exists())
            sync_manifest = vault / "_live/.memory_sync_manifest.json"
            self.assertTrue(sync_manifest.exists())
            self.assertNotIn("_live/graph", sync_manifest.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(td, ignore_errors=True)

    def test_fast_forward_only_remote_ahead(self):
        td = Path(tempfile.mkdtemp(prefix="sbmem-v2-git-"))
        git_environment = patch.dict(os.environ, {
            "GIT_CONFIG_GLOBAL": str(td / "global.gitconfig"),
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_COUNT": "0",
        })
        git_environment.start()
        try:
            subprocess.run(["git", "config", "--global", "init.defaultBranch", "master"], check=True)
            self.assertEqual(subprocess.check_output(
                ["git", "config", "--global", "init.defaultBranch"], text=True).strip(), "master")
            bare = td / "remote.git"
            seed = td / "seed"
            clone = td / "memory"
            subprocess.run(["git", "init", "--bare", "--initial-branch=main", str(bare)], check=True, capture_output=True)
            subprocess.run(["git", "init", "--initial-branch=main", str(seed)], check=True, capture_output=True)
            for args in (("user.email", "test@example.invalid"), ("user.name", "Memory Test")):
                subprocess.run(["git", "-C", str(seed), "config", *args], check=True)
            (seed / "state.txt").write_text("one\n")
            subprocess.run(["git", "-C", str(seed), "add", "state.txt"], check=True)
            subprocess.run(["git", "-C", str(seed), "commit", "-m", "one"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(seed), "branch", "-M", "main"], check=True)
            subprocess.run(["git", "-C", str(seed), "remote", "add", "origin", str(bare)], check=True)
            subprocess.run(["git", "-C", str(seed), "push", "-u", "origin", "main"], check=True, capture_output=True)
            subprocess.run(["git", "clone", str(bare), str(clone)], check=True, capture_output=True)
            self.assertEqual(subprocess.check_output(
                ["git", "-C", str(bare), "symbolic-ref", "HEAD"], text=True).strip(), "refs/heads/main")
            self.assertEqual(subprocess.check_output(
                ["git", "-C", str(clone), "branch", "--show-current"], text=True).strip(), "main")
            subprocess.run(["git", "-C", str(clone), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(clone), "config", "user.name", "Memory Test"], check=True)
            (seed / "state.txt").write_text("two\n")
            subprocess.run(["git", "-C", str(seed), "commit", "-am", "two"], check=True, capture_output=True)
            subprocess.run(["git", "-C", str(seed), "push"], check=True, capture_output=True)
            state, detail = sync_repo(clone, "main")
            self.assertEqual(state, "ONLINE")
            self.assertIn("Fast-forwarded", detail)
            self.assertEqual((clone / "state.txt").read_text(), "two\n")
            subprocess.run(["git", "-C", str(clone), "switch", "-c", "wrong-branch"], check=True, capture_output=True)
            self.assertEqual(sync_repo(clone, "main")[0], "SYNC BLOCKED")
        finally:
            git_environment.stop()
            shutil.rmtree(td, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
