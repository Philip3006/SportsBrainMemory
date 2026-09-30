import argparse
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from sync_from_sportsbrain import source_state, import_source, allowed_path, BRANCH
from sync_memory import sync_repo, sync_vault, seed_vault, refresh_runtime_graph
from install_memory_sync_launchagent import install, LABEL
from check_source_sync_branch import check


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True, stderr=subprocess.DEVNULL).strip()


def independent_memory(source, destination):
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(
        ".git", "__pycache__", ".memory-build", ".pytest_cache"))
    git(destination, "init", "--initial-branch=main")
    git(destination, "config", "user.email", "test@example.invalid")
    git(destination, "config", "user.name", "Test")
    git(destination, "add", ".")
    git(destination, "commit", "-m", "memory fixture")
    return destination


class AutomaticSyncTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name).resolve()
        self.source = self.root / "source"
        self.source.mkdir()
        git(self.source, "init", "-b", "main")
        git(self.source, "config", "user.email", "test@example.invalid")
        git(self.source, "config", "user.name", "Test")
        (self.source / "src").mkdir()
        (self.source / "src/model.py").write_text("frozen = True\n")
        self.commit("source (#240)")
        self.release = git(self.source, "rev-parse", "HEAD")

    def tearDown(self):
        self.tmp.cleanup()

    def commit(self, message):
        git(self.source, "add", ".")
        git(self.source, "commit", "-m", message)
        git(self.source, "update-ref", "refs/remotes/origin/main", git(self.source, "rev-parse", "HEAD"))

    def memory(self):
        root = self.root / "memory"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "__pycache__", ".memory-build"))
        manifest = json.loads((root / "_meta/MEMORY_V2.json").read_text())
        manifest["source_latest_meaningful_sha"] = self.release
        (root / "_meta/MEMORY_V2.json").write_text(json.dumps(manifest))
        (root / "_meta/source_sync_status.json").unlink(missing_ok=True)
        # Transaction tests need repository history, not the caller's Git config.
        git(root, "init", "-b", "main")
        git(root, "config", "user.email", "test@example.invalid")
        git(root, "config", "user.name", "Test")
        git(root, "add", ".")
        git(root, "commit", "-m", "memory fixture")
        return root

    def test_runtime_commit_is_not_source_release(self):
        (self.source / "docs/data").mkdir(parents=True)
        (self.source / "docs/data/health.json").write_text('{"api_key":"not ingested"}')
        self.commit("auto health")
        state = source_state(self.source)
        self.assertEqual(state["source_release_sha"], self.release)
        self.assertNotEqual(state["source_main_sha"], self.release)

    def test_source_change_advances_release(self):
        (self.source / "src/model.py").write_text("frozen = True\n# source contract\n")
        self.commit("contract (#241)")
        self.assertEqual(source_state(self.source)["source_release_sha"], git(self.source, "rev-parse", "HEAD"))

    def test_import_deterministic_noop_no_closure(self):
        memory = self.memory()
        other = self.root / "independent-memory"
        independent_memory(memory, other)
        self.assertNotEqual(git(memory, "rev-parse", "--absolute-git-dir"), git(other, "rev-parse", "--absolute-git-dir"))
        before = {str(p.relative_to(memory)): p.read_bytes() for p in (memory / "findings/records").rglob("*.md")}
        first = import_source(memory, self.source, validate=False)
        bytes_before = {p: (memory / p).read_bytes() for p in first["changed_files"]}
        self.assertEqual(import_source(memory, self.source, validate=False), {"status": "NO_OP"})
        self.assertEqual(bytes_before, {p: (memory / p).read_bytes() for p in first["changed_files"]})
        self.assertEqual(before, {str(p.relative_to(memory)): p.read_bytes() for p in (memory / "findings/records").rglob("*.md")})
        independently = import_source(other, self.source, validate=False)
        self.assertEqual(first["changed_files"], independently["changed_files"])
        self.assertEqual(bytes_before, {p: (other / p).read_bytes() for p in first["changed_files"]})
        copy = self.root / "copy"
        independent_memory(memory, copy)
        self.assertEqual(import_source(copy, self.source, validate=False), {"status": "NO_OP"})

    def test_validation_failure_preserves_canonical_memory(self):
        memory = self.memory()
        before = (memory / "CURRENT_STATE.md").read_bytes()
        with patch("sync_from_sportsbrain.validations", side_effect=RuntimeError("failure")):
            with self.assertRaises(RuntimeError):
                import_source(memory, self.source)
        self.assertEqual(before, (memory / "CURRENT_STATE.md").read_bytes())
        self.assertFalse((memory / "_meta/source_sync_status.json").exists())

    def test_scope_namespace(self):
        self.assertEqual(BRANCH, "automation/sportsbrain-source-sync")
        self.assertTrue(allowed_path("CURRENT_STATE.md"))
        self.assertFalse(allowed_path("tools/memory.py"))
        self.assertFalse(allowed_path("findings/records/FND-1.md"))
        self.assertFalse(allowed_path(".obsidian/workspace.json"))

    def test_secret_source_payload_and_commit_title_not_ingested(self):
        secret = "ghp_" + "A" * 40
        (self.source / "src/model.py").write_text(secret)
        self.commit(secret)
        result = import_source(self.memory(), self.source, validate=False)
        self.assertNotIn(secret, json.dumps(result))

    def test_automation_owned_commit_passes(self):
        git(self.source, "checkout", "-b", BRANCH)
        git(self.source, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        (self.source / "CURRENT_STATE.md").write_text("source-only observation")
        git(self.source, "add", ".")
        git(self.source, "commit", "-m", "memory: automatic source evidence sync")
        self.assertEqual(check(self.source), ["CURRENT_STATE.md"])

    def test_automation_manual_commit_rejected(self):
        git(self.source, "checkout", "-b", BRANCH)
        (self.source / "CURRENT_STATE.md").write_text("manual")
        git(self.source, "add", ".")
        git(self.source, "commit", "-m", "manual")
        with self.assertRaises(ValueError):
            check(self.source)

    def test_bot_main_merge_remains_guarded_with_clean_worktree(self):
        git(self.source, "checkout", "-b", BRANCH)
        git(self.source, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        (self.source / "CURRENT_STATE.md").write_text("source-only observation")
        git(self.source, "add", ".")
        git(self.source, "commit", "-m", "memory: automatic source evidence sync")
        git(self.source, "checkout", "main")
        (self.source / "main-change.md").write_text("new main")
        self.commit("main advance")
        git(self.source, "checkout", BRANCH)
        git(self.source, "merge", "--no-edit", "-m", "memory: automatic source evidence sync", "origin/main")
        self.assertEqual(git(self.source, "status", "--porcelain"), "")
        self.assertEqual(check(self.source), ["CURRENT_STATE.md"])

    def test_no_automation_diff_is_clean_noop(self):
        git(self.source, "checkout", "-b", BRANCH)
        self.assertEqual(git(self.source, "diff", "--name-only", "origin/main...HEAD"), "")

    def test_independent_memory_ignores_git_and_caches(self):
        fixture = self.root / "minimal"
        fixture.mkdir()
        (fixture / "note.md").write_text("fixture")
        for name in (".git", "__pycache__", ".memory-build", ".pytest_cache"):
            (fixture / name).mkdir()
            (fixture / name / "sentinel").write_text("never copy")
        copied = independent_memory(fixture, self.root / "hermetic")
        for name in (".git", "__pycache__", ".memory-build", ".pytest_cache"):
            self.assertFalse((copied / name / "sentinel").exists())
        self.assertEqual(git(copied, "branch", "--show-current"), "main")

    def test_automation_unexpected_file_rejected(self):
        git(self.source, "checkout", "-b", BRANCH)
        (self.source / "src/model.py").write_text("unsafe")
        git(self.source, "add", ".")
        git(self.source, "commit", "-m", "memory: automatic source evidence sync")
        with self.assertRaises(ValueError):
            check(self.source)

    def test_automation_secret_in_allowlisted_file_rejected(self):
        git(self.source, "checkout", "-b", BRANCH)
        git(self.source, "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
        (self.source / "CURRENT_STATE.md").write_text("ghp_" + "A" * 40)
        git(self.source, "add", ".")
        git(self.source, "commit", "-m", "memory: automatic source evidence sync")
        with self.assertRaises(ValueError):
            check(self.source)

    def test_local_edits_block_before_fetch(self):
        (self.source / "src/model.py").write_text("local edit")
        state, _ = sync_repo(self.source, "main")
        self.assertEqual(state, "SYNC BLOCKED")

    def test_divergence_blocks(self):
        remote = self.root / "remote.git"
        subprocess.run(["git", "clone", "--bare", str(self.source), str(remote)], check=True, capture_output=True)
        git(self.source, "remote", "add", "origin", str(remote))
        elsewhere = self.root / "elsewhere"
        subprocess.run(["git", "clone", str(remote), str(elsewhere)], check=True, capture_output=True)
        git(elsewhere, "config", "user.email", "test@example.invalid")
        git(elsewhere, "config", "user.name", "Test")
        (elsewhere / "remote.md").write_text("remote")
        git(elsewhere, "add", "."); git(elsewhere, "commit", "-m", "remote"); git(elsewhere, "push")
        (self.source / "local.md").write_text("local")
        self.commit("local")
        state, detail = sync_repo(self.source, "main")
        self.assertEqual(state, "SYNC BLOCKED")
        self.assertIn("diverged", detail)

    def test_default_sync_branch_main(self):
        script = (ROOT / "tools/sync_memory.py").read_text()
        self.assertIn('"--branch", default="main"', script)
        self.assertNotIn('default="feat/memory-v2-live-obsidian"', script)

    def test_new_vault_collision_and_ui_preserved(self):
        memory, vault = self.root / "notes", self.root / "vault"
        memory.mkdir(); vault.mkdir()
        (memory / "canonical.md").write_text("first")
        (vault / ".obsidian").mkdir()
        (vault / ".obsidian/workspace.json").write_text("personal UI")
        seed_vault(memory, vault)
        (memory / "new.md").write_text("canonical")
        (vault / "new.md").write_text("personal note")
        ok, _, _ = sync_vault(memory, vault)
        self.assertFalse(ok)
        self.assertEqual((vault / "new.md").read_text(), "personal note")
        self.assertEqual((vault / ".obsidian/workspace.json").read_text(), "personal UI")

    def test_graph_failure_marks_degraded_preserves_last_good(self):
        memory, vault = self.root / "notes", self.root / "vault"
        memory.mkdir(); (vault / "_live/graph").mkdir(parents=True)
        good = vault / "_live/graph/GRAPH_MANIFEST.json"
        good.write_text("last good")
        (vault / "_live/SEMANTIC_GRAPH_STATUS.json").write_text('{"status":"ONLINE"}')
        with patch("memorylib.semantic_graph.build_semantic_graph_atomic", side_effect=ValueError("test")):
            result, _ = refresh_runtime_graph(memory, vault)
        self.assertEqual(result["status"], "DEGRADED")
        self.assertEqual(good.read_text(), "last good")

    def test_launchagent_installer_idempotent_status_uninstall(self):
        memory = self.memory(); vault = self.root / "vault"; vault.mkdir()
        args = argparse.Namespace(home=self.root, memory_repo=memory, vault=vault,
                                  source_repo=self.source, python=Path(sys.executable), status=False, uninstall=False)
        calls = []; loaded = False
        def run(command, **kwargs):
            nonlocal loaded
            calls.append(command)
            code = 0
            if command[1] == "print": code = 0 if loaded else 1
            if command[1] == "bootstrap": loaded = True
            if command[1] == "bootout": loaded = False
            return subprocess.CompletedProcess(command, code)
        self.assertTrue(install(args, run=run)["changed"])
        path = self.root / "Library/LaunchAgents" / f"{LABEL}.plist"
        plist = plistlib.loads(path.read_bytes())
        self.assertTrue(plist["RunAtLoad"]); self.assertEqual(plist["StartInterval"], 300)
        self.assertEqual(plist["ProgramArguments"][-1], "main")
        self.assertFalse(install(args, run=run)["changed"])
        self.assertEqual(sum(c[1] == "bootstrap" for c in calls), 1)
        args.status = True
        self.assertTrue(install(args, run=run)["loaded"])
        args.status = False; args.uninstall = True
        self.assertFalse(install(args, run=run)["installed"])
        self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
