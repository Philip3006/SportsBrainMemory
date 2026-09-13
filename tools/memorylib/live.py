"""Read-only source inspection and near-live Obsidian projections."""
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
from typing import Any

from .v2 import V2_GENERATED_MARKER, file_sha256, freshness_state, parse_timestamp, read_manifest


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError((result.stderr or result.stdout).strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _git_optional(repo: Path, *args: str) -> str | None:
    try:
        return _git(repo, *args)
    except RuntimeError:
        return None


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _read_health(source_repo: Path) -> dict[str, Any]:
    path = source_repo / "docs" / "data" / "health.json"
    if not path.exists():
        return {"overall": "unknown", "generated_at": None, "jobs": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"overall": "unknown", "generated_at": None, "jobs": []}


def _meaningful_commit(source_repo: Path, ref: str) -> tuple[str, str, str]:
    raw = _git_optional(source_repo, "log", ref, "--format=%H%x09%aI%x09%s", "--no-merges", "-n", "60") or ""
    for line in raw.splitlines():
        parts = line.split("\t", 2)
        if len(parts) == 3 and not parts[2].lower().startswith("auto:"):
            return parts[0], parts[1], parts[2]
    head = _git_optional(source_repo, "rev-parse", ref) or "UNRESOLVED"
    return head, _iso_now(), "No meaningful non-runtime commit found"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text.rstrip() + "\n", encoding="utf-8")
    temporary.replace(path)


def render_live_status(memory_repo: Path, vault: Path, source_repo: Path, *, sync_state: str = "ONLINE", sync_detail: str = "", last_sync_at: str | None = None) -> dict[str, Any]:
    manifest = read_manifest(memory_repo)
    now = _iso_now()
    memory_head = _git_optional(memory_repo, "rev-parse", "HEAD") or "UNRESOLVED"
    memory_branch = _git_optional(memory_repo, "branch", "--show-current") or "UNRESOLVED"
    source_ref = "origin/main" if _git_optional(source_repo, "rev-parse", "--verify", "origin/main") else "main"
    source_head = _git_optional(source_repo, "rev-parse", source_ref) or "UNRESOLVED"
    meaningful_sha, meaningful_at, meaningful_subject = _meaningful_commit(source_repo, source_ref)
    health = _read_health(source_repo)
    health_overall = str(health.get("overall", "unknown")).lower()
    try:
        freshness = freshness_state(manifest["canonical_updated_at"], meaningful_at)
    except Exception:
        freshness = "STALE"
    if sync_state != "ONLINE":
        overall = sync_state
    elif health_overall not in {"ok", "healthy"}:
        overall = "DEGRADED"
    elif freshness == "STALE":
        overall = "STALE"
    else:
        overall = "ONLINE"

    prs = []
    refs = _git_optional(source_repo, "for-each-ref", "--format=%(refname:short)\t%(objectname)", "refs/remotes/origin") or ""
    for line in refs.splitlines():
        if "top5-shadow-readiness" in line:
            ref, sha = line.split("\t", 1)
            main_log = _git_optional(source_repo, "log", source_ref, "--format=%H%x09%s", "-n", "120") or ""
            merged_line = next((item for item in main_log.splitlines() if "#56" in item and "top-5" in item.lower()), None)
            if merged_line:
                merge_sha, merge_subject = merged_line.split("\t", 1)
                prs.append(f"- PR #56 / `{ref}` — head `{sha}` — **merged into `{source_ref}` at `{merge_sha}`**; live activation remains disabled")
            else:
                prs.append(f"- PR #56 / `{ref}` — `{sha}` — **open/not merged**")
    if not prs:
        main_log = _git_optional(source_repo, "log", source_ref, "--format=%H%x09%s", "-n", "120") or ""
        merged_line = next((item for item in main_log.splitlines() if "#56" in item and "top-5" in item.lower()), None)
        if merged_line:
            merge_sha, _ = merged_line.split("\t", 1)
            prs.append(f"- PR #56 / `feat/top5-shadow-readiness` — **merged into `{source_ref}` at `{merge_sha}`**; live activation remains disabled")
        else:
            prs.append("- PR #56 / `feat/top5-shadow-readiness` — remote ref not available in this checkout")
    jobs = health.get("jobs", []) if isinstance(health.get("jobs"), list) else []
    relevant_jobs = [j for j in jobs if isinstance(j, dict) and j.get("job") in {"odds_refresh", "aggregate_health", "bundesliga2_live_push", "consume_pending_bets"}]
    ci_lines = [
        f"- Local source health: **{health_overall.upper()}** (generated `{health.get('generated_at', 'unknown')}`)",
        f"- Relevant job records: `{len(relevant_jobs)}`",
        "- Live GitHub CI: not queried by this local-only renderer; source refs and checked-in health are shown instead.",
    ]
    sync_text = sync_detail or "No sync warning."
    status_text = "\n".join([
        V2_GENERATED_MARKER,
        "# SportsBrain Live Status",
        "",
        f"- Status: **{overall}**",
        f"- Generated at: `{now}`",
        f"- Source main SHA: `{source_head}` ({source_ref})",
        f"- Latest meaningful source merge: `{meaningful_sha}` — {meaningful_subject} ({meaningful_at})",
        f"- Current Memory canonical SHA: `{memory_head}` ({memory_branch})",
        f"- Memory freshness: **{freshness}** — canonical updated `{manifest.get('canonical_updated_at', 'unknown')}`",
        f"- Last sync attempt: `{last_sync_at or now}`",
        "",
        "## CURRENT BUILDERS",
        "",
        "- **Builder A — Research:** final Top-5 audit active; true A/B/A' contamination, BL1 parity, corrected statistics, no sealed-data access.",
        "- **Builder B — Production:** PR #56 Shadow Readiness merged but disabled-by-default; no live activation.",
        f"- **Builder C — Memory/Observability:** branch `{memory_branch}`; canonical/live separation and safe sync maintained.",
        "",
        "## OPEN PRs",
        "",
        *prs,
        "",
        "## CI / RUNTIME",
        "",
        *ci_lines,
        "",
        "## STABILITY",
        "",
        "- Engineering state: **technically complete** per the current canonical handoff.",
        "- Formal 72h Stability Soak: **DEFERRED** on external free-quota dependency; not fabricated or started.",
        "",
        "## TOP-5",
        "",
        "- Research baseline: BL1 v7 frozen; DEV/CALIB/HOLDOUT semantics retained; 2425 and 2526 sealed.",
        "- Production architecture: complete, disabled by default, cumulative rollout gates, no active registration.",
        "- Shadow Readiness: merged hardening is disabled-by-default; exact production activation remains a CEO gate.",
        "",
        "## SIGNAL-TIME",
        "",
        "- Approved shape only: event-relative bounded window + minimum/maximum lead time + maximum odds age + separate closing capture + idempotent dispatch + bulk market reuse.",
        "- Exact production values: **not approved**.",
        "",
        "## SYNC",
        "",
        f"- `{sync_state}` — {sync_text}",
        "- Safety: fetch first; fast-forward only; no hard reset; no local-edit discard; conflicts block sync.",
        "",
        "## DEFERRED DEPENDENCIES / NEXT CEO GATE",
        "",
        "- Resolve the external free-quota dependency before the 72h soak.",
        "- Review the merged PR #56 hardening and decide whether any disabled Shadow Readiness activation is warranted.",
        "- Approve exact Signal-Time values only after schedule/quota evidence.",
        "- Champions League remains after Top-5 completion.",
        "",
    ])
    _write(vault / "_live" / "LIVE_STATUS.md", status_text)
    _write(vault / "_live" / "BUILDERS.md", "\n".join([V2_GENERATED_MARKER, "# Builders", "", "- Builder A — Research", "- Builder B — Production", "- Builder C — Memory/Observability", "- CODEX is the sole builder platform."]))
    _write(vault / "_live" / "PRS.md", "\n".join([V2_GENERATED_MARKER, "# Open SportsBrain PRs", "", *prs]))
    _write(vault / "_live" / "CI_STATUS.md", "\n".join([V2_GENERATED_MARKER, "# CI and Runtime Status", "", *ci_lines]))
    _write(vault / "_live" / "SYNC_STATUS.md", "\n".join([V2_GENERATED_MARKER, "# Memory Sync Status", "", f"- Status: **{sync_state}**", f"- Last attempt: `{last_sync_at or now}`", f"- {sync_text}", "", "No hard reset or destructive merge is permitted."]))
    payload = {"generated_at": now, "status": overall, "sync_state": sync_state, "source_main_sha": source_head, "latest_meaningful_sha": meaningful_sha, "memory_sha": memory_head, "memory_branch": memory_branch, "memory_freshness": freshness}
    _write(vault / "_live" / "STATUS.json", json.dumps(payload, indent=2, sort_keys=True) + "\n")
    return payload
