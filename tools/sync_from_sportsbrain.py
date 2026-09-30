#!/usr/bin/env python3
"""Deterministic, source-only SportsBrain -> existing Memory V2 ingestion.

Never reads working-tree runtime/private payloads, credentials or chat handoffs.
All changes are validated in an isolated copy before canonical files change.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from memorylib.dashboard import render_all
from memorylib.registry import Registry
from memorylib.v2 import ingest_events

BRANCH = "automation/sportsbrain-source-sync"
STATUS_PATH = "_meta/source_sync_status.json"
MANIFEST_PATH = "_meta/MEMORY_V2.json"
RUNTIME_PREFIXES = ("data/", "docs/data/", "results/", "logs/")
GENERATED = {
    "00_HOME.md", "CURRENT_STATE.md", "CURRENT_PRIORITIES.md", "CURRENT_BLOCKERS.md",
    "CURRENT_TASK.md", "findings/OPEN.md", "findings/RESOLVED.md",
    "builder/CURRENT_CONTEXT_PACKET.md",
}


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def dump(value):
    return json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def allowed_path(path):
    return (path in GENERATED or path in {STATUS_PATH, MANIFEST_PATH}
            or re.fullmatch(r"events/records/EVT-\d{8}-\d+\.json", path) is not None
            or re.fullmatch(r"state/records/STATE-[A-Z0-9-]+\.md", path) is not None
            or path.startswith(("views/", "mocs/", "builder/context/")))


def meaningful_paths(repo, commit):
    parents = git(repo, "show", "-s", "--format=%P", commit).split()
    paths = (git(repo, "diff", "--name-only", parents[0], commit) if parents else
             git(repo, "diff-tree", "--root", "--no-commit-id", "--name-only", "-r", commit)).splitlines()
    return sorted({p for p in paths if not p.startswith(RUNTIME_PREFIXES)})


def source_state(repo):
    head = git(repo, "rev-parse", "refs/remotes/origin/main")
    commits = git(repo, "rev-list", "--first-parent", head).splitlines()
    release = next((sha for sha in commits if meaningful_paths(repo, sha)), None)
    if release is None:
        raise ValueError("No provable source release")
    # Existing marker is useful corroboration, not authority over a newer source
    # commit. Read only its SHA, never arbitrary source/runtime payloads.
    marker = subprocess.run(["git", "-C", str(repo), "show", f"{head}:docs/data/provenance_meta.json"],
                            capture_output=True, text=True)
    marker_sha = None
    if marker.returncode == 0:
        marker_sha = json.loads(marker.stdout).get("source_release_sha")
        if not isinstance(marker_sha, str) or not re.fullmatch(r"[0-9a-f]{40}", marker_sha):
            raise ValueError("Invalid source marker SHA")
        if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", marker_sha, head]).returncode:
            raise ValueError("Source marker is not an ancestor of main")
    return {"source_main_sha": head, "source_release_sha": release,
            "runtime_data_head": head, "source_marker_sha": marker_sha,
            "evidence_timestamp": git(repo, "show", "-s", "--format=%cI", head)}


def validations(root):
    commands = [
        ["-m", "unittest", "discover", "-s", "tests", "-q"],
        ["tools/validate_memory.py"], ["tools/validate_operational_memory.py"],
        ["tools/validate_graph.py"],
        ["tools/validate_visual_metadata.py", "--check-report", "views/visual_metadata.json", "--json"],
        ["tools/memory.py", "acceptance"],
    ]
    import sys
    for command in commands:
        subprocess.run([sys.executable, *command], cwd=root, check=True, stdout=subprocess.DEVNULL)
    subprocess.run(["git", "-C", str(root), "diff", "--check"], check=True)


def plan(root, source):
    state = source_state(source)
    old = json.loads((root / STATUS_PATH).read_text()) if (root / STATUS_PATH).exists() else {}
    if all(old.get(k) == state[k] for k in ("source_main_sha", "source_release_sha")):
        return None
    previous = old.get("source_release_sha") or json.loads((root / MANIFEST_PATH).read_text()).get("source_latest_meaningful_sha")
    if previous and subprocess.run(["git", "-C", str(source), "merge-base", "--is-ancestor", previous, state["source_main_sha"]]).returncode:
        raise ValueError("Source history diverged from last import")
    commits = git(source, "rev-list", "--first-parent", f"{previous}..{state['source_release_sha']}" if previous else state["source_release_sha"]).splitlines()
    changes = []
    for sha in reversed(commits):
        paths = meaningful_paths(source, sha)
        if not paths:
            continue
        # PR linkage is an evidence hint proven by canonical squash subject,
        # never an independent claim about deployment or production health.
        subject = git(source, "show", "-s", "--format=%s", sha)
        match = re.search(r"\(#(\d+)\)$", subject)
        changes.append({"commit_sha": sha, "pr_number": int(match[1]) if match else None,
                        "source_path_count": len(paths)})
    known = old.get("source_changes", [])
    known_shas = {row["commit_sha"] for row in known}
    changes = known + [row for row in changes if row["commit_sha"] not in known_shas]
    state.update(schema="sportsbrain-source-sync-v1", status="ONLINE",
                 last_successful_import=state["source_main_sha"], failure_reason=None,
                 validation_status="PASS", source_changes=changes,
                 production_truth="NOT_INFERRED_FROM_SOURCE", no_auto_closure=True)
    stamp = state["evidence_timestamp"]
    event_id = f"EVT-{stamp[:10].replace('-', '')}-{int(state['source_main_sha'], 16)}"
    event = {"event_id": event_id, "timestamp": stamp, "type": "RESEARCH_GATE",
             "domain": "source-observation", "summary": "Git source identities observed; no production or CEO closure claim.",
             "source_repository": "Philip3006/sportsbrain", "source_sha": state["source_release_sha"],
             "builder": "SYSTEM", "builder_number": "SYSTEM", "ceo_gate_state": "UNCHANGED",
             "affected_workstreams": [], "findings": [], "invariants": [], "supersedes": [],
             "evidence": [f"Git main {state['source_main_sha']}", f"Source release {state['source_release_sha']}"],
             "verification_state": "merged_source", "canonical": True}
    registry = Registry(root).scan()
    records = [o for o in registry.objects if o.object_type == "project-state" and o.status == "current"]
    if len(records) != 1:
        raise ValueError("Expected exactly one canonical current state")
    target = records[0].relpath
    text = (root / target).read_text()
    for key, value in {"source_release_sha": state["source_release_sha"],
                       "runtime_data_head": state["runtime_data_head"]}.items():
        text, count = re.subn(rf"(?m)^{key}: .*?$", f"{key}: {value}", text, count=1)
        if count != 1:
            raise ValueError("Missing source identity field in canonical owner")
    start = "<!-- SOURCE SYNC OBSERVATION -->"
    text = text.split(start)[0].rstrip() + "\n\n" + start + "\n## Source-only observation\n\n"
    text += (f"Inspected main `{state['source_main_sha']}`; source release `{state['source_release_sha']}`.\n"
             "Earlier manual narrative above remains historical/CEO evidence, not a fresh deployment observation.\n"
             "This import grants no activation/publication/betting authority and closes no CEO finding.\n")
    manifest = json.loads((root / MANIFEST_PATH).read_text())
    manifest.update(source_main_sha=state["source_main_sha"], source_latest_meaningful_sha=state["source_release_sha"],
                    source_runtime_head_observed=state["runtime_data_head"],
                    source_latest_meaningful_at=git(source, "show", "-s", "--format=%cI", state["source_release_sha"]),
                    canonical_updated_at=stamp, canonical_status="FRESH")
    return state, event, [
        {"path": target, "content": text},
        {"path": STATUS_PATH, "content": dump(state)},
        {"path": MANIFEST_PATH, "content": dump(manifest)},
    ]


def import_source(root, source, *, validate=True, dry_run=False):
    root, source = root.resolve(), source.resolve()
    payload = plan(root, source)
    if payload is None:
        return {"status": "NO_OP"}
    state, event, records = payload
    with tempfile.TemporaryDirectory(prefix="memory-source-import-") as td:
        stage = (Path(td) / "memory").resolve()
        shutil.copytree(root, stage, ignore=shutil.ignore_patterns(".git", "__pycache__", ".memory-build", ".pytest_cache"))
        # Immutable install-manifest tests require local Git history. A shared
        # local bare clone supplies objects/refs without copying credential config.
        subprocess.run(["git", "clone", "--bare", "--shared", "--local", str(root), str(stage / ".git")],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "--git-dir", str(stage / ".git"), "config", "core.bare", "false"], check=True)
        ingest_events(stage, [event], canonical_records=records, validate_after=False)
        render_all(stage)
        if validate:
            validations(stage)
        changed = [p.relative_to(stage).as_posix() for p in stage.rglob("*")
                   if not any(part in {"__pycache__", ".memory-build", ".git"} for part in p.relative_to(stage).parts)
                   and p.is_file()
                   and (not (root / p.relative_to(stage)).exists() or p.read_bytes() != (root / p.relative_to(stage)).read_bytes())
                   ]
        if any(not allowed_path(p) for p in changed):
            raise ValueError("Unexpected importer scope: " + ", ".join(p for p in changed if not allowed_path(p)))
        if not dry_run:
            # Validated copy only; rollback if filesystem publication fails.
            originals = {p: (root / p).read_bytes() if (root / p).exists() else None for p in changed}
            try:
                for rel in changed:
                    path = root / rel
                    path.parent.mkdir(parents=True, exist_ok=True)
                    temporary = path.with_suffix(path.suffix + ".tmp")
                    temporary.write_bytes((stage / rel).read_bytes())
                    temporary.replace(path)
            except Exception:
                for rel, content in originals.items():
                    if content is None:
                        (root / rel).unlink(missing_ok=True)
                    else:
                        (root / rel).write_bytes(content)
                raise
    return {"status": "ONLINE", "source": state, "changed_files": sorted(changed), "dry_run": dry_run}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", type=Path, required=True)
    parser.add_argument("--memory-repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--status-output", type=Path)
    args = parser.parse_args()
    try:
        result = import_source(args.memory_repo, args.source_repo, dry_run=args.dry_run)
    except Exception as exc:
        result = {"status": "SYNC_BLOCKED", "failure_reason": type(exc).__name__, "validation_status": "FAIL",
                  "source_main_sha": None, "source_release_sha": None, "last_successful_import": None}
        previous = args.memory_repo / STATUS_PATH
        if previous.exists():
            old = json.loads(previous.read_text())
            result["last_successful_import"] = old.get("last_successful_import")
        try:
            current = source_state(args.source_repo)
            result.update({key: current[key] for key in ("source_main_sha", "source_release_sha")})
        except Exception:
            pass
        if args.status_output:
            args.status_output.write_text(dump(result))
        print(dump(result))
        return 1
    if args.status_output:
        args.status_output.write_text(dump(result))
    print(dump(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
