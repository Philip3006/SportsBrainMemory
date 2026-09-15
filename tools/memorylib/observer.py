"""Read-only source observation and non-canonical operational evidence.

This module deliberately keeps source observations outside ``events/records``.
It may read GitHub through the authenticated ``gh`` client and may write only
runtime projections below an Obsidian vault's ``_live`` directory.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

from .v2 import FROZEN_RESEARCH_SHA, freshness_state

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHORT_SHA_RE = re.compile(r"\b[0-9a-f]{7,40}\b")
PR_RE = re.compile(r"(?:pull\s*request|PR)\s*#?(\d+)", re.IGNORECASE)
BUILDER_HEADER_RE = re.compile(r"^BUILDER: ([123])$")
BLOCKER_CLASSES = {"INTERNAL", "EXTERNAL", "CEO_DECISION_REQUIRED", "SAFETY_CRITICAL"}
SECRET_RE = re.compile(r"(?i)(?:bearer\s+|gh[pousr]_)[A-Za-z0-9._-]{20,}")


class ObserverError(RuntimeError):
    """A source observation could not be completed safely."""


class CandidateValidationError(ValueError):
    """A candidate or operational evidence payload is malformed."""


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def _age_state(updated_at: str, now: str) -> str:
    updated = _parse_time(updated_at)
    current = _parse_time(now)
    hours = max(0.0, (current - updated).total_seconds() / 3600.0)
    if hours <= 6:
        return "FRESH"
    if hours <= 24:
        return "AGING"
    return "STALE"


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default
    except (OSError, json.JSONDecodeError):
        return default


def _write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        json.dump(payload, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")
        temporary = Path(handle.name)
    temporary.replace(path)


def _sha_or_none(value: Any, field: str) -> str | None:
    if value in (None, "", "null"):
        return None
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        raise ObserverError(f"malformed GitHub response: {field} must be a 40-character lowercase SHA")
    return value


def _head_sha(raw: dict[str, Any]) -> Any:
    if "head_sha" in raw:
        return raw.get("head_sha")
    head = raw.get("head")
    return head.get("sha") if isinstance(head, dict) else None


def _merge_sha(raw: dict[str, Any]) -> Any:
    if "merge_sha" in raw:
        return raw.get("merge_sha")
    if "merge_commit_sha" in raw:
        return raw.get("merge_commit_sha")
    merge = raw.get("merge_commit")
    return merge.get("oid") if isinstance(merge, dict) else None


def normalize_pr(repository: str, raw: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(raw, dict) or not isinstance(raw.get("number"), int):
        raise ObserverError("malformed GitHub response: pull request number is missing")
    state = str(raw.get("state", "")).upper()
    merged_at = raw.get("merged_at")
    if merged_at:
        state = "MERGED"
    elif state not in {"OPEN", "CLOSED"}:
        raise ObserverError(f"malformed GitHub response: unsupported PR state {state!r}")
    head_sha = _sha_or_none(_head_sha(raw), "head.sha")
    merge_sha = _sha_or_none(_merge_sha(raw), "merge_commit_sha")
    if state == "MERGED" and merge_sha is None:
        raise ObserverError("malformed GitHub response: merged PR has no merge SHA")
    return {
        "repository": repository,
        "number": raw["number"],
        "state": state,
        "title": str(raw.get("title", "")),
        "html_url": raw.get("html_url") or raw.get("url"),
        "head_branch": (raw.get("head") or {}).get("ref") if isinstance(raw.get("head"), dict) else raw.get("head_branch"),
        "base_branch": (raw.get("base") or {}).get("ref") if isinstance(raw.get("base"), dict) else raw.get("base_branch"),
        "head_sha": head_sha,
        "merge_sha": merge_sha,
        "merged_at": merged_at,
        "updated_at": raw.get("updated_at"),
        "created_at": raw.get("created_at"),
    }


class GitHubClient:
    """Minimal GET-only GitHub client backed by authenticated ``gh api``."""

    def __init__(self, gh_bin: str = "gh") -> None:
        self.gh_bin = gh_bin

    def api(self, endpoint: str) -> Any:
        result = subprocess.run([self.gh_bin, "api", endpoint], capture_output=True, text=True, check=False)
        if result.returncode:
            detail = (result.stderr or result.stdout).strip() or "unknown GitHub API error"
            raise ObserverError(f"GitHub unavailable for {endpoint}: {detail}")
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise ObserverError(f"malformed GitHub response for {endpoint}: invalid JSON") from exc

    def repo_snapshot(self, repository: str) -> dict[str, Any]:
        main = self.api(f"repos/{repository}/commits/main")
        if not isinstance(main, dict):
            raise ObserverError(f"malformed GitHub response for {repository}: main commit is not an object")
        main_sha = _sha_or_none(main.get("sha"), "main.sha")
        if main_sha is None:
            raise ObserverError(f"malformed GitHub response for {repository}: main SHA is missing")
        raw_prs = self.api(f"repos/{repository}/pulls?state=all&sort=updated&direction=desc&per_page=100")
        if not isinstance(raw_prs, list):
            raise ObserverError(f"malformed GitHub response for {repository}: pull requests are not a list")
        pull_requests = [normalize_pr(repository, item) for item in raw_prs]
        merged = sorted((p for p in pull_requests if p["state"] == "MERGED"), key=lambda p: p.get("merged_at") or "", reverse=True)
        open_prs = [p for p in pull_requests if p["state"] == "OPEN"]
        closed = [p for p in pull_requests if p["state"] == "CLOSED"]
        return {
            "repository": repository,
            "observed_at": now_utc(),
            "main_sha": main_sha,
            "main_message": ((main.get("commit") or {}).get("message") or "").splitlines()[0],
            "pull_requests": pull_requests,
            "latest_merged_prs": merged[:25],
            "open_prs": open_prs,
            "closed_unmerged_prs": closed,
            "ci": self._ci_snapshot(repository, main_sha),
        }

    def _ci_snapshot(self, repository: str, sha: str) -> dict[str, Any]:
        try:
            runs = self.api(f"repos/{repository}/actions/runs?head_sha={sha}&per_page=20")
            statuses = runs.get("workflow_runs", []) if isinstance(runs, dict) else []
            return {
                "status": "AVAILABLE",
                "workflow_count": len(statuses),
                "completed": sum(1 for item in statuses if item.get("status") == "completed"),
                "successful": sum(1 for item in statuses if item.get("conclusion") == "success"),
                "failed": sum(1 for item in statuses if item.get("conclusion") in {"failure", "cancelled", "timed_out"}),
            }
        except ObserverError as exc:
            return {"status": "UNAVAILABLE", "error": str(exc)}


class FixtureGitHubClient:
    """Deterministic client used by tests and offline observer rehearsals."""

    def __init__(self, snapshots: dict[str, Any]) -> None:
        self.snapshots = snapshots

    def repo_snapshot(self, repository: str) -> dict[str, Any]:
        raw = self.snapshots.get(repository)
        if isinstance(raw, Exception):
            raise raw
        if not isinstance(raw, dict):
            raise ObserverError(f"fixture has no snapshot for {repository}")
        main_sha = _sha_or_none(raw.get("main_sha"), "main_sha")
        if main_sha is None:
            raise ObserverError(f"fixture for {repository} has no main_sha")
        prs = [normalize_pr(repository, item) for item in raw.get("pull_requests", [])]
        merged = sorted((p for p in prs if p["state"] == "MERGED"), key=lambda p: p.get("merged_at") or "", reverse=True)
        return {
            "repository": repository,
            "observed_at": raw.get("observed_at") or now_utc(),
            "main_sha": main_sha,
            "main_message": raw.get("main_message", "fixture"),
            "pull_requests": prs,
            "latest_merged_prs": merged[:25],
            "open_prs": [p for p in prs if p["state"] == "OPEN"],
            "closed_unmerged_prs": [p for p in prs if p["state"] == "CLOSED"],
            "ci": raw.get("ci", {"status": "AVAILABLE", "workflow_count": 0, "completed": 0, "successful": 0, "failed": 0}),
        }


def candidate_id(repository: str, pr_number: int, head_sha: str | None, merge_sha: str | None) -> str:
    identity = "|".join((repository, str(pr_number), head_sha or "", merge_sha or ""))
    return "SRC-CAND-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]


def candidate_from_pr(pr: dict[str, Any], observed_at: str) -> dict[str, Any]:
    cid = candidate_id(pr["repository"], pr["number"], pr.get("head_sha"), pr.get("merge_sha"))
    return {
        "candidate_id": cid,
        "candidate_type": "SOURCE_CANDIDATE_EVENT",
        "canonical": False,
        "promotion_required": True,
        "observed_at": observed_at,
        "first_observed_at": observed_at,
        "last_observed_at": observed_at,
        "observation_count": 1,
        "source_repository": pr["repository"],
        "source_pr": pr["number"],
        "source_state": pr["state"],
        "source_sha": pr.get("head_sha"),
        "source_merge_sha": pr.get("merge_sha"),
        "summary": f"Observed {pr['repository']} PR #{pr['number']} {pr['state']}: {pr.get('title', '')}".strip(),
        "builder": "SYSTEM",
        "builder_number": "SYSTEM",
        "ceo_gate_state": "candidate_pending_ceo_review",
        "verification_state": "observed_source",
        "affected_workstreams": ["SOURCE-OBSERVER"],
        "findings": [],
        "invariants": ["NO-AUTOMATIC-CANONICAL-PROMOTION"],
        "supersedes": [],
        "evidence": [
            f"GitHub observation of {pr['repository']} PR #{pr['number']}",
            f"head SHA: {pr.get('head_sha') or 'UNAVAILABLE'}",
            f"merge SHA: {pr.get('merge_sha') or 'UNAVAILABLE'}",
        ],
        "dedupe_key": {
            "repository": pr["repository"],
            "pr": pr["number"],
            "head_sha": pr.get("head_sha"),
            "merge_sha": pr.get("merge_sha"),
        },
        "url": pr.get("html_url"),
    }


def validate_candidate(candidate: dict[str, Any]) -> None:
    required = {
        "candidate_id", "candidate_type", "canonical", "promotion_required", "observed_at",
        "source_repository", "source_pr", "source_state", "source_sha", "source_merge_sha",
        "summary", "builder", "builder_number", "ceo_gate_state", "verification_state",
        "affected_workstreams", "findings", "invariants", "supersedes", "evidence", "dedupe_key",
    }
    missing = sorted(required - set(candidate))
    if missing:
        raise CandidateValidationError("candidate missing field(s): " + ", ".join(missing))
    if candidate.get("candidate_type") != "SOURCE_CANDIDATE_EVENT":
        raise CandidateValidationError("candidate_type must be SOURCE_CANDIDATE_EVENT")
    if candidate.get("canonical") is not False or candidate.get("promotion_required") is not True:
        raise CandidateValidationError("source candidates must remain non-canonical and require promotion")
    if not isinstance(candidate.get("source_repository"), str) or not candidate["source_repository"].strip():
        raise CandidateValidationError("source_repository must be non-empty")
    if not isinstance(candidate.get("source_pr"), int) or candidate["source_pr"] < 1:
        raise CandidateValidationError("source_pr must be a positive integer")
    for field in ("source_sha", "source_merge_sha"):
        value = candidate.get(field)
        if value is not None and (not isinstance(value, str) or not SHA_RE.fullmatch(value)):
            raise CandidateValidationError(f"{field} must be null or a 40-character lowercase SHA")
    if candidate.get("builder") != "SYSTEM" or candidate.get("builder_number") != "SYSTEM":
        raise CandidateValidationError("source candidates must identify SYSTEM, not an ambiguous builder")
    try:
        _parse_time(candidate["observed_at"])
    except (TypeError, ValueError) as exc:
        raise CandidateValidationError("observed_at must be timezone-aware ISO-8601") from exc
    dedupe = candidate.get("dedupe_key")
    if not isinstance(dedupe, dict):
        raise CandidateValidationError("dedupe_key must be an object")
    expected = candidate_id(candidate["source_repository"], candidate["source_pr"], candidate.get("source_sha"), candidate.get("source_merge_sha"))
    if candidate.get("candidate_id") != expected:
        raise CandidateValidationError("candidate_id does not match repository/PR/head/merge identity")
    if any(SECRET_RE.search(str(value)) for value in candidate.values()):
        raise CandidateValidationError("secret-like material detected in candidate")


def validate_candidate_store(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        return ["candidate store schema must be 1"]
    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        return ["candidate store candidates must be a list"]
    ids: set[str] = set()
    dedupe: set[str] = set()
    for index, candidate in enumerate(candidates):
        try:
            validate_candidate(candidate)
        except CandidateValidationError as exc:
            errors.append(f"candidates[{index}]: {exc}")
            continue
        cid = candidate["candidate_id"]
        key = json.dumps(candidate["dedupe_key"], sort_keys=True)
        if cid in ids:
            errors.append(f"duplicate candidate_id: {cid}")
        if key in dedupe:
            errors.append(f"duplicate candidate identity: {cid}")
        ids.add(cid)
        dedupe.add(key)
    return errors


def _merge_candidates(previous: list[dict[str, Any]], fresh: list[dict[str, Any]], observed_at: str) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {item.get("candidate_id"): dict(item) for item in previous if isinstance(item, dict) and item.get("candidate_id")}
    for candidate in fresh:
        existing = merged.get(candidate["candidate_id"])
        if existing is None:
            merged[candidate["candidate_id"]] = candidate
            continue
        existing["last_observed_at"] = observed_at
        existing["observation_count"] = int(existing.get("observation_count", 1)) + 1
    return [merged[key] for key in sorted(merged)]


def _source_conflicts(memory_repo: Path, snapshots: dict[str, dict[str, Any]], errors: list[dict[str, Any]], previous: dict[str, Any]) -> list[dict[str, Any]]:
    conflicts: list[dict[str, Any]] = []
    source_repo = "Philip3006/sportsbrain"
    observed = {p["number"]: p for p in snapshots.get(source_repo, {}).get("pull_requests", [])}
    if source_repo not in snapshots:
        return conflicts
    event_dir = memory_repo / "events" / "records"
    merge_re = re.compile(r"(?:merge commit|merge SHA|squash SHA)[: ]+([0-9a-f]{40})", re.IGNORECASE)
    for path in sorted(event_dir.glob("*.json")) if event_dir.exists() else []:
        event = _read_json(path, {})
        if not isinstance(event, dict) or event.get("source_repository") != source_repo or not isinstance(event.get("source_pr"), int):
            continue
        number = event["source_pr"]
        current = observed.get(number)
        if current is None:
            conflicts.append({"type": "CANONICAL_SOURCE_MISSING", "severity": "ERROR", "pr": number, "path": str(path.relative_to(memory_repo))})
            continue
        expected_state = "MERGED" if event.get("type") == "PR_MERGED" else None
        if expected_state and current.get("state") != expected_state:
            conflicts.append({"type": "PR_STATE_MISMATCH", "severity": "ERROR", "pr": number, "expected": expected_state, "observed": current.get("state")})
        expected_head = event.get("source_sha")
        if expected_head and current.get("head_sha") and expected_head != current.get("head_sha"):
            conflicts.append({"type": "SOURCE_HEAD_MISMATCH", "severity": "ERROR", "pr": number, "expected": expected_head, "observed": current.get("head_sha")})
        evidence = " ".join(str(item) for item in event.get("evidence", []))
        merge_match = merge_re.search(evidence)
        if merge_match and current.get("merge_sha") and merge_match.group(1) != current.get("merge_sha"):
            conflicts.append({"type": "SOURCE_MERGE_SHA_MISMATCH", "severity": "ERROR", "pr": number, "expected": merge_match.group(1), "observed": current.get("merge_sha")})

    manifest = _read_json(memory_repo / "_meta" / "MEMORY_V2.json", {})
    if manifest.get("frozen_research_sha") != FROZEN_RESEARCH_SHA:
        conflicts.append({"type": "RESEARCH_SHA_MISMATCH", "severity": "SAFETY_CRITICAL", "expected": FROZEN_RESEARCH_SHA, "observed": manifest.get("frozen_research_sha")})
    research = _read_text(memory_repo / "workstreams" / "TOP5-RESEARCH.md")
    if not all(token in research for token in ("2425", "2526", "SEALED")):
        conflicts.append({"type": "SEALED_STATE_CONFLICT", "severity": "SAFETY_CRITICAL", "detail": "2425/2526 SEALED markers are incomplete"})
    safety = "\n".join(_read_text(memory_repo / name) for name in ("CURRENT_STATE.md", "CURRENT_PRIORITIES.md", "workstreams/TOP5-SHADOW-INTEGRATION.md", "workstreams/TOP5-ACTIVATION-READINESS.md"))
    if "NO-BET" not in safety:
        conflicts.append({"type": "NO_BET_STATE_CONFLICT", "severity": "SAFETY_CRITICAL", "detail": "NO-BET marker is absent from current operational truth"})
    if "not approved" not in safety.lower() and "no live activation" not in safety.lower():
        conflicts.append({"type": "LIVE_ACTIVATION_STATE_CONFLICT", "severity": "SAFETY_CRITICAL", "detail": "no-live-activation restriction is absent"})
    for handoff in previous.get("builder_handoffs", []) if isinstance(previous.get("builder_handoffs"), list) else []:
        observed_at = handoff.get("observed_at") if isinstance(handoff, dict) else None
        if observed_at:
            try:
                if _age_state(observed_at, now_utc()) == "STALE":
                    conflicts.append({"type": "BUILDER_STATUS_STALE", "severity": "CEO_DECISION_REQUIRED", "builder_number": handoff.get("builder_number"), "observed_at": observed_at})
            except (TypeError, ValueError):
                conflicts.append({"type": "BUILDER_STATUS_STALE", "severity": "CEO_DECISION_REQUIRED", "builder_number": handoff.get("builder_number")})
    return conflicts


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    except OSError:
        return ""


def _canonical_freshness(memory_repo: Path) -> str:
    manifest = _read_json(memory_repo / "_meta" / "MEMORY_V2.json", {})
    try:
        return freshness_state(manifest["canonical_updated_at"], manifest["source_latest_meaningful_at"])
    except Exception:
        return "STALE"


def observe_sources(
    memory_repo: Path,
    client: Any,
    repositories: list[str] | None = None,
    previous: dict[str, Any] | None = None,
    observed_at: str | None = None,
) -> dict[str, Any]:
    observed_at = observed_at or now_utc()
    previous = previous or {}
    repositories = repositories or ["Philip3006/sportsbrain", "Philip3006/SportsBrainMemory"]
    snapshots: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    drift: list[dict[str, Any]] = []
    for repository in repositories:
        try:
            snapshot = client.repo_snapshot(repository)
            snapshots[repository] = snapshot
            before = (previous.get("repositories") or {}).get(repository, {})
            if before.get("main_sha") and before.get("main_sha") != snapshot.get("main_sha"):
                drift.append({"repository": repository, "previous_main_sha": before["main_sha"], "current_main_sha": snapshot["main_sha"], "detected_at": observed_at})
        except Exception as exc:
            errors.append({"repository": repository, "type": "SOURCE_UNAVAILABLE", "detail": str(exc)})

    old_candidates = previous.get("candidates", []) if isinstance(previous.get("candidates"), list) else []
    fresh_candidates = [candidate_from_pr(pr, observed_at) for snapshot in snapshots.values() for pr in snapshot.get("pull_requests", [])]
    candidates = _merge_candidates(old_candidates, fresh_candidates, observed_at)
    conflicts = _source_conflicts(memory_repo, snapshots, errors, previous)
    pr59 = [candidate for candidate in candidates if candidate.get("source_repository") == "Philip3006/sportsbrain" and candidate.get("source_pr") == 59]
    now = now_utc()
    observer_freshness = _age_state(observed_at, now) if snapshots else ("STALE" if not previous.get("observed_at") else _age_state(previous["observed_at"], now))
    status = "ONLINE" if not errors else "DEGRADED"
    if not snapshots and previous.get("repositories"):
        snapshots = previous["repositories"]
        status = "DEGRADED"
    return {
        "schema": 1,
        "observed_at": observed_at,
        "status": status,
        "observer_freshness": observer_freshness,
        "canonical_freshness": _canonical_freshness(memory_repo),
        "repositories": snapshots,
        "source_drift": drift,
        "errors": errors,
        "conflicts": conflicts,
        "candidates": candidates,
        "pr_59": {
            "detected": bool(pr59),
            "candidate_ids": [item["candidate_id"] for item in pr59],
            "state": pr59[0].get("source_state") if pr59 else None,
            "promotion_required": bool(pr59),
        },
        "blockers": [
            {
                "blocker_id": "BLK-TOP5-PROVIDER-QUOTA",
                "classification": "EXTERNAL",
                "status": "REPORTED_OPEN",
                "summary": "The Odds API quota is exhausted; real provider evidence is blocked.",
                "resolution_requires": "external quota restoration and explicit verification",
                "auto_resolve": False,
            }
        ],
        "builder_handoffs": previous.get("builder_handoffs", []),
    }


def validate_blocker(blocker: dict[str, Any]) -> None:
    required = {"blocker_id", "classification", "status", "summary", "auto_resolve"}
    missing = sorted(required - set(blocker))
    if missing:
        raise CandidateValidationError("blocker missing field(s): " + ", ".join(missing))
    if blocker["classification"] not in BLOCKER_CLASSES:
        raise CandidateValidationError("blocker classification must be INTERNAL, EXTERNAL, CEO_DECISION_REQUIRED, or SAFETY_CRITICAL")
    if blocker.get("auto_resolve") is not False:
        raise CandidateValidationError("blockers may not be automatically resolved")


def _extract_first(pattern: str, text: str) -> str | None:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip().strip("`") if match else None


def parse_builder_handoff(text: str, observed_at: str | None = None) -> dict[str, Any]:
    lines = text.splitlines()
    first = next((line.strip() for line in lines if line.strip()), "")
    match = BUILDER_HEADER_RE.fullmatch(first)
    if not match:
        raise CandidateValidationError("handoff must begin with exactly BUILDER: 1, BUILDER: 2, or BUILDER: 3")
    builder_number = int(match.group(1))
    normalized = "\n".join(line.strip() for line in lines if line.strip())
    role = _extract_first(r"^ROLE:\s*(.+)$", normalized)
    branch = _extract_first(r"(?:local\s+)?branch:\s*([^\n]+)", normalized)
    head = _extract_first(r"(?:exact\s+)?head(?:\s+sha)?\s*:\s*([0-9a-f]{40})", normalized)
    if head is None:
        head = _extract_first(r"\bcommit\s*:\s*([0-9a-f]{40})", normalized)
    pr_match = PR_RE.search(normalized)
    status = _extract_first(r"^status:\s*(.+)$", normalized)
    tests = _extract_first(r"(?:tests?|test suite):\s*([^\n]+)", normalized)
    tests_passed_match = re.search(r"(\d+)\s+passed", normalized, re.IGNORECASE)
    ci = _extract_first(r"^CI:\s*(.+)$", normalized)
    blockers_text = _extract_first(r"^blockers?:\s*(.+)$", normalized)
    safety = [line for line in lines if re.search(r"safety|no production|no runtime|no mutation|no live", line, re.IGNORECASE)]
    blocker_items: list[dict[str, Any]] = []
    if blockers_text and blockers_text.lower() not in {"none", "n/a", "-"}:
        lowered = blockers_text.lower()
        classification = "EXTERNAL" if any(token in lowered for token in ("quota", "provider", "credential", "outage")) else "CEO_DECISION_REQUIRED"
        blocker_items.append({
            "blocker_id": "BLK-HANDOFF-" + hashlib.sha256(blockers_text.encode("utf-8")).hexdigest()[:16],
            "classification": classification,
            "status": "REPORTED_OPEN",
            "summary": blockers_text,
            "auto_resolve": False,
        })
    observed_at = observed_at or now_utc()
    identity = "|".join((str(builder_number), branch or "", head or "", str(pr_match.group(1) if pr_match else ""), status or ""))
    evidence_id = "HANDOFF-CAND-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:24]
    result = {
        "candidate_id": evidence_id,
        "candidate_type": "CANDIDATE_OPERATIONAL_EVIDENCE",
        "canonical": False,
        "promotion_required": True,
        "observed_at": observed_at,
        "builder": f"Builder {builder_number}",
        "builder_number": builder_number,
        "role": role,
        "branch": branch.strip() if branch else None,
        "head_sha": head,
        "source_pr": int(pr_match.group(1)) if pr_match else None,
        "status": status,
        "tests": tests,
        "tests_passed": int(tests_passed_match.group(1)) if tests_passed_match else None,
        "ci": ci,
        "blockers": blocker_items,
        "safety_confirmation": safety,
        "raw_header": first,
    }
    if any(SECRET_RE.search(str(value)) for value in result.values()):
        raise CandidateValidationError("secret-like material detected in handoff")
    return result


def validate_handoff_evidence(evidence: dict[str, Any]) -> None:
    if evidence.get("candidate_type") != "CANDIDATE_OPERATIONAL_EVIDENCE" or evidence.get("canonical") is not False or evidence.get("promotion_required") is not True:
        raise CandidateValidationError("builder handoff evidence must remain non-canonical and require promotion")
    builder_number = evidence.get("builder_number")
    if builder_number not in {1, 2, 3} or evidence.get("builder") != f"Builder {builder_number}":
        raise CandidateValidationError("handoff builder identity must be an explicit matching Builder 1/2/3")
    if evidence.get("head_sha") is not None and not SHA_RE.fullmatch(str(evidence["head_sha"])):
        raise CandidateValidationError("handoff head_sha must be a full lowercase SHA when present")
    for blocker in evidence.get("blockers", []):
        validate_blocker(blocker)


def ingest_handoff(store_path: Path, evidence: dict[str, Any]) -> dict[str, Any]:
    validate_handoff_evidence(evidence)
    payload = _read_json(store_path, {"schema": 1, "candidates": []})
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        payload = {"schema": 1, "candidates": []}
    candidates = payload.setdefault("candidates", [])
    existing = next((item for item in candidates if item.get("candidate_id") == evidence["candidate_id"]), None)
    if existing is None:
        candidates.append(evidence)
    else:
        existing["last_observed_at"] = evidence["observed_at"]
        existing["observation_count"] = int(existing.get("observation_count", 1)) + 1
    payload["generated_at"] = now_utc()
    payload["candidates"] = sorted(candidates, key=lambda item: item.get("candidate_id", ""))
    _write_json_atomic(store_path, payload)
    return evidence


def render_control_plane(payload: dict[str, Any]) -> str:
    repositories = payload.get("repositories", {})
    sports = repositories.get("Philip3006/sportsbrain", {})
    memory = repositories.get("Philip3006/SportsBrainMemory", {})
    lines = [
        "<!-- GENERATED BY SportsBrainMemory Source Observer: RUNTIME ONLY -->",
        "# SportsBrain CEO Control Plane",
        "",
        f"- Project status: **{payload.get('status', 'DEGRADED')}**",
        f"- Observer freshness: **{payload.get('observer_freshness', 'STALE')}**",
        f"- Canonical Memory freshness: **{payload.get('canonical_freshness', 'STALE')}**",
        f"- Observed at: `{payload.get('observed_at', 'unknown')}`",
        "",
        "## Builder State",
        "",
        "- Builder 1 — Real NO-BET Shadow Execution active; real provider evidence blocked by the reported external Odds API quota exhaustion.",
        "- Builder 2 — Independent Shadow Validation Gate merged; New Provider Redundancy workstream active.",
        "- Builder 3 — Memory Source Observer / CEO Control Plane active; canonical history remains append-only.",
        "",
        "## Top-5 Safety State",
        "",
        "- NO-BET",
        "- unpublished",
        "- no live activation",
        "- no production model selected",
        "- Research SHA: `6eaabbec7d0182103d815c72fae4976e261b40aa`",
        "- 2425 / 2526: **SEALED**",
        "",
        "## Source Main",
        "",
        f"- SportsBrain main: `{sports.get('main_sha', 'UNAVAILABLE')}`",
        f"- Memory main: `{memory.get('main_sha', 'UNAVAILABLE')}`",
        "",
        "## Latest Merged PRs",
        "",
    ]
    for repo, snapshot in repositories.items():
        for pr in snapshot.get("latest_merged_prs", [])[:10]:
            lines.append(f"- `{repo}` PR #{pr['number']} — **MERGED** — head `{pr.get('head_sha') or 'UNAVAILABLE'}` — merge `{pr.get('merge_sha') or 'UNAVAILABLE'}` — {pr.get('title', '')}")
    lines += ["", "## Open PRs", ""]
    for repo, snapshot in repositories.items():
        for pr in snapshot.get("open_prs", [])[:20]:
            lines.append(f"- `{repo}` PR #{pr['number']} — **OPEN** — head `{pr.get('head_sha') or 'UNAVAILABLE'}` — {pr.get('title', '')}")
    lines += ["", "## Candidate Events", "", "All source candidates remain non-canonical and require explicit CEO promotion.", ""]
    for candidate in payload.get("candidates", [])[-30:]:
        lines.append(f"- `{candidate['candidate_id']}` — `{candidate['source_repository']}` PR #{candidate['source_pr']} — {candidate['source_state']} — promotion required")
    lines += ["", "## Blockers", ""]
    for blocker in payload.get("blockers", []):
        lines.append(f"- `{blocker['classification']}` `{blocker['status']}` — {blocker['summary']} (auto-resolve: no)")
    lines += ["", "## Source Conflicts / Mismatches", ""]
    if payload.get("conflicts"):
        for conflict in payload["conflicts"]:
            lines.append(f"- **{conflict.get('severity', 'ERROR')}** `{conflict.get('type')}` — {json.dumps(conflict, sort_keys=True)}")
    else:
        lines.append("- None detected in the observed source set.")
    lines += ["", "## PR #59", "", f"- Detected independently: **{payload.get('pr_59', {}).get('detected', False)}**; candidate promotion required: **{payload.get('pr_59', {}).get('promotion_required', False)}**.", "", "## Failure Behavior", "", "- GitHub/source failures preserve last-known snapshots and candidates; they never rewrite canonical Memory or replace it with empty data.", "- This file is runtime-only and is not canonical history.", ""]
    return "\n".join(lines)


def write_runtime_outputs(vault: Path, payload: dict[str, Any]) -> None:
    live = vault / "_live"
    _write_json_atomic(live / "SOURCE_OBSERVER.json", payload)
    _write_json_atomic(live / "SOURCE_CANDIDATES.json", {"schema": 1, "generated_at": payload.get("observed_at"), "candidates": payload.get("candidates", [])})
    _write_json_atomic(live / "BLOCKERS.json", {"schema": 1, "generated_at": payload.get("observed_at"), "blockers": payload.get("blockers", [])})
    _write_json_atomic(live / "BUILDER_HANDOFFS.json", {"schema": 1, "generated_at": payload.get("observed_at"), "candidates": payload.get("builder_handoffs", [])})
    live.mkdir(parents=True, exist_ok=True)
    temporary = live / "CEO_CONTROL_PLANE.md.tmp"
    temporary.write_text(render_control_plane(payload).rstrip() + "\n", encoding="utf-8")
    temporary.replace(live / "CEO_CONTROL_PLANE.md")


def observe_and_write(memory_repo: Path, vault: Path, client: Any | None = None, repositories: list[str] | None = None) -> dict[str, Any]:
    client = client or GitHubClient()
    previous = _read_json(vault / "_live" / "SOURCE_OBSERVER.json", {})
    payload = observe_sources(memory_repo, client, repositories=repositories, previous=previous)
    write_runtime_outputs(vault, payload)
    return payload
