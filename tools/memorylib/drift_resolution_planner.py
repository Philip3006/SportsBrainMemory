"""Read-only Memory Drift Resolution Planner V7.

This module turns existing Consistency Auditor V5 findings and optional
Dispatcher Context Envelope V1 evidence into a deterministic review plan. It
does not repair files, promote candidates, resolve history, or grant authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
from typing import Any, Iterable, Mapping, TypedDict

from .consistency_auditor import ConsistencyAudit, audit_consistency
from .context_compiler import _digest, _normal_text, _parse_time, _stable
from .dispatcher_context_envelope import (
    CLASSIFICATIONS,
    DispatcherContextEnvelope,
    _audit_semantic_digest as _v5_audit_semantic_digest,
    _validate_payload,
)
from .governance import BUILDER_NUMBERS, BUILDER_ROLES


PLANNER_SCHEMA = 7
PLANNER_VERSION = "memory-drift-resolution-planner-v7.0"
PLANNER_STATUSES = frozenset({
    "REMEDIATION_NOT_REQUIRED",
    "REMEDIATION_REVIEW_REQUIRED",
    "REMEDIATION_FAILED_CLOSED",
})
REMEDIATION_CLASSES = frozenset({
    "NO_ACTION",
    "REFRESH_CURRENT_VIEW",
    "REGENERATE_DERIVED_VIEW",
    "REVIEW_CANONICAL_CONFLICT",
    "PROMOTION_REVIEW_REQUIRED",
    "REMOVE_UNSUPPORTED_RUNTIME_REFERENCE",
    "GOVERNANCE_REVIEW_REQUIRED",
    "SAFETY_REVIEW_REQUIRED",
    "INSUFFICIENT_EVIDENCE",
})
DISPATCHER_IMPACTS = frozenset({"CONTEXT_BLOCKING", "CONTEXT_DEGRADED", "NON_BLOCKING"})
SAFETY_MARKERS = (
    "NO-BET",
    "NO-LIVE-ACTIVATION",
    "SEALED 2425/2526",
    "Closing odds benchmark-only",
)
DEFAULT_PROHIBITED_ACTIONS = (
    "do not execute proposed remediation automatically",
    "do not rewrite canonical history or mutate canonical records",
    "do not mutate Vault runtime, Semantic Graph runtime, or runtime candidates",
    "do not promote evidence, launch Builders/Dispatcher, merge, deploy, or activate production",
    "do not grant CEO authorization or access sealed 2425/2526 data",
)


class DriftPlannerError(ValueError):
    """A planner input or generated plan failed closed."""


class DriftPlannerValidationError(DriftPlannerError):
    """A persisted remediation plan failed its contract."""


class DriftResolutionPlan(TypedDict, total=False):
    schema_version: int
    planner_version: str
    planner_id: str
    planner_status: str
    source_memory_sha: str
    reference_time: str
    consistency_audit_digest: str
    consistency_audit_ref: str
    consistency_audit: dict[str, Any]
    dispatcher_context_envelope_digest: str | None
    dispatcher_context_envelope_ref: str | None
    dispatcher_context_envelope: dict[str, Any] | None
    dispatcher_classification: str
    governed_builders: dict[str, str]
    findings: list[dict[str, Any]]
    summary: dict[str, Any]
    review_flags: list[str]
    safety_invariants: list[dict[str, str]]
    prohibited_actions: list[str]
    actions_are_proposals_only: bool
    automatic_repair: bool
    candidate_promotion: bool
    authorization_created: bool
    source_provenance: list[str]
    semantic_plan_digest: str
    generated_at: str


@dataclass(frozen=True)
class DriftResolutionCompilation:
    plan: DriftResolutionPlan
    markdown: str


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _audit_payload(audit: ConsistencyAudit | Mapping[str, Any]) -> dict[str, Any]:
    return audit.to_dict() if isinstance(audit, ConsistencyAudit) else dict(audit)


def _validate_audit_input(audit: Mapping[str, Any]) -> None:
    required = {"schema_version", "source_memory_sha", "reference_time", "overall_status", "runtime_available", "findings", "semantic_digest"}
    missing = sorted(required - set(audit))
    if missing:
        raise DriftPlannerError("V5 audit missing field(s): " + ", ".join(missing))
    if not isinstance(audit.get("findings"), list):
        raise DriftPlannerError("V5 audit findings must be a list")
    if audit.get("semantic_digest") != _v5_audit_semantic_digest(audit):
        raise DriftPlannerError("V5 audit semantic digest does not match its findings")


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _read_envelope(value: Path | Mapping[str, Any] | DispatcherContextEnvelope | None) -> dict[str, Any] | None:
    if value is None:
        return None
    if isinstance(value, Mapping):
        try:
            return dict(_validate_payload(value))
        except Exception as exc:
            raise DriftPlannerError(f"Dispatcher Context Envelope is invalid: {exc}") from exc
    path = Path(value)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DriftPlannerError(f"Dispatcher Context Envelope is not valid JSON: {path}") from exc
    return _read_envelope(payload)


def _path_groups(paths: Iterable[Any]) -> tuple[list[str], list[str]]:
    canonical: set[str] = set()
    runtime: set[str] = set()
    for raw in paths:
        path = _normal_text(raw)
        if not path:
            continue
        if path.startswith("_live/") or "/_live/" in path or path.startswith("live/"):
            runtime.add(path)
        else:
            canonical.add(path)
    return sorted(canonical), sorted(runtime)


def _authority_classes(finding: Mapping[str, Any]) -> tuple[list[str], list[str], list[str]]:
    values = {str(item).upper() for item in finding.get("authority_classes", []) if _normal_text(item)}
    for item in finding.get("evidence", []) if isinstance(finding.get("evidence"), list) else []:
        if isinstance(item, Mapping):
            for key in ("authority_class", "source_authority", "target_authority"):
                value = item.get(key)
                if value:
                    values.add(str(value).upper())
    values = set(values)
    authoritative = sorted(values & {"CANONICAL", "VERIFIED"})
    non_authoritative = sorted(values - {"CANONICAL", "VERIFIED"})
    conflicting = sorted(values) if str(finding.get("status", "")).upper() in {"CONFLICT", "GOVERNANCE_DRIFT"} and len(values) > 1 else []
    if not conflicting and len(authoritative) > 1:
        conflicting = authoritative[1:]
    return authoritative, conflicting, non_authoritative


def _finding_text(finding: Mapping[str, Any]) -> str:
    return " ".join(str(finding.get(key) or "") for key in ("status", "domain", "summary", "recommended_human_action")).casefold()


def _kind(finding: Mapping[str, Any]) -> str:
    status = str(finding.get("status", "")).upper()
    domain = str(finding.get("domain", "")).casefold()
    text = _finding_text(finding)
    if status == "SAFETY_INVARIANT_MISSING" or domain == "safety" or "no-bet" in text or "no-live" in text or "sealed" in text:
        return "safety"
    if status == "GOVERNANCE_DRIFT" or domain == "governance" or "unsupported builder" in text:
        return "governance"
    if domain in {"dependencies", "authority"} and status in {"CONFLICT", "MISSING", "NONAUTHORITATIVE_ONLY"}:
        return "dependency"
    if status == "STALE" or "stale" in text:
        return "stale"
    if status == "UNKNOWN" or "unknown" in text:
        return "unknown"
    if status == "NONAUTHORITATIVE_ONLY" or "non-authoritative" in text or "candidate" in text or "runtime-derived" in text:
        return "candidate"
    if status == "CONFLICT" or domain in {"semantic_graph", "builder_status", "documentation", "current_view"}:
        return "conflict"
    return "warning"


def _priority(kind: str) -> int:
    return {"safety": 100, "governance": 90, "dependency": 80, "conflict": 70, "stale": 60, "candidate": 50, "unknown": 45, "warning": 30}.get(kind, 0)


def _remediation(kind: str, finding: Mapping[str, Any], canonical_paths: list[str], runtime_paths: list[str]) -> str:
    status = str(finding.get("status", "")).upper()
    domain = str(finding.get("domain", "")).casefold()
    if kind == "safety":
        return "SAFETY_REVIEW_REQUIRED"
    if kind == "governance":
        if "unsupported builder" in _finding_text(finding) or "builder 6" in _finding_text(finding) or "builder 7" in _finding_text(finding) or "builder 8" in _finding_text(finding):
            return "REMOVE_UNSUPPORTED_RUNTIME_REFERENCE"
        return "GOVERNANCE_REVIEW_REQUIRED"
    if kind == "dependency":
        return "REVIEW_CANONICAL_CONFLICT" if status == "CONFLICT" or domain == "authority" else "INSUFFICIENT_EVIDENCE"
    if kind == "conflict":
        if runtime_paths and not canonical_paths:
            return "REGENERATE_DERIVED_VIEW"
        return "REVIEW_CANONICAL_CONFLICT"
    if kind == "stale":
        return "REFRESH_CURRENT_VIEW" if canonical_paths else "INSUFFICIENT_EVIDENCE"
    if kind == "candidate":
        return "PROMOTION_REVIEW_REQUIRED"
    if kind == "unknown":
        return "INSUFFICIENT_EVIDENCE"
    if domain in {"documentation", "current_view"}:
        return "REGENERATE_DERIVED_VIEW"
    return "NO_ACTION"


def _dispatcher_impact(kind: str, finding: Mapping[str, Any], classification: str, remediation: str) -> str:
    status = str(finding.get("status", "")).upper()
    if kind in {"safety", "governance", "dependency"}:
        return "CONTEXT_BLOCKING"
    if classification == "CONTEXT_FAILED_CLOSED" and str(finding.get("severity", "")).upper() == "ERROR":
        return "CONTEXT_BLOCKING"
    if kind in {"conflict", "stale", "unknown", "candidate"}:
        if classification in {"CONTEXT_CONFLICT", "CONTEXT_STALE", "CONTEXT_UNKNOWN", "CONTEXT_FAILED_CLOSED"}:
            return "CONTEXT_BLOCKING" if kind in {"conflict", "unknown"} else "CONTEXT_DEGRADED"
        return "CONTEXT_DEGRADED"
    if status in {"FAILED_CLOSED", "SAFETY_INVARIANT_MISSING", "GOVERNANCE_DRIFT"}:
        return "CONTEXT_BLOCKING"
    return "NON_BLOCKING"


def _human_action(finding: Mapping[str, Any], kind: str, remediation: str) -> str:
    action = _normal_text(finding.get("recommended_human_action"))
    if action:
        return action
    return {
        "NO_ACTION": "No remediation is proposed; retain the evidence and continue manual observation.",
        "REFRESH_CURRENT_VIEW": "Review the source evidence and refresh the affected current view manually.",
        "REGENERATE_DERIVED_VIEW": "Review the source evidence and regenerate the affected derived projection manually.",
        "REVIEW_CANONICAL_CONFLICT": "Preserve both sources and require an explicit human review of the canonical conflict.",
        "PROMOTION_REVIEW_REQUIRED": "Do not promote the candidate; obtain explicit human evidence and governance review.",
        "REMOVE_UNSUPPORTED_RUNTIME_REFERENCE": "Remove the unsupported runtime reference only after governance confirms the correction.",
        "GOVERNANCE_REVIEW_REQUIRED": "Require governance review before changing any Builder identity or role reference.",
        "SAFETY_REVIEW_REQUIRED": "Require safety and CEO review before any change touching a protected invariant.",
        "INSUFFICIENT_EVIDENCE": "Obtain the missing or authoritative evidence; do not infer the current state.",
    }[remediation]


def _source_paths(finding: Mapping[str, Any]) -> list[str]:
    values = finding.get("source_paths", [])
    return sorted({_normal_text(item) for item in values if _normal_text(item)}) if isinstance(values, list) else []


def _remediation_item(
    finding: Mapping[str, Any],
    *,
    classification: str,
    audit: Mapping[str, Any],
    envelope: Mapping[str, Any] | None,
) -> dict[str, Any]:
    kind = _kind(finding)
    paths = _source_paths(finding)
    canonical_paths, runtime_paths = _path_groups(paths)
    authoritative, conflicting, non_authoritative = _authority_classes(finding)
    remediation = _remediation(kind, finding, canonical_paths, runtime_paths)
    status = str(finding.get("status", "UNKNOWN")).upper()
    unresolved = status in {"CONFLICT", "GOVERNANCE_DRIFT", "SAFETY_INVARIANT_MISSING"} or "ceo" in _finding_text(finding)
    impact = _dispatcher_impact(kind, finding, classification, remediation)
    promotion = remediation == "PROMOTION_REVIEW_REQUIRED" or bool(set(non_authoritative) & {"CANDIDATE", "CANDIDATE_OPERATIONAL_EVIDENCE", "RUNTIME_DERIVED"})
    fail_reason = None
    if impact == "CONTEXT_BLOCKING":
        fail_reason = f"{status} finding requires review before Dispatcher context can be treated as current"
    if classification == "CONTEXT_FAILED_CLOSED" and status not in {"WARNING", "CONSISTENT"}:
        fail_reason = fail_reason or "V6 classified the context failed closed"
    item: dict[str, Any] = {
        "finding_id": str(finding.get("finding_id") or "UNKNOWN-FINDING"),
        "source_finding_status": status,
        "domain": str(finding.get("domain") or "unknown"),
        "severity": str(finding.get("severity") or "WARNING"),
        "affected_entities": sorted(str(value) for value in finding.get("affected_entities", []) if _normal_text(value)),
        "authoritative_source_classes": authoritative,
        "conflicting_source_classes": conflicting,
        "non_authoritative_source_classes": non_authoritative,
        "affected_canonical_current_view_paths": canonical_paths,
        "affected_runtime_paths": runtime_paths,
        "dispatcher_impact": impact,
        "remediation_class": remediation,
        "proposed_human_action": _human_action(finding, kind, remediation),
        "canonical_mutation_required": remediation == "REVIEW_CANONICAL_CONFLICT",
        "runtime_only_cleanup_required": remediation in {"REMOVE_UNSUPPORTED_RUNTIME_REFERENCE", "REGENERATE_DERIVED_VIEW"} and bool(runtime_paths),
        "evidence_promotion_required": promotion,
        "prerequisite_evidence": sorted(set(paths) | {str(value) for value in finding.get("affected_entities", []) if _normal_text(value)}),
        "unresolved_ceo_decision": unresolved,
        "unresolved_ceo_decision_detail": _normal_text(finding.get("summary")) if unresolved else None,
        "fail_closed_reason": fail_reason,
        "provenance": {
            "source_memory_sha": audit.get("source_memory_sha"),
            "consistency_audit_digest": audit.get("semantic_digest"),
            "source_paths": paths,
            "source_finding_id": str(finding.get("finding_id") or "UNKNOWN-FINDING"),
            "dispatcher_context_envelope_digest": envelope.get("semantic_envelope_digest") if envelope else None,
        },
        "source_evidence": {
            "evidence": _stable(finding.get("evidence", [])),
            "authority_classes": _stable(finding.get("authority_classes", [])),
            "recommended_human_action": _normal_text(finding.get("recommended_human_action")),
        },
        "remediation_digest": "",
    }
    item["remediation_digest"] = _digest({key: value for key, value in item.items() if key != "remediation_digest"})
    return item


def _safety_invariants(envelope: Mapping[str, Any] | None) -> list[dict[str, str]]:
    result: dict[str, dict[str, str]] = {}
    for item in (envelope or {}).get("safety_invariants", []) if envelope else []:
        if isinstance(item, Mapping):
            key = str(item.get("invariant_id") or item.get("entity_id") or item.get("id") or "")
            if key:
                record = {str(k): str(v) for k, v in item.items() if v not in (None, "", [], {})}
                record.setdefault("invariant_id", key)
                record.setdefault("statement", str(item.get("summary") or item.get("label") or item.get("text") or key))
                result[key] = record
    for marker in SAFETY_MARKERS:
        key = marker.replace(" ", "-").upper()
        result.setdefault(key, {"invariant_id": key, "statement": marker, "authority": "GOVERNED_SAFETY_BOUNDARY"})
    return [result[key] for key in sorted(result)]


def _plan_digest(plan: Mapping[str, Any]) -> str:
    ignored = {"semantic_plan_digest", "generated_at"}
    def clean(value: Any) -> Any:
        if isinstance(value, Mapping):
            return {str(key): clean(child) for key, child in sorted(value.items(), key=lambda pair: str(pair[0])) if key not in ignored}
        if isinstance(value, list):
            return [clean(child) for child in value]
        return value
    return _digest(clean(plan))


def _summary(items: list[Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "finding_count": len(items),
        "context_blocking_count": sum(item["dispatcher_impact"] == "CONTEXT_BLOCKING" for item in items),
        "context_degraded_count": sum(item["dispatcher_impact"] == "CONTEXT_DEGRADED" for item in items),
        "non_blocking_count": sum(item["dispatcher_impact"] == "NON_BLOCKING" for item in items),
        "canonical_mutation_proposals": sum(bool(item["canonical_mutation_required"]) for item in items),
        "runtime_cleanup_proposals": sum(bool(item["runtime_only_cleanup_required"]) for item in items),
        "promotion_review_count": sum(bool(item["evidence_promotion_required"]) for item in items),
        "by_remediation_class": {
            name: sum(item["remediation_class"] == name for item in items)
            for name in sorted(REMEDIATION_CLASSES)
            if any(item["remediation_class"] == name for item in items)
        },
    }


def _plan_markdown(plan: Mapping[str, Any]) -> str:
    lines = [
        "<!-- GENERATED BY SportsBrain Memory Drift Resolution Planner V7: NONCANONICAL EXTERNAL ARTIFACT -->",
        "# SportsBrain Memory Drift Resolution Plan V7", "",
        f"- Planner status: **{plan['planner_status']}**",
        f"- Planner ID: `{plan['planner_id']}`",
        f"- Source Memory SHA: `{plan['source_memory_sha']}`",
        f"- Reference time: `{plan['reference_time']}`",
        f"- Semantic plan digest: `{plan['semantic_plan_digest']}`",
        "- Read-only: **true**; all remediation entries are proposals for human review only.", "",
        "## Evidence Chain", "",
        f"- V5 Consistency Audit: `{plan['consistency_audit_digest']}` ({plan['consistency_audit_ref']})",
        f"- V6 Dispatcher Context Envelope: `{plan['dispatcher_context_envelope_digest'] or 'NOT_PROVIDED'}` ({plan['dispatcher_context_envelope_ref'] or 'NOT_PROVIDED'})",
        f"- V6 classification: **{plan['dispatcher_classification']}**", "",
        "## Safety Boundaries", "",
    ]
    lines.extend(f"- **{item['statement']}**" for item in plan["safety_invariants"])
    lines.extend(["", "## Summary", "", f"- {json.dumps(_stable(plan['summary']), ensure_ascii=False, sort_keys=True)}", ""])
    lines.extend(["## Review Flags", ""])
    if plan.get("review_flags"):
        lines.extend(f"- **{flag}**" for flag in plan["review_flags"])
    else:
        lines.append("- None.")
    lines.extend(["", "## Proposed Remediations", ""])
    if not plan["findings"]:
        lines.append("- No remediation required.")
    for item in plan["findings"]:
        lines.extend([
            f"### `{item['finding_id']}` — {item['remediation_class']}",
            "",
            f"- Source: **{item['severity']} / {item['source_finding_status']}** in `{item['domain']}`",
            f"- Dispatcher impact: **{item['dispatcher_impact']}**",
            f"- Canonical/current-view paths: `{json.dumps(item['affected_canonical_current_view_paths'], ensure_ascii=False)}`",
            f"- Runtime paths: `{json.dumps(item['affected_runtime_paths'], ensure_ascii=False)}`",
            f"- Human action: {item['proposed_human_action']}",
            f"- CEO decision required: **{str(item['unresolved_ceo_decision']).lower()}**",
            f"- Remediation digest: `{item['remediation_digest']}`", "",
        ])
    lines.extend([
        "## Prohibited Automatic Actions", "",
        *[f"- {action}" for action in plan["prohibited_actions"]], "",
        "No file, runtime projection, candidate, canonical record, authorization, scheduler, production system, Cloudflare resource, ledger, or sealed Research data was changed by this planner.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def plan_drift_resolution(
    root: Path,
    *,
    envelope: Path | Mapping[str, Any] | DispatcherContextEnvelope | None = None,
    vault: Path | None = None,
    reference_time: str | None = None,
    audit: ConsistencyAudit | Mapping[str, Any] | None = None,
) -> DriftResolutionCompilation:
    """Build a deterministic review plan without executing any remediation."""
    root = Path(root).resolve()
    reference = reference_time or _iso_now()
    if _parse_time(reference) is None:
        raise DriftPlannerError("reference_time must be timezone-aware ISO-8601")
    audit_payload = _audit_payload(audit if audit is not None else audit_consistency(root, vault=vault, reference_time=reference))
    _validate_audit_input(audit_payload)
    envelope_payload = _read_envelope(envelope)
    source_sha = str(audit_payload.get("source_memory_sha") or "")
    review_flags: set[str] = set()
    classification = str((envelope_payload or {}).get("classification") or "CONTEXT_UNKNOWN")
    if classification not in CLASSIFICATIONS:
        raise DriftPlannerError("unsupported V6 context classification")
    if envelope_payload is None:
        review_flags.add("V6_ENVELOPE_UNAVAILABLE")
    elif envelope_payload.get("source_memory_sha") != source_sha:
        review_flags.add("V6_SOURCE_SHA_STALE")
    if classification in {"CONTEXT_FAILED_CLOSED", "CONTEXT_CONFLICT", "CONTEXT_STALE", "CONTEXT_UNKNOWN"}:
        review_flags.add("V6_" + classification)
    findings = [dict(item) for item in audit_payload.get("findings", []) if isinstance(item, Mapping)]
    findings.sort(key=lambda item: (-_priority(_kind(item)), 0 if str(item.get("severity", "")).upper() == "ERROR" else 1, str(item.get("domain", "")), str(item.get("finding_id", ""))))
    items = [_remediation_item(item, classification=classification, audit=audit_payload, envelope=envelope_payload) for item in findings]
    for item in items:
        if item["dispatcher_impact"] == "CONTEXT_BLOCKING":
            review_flags.add("CONTEXT_BLOCKING_FINDINGS")
        if item["unresolved_ceo_decision"]:
            review_flags.add("UNRESOLVED_CEO_DECISION")
    failed = classification == "CONTEXT_FAILED_CLOSED" or any(item["dispatcher_impact"] == "CONTEXT_BLOCKING" and item["severity"].upper() == "ERROR" for item in items)
    if not findings:
        planner_status = "REMEDIATION_NOT_REQUIRED"
    elif failed:
        planner_status = "REMEDIATION_FAILED_CLOSED"
    else:
        planner_status = "REMEDIATION_REVIEW_REQUIRED"
    summary = _summary(items)
    audit_digest = str(audit_payload.get("semantic_digest") or "")
    envelope_digest = str(envelope_payload.get("semantic_envelope_digest")) if envelope_payload else None
    plan: DriftResolutionPlan = {
        "schema_version": PLANNER_SCHEMA,
        "planner_version": PLANNER_VERSION,
        "planner_id": "DRIFT-PLAN-" + _digest({"source_memory_sha": source_sha, "audit_digest": audit_digest, "envelope_digest": envelope_digest, "reference_time": reference})[:20],
        "planner_status": planner_status,
        "source_memory_sha": source_sha,
        "reference_time": reference,
        "consistency_audit_digest": audit_digest,
        "consistency_audit_ref": f"memory://consistency-audit-v5/{audit_digest}",
        "consistency_audit": audit_payload,
        "dispatcher_context_envelope_digest": envelope_digest,
        "dispatcher_context_envelope_ref": f"memory://dispatcher-envelope-v1/{envelope_digest}" if envelope_digest else None,
        "dispatcher_context_envelope": envelope_payload,
        "dispatcher_classification": classification,
        "governed_builders": {str(number): BUILDER_ROLES[number] for number in BUILDER_NUMBERS},
        "findings": items,
        "summary": summary,
        "review_flags": sorted(review_flags),
        "safety_invariants": _safety_invariants(envelope_payload),
        "prohibited_actions": sorted(set(DEFAULT_PROHIBITED_ACTIONS)),
        "actions_are_proposals_only": True,
        "automatic_repair": False,
        "candidate_promotion": False,
        "authorization_created": False,
        "source_provenance": sorted(set(
            [str(path) for item in items for path in item.get("provenance", {}).get("source_paths", [])]
            + ["tools/memorylib/consistency_auditor.py", "tools/memorylib/dispatcher_context_envelope.py"]
        )),
        "semantic_plan_digest": "",
        "generated_at": _iso_now(),
    }
    plan["semantic_plan_digest"] = _plan_digest(plan)
    try:
        from .context_compiler import _assert_secret_free
        _assert_secret_free(audit_payload)
    except Exception as exc:
        raise DriftPlannerError(f"audit contains secret-like material: {exc}") from exc
    return DriftResolutionCompilation(plan=plan, markdown=_plan_markdown(plan))


compile_drift_resolution_plan = plan_drift_resolution
build_drift_resolution_plan = plan_drift_resolution


def _validate_plan_payload(payload: Mapping[str, Any]) -> DriftResolutionPlan:
    required = {
        "schema_version", "planner_version", "planner_id", "planner_status", "source_memory_sha", "reference_time",
        "consistency_audit_digest", "consistency_audit_ref", "consistency_audit", "dispatcher_context_envelope_digest",
        "dispatcher_context_envelope_ref", "dispatcher_context_envelope", "dispatcher_classification", "governed_builders",
        "findings", "summary", "review_flags", "safety_invariants", "prohibited_actions", "actions_are_proposals_only",
        "automatic_repair", "candidate_promotion", "authorization_created", "source_provenance", "semantic_plan_digest", "generated_at",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise DriftPlannerValidationError("drift plan missing field(s): " + ", ".join(missing))
    if payload.get("schema_version") != PLANNER_SCHEMA or payload.get("planner_version") != PLANNER_VERSION:
        raise DriftPlannerValidationError("unsupported drift planner schema/version")
    if payload.get("planner_status") not in PLANNER_STATUSES:
        raise DriftPlannerValidationError("invalid planner_status")
    if payload.get("dispatcher_classification") not in CLASSIFICATIONS:
        raise DriftPlannerValidationError("invalid Dispatcher Context classification")
    builders = payload.get("governed_builders")
    expected_builders = {str(number): BUILDER_ROLES[number] for number in BUILDER_NUMBERS}
    if builders != expected_builders:
        raise DriftPlannerValidationError("governed Builder roster is not exactly Builder 1 through Builder 5")
    for field_name in ("findings", "review_flags", "safety_invariants", "prohibited_actions", "source_provenance"):
        if not isinstance(payload.get(field_name), list):
            raise DriftPlannerValidationError(f"{field_name} must be a list")
    if payload.get("actions_are_proposals_only") is not True or payload.get("automatic_repair") is not False or payload.get("candidate_promotion") is not False or payload.get("authorization_created") is not False:
        raise DriftPlannerValidationError("planner safety flags claim execution, promotion, or authorization")
    audit = payload.get("consistency_audit")
    if not isinstance(audit, Mapping) or audit.get("semantic_digest") != payload.get("consistency_audit_digest"):
        raise DriftPlannerValidationError("V5 audit digest is inconsistent")
    if not isinstance(audit.get("findings"), list):
        raise DriftPlannerValidationError("V5 audit findings must be a list")
    if audit.get("source_memory_sha") != payload.get("source_memory_sha"):
        raise DriftPlannerValidationError("V5 audit source Memory SHA is inconsistent")
    if audit.get("semantic_digest") != _v5_audit_semantic_digest(audit):
        raise DriftPlannerValidationError("V5 audit semantic digest does not match its findings")
    if not isinstance(payload.get("summary"), Mapping):
        raise DriftPlannerValidationError("summary must be an object")
    envelope = payload.get("dispatcher_context_envelope")
    if envelope is not None:
        try:
            validated = _validate_payload(envelope)
        except Exception as exc:
            raise DriftPlannerValidationError(f"embedded V6 envelope is invalid: {exc}") from exc
        if validated.get("semantic_envelope_digest") != payload.get("dispatcher_context_envelope_digest"):
            raise DriftPlannerValidationError("V6 envelope digest is inconsistent")
        if validated.get("classification") != payload.get("dispatcher_classification"):
            raise DriftPlannerValidationError("V6 envelope classification is inconsistent")
        if payload.get("dispatcher_context_envelope_ref") != f"memory://dispatcher-envelope-v1/{payload.get('dispatcher_context_envelope_digest')}":
            raise DriftPlannerValidationError("V6 envelope reference is inconsistent")
    elif payload.get("dispatcher_context_envelope_digest") is not None or payload.get("dispatcher_context_envelope_ref") is not None:
        raise DriftPlannerValidationError("missing V6 envelope cannot have a digest/reference")
    marker_text = json.dumps(payload.get("safety_invariants"), ensure_ascii=False).upper()
    for marker in SAFETY_MARKERS:
        if marker.upper() not in marker_text:
            raise DriftPlannerValidationError(f"safety marker missing from plan: {marker}")
    for item in payload.get("findings", []):
        if not isinstance(item, Mapping):
            raise DriftPlannerValidationError("each remediation finding must be an object")
        item_required = {
            "finding_id", "source_finding_status", "domain", "severity", "affected_entities",
            "authoritative_source_classes", "conflicting_source_classes", "non_authoritative_source_classes",
            "affected_canonical_current_view_paths", "affected_runtime_paths", "dispatcher_impact",
            "remediation_class", "proposed_human_action", "canonical_mutation_required",
            "runtime_only_cleanup_required", "evidence_promotion_required", "prerequisite_evidence",
            "unresolved_ceo_decision", "unresolved_ceo_decision_detail", "fail_closed_reason", "provenance",
            "source_evidence", "remediation_digest",
        }
        missing_item = sorted(item_required - set(item))
        if missing_item:
            raise DriftPlannerValidationError(f"remediation {item.get('finding_id')} missing field(s): {', '.join(missing_item)}")
        if item.get("remediation_class") not in REMEDIATION_CLASSES or item.get("dispatcher_impact") not in DISPATCHER_IMPACTS:
            raise DriftPlannerValidationError("invalid remediation class or Dispatcher impact")
        expected_digest = _digest({key: value for key, value in item.items() if key != "remediation_digest"})
        if item.get("remediation_digest") != expected_digest:
            raise DriftPlannerValidationError(f"remediation digest mismatch for {item.get('finding_id')}")
    audit_findings = [item for item in audit.get("findings", []) if isinstance(item, Mapping)]
    audit_by_id = {str(item.get("finding_id") or "UNKNOWN-FINDING"): item for item in audit_findings}
    if len(audit_by_id) != len(audit_findings):
        raise DriftPlannerValidationError("V5 audit contains duplicate finding identities")
    for item in payload.get("findings", []):
        source = audit_by_id.get(str(item.get("finding_id")))
        if source is None:
            raise DriftPlannerValidationError(f"remediation has no matching V5 finding: {item.get('finding_id')}")
        expected = _remediation_item(
            source,
            classification=str(payload["dispatcher_classification"]),
            audit=audit,
            envelope=envelope if isinstance(envelope, Mapping) else None,
        )
        if dict(item) != expected:
            raise DriftPlannerValidationError(f"remediation fields are not derived from V5 finding: {item.get('finding_id')}")
    if payload.get("summary") != _summary(payload["findings"]):
        raise DriftPlannerValidationError("summary does not match remediation findings")
    try:
        from .context_compiler import _assert_secret_free
        # The plan deliberately contains governance booleans whose field names
        # include "authorization"; scan the untrusted evidence payload rather
        # than rejecting those explicit, immutable safety flags.
        _assert_secret_free(audit)
    except Exception as exc:
        raise DriftPlannerValidationError(f"drift plan contains secret-like material: {exc}") from exc
    if _parse_time(payload.get("reference_time")) is None or _parse_time(payload.get("generated_at")) is None:
        raise DriftPlannerValidationError("reference_time and generated_at must be timezone-aware ISO-8601")
    if payload.get("semantic_plan_digest") != _plan_digest(payload):
        raise DriftPlannerValidationError("semantic_plan_digest does not match plan content")
    return dict(payload)  # type: ignore[return-value]


def validate_drift_resolution_plan(path: Path) -> DriftResolutionPlan:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DriftPlannerValidationError(f"drift plan is not valid JSON: {path}") from exc
    return _validate_plan_payload(payload)


def inspect_drift_resolution_plan(path: Path) -> dict[str, Any]:
    payload = validate_drift_resolution_plan(path)
    return {
        "schema_version": payload["schema_version"],
        "planner_id": payload["planner_id"],
        "planner_status": payload["planner_status"],
        "source_memory_sha": payload["source_memory_sha"],
        "dispatcher_classification": payload["dispatcher_classification"],
        "finding_count": payload["summary"]["finding_count"],
        "review_flags": payload["review_flags"],
        "semantic_plan_digest": payload["semantic_plan_digest"],
    }


def _ensure_external_output(root: Path, vault: Path | None, output: Path) -> tuple[Path, Path]:
    root = Path(root).resolve()
    vault = Path(vault).resolve() if vault else None
    raw = Path(output)
    resolved = raw.resolve(strict=False)
    if _inside(resolved, root):
        raise DriftPlannerError("drift plan output must be outside canonical Memory")
    if vault and _inside(resolved, vault):
        raise DriftPlannerError("drift plan output must be outside the external Vault")
    if raw.suffix.lower() == ".json":
        directory = resolved.parent
        json_path = resolved
    else:
        directory = resolved
        json_path = resolved / "DRIFT_RESOLUTION_PLAN.json"
    directory.mkdir(parents=True, exist_ok=True)
    return json_path, json_path.with_suffix(".md")


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def write_drift_resolution_plan(compilation: DriftResolutionCompilation, output: Path, *, root: Path, vault: Path | None = None) -> dict[str, str]:
    json_path, markdown_path = _ensure_external_output(root, vault, Path(output))
    _atomic_write(json_path, json.dumps(compilation.plan, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    _atomic_write(markdown_path, compilation.markdown)
    validate_drift_resolution_plan(json_path)
    return {"json": str(json_path), "markdown": str(markdown_path), "semantic_plan_digest": compilation.plan["semantic_plan_digest"]}


write_drift_plan = write_drift_resolution_plan
