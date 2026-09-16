"""Deterministic Builder Bootstrap V4 delivery over Context Compiler V3.

Bootstrap packs are noncanonical delivery artifacts. They package selected
evidence for a named Builder without launching work, authorizing execution, or
changing canonical Memory.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import tempfile
import re
from typing import Any, Iterable, Mapping, TypedDict

from .context_compiler import (
    ContextCompilerError,
    ContextRequest,
    _assert_secret_free,
    _digest,
    _ensure_external_context_output,
    _normal_text,
    _parse_time,
    _safe_request_id,
    _semantic_value,
    _stable,
    compile_context,
    validate_context_pack,
)
from .governance import BUILDER_NUMBERS, BUILDER_NUMBER_SET, BUILDER_ROLES


BOOTSTRAP_SCHEMA = 4
BOOTSTRAP_VERSION = "memory-builder-bootstrap-v4.0"
BOOTSTRAP_DIR = "_live/builder-bootstrap"

DEPENDENCY_RELATIONS = {
    "depends_on", "blocked_by", "blocks", "implements", "verification",
    "verified_by", "governed_by", "constrained_by", "invariant", "workstream",
}

PROHIBITED_OPERATIONS = (
    "launch Builder agents or any other agent",
    "launch or schedule the Night Shift Dispatcher",
    "modify SportsBrain production, runtime state, Cloudflare, or ledger",
    "modify canonical Memory history or promote runtime candidates",
    "merge, rebase, force-push, deploy, or activate live behavior",
    "place bets or remove NO-BET/no-live-activation controls",
    "unlock or modify sealed 2425/2526 Research data",
    "modify LaunchAgent configuration or its 90-second cadence",
)

VERIFICATION_REQUIREMENTS = (
    "verify the exact source Memory SHA and semantic digests before acting",
    "validate the embedded Context Compiler V3 pack and all provenance",
    "stop and request CEO review on conflicting, stale, unknown, or missing evidence",
    "preserve NO-BET, no-live-activation, and sealed 2425/2526 invariants",
    "keep all runtime candidates noncanonical and promotion-gated",
)


class BuilderBootstrapPack(TypedDict, total=False):
    schema_version: int
    bootstrap_version: str
    bootstrap_id: str
    builder: dict[str, Any]
    task_identity: dict[str, Any]
    context_request: dict[str, Any]
    context_pack: dict[str, Any]
    authoritative_dependencies: list[dict[str, Any]]
    required_dependencies: list[str]
    required_dependency_status: list[dict[str, Any]]
    missing_dependencies: list[dict[str, Any]]
    active_blockers: list[dict[str, Any]]
    required_cross_builder_contracts: list[dict[str, Any]]
    safety_invariants: list[dict[str, Any]]
    allowed_scope: dict[str, list[str]] | None
    prohibited_operations: list[str]
    verification_requirements: list[str]
    unresolved_ceo_decisions: list[dict[str, Any]]
    stale_evidence: list[dict[str, Any]]
    conflicting_evidence: list[dict[str, Any]]
    unknown_evidence: list[dict[str, Any]]
    review_flags: list[str]
    execution_authorization: str
    safety_decision: str
    source_memory_sha: str
    semantic_digest: str
    semantic_graph_digest: str
    bootstrap_digest: str
    generated_at: str


class BuilderBootstrapError(ValueError):
    """A bootstrap request or derived delivery pack is invalid."""


class BuilderBootstrapValidationError(BuilderBootstrapError):
    """A persisted bootstrap pack fails its structural contract."""


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _values(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    result: list[str] = []
    for item in values:
        if isinstance(item, Mapping):
            item = item.get("id") or item.get("name") or item.get("path") or item.get("value")
        text = _normal_text(item)
        if text:
            result.append(text)
    return sorted(set(result))


def _builder_number(value: Any) -> int:
    if isinstance(value, bool):
        raise BuilderBootstrapError("builder must be an explicit integer from 1 through 5")
    if isinstance(value, int):
        number = value
    else:
        match = re.fullmatch(r"(?:BUILDER[_: ]*)?([1-5])", _normal_text(value), re.IGNORECASE)
        if not match:
            raise BuilderBootstrapError("builder must be exactly Builder 1 through Builder 5")
        number = int(match.group(1))
    if number not in BUILDER_NUMBER_SET:
        raise BuilderBootstrapError("builder must be exactly 1, 2, 3, 4, or 5")
    return number


def _metadata_value(metadata: Mapping[str, Any], value: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in value and value[key] not in (None, "", []):
            return value[key]
        if key in metadata and metadata[key] not in (None, "", []):
            return metadata[key]
    return None


@dataclass(frozen=True)
class BuilderBootstrapRequest:
    bootstrap_id: str
    builder_number: int
    task_id: str
    task: str = ""
    workstream: str = ""
    task_metadata: dict[str, Any] = field(default_factory=dict)
    repository_scope: tuple[str, ...] = ()
    path_scope: tuple[str, ...] = ()
    required_dependencies: tuple[str, ...] = ()
    prohibited_operations: tuple[str, ...] = ()
    verification_requirements: tuple[str, ...] = ()
    token_budget: int = 6000
    max_entity_count: int = 80
    freshness_requirement: str = "ANY"
    include_runtime: bool = False
    context_request_id: str = ""
    generated_at: str = ""

    def __post_init__(self) -> None:
        number = _builder_number(self.builder_number)
        object.__setattr__(self, "builder_number", number)
        metadata = dict(self.task_metadata or {})
        _assert_secret_free(metadata, "task_metadata")
        object.__setattr__(self, "task_metadata", metadata)
        task_id = _normal_text(self.task_id)
        if not task_id:
            raise BuilderBootstrapError("task_id is required or must be derivable from task metadata")
        object.__setattr__(self, "task_id", _safe_request_id(task_id))
        object.__setattr__(self, "bootstrap_id", _safe_request_id(self.bootstrap_id))
        timestamp = self.generated_at or _iso_now()
        if _parse_time(timestamp) is None:
            raise BuilderBootstrapError("generated_at must be timezone-aware ISO-8601")
        object.__setattr__(self, "generated_at", timestamp)
        freshness = str(self.freshness_requirement).upper()
        if freshness not in {"ANY", "FRESH_ONLY", "FRESH_OR_AGING"}:
            raise BuilderBootstrapError(f"unsupported freshness_requirement: {freshness!r}")
        object.__setattr__(self, "freshness_requirement", freshness)
        if not isinstance(self.token_budget, int) or isinstance(self.token_budget, bool) or self.token_budget < 64:
            raise BuilderBootstrapError("token_budget must be an integer >= 64")
        if not isinstance(self.max_entity_count, int) or isinstance(self.max_entity_count, bool) or self.max_entity_count < 1:
            raise BuilderBootstrapError("max_entity_count must be a positive integer")
        for name in ("repository_scope", "path_scope", "required_dependencies", "prohibited_operations", "verification_requirements"):
            object.__setattr__(self, name, tuple(_values(getattr(self, name))))
        if self.context_request_id:
            object.__setattr__(self, "context_request_id", _safe_request_id(self.context_request_id))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "BuilderBootstrapRequest":
        if not isinstance(value, Mapping):
            raise BuilderBootstrapError("bootstrap request must be an object")
        metadata = value.get("task_metadata") or value.get("metadata") or {}
        if not isinstance(metadata, Mapping):
            raise BuilderBootstrapError("task_metadata must be an object")
        metadata = dict(metadata)
        _assert_secret_free(metadata, "task_metadata")
        raw_builder = _metadata_value(metadata, value, "builder_number", "builder")
        number = _builder_number(raw_builder)
        task = _normal_text(_metadata_value(metadata, value, "task", "objective", "description"))
        workstream = _normal_text(_metadata_value(metadata, value, "workstream"))
        task_id = _normal_text(_metadata_value(metadata, value, "task_id", "current_task_id"))
        if not task_id:
            task_id = "TASK-" + _digest({"builder_number": number, "task": task, "workstream": workstream, "metadata": _semantic_value(metadata)})[:16]
        repositories = _values(_metadata_value(metadata, value, "repository_scope", "allowed_repositories", "repository"))
        paths = _values(_metadata_value(metadata, value, "path_scope", "allowed_paths", "paths"))
        dependencies = _values(_metadata_value(metadata, value, "required_dependencies", "dependencies"))
        prohibited = _values(_metadata_value(metadata, value, "prohibited_operations", "prohibited"))
        verification = _values(_metadata_value(metadata, value, "verification_requirements", "verification"))
        provisional: dict[str, Any] = {
            "bootstrap_id": str(value.get("bootstrap_id") or ""),
            "builder_number": number,
            "task_id": task_id,
            "task": task,
            "workstream": workstream,
            "task_metadata": metadata,
            "repository_scope": repositories,
            "path_scope": paths,
            "required_dependencies": dependencies,
            "prohibited_operations": prohibited,
            "verification_requirements": verification,
            "token_budget": value.get("token_budget", value.get("budget_tokens", 6000)),
            "max_entity_count": value.get("max_entity_count", value.get("max_entities", 80)),
            "freshness_requirement": value.get("freshness_requirement", value.get("freshness", "ANY")),
            "include_runtime": bool(value.get("include_runtime", False)),
            "context_request_id": str(value.get("context_request_id") or ""),
            "generated_at": str(value.get("generated_at") or _iso_now()),
        }
        if not provisional["bootstrap_id"]:
            semantic = dict(provisional)
            semantic.pop("generated_at", None)
            provisional["bootstrap_id"] = "BOOT-" + _digest(_semantic_value(semantic))[:16]
        return cls(**provisional)

    def semantic_dict(self) -> dict[str, Any]:
        return {
            "bootstrap_id": self.bootstrap_id,
            "builder_number": self.builder_number,
            "task_id": self.task_id,
            "task": self.task,
            "workstream": self.workstream,
            "task_metadata": _stable(self.task_metadata),
            "repository_scope": list(self.repository_scope),
            "path_scope": list(self.path_scope),
            "required_dependencies": list(self.required_dependencies),
            "prohibited_operations": list(self.prohibited_operations),
            "verification_requirements": list(self.verification_requirements),
            "token_budget": self.token_budget,
            "max_entity_count": self.max_entity_count,
            "freshness_requirement": self.freshness_requirement,
            "include_runtime": self.include_runtime,
            "context_request_id": self.context_request_id,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self.semantic_dict()
        result["generated_at"] = self.generated_at
        return result


def _context_request(request: BuilderBootstrapRequest) -> ContextRequest:
    context_id = request.context_request_id or "CTX-" + _digest({"bootstrap": request.semantic_dict()})[:16]
    metadata = request.task_metadata
    seeds = _values(metadata.get("entity_seeds") or metadata.get("seeds"))
    seeds.extend(request.required_dependencies)
    domains = _values(metadata.get("requested_domains") or metadata.get("domains"))
    return ContextRequest.from_mapping({
        "request_id": context_id,
        "consumer_type": f"BUILDER_{request.builder_number}",
        "builder_number": request.builder_number,
        "task": request.task,
        "workstream": request.workstream,
        "repository_scope": list(request.repository_scope),
        "entity_seeds": sorted(set(seeds)),
        "requested_domains": domains,
        "token_budget": request.token_budget,
        "max_entity_count": request.max_entity_count,
        "freshness_requirement": request.freshness_requirement,
        "include_runtime": request.include_runtime,
        "generated_at": request.generated_at,
    })


def _compact_item(item: Mapping[str, Any]) -> dict[str, Any]:
    fields = (
        "entity_id", "namespace", "stable_id", "label", "authority_class", "canonical",
        "status", "summary", "freshness", "selection_reason", "selection_reasons",
        "candidate_type", "promotion_required", "runtime_status", "blocker", "provenance",
        "role", "branch", "head_sha", "source_pr", "tests", "tests_passed", "ci",
        "blocker_count", "observed_at",
    )
    result = {key: item[key] for key in fields if key in item}
    if item.get("source_excerpt"):
        result["source_excerpt"] = str(item["source_excerpt"])[:800]
    _assert_secret_free(result, "bootstrap.context_reference")
    return result


def _item_status(item: Mapping[str, Any]) -> str:
    blocker = item.get("blocker")
    if isinstance(blocker, Mapping) and blocker.get("status"):
        return str(blocker["status"])
    return str(item.get("status") or "")


def _matches(item: Mapping[str, Any], needle: str) -> bool:
    target = _normal_text(needle).casefold()
    if not target:
        return False
    values = [item.get("entity_id"), item.get("stable_id"), item.get("label"), item.get("summary")]
    provenance = item.get("provenance")
    if isinstance(provenance, Mapping):
        values.extend(provenance.get("source_paths") or [])
    return any(target == _normal_text(value).casefold() for value in values if value not in (None, ""))


def _is_mandatory_conflict(conflict: Mapping[str, Any]) -> bool:
    if conflict.get("mandatory") is True:
        return True
    fields = " ".join(str(conflict.get(key) or "") for key in ("category", "classification", "priority", "domain", "type", "code")).upper()
    return any(token in fields for token in ("SAFETY", "BLOCKER", "SEALED", "NO-BET", "NO-LIVE")) and str(conflict.get("severity", "")).upper() in {"ERROR", "FATAL", "SAFETY_CRITICAL", "CEO_DECISION_REQUIRED"}


def _bootstrap_semantic(value: Mapping[str, Any]) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _bootstrap_semantic(child)
            for key, child in value.items()
            if key not in {"bootstrap_digest", "generated_at", "cache_key", "first_observed_at", "last_observed_at", "observation_count"}
        }
    if isinstance(value, list):
        return [_bootstrap_semantic(child) for child in value]
    return value


def _bootstrap_digest(pack: Mapping[str, Any]) -> str:
    return _digest(_bootstrap_semantic(pack))


def _context_items(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    values = pack.get("included_entities", [])
    return [dict(item) for item in values if isinstance(item, Mapping)]


def _context_item_map(pack: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(item.get("entity_id")): item for item in _context_items(pack) if item.get("entity_id")}


def _builder_evidence_role(items: Iterable[Mapping[str, Any]], number: int) -> str | None:
    stable_id = f"BUILDER-{number}"
    for item in items:
        if item.get("namespace") != "BUILDER" or item.get("stable_id") != stable_id:
            continue
        runtime = item.get("runtime_status")
        if isinstance(runtime, Mapping) and _normal_text(runtime.get("role")):
            return _normal_text(runtime["role"])
    return None


def _dependency_records(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _context_item_map(pack)
    result: list[dict[str, Any]] = []
    for edge in pack.get("included_edges", []):
        if not isinstance(edge, Mapping) or edge.get("relation") not in DEPENDENCY_RELATIONS:
            continue
        source = items.get(str(edge.get("source")))
        target = items.get(str(edge.get("target")))
        if not source or not target:
            continue
        if source.get("authority_class") not in {"CANONICAL", "VERIFIED"}:
            continue
        if target.get("authority_class") not in {"CANONICAL", "VERIFIED"}:
            continue
        result.append({
            "source": source.get("entity_id"),
            "target": target.get("entity_id"),
            "relation": edge.get("relation"),
            "source_authority": source.get("authority_class"),
            "target_authority": target.get("authority_class"),
            "source_summary": source.get("summary") or source.get("label"),
            "target_summary": target.get("summary") or target.get("label"),
            "provenance": {
                "source_path": edge.get("source_path"),
                "field": edge.get("field"),
                "raw_target": edge.get("raw_target"),
            },
        })
    return sorted(result, key=lambda item: (str(item.get("source")), str(item.get("relation")), str(item.get("target"))))


def _required_dependency_status(request: BuilderBootstrapRequest, pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    items = _context_items(pack)
    statuses: list[dict[str, Any]] = []
    for dependency in request.required_dependencies:
        matches = [item for item in items if _matches(item, dependency)]
        authoritative = [item for item in matches if item.get("authority_class") in {"CANONICAL", "VERIFIED"}]
        if authoritative:
            value = {"dependency": dependency, "required": True, "status": "SATISFIED_AUTHORITATIVE"}
        elif matches:
            value = {
                "dependency": dependency,
                "required": True,
                "status": "PRESENT_NONAUTHORITATIVE",
                "matching_evidence": [
                    {"entity_id": item.get("entity_id"), "authority_class": item.get("authority_class")}
                    for item in sorted(matches, key=lambda item: str(item.get("entity_id")))
                ],
            }
        else:
            value = {"dependency": dependency, "required": True, "status": "MISSING"}
        statuses.append(value)
    return statuses


def _missing_dependencies(request: BuilderBootstrapRequest, pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        value for value in _required_dependency_status(request, pack)
        if value.get("status") != "SATISFIED_AUTHORITATIVE"
    ]


def _active_blockers(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for item in _context_items(pack):
        if item.get("namespace") != "BLOCKER":
            continue
        status = _item_status(item).upper()
        if status in {"RESOLVED", "CLOSED", "REPORTED_CHANGED"}:
            continue
        value = _compact_item(item)
        value["operational_status"] = status or "UNKNOWN"
        if status == "PRESERVED_UNVERIFIED":
            value["review_required"] = True
        result.append(value)
    return sorted(result, key=lambda item: (str(item.get("entity_id")), str(item.get("operational_status"))))


def _contracts(pack: Mapping[str, Any], builder_number: int) -> list[dict[str, Any]]:
    result = []
    for item in _context_items(pack):
        reasons = {str(reason) for reason in item.get("selection_reasons", [])}
        text = " ".join(str(item.get(key) or "") for key in ("label", "summary", "source_excerpt")).casefold()
        if "REQUIRED_CROSS_BUILDER_CONTRACT" not in reasons and "contract" not in text:
            continue
        value = _compact_item(item)
        value["for_builder"] = builder_number
        result.append(value)
    return sorted(result, key=lambda item: str(item.get("entity_id")))


def _safety_invariants(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in _context_items(pack):
        if item.get("namespace") != "INVARIANT" and "SAFETY_INVARIANT" not in {str(reason) for reason in item.get("selection_reasons", [])}:
            continue
        result.append(_compact_item(item))
    return sorted(result, key=lambda item: str(item.get("entity_id")))


def _unresolved_decisions(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in _context_items(pack):
        if item.get("namespace") != "DECISION":
            continue
        if "SUPERSEDED_HISTORY" in {str(reason) for reason in item.get("selection_reasons", [])}:
            continue
        status = _item_status(item).upper()
        text = " ".join(str(item.get(key) or "") for key in ("label", "summary", "source_excerpt")).casefold()
        if status in {"OPEN", "ACTIVE", "CURRENT", "PENDING", "UNRESOLVED", "CEO_DECISION_REQUIRED"} or "ceo" in text:
            result.append(_compact_item(item))
    return sorted(result, key=lambda item: str(item.get("entity_id")))


def _stale_evidence(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [
            _compact_item(item)
            for item in _context_items(pack)
            if item.get("freshness") == "STALE"
            and (item.get("authority_class") in {"CANDIDATE", "RUNTIME_DERIVED"} or item.get("namespace") == "BUILDER")
        ],
        key=lambda item: str(item.get("entity_id")),
    )


def _unknown_evidence(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = []
    for item in _context_items(pack):
        runtime = item.get("runtime_status")
        if (isinstance(runtime, Mapping) and str(runtime.get("state", "")).upper() == "UNKNOWN") or item.get("freshness") == "UNKNOWN":
            result.append(_compact_item(item))
    return sorted(result, key=lambda item: str(item.get("entity_id")))


def _conflicting_evidence(pack: Mapping[str, Any]) -> list[dict[str, Any]]:
    values = [dict(item) for item in pack.get("conflicts", []) if isinstance(item, Mapping)]
    values.extend(
        {"warning": warning}
        for warning in pack.get("warnings", [])
        if "CONFLICT" in str(warning).upper()
    )
    return sorted(values, key=lambda item: json.dumps(_stable(item), sort_keys=True, ensure_ascii=True))


def _current_builder_evidence(pack: Mapping[str, Any], number: int) -> dict[str, Any] | None:
    for item in _context_items(pack):
        if item.get("namespace") == "BUILDER" and item.get("stable_id") == f"BUILDER-{number}":
            runtime = item.get("runtime_status")
            if isinstance(runtime, Mapping) and str(runtime.get("state", "")).upper() != "UNKNOWN":
                value = _compact_item(runtime)
                value["blocker_state"] = "REPORTED" if int(runtime.get("blocker_count", 0) or 0) > 0 else "NONE REPORTED"
                return value
            return {"state": "UNKNOWN", "message": "NO CURRENT HANDOFF EVIDENCE", "freshness": "UNKNOWN"}
    return {"state": "UNKNOWN", "message": "NO CURRENT HANDOFF EVIDENCE", "freshness": "UNKNOWN"}


def _markdown_section(lines: list[str], title: str, values: Iterable[str]) -> None:
    content = [value for value in values if _normal_text(value)]
    if not content:
        return
    lines.extend([f"## {title}", ""])
    lines.extend(content)
    lines.append("")


@dataclass(frozen=True)
class BuilderBootstrapCompilation:
    pack: BuilderBootstrapPack
    markdown: str


def _bootstrap_markdown(pack: Mapping[str, Any]) -> str:
    builder = pack["builder"]
    task = pack["task_identity"]
    context = pack["context_pack"]
    lines = [
        "<!-- GENERATED BY SportsBrain Memory Builder Bootstrap V4: NONCANONICAL EXTERNAL ARTIFACT -->",
        "# SportsBrain Builder Bootstrap Pack V4", "",
        "- Builder: **BUILDER: %s**" % builder["number"],
        "- Role baseline: **%s**" % builder["role_baseline"],
        "- Current evidence role: **%s**" % builder["role"],
        "- Task: `%s` — %s" % (task["task_id"], task.get("task") or "No task description supplied."),
        "- Source Memory SHA: `%s`" % pack["source_memory_sha"],
        "- Semantic digest: `%s`" % pack["semantic_digest"],
        "- Bootstrap digest: `%s`" % pack["bootstrap_digest"],
        "- Execution authorization: **NOT PROVIDED**",
        "- Safety decision: **NOT EVALUATED**", "",
    ]
    _markdown_section(lines, "CONTEXT COMPILER V3", [
        f"- Request: `{context.get('request_id')}`; context digest `{context.get('context_digest')}`.",
        f"- Graph available: **{str(context.get('graph_available', False)).lower()}**; freshness: **{context.get('freshness_state', 'UNKNOWN')}**.",
        f"- Included entities: {context.get('included_entity_count', 0)}; estimated tokens: {context.get('estimated_tokens', 0)} / {context.get('token_budget', 0)}.",
    ])
    for title, key in (
        ("AUTHORITATIVE DEPENDENCIES", "authoritative_dependencies"),
        ("REQUIRED DEPENDENCY STATUS", "required_dependency_status"),
        ("MISSING / NON-AUTHORITATIVE DEPENDENCIES", "missing_dependencies"),
        ("ACTIVE BLOCKERS", "active_blockers"),
        ("REQUIRED CROSS-BUILDER CONTRACTS", "required_cross_builder_contracts"),
        ("SAFETY INVARIANTS", "safety_invariants"),
        ("UNRESOLVED CEO DECISIONS", "unresolved_ceo_decisions"),
        ("STALE EVIDENCE", "stale_evidence"),
        ("CONFLICTING EVIDENCE", "conflicting_evidence"),
        ("UNKNOWN EVIDENCE", "unknown_evidence"),
    ):
        values = [f"- `{item.get('entity_id') or item.get('dependency') or item.get('source')}` — {json.dumps(_stable(item), ensure_ascii=False, sort_keys=True)}" for item in pack.get(key, [])]
        _markdown_section(lines, title, values)
    scope = pack.get("allowed_scope")
    if scope is not None:
        _markdown_section(lines, "ALLOWED REPOSITORY / PATH SCOPE", [f"- {json.dumps(_stable(scope), ensure_ascii=False, sort_keys=True)}"])
    _markdown_section(lines, "REVIEW FLAGS", [f"- **{flag}**" for flag in pack.get("review_flags", [])])
    _markdown_section(lines, "PROHIBITED OPERATIONS", [f"- {value}" for value in pack.get("prohibited_operations", [])])
    _markdown_section(lines, "VERIFICATION REQUIREMENTS", [f"- {value}" for value in pack.get("verification_requirements", [])])
    _markdown_section(lines, "BOUNDARY", [
        "- This package delivers context only. It does not decide execution safety, grant CEO authorization, launch agents or dispatchers, merge, deploy, or promote candidates.",
        "- Runtime-derived evidence remains noncanonical; canonical history and sealed 2425/2526 data are unchanged.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def _safe_task_identity(request: BuilderBootstrapRequest) -> dict[str, Any]:
    value = {
        "task_id": request.task_id,
        "task": request.task,
        "workstream": request.workstream,
        "metadata": _stable(request.task_metadata),
        "scope": _scope(request),
    }
    _assert_secret_free(value, "task_identity")
    return value


def _scope(request: BuilderBootstrapRequest) -> dict[str, list[str]] | None:
    if not request.repository_scope and not request.path_scope:
        return None
    return {
        "repositories": list(request.repository_scope),
        "paths": list(request.path_scope),
    }


def _unique_values(*groups: Iterable[str]) -> list[str]:
    return sorted({value for group in groups for value in group if _normal_text(value)})


def _derive_sections(
    request: BuilderBootstrapRequest,
    context_pack: Mapping[str, Any],
) -> dict[str, Any]:
    """Derive every evidence-facing V4 section from the embedded V3 pack."""
    items = _context_items(context_pack)
    dependency_status = _required_dependency_status(request, context_pack)
    missing = [value for value in dependency_status if value.get("status") != "SATISFIED_AUTHORITATIVE"]
    dependency_by_name = {value["dependency"]: value for value in dependency_status}
    authoritative = _dependency_records(context_pack)
    for dependency in request.required_dependencies:
        if dependency_by_name[dependency].get("status") != "SATISFIED_AUTHORITATIVE":
            continue
        matches = [
            item for item in items
            if _matches(item, dependency) and item.get("authority_class") in {"CANONICAL", "VERIFIED"}
        ]
        if matches and not any(
            entry.get("target") in {item.get("entity_id") for item in matches}
            or entry.get("source") in {item.get("entity_id") for item in matches}
            for entry in authoritative
        ):
            authoritative.append({
                "dependency": dependency,
                "entity_id": matches[0].get("entity_id"),
                "authority_class": matches[0].get("authority_class"),
                "summary": matches[0].get("summary") or matches[0].get("label"),
                "provenance": matches[0].get("provenance", {}),
            })
    authoritative = sorted(authoritative, key=lambda item: json.dumps(_stable(item), sort_keys=True, ensure_ascii=True))

    conflicts = _conflicting_evidence(context_pack)
    stale = _stale_evidence(context_pack)
    unknown = _unknown_evidence(context_pack)
    blockers = _active_blockers(context_pack)
    contracts = _contracts(context_pack, request.builder_number)
    invariants = _safety_invariants(context_pack)
    decisions = _unresolved_decisions(context_pack)
    role = _builder_evidence_role(items, request.builder_number) or "UNKNOWN / NO CURRENT HANDOFF EVIDENCE"
    review_flags: set[str] = set()
    if conflicts:
        review_flags.add("CONTEXT_CONFLICT")
    if stale:
        review_flags.add("STALE_EVIDENCE")
    if unknown:
        review_flags.add("UNKNOWN_EVIDENCE")
    if any(item.get("status") == "MISSING" for item in missing):
        review_flags.add("MISSING_DEPENDENCY")
    if any(item.get("status") == "PRESENT_NONAUTHORITATIVE" for item in missing):
        review_flags.add("DEPENDENCY_AUTHORITY_MISSING")
    if request.include_runtime and not context_pack.get("graph_available", False):
        review_flags.add("RUNTIME_GRAPH_UNAVAILABLE")
    if context_pack.get("truncated"):
        review_flags.add("TRUNCATED_CONTEXT")
    if decisions:
        review_flags.add("UNRESOLVED_CEO_DECISION")
    if any(item.get("review_required") for item in blockers):
        review_flags.add("PRESERVED_UNVERIFIED")
    return {
        "authoritative_dependencies": authoritative,
        "required_dependency_status": dependency_status,
        "missing_dependencies": missing,
        "active_blockers": blockers,
        "required_cross_builder_contracts": contracts,
        "safety_invariants": invariants,
        "unresolved_ceo_decisions": decisions,
        "stale_evidence": stale,
        "conflicting_evidence": conflicts,
        "unknown_evidence": unknown,
        "review_flags": sorted(review_flags),
        "role": role,
        "current_evidence": _current_builder_evidence(context_pack, request.builder_number),
    }


def compile_builder_bootstrap(
    root: Path,
    request: BuilderBootstrapRequest | Mapping[str, Any],
    *,
    vault: Path | None = None,
) -> BuilderBootstrapCompilation:
    """Compile one deterministic, noncanonical Builder Bootstrap V4 pack."""
    root = Path(root).resolve()
    request_obj = request if isinstance(request, BuilderBootstrapRequest) else BuilderBootstrapRequest.from_mapping(request)
    _assert_secret_free(request_obj.to_dict(), "bootstrap_request")
    context_request = _context_request(request_obj)
    compilation = compile_context(root, context_request, vault=Path(vault).resolve() if vault else None)
    context_pack = compilation.pack
    conflicts = _conflicting_evidence(context_pack)
    mandatory_conflicts = [item for item in conflicts if _is_mandatory_conflict(item)]
    if mandatory_conflicts:
        identifiers = ", ".join(str(item.get("type") or item.get("code") or item.get("warning") or "CONFLICT") for item in mandatory_conflicts)
        raise BuilderBootstrapError(f"mandatory context conflict requires CEO review: {identifiers}")

    derived = _derive_sections(request_obj, context_pack)

    prohibited = _unique_values(PROHIBITED_OPERATIONS, request_obj.prohibited_operations)
    verification = _unique_values(VERIFICATION_REQUIREMENTS, request_obj.verification_requirements)
    pack: BuilderBootstrapPack = {
        "schema_version": BOOTSTRAP_SCHEMA,
        "bootstrap_version": BOOTSTRAP_VERSION,
        "bootstrap_id": request_obj.bootstrap_id,
        "builder": {
            "number": request_obj.builder_number,
            "label": f"Builder {request_obj.builder_number}",
            "role": derived["role"],
            "role_baseline": BUILDER_ROLES[request_obj.builder_number],
            "current_evidence": derived["current_evidence"],
        },
        "task_identity": _safe_task_identity(request_obj),
        "context_request": context_request.to_dict(),
        "context_pack": context_pack,
        "authoritative_dependencies": derived["authoritative_dependencies"],
        "required_dependencies": list(request_obj.required_dependencies),
        "required_dependency_status": derived["required_dependency_status"],
        "missing_dependencies": derived["missing_dependencies"],
        "active_blockers": derived["active_blockers"],
        "required_cross_builder_contracts": derived["required_cross_builder_contracts"],
        "safety_invariants": derived["safety_invariants"],
        "allowed_scope": _scope(request_obj),
        "prohibited_operations": prohibited,
        "verification_requirements": verification,
        "unresolved_ceo_decisions": derived["unresolved_ceo_decisions"],
        "stale_evidence": derived["stale_evidence"],
        "conflicting_evidence": derived["conflicting_evidence"],
        "unknown_evidence": derived["unknown_evidence"],
        "review_flags": derived["review_flags"],
        "execution_authorization": "NOT_PROVIDED",
        "safety_decision": "NOT_EVALUATED",
        "source_memory_sha": context_pack["source_memory_sha"],
        "semantic_digest": context_pack["context_digest"],
        "semantic_graph_digest": context_pack["semantic_graph_digest"],
        "bootstrap_digest": "",
        "generated_at": request_obj.generated_at,
    }
    pack["bootstrap_digest"] = _bootstrap_digest(pack)
    _assert_secret_free(pack, "builder_bootstrap")
    return BuilderBootstrapCompilation(pack=pack, markdown=_bootstrap_markdown(pack))


build_builder_bootstrap = compile_builder_bootstrap
compile_bootstrap_pack = compile_builder_bootstrap


def _request_from_pack(payload: Mapping[str, Any]) -> BuilderBootstrapRequest:
    task = payload.get("task_identity")
    context = payload.get("context_request")
    builder = payload.get("builder")
    scope = task.get("scope") if isinstance(task, Mapping) else None
    if not isinstance(task, Mapping) or not isinstance(context, Mapping) or not isinstance(builder, Mapping):
        raise BuilderBootstrapValidationError("bootstrap request provenance is incomplete")
    if scope is not None and (not isinstance(scope, Mapping) or not isinstance(scope.get("repositories"), list) or not isinstance(scope.get("paths"), list)):
        raise BuilderBootstrapValidationError("task identity scope is invalid")
    required = payload.get("required_dependencies")
    if not isinstance(required, list) or not all(isinstance(value, str) and value.strip() for value in required):
        raise BuilderBootstrapValidationError("required_dependencies must be a list of non-empty strings")
    return BuilderBootstrapRequest.from_mapping({
        "bootstrap_id": payload.get("bootstrap_id"),
        "builder_number": builder.get("number"),
        "task_id": task.get("task_id"),
        "task": task.get("task", ""),
        "workstream": task.get("workstream", ""),
        "task_metadata": task.get("metadata", {}),
        "repository_scope": (scope or {}).get("repositories", []) if isinstance(scope, Mapping) else [],
        "path_scope": (scope or {}).get("paths", []) if isinstance(scope, Mapping) else [],
        "required_dependencies": required,
        "prohibited_operations": payload.get("prohibited_operations", []),
        "verification_requirements": payload.get("verification_requirements", []),
        "token_budget": context.get("token_budget", 6000),
        "max_entity_count": context.get("max_entity_count", 80),
        "freshness_requirement": context.get("freshness_requirement", "ANY"),
        "include_runtime": context.get("include_runtime", False),
        "context_request_id": context.get("request_id", ""),
        "generated_at": payload.get("generated_at"),
    })


def _validate_pack_payload(payload: Mapping[str, Any], *, expected_budget: int | None = None) -> BuilderBootstrapPack:
    if not isinstance(payload, Mapping):
        raise BuilderBootstrapValidationError("bootstrap pack must be an object")
    required = {
        "schema_version", "bootstrap_version", "bootstrap_id", "builder", "task_identity",
        "context_request", "context_pack", "authoritative_dependencies", "required_dependencies",
        "required_dependency_status", "missing_dependencies",
        "active_blockers", "required_cross_builder_contracts", "safety_invariants", "allowed_scope",
        "prohibited_operations", "verification_requirements", "unresolved_ceo_decisions",
        "stale_evidence", "conflicting_evidence", "unknown_evidence", "review_flags",
        "execution_authorization", "safety_decision", "source_memory_sha", "semantic_digest",
        "semantic_graph_digest", "bootstrap_digest", "generated_at",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise BuilderBootstrapValidationError("bootstrap pack missing field(s): " + ", ".join(missing))
    if payload.get("schema_version") != BOOTSTRAP_SCHEMA or payload.get("bootstrap_version") != BOOTSTRAP_VERSION:
        raise BuilderBootstrapValidationError("unsupported Builder Bootstrap schema/version")
    if not isinstance(payload.get("bootstrap_id"), str) or not payload["bootstrap_id"].strip():
        raise BuilderBootstrapValidationError("bootstrap_id must be a non-empty identifier")
    builder = payload.get("builder")
    if not isinstance(builder, Mapping) or builder.get("number") not in BUILDER_NUMBERS:
        raise BuilderBootstrapValidationError("builder identity must be exactly 1 through 5")
    number = int(builder["number"])
    if builder.get("label") != f"Builder {number}" or builder.get("role_baseline") != BUILDER_ROLES[number]:
        raise BuilderBootstrapValidationError("builder identity role baseline does not match Builder 1–5 contract")
    if not isinstance(builder.get("role"), str) or not builder["role"].strip():
        raise BuilderBootstrapValidationError("builder role must be explicit or UNKNOWN")
    task = payload.get("task_identity")
    if not isinstance(task, Mapping) or not task.get("task_id"):
        raise BuilderBootstrapValidationError("task_identity must include task_id")
    if not isinstance(task.get("metadata", {}), Mapping) or "scope" not in task:
        raise BuilderBootstrapValidationError("task_identity must preserve metadata and scope provenance")
    context_request_payload = payload.get("context_request")
    if not isinstance(context_request_payload, Mapping):
        raise BuilderBootstrapValidationError("context_request must be an object")
    context = payload.get("context_pack")
    if not isinstance(context, Mapping):
        raise BuilderBootstrapValidationError("context_pack must be an object")
    temp_dir = Path(tempfile.mkdtemp(prefix="sbmem-bootstrap-validate-"))
    temp_path = temp_dir / "context.json"
    try:
        _write_json(temp_path, context)
        validate_context_pack(temp_path, expected_budget=expected_budget)
    except ContextCompilerError as exc:
        raise BuilderBootstrapValidationError(f"embedded Context Compiler V3 pack is invalid: {exc}") from exc
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
    if context.get("consumer") != f"BUILDER_{number}":
        raise BuilderBootstrapValidationError("embedded context consumer does not match builder")
    if payload.get("source_memory_sha") != context.get("source_memory_sha"):
        raise BuilderBootstrapValidationError("source_memory_sha does not match embedded context")
    if payload.get("semantic_digest") != context.get("context_digest"):
        raise BuilderBootstrapValidationError("semantic_digest does not match embedded Context Compiler digest")
    if payload.get("semantic_graph_digest") != context.get("semantic_graph_digest"):
        raise BuilderBootstrapValidationError("semantic_graph_digest does not match embedded context")
    try:
        expected_request = _request_from_pack(payload)
        expected_context_request = _context_request(expected_request).to_dict()
    except (BuilderBootstrapError, ContextCompilerError) as exc:
        raise BuilderBootstrapValidationError(f"bootstrap request provenance is invalid: {exc}") from exc
    if dict(context_request_payload) != expected_context_request:
        raise BuilderBootstrapValidationError("context_request does not match task/request provenance")
    derived = _derive_sections(expected_request, context)
    derived_fields = (
        "authoritative_dependencies", "required_dependency_status", "missing_dependencies",
        "active_blockers", "required_cross_builder_contracts", "safety_invariants",
        "unresolved_ceo_decisions", "stale_evidence", "conflicting_evidence",
        "unknown_evidence", "review_flags",
    )
    for field_name in derived_fields:
        if payload.get(field_name) != derived[field_name]:
            raise BuilderBootstrapValidationError(f"derived field does not match embedded context: {field_name}")
    if payload.get("allowed_scope") != _scope(expected_request):
        raise BuilderBootstrapValidationError("allowed_scope does not match task identity scope")
    if builder.get("role") != derived["role"] or builder.get("current_evidence") != derived["current_evidence"]:
        raise BuilderBootstrapValidationError("Builder current evidence or role does not match embedded context")
    if payload.get("execution_authorization") != "NOT_PROVIDED" or payload.get("safety_decision") != "NOT_EVALUATED":
        raise BuilderBootstrapValidationError("bootstrap must not claim authorization or a safety decision")
    for field_name in ("authoritative_dependencies", "missing_dependencies", "active_blockers", "required_cross_builder_contracts", "safety_invariants", "unresolved_ceo_decisions", "stale_evidence", "conflicting_evidence", "unknown_evidence", "review_flags", "prohibited_operations", "verification_requirements"):
        if not isinstance(payload.get(field_name), list):
            raise BuilderBootstrapValidationError(f"{field_name} must be a list")
    if len(payload["prohibited_operations"]) != len(set(payload["prohibited_operations"])) or len(payload["verification_requirements"]) != len(set(payload["verification_requirements"])):
        raise BuilderBootstrapValidationError("prohibited and verification lists must be deterministic and duplicate-free")
    if not set(PROHIBITED_OPERATIONS).issubset(payload["prohibited_operations"]):
        raise BuilderBootstrapValidationError("required prohibited-operation boundary is incomplete")
    if not set(VERIFICATION_REQUIREMENTS).issubset(payload["verification_requirements"]):
        raise BuilderBootstrapValidationError("required verification boundary is incomplete")
    allowed_scope = payload.get("allowed_scope")
    if allowed_scope is not None and (not isinstance(allowed_scope, Mapping) or not isinstance(allowed_scope.get("repositories"), list) or not isinstance(allowed_scope.get("paths"), list)):
        raise BuilderBootstrapValidationError("allowed_scope must be null or contain repository/path lists")
    try:
        _parse_time(payload.get("generated_at"))
        if _parse_time(payload.get("generated_at")) is None:
            raise ValueError
    except (TypeError, ValueError):
        raise BuilderBootstrapValidationError("generated_at must be timezone-aware ISO-8601")
    _assert_secret_free(payload, "builder_bootstrap")
    if payload.get("bootstrap_digest") != _bootstrap_digest(payload):
        raise BuilderBootstrapValidationError("bootstrap_digest does not match semantic package content")
    return dict(payload)  # type: ignore[return-value]


def validate_builder_bootstrap(path: Path, *, expected_budget: int | None = None) -> BuilderBootstrapPack:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise BuilderBootstrapValidationError(f"bootstrap pack is not valid JSON: {path}") from exc
    return _validate_pack_payload(payload, expected_budget=expected_budget)


def inspect_builder_bootstrap(path: Path) -> dict[str, Any]:
    payload = validate_builder_bootstrap(path)
    builder = payload["builder"]
    context = payload["context_pack"]
    return {
        "schema_version": payload["schema_version"],
        "bootstrap_version": payload["bootstrap_version"],
        "bootstrap_id": payload["bootstrap_id"],
        "builder": builder,
        "task_identity": payload["task_identity"],
        "source_memory_sha": payload["source_memory_sha"],
        "semantic_digest": payload["semantic_digest"],
        "bootstrap_digest": payload["bootstrap_digest"],
        "context": {
            "request_id": context["request_id"],
            "included_entity_count": context["included_entity_count"],
            "estimated_tokens": context["estimated_tokens"],
            "graph_available": context.get("graph_available", False),
            "freshness_state": context.get("freshness_state", "UNKNOWN"),
        },
        "review_flags": payload["review_flags"],
        "active_blocker_count": len(payload["active_blockers"]),
        "missing_dependency_count": len(payload["missing_dependencies"]),
    }


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def _ensure_external_bootstrap_output(root: Path, vault: Path) -> Path:
    """Reject the actual resolved V4 output target if it enters canonical Memory."""
    root = Path(root).resolve()
    target = (Path(vault) / BOOTSTRAP_DIR).resolve()
    try:
        target.relative_to(root)
    except ValueError:
        return target
    raise ContextCompilerError(
        f"Builder Bootstrap output must be outside the canonical Memory checkout: {target}"
    )


def build_builder_bootstrap_atomic(
    root: Path,
    request: BuilderBootstrapRequest | Mapping[str, Any],
    *,
    vault: Path,
) -> dict[str, Any]:
    """Build and safely promote one noncanonical pack into an external Vault."""
    root = Path(root).resolve()
    vault = Path(vault).resolve()
    _ensure_external_context_output(root, vault)
    _ensure_external_bootstrap_output(root, vault)
    compilation = compile_builder_bootstrap(root, request, vault=vault)
    request_obj = request if isinstance(request, BuilderBootstrapRequest) else BuilderBootstrapRequest.from_mapping(request)
    output_dir = vault / BOOTSTRAP_DIR
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{request_obj.bootstrap_id}.json"
    md_path = output_dir / f"{request_obj.bootstrap_id}.md"
    temp_dir = Path(tempfile.mkdtemp(prefix=".builder-bootstrap-", dir=str(output_dir.parent)))
    previous: dict[Path, bytes | None] = {path: path.read_bytes() if path.exists() else None for path in (json_path, md_path)}
    try:
        temp_json = temp_dir / json_path.name
        temp_md = temp_dir / md_path.name
        _write_json(temp_json, compilation.pack)
        temp_md.write_text(compilation.markdown, encoding="utf-8")
        validate_builder_bootstrap(temp_json, expected_budget=compilation.pack["context_pack"]["token_budget"])
        output_dir.mkdir(parents=True, exist_ok=True)
        os.replace(temp_json, json_path)
        os.replace(temp_md, md_path)
        return {
            "status": "ONLINE",
            "json": str(json_path),
            "markdown": str(md_path),
            "bootstrap_digest": compilation.pack["bootstrap_digest"],
            "pack": compilation.pack,
        }
    except Exception:
        for path, data in previous.items():
            if data is None:
                path.unlink(missing_ok=True)
            else:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(data)
        raise
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
