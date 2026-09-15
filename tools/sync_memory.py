#!/usr/bin/env python3
"""Safe Memory clone -> Obsidian vault synchronizer.

The synchronizer is intentionally conservative: a remote update is applied
only as a Git fast-forward, and a Vault file changed since the last manifest
blocks the copy.  Runtime status is still rendered so the failure is visible.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from memorylib.live import render_live_status
from memorylib.v2 import file_sha256

EXCLUDES = {".git", ".obsidian", ".claude", ".memory-build", ".memory-backups", "__pycache__", ".pytest_cache", "_live"}
RETIRED_GENERATED_FILES = {
    "builder/context/BUILDER_A_RESEARCH.md",
    "builder/context/BUILDER_B_PRODUCTION.md",
    "builder/context/BUILDER_C_MEMORY.md",
}
LOCK_PATH = Path("/tmp/sportsbrain-memory-v2-sync.lock")


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if check and result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or f"git {' '.join(args)} failed")
    return result


def source_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file() and not any(part in EXCLUDES for part in path.relative_to(root).parts):
            yield path


def vault_manifest(vault: Path) -> dict[str, str]:
    path = vault / "_live" / ".memory_sync_manifest.json"
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("files", {}) if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def write_manifest(vault: Path, files: dict[str, str]) -> None:
    path = vault / "_live" / ".memory_sync_manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": 1, "generated_at": now(), "files": dict(sorted(files.items()))}
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def snapshot_vault(vault: Path) -> Path:
    backup_root = vault / ".memory-backups" / f"pre-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    backup_root.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(vault, backup_root, ignore=shutil.ignore_patterns(".memory-backups"))
    return backup_root


def copy_one(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
    shutil.copy2(source, temporary)
    temporary.replace(target)


def seed_vault(memory: Path, vault: Path) -> tuple[dict[str, str], str]:
    backup = snapshot_vault(vault)
    manifest: dict[str, str] = {}
    for source in source_files(memory):
        rel = source.relative_to(memory).as_posix()
        target = vault / rel
        copy_one(source, target)
        manifest[rel] = file_sha256(target)
    write_manifest(vault, manifest)
    return manifest, f"Seeded canonical Memory into Vault; pre-sync snapshot: {backup}"


def sync_vault(memory: Path, vault: Path) -> tuple[bool, str, dict[str, str]]:
    previous = vault_manifest(vault)
    if not previous:
        return False, "No sync manifest exists; initial seed is required and was not performed automatically.", previous
    source_relpaths = {source.relative_to(memory).as_posix() for source in source_files(memory)}
    conflicts: list[str] = []
    for rel, expected in previous.items():
        path = vault / rel
        if not path.exists() or file_sha256(path) != expected:
            conflicts.append(rel)
    if conflicts:
        return False, "Vault local edits/conflicts detected; sync stopped: " + ", ".join(conflicts[:20]), previous
    removed: list[str] = []
    for rel, expected in previous.items():
        if rel in RETIRED_GENERATED_FILES and rel not in source_relpaths:
            path = vault / rel
            if path.exists():
                path.unlink()
                removed.append(rel)
    current: dict[str, str] = {}
    for source in source_files(memory):
        rel = source.relative_to(memory).as_posix()
        target = vault / rel
        if not target.exists() or file_sha256(source) != file_sha256(target):
            copy_one(source, target)
        current[rel] = file_sha256(target)
    write_manifest(vault, current)
    detail = "Vault canonical files synchronized without overwriting local edits."
    if removed:
        detail += " Removed unchanged retired generated packets: " + ", ".join(sorted(removed)) + "."
    return True, detail, current


def sync_repo(memory: Path, branch: str) -> tuple[str, str]:
    fetched = git(memory, "fetch", "--prune", "origin", check=False)
    if fetched.returncode:
        return "DEGRADED", "Remote fetch failed; local canonical files were not pulled: " + (fetched.stderr.strip() or "unknown fetch error")
    current = git(memory, "branch", "--show-current").stdout.strip()
    if current != branch:
        return "SYNC BLOCKED", f"Current Memory branch is {current!r}; configured sync branch is {branch!r}. No pull attempted."
    status = git(memory, "status", "--porcelain", "--untracked-files=all").stdout.splitlines()
    allowed_prefixes = ("_changeset_p0c001_closure.json", ".claude/", ".obsidian/", "_live/", ".pytest_cache/", ".memory-backups/")
    unsafe = [line for line in status if line[3:] and not line[3:].startswith(allowed_prefixes)]
    if unsafe:
        return "SYNC BLOCKED", "Memory clone has local edits; no pull attempted: " + ", ".join(unsafe[:12])
    remote_ref = f"origin/{branch}"
    remote = git(memory, "rev-parse", "--verify", remote_ref, check=False)
    if remote.returncode:
        return "DEGRADED", f"Remote branch {remote_ref} is not available yet; local branch retained."
    local_sha = git(memory, "rev-parse", "HEAD").stdout.strip()
    remote_sha = remote.stdout.strip()
    if local_sha == remote_sha:
        return "ONLINE", "Memory branch is synchronized with its remote ref."
    ahead = git(memory, "merge-base", "--is-ancestor", remote_ref, "HEAD", check=False).returncode == 0
    behind = git(memory, "merge-base", "--is-ancestor", "HEAD", remote_ref, check=False).returncode == 0
    if ahead and not behind:
        return "DEGRADED", f"Local Memory branch is ahead of {remote_ref}; no pull needed."
    if not behind:
        return "SYNC BLOCKED", f"Memory branch diverged from {remote_ref}; fast-forward-only policy stopped sync."
    pulled = git(memory, "merge", "--ff-only", remote_ref, check=False)
    if pulled.returncode:
        return "SYNC BLOCKED", "Fast-forward pull failed; no local changes were discarded: " + (pulled.stderr.strip() or "unknown merge error")
    return "ONLINE", f"Fast-forwarded Memory branch to {remote_ref}."


def refresh_runtime_graph(memory: Path, vault: Path) -> tuple[dict, str]:
    """Refresh the Vault graph after canonical/runtime inputs are current."""
    from memorylib.semantic_graph import build_semantic_graph_atomic

    try:
        result = build_semantic_graph_atomic(memory, vault)
        return {
            "status": "ONLINE",
            "graph_root": "_live/graph",
            "graph_digest": result["graph_digest"],
            "runtime_included": True,
            "validation": result.get("validation", {"errors": 0, "warnings": 0}),
            "health": result.get("health", {}),
        }, "Semantic Graph V2 runtime projection refreshed and validated."
    except Exception as exc:
        status_path = vault / "_live" / "SEMANTIC_GRAPH_STATUS.json"
        try:
            status = json.loads(status_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            status = {"status": "DEGRADED", "graph_root": "_live/graph", "last_good_graph": False}
        status.setdefault("status", "DEGRADED")
        status.setdefault("graph_root", "_live/graph")
        status["error"] = str(exc)
        return status, f"Semantic Graph V2 refresh failed safely; last valid graph was preserved: {exc}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--memory-repo", required=True, type=Path)
    parser.add_argument("--vault", required=True, type=Path)
    parser.add_argument("--source-repo", required=True, type=Path)
    parser.add_argument("--branch", default="feat/memory-v2-live-obsidian")
    parser.add_argument("--seed", action="store_true", help="one-time recoverable seed of the existing Vault")
    args = parser.parse_args()
    lock = LOCK_PATH.open("w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        return 0
    timestamp = now()
    try:
        graph_status = None
        if args.seed:
            _, detail = seed_vault(args.memory_repo, args.vault)
            sync_state = "ONLINE"
            graph_status, graph_detail = refresh_runtime_graph(args.memory_repo, args.vault)
            if graph_status.get("status") != "ONLINE":
                sync_state = "DEGRADED"
            detail += " " + graph_detail
        else:
            sync_state, detail = sync_repo(args.memory_repo, args.branch)
            if sync_state in {"ONLINE", "DEGRADED"}:
                copied, vault_detail, _ = sync_vault(args.memory_repo, args.vault)
                if not copied:
                    sync_state = "SYNC BLOCKED"
                else:
                    graph_status, graph_detail = refresh_runtime_graph(args.memory_repo, args.vault)
                    if graph_status.get("status") != "ONLINE":
                        sync_state = "DEGRADED"
                    vault_detail += " " + graph_detail
                detail = detail + " " + vault_detail
        render_live_status(args.memory_repo, args.vault, args.source_repo, sync_state=sync_state, sync_detail=detail, last_sync_at=timestamp, semantic_graph=graph_status)
        return 0
    except Exception as exc:
        try:
            render_live_status(args.memory_repo, args.vault, args.source_repo, sync_state="SYNC BLOCKED", sync_detail=f"Synchronizer exception: {exc}", last_sync_at=timestamp)
        except Exception:
            pass
        print(f"Memory sync failed safely: {exc}", file=sys.stderr)
        return 1
    finally:
        fcntl.flock(lock, fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
