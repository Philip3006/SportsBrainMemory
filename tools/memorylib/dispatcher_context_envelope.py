"""Read-only Dispatcher Context Envelope V1 over Memory Context V3/V4/V5.

The envelope is the stable seam between a future dispatcher and Memory.  It
packages already compiled context; it does not implement retrieval policy,
make a safety decision, grant authority, launch work, or mutate canonical or
runtime state.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any, Iterable, Mapping, TypedDict

from .builder_bootstrap import (
    BuilderBootstrapError,
    BuilderBootstrapRequest,
    compile_builder_bootstrap,
    validate_builder_bootstrap,
)
from .consistency_auditor import ConsistencyAudit, audit_consistency
from .context_compiler import (
    ContextCompilerError,
    ContextRequest,
    _assert_secret_free,
    _digest,
    _normal_text,
    _parse_time,
    _safe_request_id,
    _semantic_value,
    _stable,
    compile_context,
    validate_context_pack,
)
from .governance import BUILDER_NUMBERS, BUILDER_ROLES


ENVELOPE_SCHEMA = 1
ENVELOPE_VERSION = "memory-dispatcher-context-envelope-v1.0"
WORKER_BUILDER_NUMBERS = (1, 2, 3, 4)
WORKER_BUILDER_SET = frozenset(WORKER_BUILDER_NUMBERS)
CLASSIFICATIONS = frozenset({
    "CONTEXT_READY",
    "CONTEXT_WARNING",
    "CONTEXT_STALE",
    "CONTEXT_CONFLICT",
    "CONTEXT_UNKNOWN",
    "CONTEXT_FAILED_CLOSED",
})
FORBIDDEN_CLASSIFICATIONS = frozenset({
    "SAFE_TO_EXECUTE", "AUTHORIZED", "APPROVED", "DEPLOYABLE",
    "MERGEABLE", "PRODUCTION_READY",
})
AUTHORIZATION_FIELDS = (
    "execution_authorization",
    "merge_authorization",
    "deployment_authorization",
    "production_activation_authorization",
    "controlled_shadow_authorization",
    "betting_authorization",
    "financial_mutation_authorization",
    "ledger_mutation_authorization",
    "model_approval",
    "production_signal_time_approval",
    "sealed_research_access",
    "provider_access",
    "quota_spend_authorization",
)
REQUIRED_AUTHORIZATION_VALUES = {field_name: "NOT_PROVIDED" for field_name in AUTHORIZATION_FIELDS}
REQUIRED_AUTHORIZATION_VALUES["safety_decision"] = "NOT_EVALUATED"
SAFETY_BOUNDARIES = (
    ("NO-BET", "NO-BET"),
    ("NO-LIVE-ACTIVATION", "NO-LIVE-ACTIVATION"),
    ("SEALED-2425-2526", "SEALED 2425/2526"),
    ("CLOSING-ODDS-BENCHMARK", "Closing odds benchmark-only"),
)
DEFAULT_PROHIBITED_OPERATIONS = (
    "do not launch Codex, Builders, agents, the Night Shift Dispatcher, or a queue",
    "do not merge, rebase, force-push, deploy, or activate live behavior",
    "do not modify SportsBrain production/runtime, Cloudflare, ledger, or betting state",
    "do not modify canonical Memory history or promote runtime candidates",
    "do not access or unlock sealed 2425/2526 Research data",
    "do not grant or infer CEO, execution, provider, quota, or financial authorization",
)
DEFAULT_VERIFICATION_REQUIREMENTS = (
    "verify the exact source Memory SHA and all embedded V3/V4/V5 digests",
    "validate this envelope and its embedded Context Compiler V3 and Builder Bootstrap V4 contracts",
    "stop for CEO review on conflict, stale, unknown, missing, or non-authoritative mandatory evidence",
    "preserve NO-BET, NO-LIVE-ACTIVATION, SEALED 2425/2526, and benchmark-only closing-odds boundaries",
)
SECRETISH_KEY_RE = re.compile(
    r"(?i)(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|password|private[_ -]?key|client[_ -]?secret|secret[_ -]?key)"
)
SECRET_VALUE_RE = re.compile(r"(?i)(?:bearer\s+|gh[pousr]_)[A-Za-z0-9._-]{20,}")


class DispatcherEnvelopeError(ValueError):
    """A dispatcher envelope request or package failed closed."""


class DispatcherEnvelopeValidationError(DispatcherEnvelopeError):
    """A persisted dispatcher envelope failed its contract."""


class DispatcherContextEnvelope(TypedDict, total=False):
    schema_version: int
    envelope_version: str
    envelope_id: str
    classification: str
    builder_number: int
    governed_role: str
    current_evidence_role: str
    task_identity: dict[str, Any]
    repository_scope: list[str]
    allowed_paths: list[str]
    prohibited_paths: list[str]
    declared_dependencies: list[str]
    reference_time: str
    token_budget: int
    context_budget: int
    context_pack: dict[str, Any]
    context_pack_digest: str
    context_pack_ref: str
    v3_pack_digest: str
    v3_pack_ref: str
    bootstrap_pack: dict[str, Any] | None
    bootstrap_digest: str | None
    bootstrap_ref: str | None
    v4_bootstrap_digest: str | None
    v4_bootstrap_ref: str | None
    consistency_audit: dict[str, Any]
    consistency_audit_digest: str
    consistency_audit_ref: str
    v5_audit_digest: str
    v5_audit_ref: str
    authoritative_dependencies: list[dict[str, Any]]
    required_dependency_states: list[dict[str, Any]]
    non_authoritative_evidence: list[dict[str, Any]]
    active_blockers: list[dict[str, Any]]
    required_cross_builder_contracts: list[dict[str, Any]]
    safety_invariants: list[dict[str, Any]]
    verification_requirements: list[str]
    unresolved_ceo_decisions: list[dict[str, Any]]
    stale_evidence: list[dict[str, Any]]
    conflicting_evidence: list[dict[str, Any]]
    unknown_evidence: list[dict[str, Any]]
    review_flags: list[str]
    source_provenance: list[str]
    source_memory_sha: str
    execution_authorization: str
    merge_authorization: str
    deployment_authorization: str
    production_activation_authorization: str
    controlled_shadow_authorization: str
    betting_authorization: str
    financial_mutation_authorization: str
    ledger_mutation_authorization: str
    model_approval: str
    production_signal_time_approval: str
    sealed_research_access: str
    provider_access: str
    quota_spend_authorization: str
    safety_decision: str
    semantic_envelope_digest: str
    generated_at: str


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _assert_envelope_secret_free(value: Any, path: str = "envelope") -> None:
    """Apply V3's secret rejection while allowing immutable control fields."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if key_text in REQUIRED_AUTHORIZATION_VALUES:
                expected = REQUIRED_AUTHORIZATION_VALUES[key_text]
                if item != expected:
                    raise DispatcherEnvelopeError(f"immutable authorization field changed at {path}.{key_text}")
            elif SECRETISH_KEY_RE.search(key_text):
                raise DispatcherEnvelopeError(f"secret-bearing field rejected at {path}.{key_text}")
            _assert_envelope_secret_free(item, f"{path}.{key_text}")
        return
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            _assert_envelope_secret_free(item, f"{path}[{index}]")
        return
    text = str(value)
    if SECRET_VALUE_RE.search(text):
        raise DispatcherEnvelopeError(f"secret-like value rejected at {path}")


def _values(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    values = value if isinstance(value, (list, tuple, set)) else [value]
    result = {_normal_text(item) for item in values if _normal_text(item)}
    return sorted(result)


def _builder_number(value: Any) -> int:
    if isinstance(value, bool):
        raise DispatcherEnvelopeError("worker builder must be an explicit integer from 1 through 4")
    if isinstance(value, int):
        number = value
    else:
        text = _normal_text(value)
        match = re.fullmatch(r"(?:BUILDER[_: ]*)?([0-9]+)", text, re.IGNORECASE)
        if not match:
            raise DispatcherEnvelopeError("worker builder identity must be exactly Builder 1 through Builder 4")
        number = int(match.group(1))
    if number not in WORKER_BUILDER_SET:
        if number == 5:
            raise DispatcherEnvelopeError("Builder 5 is the Dispatcher Owner and is not a worker target")
        raise DispatcherEnvelopeError("unsupported worker Builder; governed worker identities are exactly 1 through 4")
    return number


def _mapping_value(value: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in value and value[key] not in (None, "", []):
            return value[key]
    return None


@dataclass(frozen=True)
class DispatcherContextEnvelopeRequest:
    """External dispatcher input; no authority-bearing fields are accepted."""

    envelope_id: str
    builder_number: int
    task_id: str
    task_description: str = ""
    workstream: str = ""
    repository_scope: tuple[str, ...] = ()
    allowed_paths: tuple[str, ...] = ()
    prohibited_paths: tuple[str, ...] = ()
    declared_dependencies: tuple[str, ...] = ()
    entity_seeds: tuple[str, ...] = ()
    task_metadata: dict[str, Any] = field(default_factory=dict)
    prohibited_operations: tuple[str, ...] = ()
    verification_requirements: tuple[str, ...] = ()
    token_budget: int = 6000
    max_entity_count: int = 80
    freshness_requirement: str = "ANY"
    include_runtime: bool = False
    reference_time: str = ""
    generated_at: str = ""

    def __post_init__(self) -> None:
        number = _builder_number(self.builder_number)
        object.__setattr__(self, "builder_number", number)
        metadata = dict(self.task_metadata or {})
        try:
            _assert_secret_free(metadata, "task_metadata")
        except ContextCompilerError as exc:
            raise DispatcherEnvelopeError(str(exc)) from exc
        object.__setattr__(self, "task_metadata", metadata)
        task_id = _normal_text(self.task_id)
        if not task_id:
            raise DispatcherEnvelopeError("task_id is required")
        object.__setattr__(self, "task_id", _safe_request_id(task_id))
        object.__setattr__(self, "envelope_id", _safe_request_id(self.envelope_id))
        for name in (
            "repository_scope", "allowed_paths", "prohibited_paths", "declared_dependencies",
            "entity_seeds", "prohibited_operations", "verification_requirements",
        ):
            object.__setattr__(self, name, tuple(_values(getattr(self, name))))
        if not isinstance(self.token_budget, int) or isinstance(self.token_budget, bool) or self.token_budget < 64:
            raise DispatcherEnvelopeError("token_budget must be an integer >= 64")
        if not isinstance(self.max_entity_count, int) or isinstance(self.max_entity_count, bool) or self.max_entity_count < 1:
            raise DispatcherEnvelopeError("max_entity_count must be a positive integer")
        freshness = str(self.freshness_requirement).upper()
        if freshness not in {"ANY", "FRESH_ONLY", "FRESH_OR_AGING"}:
            raise DispatcherEnvelopeError(f"unsupported freshness_requirement: {freshness!r}")
        object.__setattr__(self, "freshness_requirement", freshness)
        reference = self.reference_time or _iso_now()
        generated = self.generated_at or _iso_now()
        if _parse_time(reference) is None or _parse_time(generated) is None:
            raise DispatcherEnvelopeError("reference_time and generated_at must be timezone-aware ISO-8601")
        object.__setattr__(self, "reference_time", reference)
        object.__setattr__(self, "generated_at", generated)

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "DispatcherContextEnvelopeRequest":
        if not isinstance(value, Mapping):
            raise DispatcherEnvelopeError("dispatcher envelope request must be an object")
        try:
            _assert_secret_free(value, "dispatcher_request")
        except ContextCompilerError as exc:
            raise DispatcherEnvelopeError(str(exc)) from exc
        metadata = _mapping_value(value, "task_metadata", "metadata") or {}
        if not isinstance(metadata, Mapping):
            raise DispatcherEnvelopeError("task_metadata must be an object")
        metadata = dict(metadata)
        raw_builder = _mapping_value(metadata, "builder_number", "builder")
        if raw_builder is None:
            raw_builder = _mapping_value(value, "builder_number", "builder")
        number = _builder_number(raw_builder)
        task = _normal_text(_mapping_value(metadata, "task", "objective", "description") or _mapping_value(value, "task", "objective", "description"))
        workstream = _normal_text(_mapping_value(metadata, "workstream") or _mapping_value(value, "workstream"))
        task_id = _normal_text(_mapping_value(metadata, "task_id", "current_task_id") or _mapping_value(value, "task_id", "current_task_id"))
        if not task_id:
            task_id = "TASK-" + _digest({"builder_number": number, "task": task, "workstream": workstream, "metadata": _semantic_value(metadata)})[:16]
        reference = str(_mapping_value(value, "reference_time", "observed_at") or _iso_now())
        envelope_id = _normal_text(_mapping_value(value, "envelope_id", "request_id") or "")
        if not envelope_id:
            envelope_id = "ENV-" + _digest({
                "builder_number": number, "task_id": task_id, "task": task,
                "workstream": workstream, "metadata": _semantic_value(metadata),
                "reference_time": reference,
            })[:20]
        repository = _mapping_value(value, "repository_scope", "repository", "source_repository")
        allowed = _mapping_value(value, "allowed_paths", "path_scope")
        prohibited_paths = _mapping_value(value, "prohibited_paths", "forbidden_paths")
        dependencies = _mapping_value(value, "declared_dependencies", "required_dependencies", "dependencies")
        seeds = _mapping_value(value, "entity_seeds", "seeds") or _mapping_value(metadata, "entity_seeds", "seeds")
        provisional: dict[str, Any] = {
            "envelope_id": envelope_id,
            "builder_number": number,
            "task_id": task_id,
            "task_description": task,
            "workstream": workstream,
            "repository_scope": _values(repository),
            "allowed_paths": _values(allowed),
            "prohibited_paths": _values(prohibited_paths),
            "declared_dependencies": _values(dependencies),
            "entity_seeds": _values(seeds),
            "task_metadata": metadata,
            "prohibited_operations": _values(_mapping_value(value, "prohibited_operations", "prohibited")),
            "verification_requirements": _values(_mapping_value(value, "verification_requirements", "verification")),
            "token_budget": value.get("token_budget", value.get("context_budget", value.get("budget_tokens", 6000))),
            "max_entity_count": value.get("max_entity_count", value.get("max_entities", 80)),
            "freshness_requirement": value.get("freshness_requirement", value.get("freshness", "ANY")),
            "include_runtime": bool(value.get("include_runtime", False)),
            "reference_time": reference,
            "generated_at": str(value.get("generated_at") or _iso_now()),
        }
        return cls(**provisional)

    def semantic_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "builder_number": self.builder_number,
            "task_id": self.task_id,
            "task_description": self.task_description,
            "workstream": self.workstream,
            "repository_scope": list(self.repository_scope),
            "allowed_paths": list(self.allowed_paths),
            "prohibited_paths": list(self.prohibited_paths),
            "declared_dependencies": list(self.declared_dependencies),
            "entity_seeds": list(self.entity_seeds),
            "task_metadata": _stable(self.task_metadata),
            "prohibited_operations": list(self.prohibited_operations),
            "verification_requirements": list(self.verification_requirements),
            "token_budget": self.token_budget,
            "max_entity_count": self.max_entity_count,
            "freshness_requirement": self.freshness_requirement,
            "include_runtime": self.include_runtime,
            "reference_time": self.reference_time,
        }

    def to_dict(self) -> dict[str, Any]:
        value = self.semantic_dict()
        value["generated_at"] = self.generated_at
        return value


@dataclass(frozen=True)
class DispatcherContextEnvelopeCompilation:
    envelope: DispatcherContextEnvelope
    markdown: str


class MemoryV4BootstrapProvider:
    """Stable read-only seam for a future dispatcher or context consumer."""

    def __init__(self, root: Path, *, vault: Path | None = None) -> None:
        self.root = Path(root).resolve()
        self.vault = Path(vault).resolve() if vault else None

    def request(
        self,
        *,
        builder: int,
        task_metadata: Mapping[str, Any] | None = None,
        repository: str | Iterable[str] | None = None,
        allowed_paths: Iterable[str] = (),
        prohibited_paths: Iterable[str] = (),
        declared_dependencies: Iterable[str] = (),
        reference_time: str | None = None,
        token_budget: int = 6000,
        **metadata: Any,
    ) -> DispatcherContextEnvelope:
        """Return one validated envelope; never launches, authorizes, or writes."""
        supplied = dict(task_metadata or {})
        supplied.update(metadata)
        request = DispatcherContextEnvelopeRequest.from_mapping({
            "builder_number": builder,
            "task_metadata": supplied,
            "repository": repository,
            "allowed_paths": list(allowed_paths),
            "prohibited_paths": list(prohibited_paths),
            "declared_dependencies": list(declared_dependencies),
            "reference_time": reference_time or _iso_now(),
            "token_budget": token_budget,
        })
        compilation = compile_dispatcher_context_envelope(self.root, request, vault=self.vault)
        _validate_in_temp(compilation.envelope, validate_dispatcher_context_envelope, request.token_budget)
        return compilation.envelope


MemoryContextProvider = MemoryV4BootstrapProvider


def _compact(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _compact(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_compact(item) for item in value]
    return value


def _semantic_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    ignored = {"semantic_envelope_digest", "generated_at"}
    def walk(item: Any) -> Any:
        if isinstance(item, Mapping):
            return {str(key): walk(child) for key, child in sorted(item.items(), key=lambda pair: str(pair[0])) if key not in ignored}
        if isinstance(item, (list, tuple)):
            return [walk(child) for child in item]
        return item
    return walk(value)


def _envelope_digest(value: Mapping[str, Any]) -> str:
    return _digest(_semantic_envelope(value))


def _ref(kind: str, digest: str | None) -> str | None:
    return f"memory://{kind}/{digest}" if digest else None


def _validate_in_temp(payload: Mapping[str, Any], validator: Any, expected_budget: int | None = None) -> None:
    temp_dir = Path(tempfile.mkdtemp(prefix="sbmem-envelope-validate-"))
    path = temp_dir / "embedded.json"
    try:
        path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        if expected_budget is None:
            validator(path)
        else:
            validator(path, expected_budget=expected_budget)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _bootstrap_request(request: DispatcherContextEnvelopeRequest) -> BuilderBootstrapRequest:
    metadata = dict(request.task_metadata)
    metadata.setdefault("entity_seeds", list(request.entity_seeds))
    metadata.setdefault("prohibited_paths", list(request.prohibited_paths))
    if request.repository_scope:
        metadata.setdefault("repository", list(request.repository_scope))
    return BuilderBootstrapRequest.from_mapping({
        "bootstrap_id": "BOOT-" + request.envelope_id,
        "builder_number": request.builder_number,
        "task_id": request.task_id,
        "task": request.task_description,
        "workstream": request.workstream,
        "task_metadata": metadata,
        "repository_scope": list(request.repository_scope),
        "path_scope": list(request.allowed_paths),
        "required_dependencies": list(request.declared_dependencies),
        "prohibited_operations": list(request.prohibited_operations),
        "verification_requirements": list(request.verification_requirements),
        "token_budget": request.token_budget,
        "max_entity_count": request.max_entity_count,
        "freshness_requirement": request.freshness_requirement,
        "include_runtime": request.include_runtime,
        "context_request_id": "CTX-" + request.envelope_id,
        "generated_at": request.reference_time,
    })


def _v5_findings(audit: ConsistencyAudit | Mapping[str, Any]) -> list[dict[str, Any]]:
    if isinstance(audit, ConsistencyAudit):
        return [dict(item) for item in audit.findings]
    values = audit.get("findings", []) if isinstance(audit, Mapping) else []
    return [dict(item) for item in values if isinstance(item, Mapping)]


def _audit_dict(audit: ConsistencyAudit | Mapping[str, Any]) -> dict[str, Any]:
    return audit.to_dict() if isinstance(audit, ConsistencyAudit) else dict(audit)


def _audit_semantic_digest(audit: Mapping[str, Any]) -> str:
    semantic = {
        "schema_version": audit.get("schema_version"),
        "source_memory_sha": audit.get("source_memory_sha"),
        "reference_time": audit.get("reference_time"),
        "overall_status": audit.get("overall_status"),
        "runtime_available": audit.get("runtime_available"),
        "findings": audit.get("findings", []),
    }
    return _digest(semantic)


def _unique_records(*groups: Iterable[Any]) -> list[dict[str, Any]]:
    values: dict[str, dict[str, Any]] = {}
    for group in groups:
        for item in group:
            if not isinstance(item, Mapping):
                continue
            record = _compact(dict(item))
            values[json.dumps(record, sort_keys=True, ensure_ascii=True)] = record
    return [values[key] for key in sorted(values)]


def _finding_records(findings: Iterable[Mapping[str, Any]], statuses: set[str]) -> list[dict[str, Any]]:
    return _unique_records(item for item in findings if str(item.get("status", "")).upper() in statuses)


def _provenance(context_pack: Mapping[str, Any], findings: Iterable[Mapping[str, Any]]) -> list[str]:
    paths: set[str] = set()
    for item in context_pack.get("included_entities", []):
        provenance = item.get("provenance", {}) if isinstance(item, Mapping) else {}
        for path in provenance.get("source_paths", []) if isinstance(provenance, Mapping) else []:
            if _normal_text(path):
                paths.add(_normal_text(path))
    for finding in findings:
        for path in finding.get("source_paths", []) if isinstance(finding, Mapping) else []:
            if _normal_text(path):
                paths.add(_normal_text(path))
    return sorted(paths)


def _safety_invariants(existing: Iterable[Any]) -> list[dict[str, Any]]:
    records = [dict(item) for item in existing if isinstance(item, Mapping)]
    by_id = {str(item.get("invariant_id") or item.get("entity_id") or item.get("id")): item for item in records}
    for identifier, statement in SAFETY_BOUNDARIES:
        by_id.setdefault(identifier, {
            "invariant_id": identifier,
            "statement": statement,
            "authority": "GOVERNED_SAFETY_BOUNDARY",
        })
    return [_compact(by_id[key]) for key in sorted(by_id)]


def _classification(
    *,
    v3: Mapping[str, Any],
    v4: Mapping[str, Any] | None,
    audit: Mapping[str, Any],
    bootstrap_error: str | None,
    source_mismatch: bool,
) -> tuple[str, set[str]]:
    findings = _v5_findings(audit)
    statuses = {str(item.get("status", "")).upper() for item in findings}
    overall = str(audit.get("overall_status", "")).upper()
    flags: set[str] = set()
    if bootstrap_error:
        flags.add("BOOTSTRAP_FAILED_CLOSED")
    if source_mismatch:
        flags.add("SOURCE_SHA_CONFLICT")
    if overall in {"SAFETY_INVARIANT_MISSING", "GOVERNANCE_DRIFT", "FAILED_CLOSED"}:
        flags.add(overall)
    for finding in findings:
        status = str(finding.get("status", "")).upper()
        code = str(finding.get("code", "")).upper()
        if status in {"SAFETY_INVARIANT_MISSING", "GOVERNANCE_DRIFT", "FAILED_CLOSED"}:
            flags.add(status)
        if code:
            flags.add("V5_" + code)
    v4_flags = set(str(item) for item in (v4 or {}).get("review_flags", []))
    flags.update(v4_flags)
    if any(flag in flags for flag in {"SAFETY_INVARIANT_MISSING", "GOVERNANCE_DRIFT", "FAILED_CLOSED", "BOOTSTRAP_FAILED_CLOSED", "SOURCE_SHA_CONFLICT"}):
        return "CONTEXT_FAILED_CLOSED", flags
    if any(
        str(item.get("domain", "")).lower() in {"dependencies", "authority"}
        and str(item.get("status", "")).upper() in {"CONFLICT", "NONAUTHORITATIVE_ONLY", "MISSING"}
        for item in findings
    ) or {"MISSING_DEPENDENCY", "DEPENDENCY_AUTHORITY_MISSING"} & v4_flags:
        flags.add("MANDATORY_DEPENDENCY_REVIEW")
        return "CONTEXT_FAILED_CLOSED", flags
    if overall == "CONFLICT":
        statuses.add("CONFLICT")
    if overall == "UNKNOWN":
        statuses.add("UNKNOWN")
    if "CONFLICT" in statuses or "CONTEXT_CONFLICT" in v4_flags or v3.get("conflicts"):
        flags.add("CONTEXT_CONFLICT")
        return "CONTEXT_CONFLICT", flags
    if "CEO_DECISION_REQUIRED" in statuses:
        flags.add("UNRESOLVED_CEO_DECISION")
        return "CONTEXT_WARNING", flags
    runtime_context_requested = bool((v3.get("request") or {}).get("include_runtime"))
    if str(v3.get("freshness_state", "")).upper() == "STALE" or "STALE" in statuses or "STALE_EVIDENCE" in v4_flags:
        flags.add("STALE_EVIDENCE")
        return "CONTEXT_STALE", flags
    if (runtime_context_requested and str(v3.get("freshness_state", "")).upper() in {"UNKNOWN", "CONFLICTING"}) or "UNKNOWN" in statuses or "UNKNOWN_EVIDENCE" in v4_flags or "RUNTIME_GRAPH_UNAVAILABLE" in v4_flags:
        flags.add("UNKNOWN_EVIDENCE")
        return "CONTEXT_UNKNOWN", flags
    if findings or v3.get("warnings") or (v4 or {}).get("review_flags"):
        return "CONTEXT_WARNING", flags
    return "CONTEXT_READY", flags


def _markdown_section(lines: list[str], title: str, values: Iterable[str]) -> None:
    values = [value for value in values if _normal_text(value)]
    lines.extend([f"## {title}", ""])
    lines.extend(values or ["- None."])
    lines.append("")


def _render_markdown(pack: Mapping[str, Any]) -> str:
    lines = [
        "<!-- GENERATED BY SportsBrain Memory Dispatcher Context Envelope V1: NONCANONICAL EXTERNAL ARTIFACT -->",
        "# SportsBrain Dispatcher Context Envelope V1", "",
        f"- Classification: **{pack['classification']}**",
        f"- Envelope ID: `{pack['envelope_id']}`",
        f"- Worker target: **BUILDER: {pack['builder_number']}**",
        f"- Governed role: **{pack['governed_role']}**",
        f"- Task: `{pack['task_identity']['task_id']}` — {pack['task_identity'].get('description') or 'No task description supplied.'}",
        f"- Source Memory SHA: `{pack['source_memory_sha']}`",
        f"- Semantic envelope digest: `{pack['semantic_envelope_digest']}`",
        "- Read-only delivery: **true**", "",
    ]
    _markdown_section(lines, "AUTHORIZATION BOUNDARY", [f"- {field_name}: **{pack[field_name]}**" for field_name in (*AUTHORIZATION_FIELDS, "safety_decision")])
    _markdown_section(lines, "CONTEXT CHAIN", [
        f"- V3 Context digest: `{pack['context_pack_digest']}` ({pack['context_pack_ref']})",
        f"- V4 Bootstrap digest: `{pack['bootstrap_digest'] or 'NOT_AVAILABLE'}` ({pack['bootstrap_ref'] or 'NOT_AVAILABLE'})",
        f"- V5 Consistency digest: `{pack['consistency_audit_digest']}` ({pack['consistency_audit_ref']})",
    ])
    _markdown_section(lines, "TASK / REPOSITORY SCOPE", [
        f"- Repositories: `{json.dumps(pack['repository_scope'], ensure_ascii=False)}`",
        f"- Allowed paths: `{json.dumps(pack['allowed_paths'], ensure_ascii=False)}`",
        f"- Prohibited paths: `{json.dumps(pack['prohibited_paths'], ensure_ascii=False)}`",
        f"- Declared dependencies: `{json.dumps(pack['declared_dependencies'], ensure_ascii=False)}`",
    ])
    for title, key in (
        ("AUTHORITATIVE DEPENDENCIES", "authoritative_dependencies"),
        ("DEPENDENCY STATES", "required_dependency_states"),
        ("NON-AUTHORITATIVE EVIDENCE", "non_authoritative_evidence"),
        ("ACTIVE BLOCKERS", "active_blockers"),
        ("REQUIRED CROSS-BUILDER CONTRACTS", "required_cross_builder_contracts"),
        ("SAFETY INVARIANTS", "safety_invariants"),
        ("UNRESOLVED CEO DECISIONS", "unresolved_ceo_decisions"),
        ("STALE EVIDENCE", "stale_evidence"),
        ("CONFLICTING EVIDENCE", "conflicting_evidence"),
        ("UNKNOWN EVIDENCE", "unknown_evidence"),
    ):
        _markdown_section(lines, title, [f"- `{json.dumps(_stable(item), ensure_ascii=False, sort_keys=True)}`" for item in pack.get(key, [])])
    _markdown_section(lines, "REVIEW FLAGS", [f"- **{flag}**" for flag in pack.get("review_flags", [])])
    _markdown_section(lines, "PROHIBITED OPERATIONS", [f"- {value}" for value in pack.get("prohibited_operations", [])])
    _markdown_section(lines, "VERIFICATION REQUIREMENTS", [f"- {value}" for value in pack.get("verification_requirements", [])])
    _markdown_section(lines, "BOUNDARY", [
        "- This package delivers context only. It does not decide whether a task is safe to execute and does not claim CEO authorization.",
        "- B5 is the Dispatcher Owner seam, not a worker target. Builders 6+ are unsupported until explicit governance changes the roster.",
        "- Runtime candidates remain canonical=false and promotion_required=true; canonical history, Vault runtime, production, and sealed data are not mutated.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def compile_dispatcher_context_envelope(
    root: Path,
    request: DispatcherContextEnvelopeRequest | Mapping[str, Any],
    *,
    vault: Path | None = None,
) -> DispatcherContextEnvelopeCompilation:
    """Compile one read-only envelope by consuming the V3, V4, and V5 layers."""
    root = Path(root).resolve()
    request_obj = request if isinstance(request, DispatcherContextEnvelopeRequest) else DispatcherContextEnvelopeRequest.from_mapping(request)
    _assert_secret_free(request_obj.to_dict(), "dispatcher_request")
    context_request = ContextRequest.from_mapping({
        "request_id": "CTX-" + request_obj.envelope_id,
        "consumer_type": f"BUILDER_{request_obj.builder_number}",
        "builder_number": request_obj.builder_number,
        "task": request_obj.task_description,
        "workstream": request_obj.workstream,
        "repository_scope": list(request_obj.repository_scope),
        "entity_seeds": sorted(set(request_obj.entity_seeds) | set(request_obj.declared_dependencies)),
        "token_budget": request_obj.token_budget,
        "max_entity_count": request_obj.max_entity_count,
        "freshness_requirement": request_obj.freshness_requirement,
        "include_runtime": request_obj.include_runtime,
        "generated_at": request_obj.reference_time,
    })
    runtime_vault = Path(vault).resolve() if vault else None
    v3_compilation = compile_context(root, context_request, vault=runtime_vault)
    context_pack = dict(v3_compilation.pack)
    _validate_in_temp(context_pack, validate_context_pack, request_obj.token_budget)
    bootstrap_error: str | None = None
    bootstrap_pack: dict[str, Any] | None = None
    try:
        bootstrap_compilation = compile_builder_bootstrap(root, _bootstrap_request(request_obj), vault=runtime_vault)
        bootstrap_pack = dict(bootstrap_compilation.pack)
        _validate_in_temp(bootstrap_pack, validate_builder_bootstrap, request_obj.token_budget)
        if bootstrap_pack.get("context_pack") != context_pack:
            raise DispatcherEnvelopeError("V3 context differs between direct compilation and Builder Bootstrap V4")
    except (BuilderBootstrapError, ContextCompilerError, DispatcherEnvelopeError) as exc:
        bootstrap_error = str(exc)
    audit = audit_consistency(root, vault=runtime_vault, reference_time=request_obj.reference_time)
    audit_payload = _audit_dict(audit)
    source_shas = {
        str(context_pack.get("source_memory_sha", "")),
        str((bootstrap_pack or {}).get("source_memory_sha", context_pack.get("source_memory_sha", ""))),
        str(audit_payload.get("source_memory_sha", "")),
    }
    source_mismatch = len(source_shas) != 1
    classification, flags = _classification(
        v3=context_pack,
        v4=bootstrap_pack,
        audit=audit_payload,
        bootstrap_error=bootstrap_error,
        source_mismatch=source_mismatch,
    )
    findings = _v5_findings(audit_payload)
    bootstrap_sections = bootstrap_pack or {}
    included = context_pack.get("included_entities", [])
    non_authoritative = [
        _compact(item) for item in included
        if isinstance(item, Mapping) and item.get("authority_class") not in {"CANONICAL", "VERIFIED"}
    ]
    stale = _unique_records(bootstrap_sections.get("stale_evidence", []), _finding_records(findings, {"STALE"}))
    conflicting = _unique_records(bootstrap_sections.get("conflicting_evidence", []), _finding_records(findings, {"CONFLICT", "GOVERNANCE_DRIFT", "SAFETY_INVARIANT_MISSING"}))
    unknown = _unique_records(bootstrap_sections.get("unknown_evidence", []), _finding_records(findings, {"UNKNOWN", "NONAUTHORITATIVE_ONLY"}))
    decisions = _unique_records(
        bootstrap_sections.get("unresolved_ceo_decisions", []),
        (item for item in findings if str(item.get("status", "")).upper() in {"CEO_DECISION_REQUIRED", "CONFLICT", "GOVERNANCE_DRIFT"}),
    )
    blockers = _unique_records(
        bootstrap_sections.get("active_blockers", []),
        (item for item in findings if str(item.get("domain", "")).lower() in {"blocker", "builder_status"} and str(item.get("status", "")).upper() not in {"CONSISTENT"}),
    )
    safety = _safety_invariants(bootstrap_sections.get("safety_invariants", []))
    prohibited_operations = sorted(set(DEFAULT_PROHIBITED_OPERATIONS) | set(bootstrap_sections.get("prohibited_operations", [])) | set(request_obj.prohibited_operations))
    verification = sorted(set(DEFAULT_VERIFICATION_REQUIREMENTS) | set(bootstrap_sections.get("verification_requirements", [])) | set(request_obj.verification_requirements))
    review_flags = sorted(set(flags) | set(bootstrap_sections.get("review_flags", [])))
    if bootstrap_error:
        review_flags.append("BOOTSTRAP_ERROR:" + bootstrap_error)
        review_flags = sorted(set(review_flags))
    pack: DispatcherContextEnvelope = {
        "schema_version": ENVELOPE_SCHEMA,
        "envelope_version": ENVELOPE_VERSION,
        "envelope_id": request_obj.envelope_id,
        "classification": classification,
        "builder_number": request_obj.builder_number,
        "governed_role": BUILDER_ROLES[request_obj.builder_number],
        "current_evidence_role": str(bootstrap_sections.get("builder", {}).get("role") or "UNKNOWN / NO CURRENT HANDOFF EVIDENCE"),
        "task_identity": {
            "task_id": request_obj.task_id,
            "description": request_obj.task_description,
            "workstream": request_obj.workstream,
            "metadata": _stable(request_obj.task_metadata),
        },
        "repository_scope": list(request_obj.repository_scope),
        "allowed_paths": list(request_obj.allowed_paths),
        "prohibited_paths": list(request_obj.prohibited_paths),
        "declared_dependencies": list(request_obj.declared_dependencies),
        "reference_time": request_obj.reference_time,
        "token_budget": request_obj.token_budget,
        "context_budget": request_obj.token_budget,
        "context_pack": context_pack,
        "context_pack_digest": str(context_pack.get("context_digest")),
        "context_pack_ref": _ref("context-v3", str(context_pack.get("context_digest"))),
        "v3_pack_digest": str(context_pack.get("context_digest")),
        "v3_pack_ref": _ref("context-v3", str(context_pack.get("context_digest"))),
        "bootstrap_pack": bootstrap_pack,
        "bootstrap_digest": str(bootstrap_pack.get("bootstrap_digest")) if bootstrap_pack else None,
        "bootstrap_ref": _ref("bootstrap-v4", str(bootstrap_pack.get("bootstrap_digest"))) if bootstrap_pack else None,
        "v4_bootstrap_digest": str(bootstrap_pack.get("bootstrap_digest")) if bootstrap_pack else None,
        "v4_bootstrap_ref": _ref("bootstrap-v4", str(bootstrap_pack.get("bootstrap_digest"))) if bootstrap_pack else None,
        "consistency_audit": audit_payload,
        "consistency_audit_digest": str(audit_payload.get("semantic_digest", "")),
        "consistency_audit_ref": _ref("consistency-audit-v5", str(audit_payload.get("semantic_digest", ""))),
        "v5_audit_digest": str(audit_payload.get("semantic_digest", "")),
        "v5_audit_ref": _ref("consistency-audit-v5", str(audit_payload.get("semantic_digest", ""))),
        "authoritative_dependencies": _compact(bootstrap_sections.get("authoritative_dependencies", [])),
        "required_dependency_states": _compact(bootstrap_sections.get("required_dependency_status", [])),
        "non_authoritative_evidence": non_authoritative,
        "active_blockers": blockers,
        "required_cross_builder_contracts": _compact(bootstrap_sections.get("required_cross_builder_contracts", [])),
        "safety_invariants": safety,
        "verification_requirements": verification,
        "unresolved_ceo_decisions": decisions,
        "stale_evidence": stale,
        "conflicting_evidence": conflicting,
        "unknown_evidence": unknown,
        "review_flags": review_flags,
        "source_provenance": _provenance(context_pack, findings),
        "source_memory_sha": str(context_pack.get("source_memory_sha", "")),
        **REQUIRED_AUTHORIZATION_VALUES,
        "semantic_envelope_digest": "",
        "generated_at": request_obj.generated_at,
    }
    _assert_envelope_secret_free(pack, "dispatcher_envelope")
    pack["semantic_envelope_digest"] = _envelope_digest(pack)
    _assert_envelope_secret_free(pack, "dispatcher_envelope")
    return DispatcherContextEnvelopeCompilation(envelope=pack, markdown=_render_markdown(pack))


build_dispatcher_context_envelope = compile_dispatcher_context_envelope
compile_context_envelope = compile_dispatcher_context_envelope


def _validate_payload(payload: Mapping[str, Any], *, expected_budget: int | None = None) -> DispatcherContextEnvelope:
    if not isinstance(payload, Mapping):
        raise DispatcherEnvelopeValidationError("dispatcher envelope must be an object")
    required = {
        "schema_version", "envelope_version", "envelope_id", "classification", "builder_number", "governed_role",
        "current_evidence_role", "task_identity", "repository_scope", "allowed_paths", "prohibited_paths",
        "declared_dependencies", "reference_time", "token_budget", "context_budget", "context_pack",
        "context_pack_digest", "context_pack_ref", "bootstrap_pack", "bootstrap_digest", "bootstrap_ref",
        "v3_pack_digest", "v3_pack_ref", "v4_bootstrap_digest", "v4_bootstrap_ref",
        "consistency_audit", "consistency_audit_digest", "consistency_audit_ref", "authoritative_dependencies",
        "v5_audit_digest", "v5_audit_ref",
        "required_dependency_states", "non_authoritative_evidence", "active_blockers", "required_cross_builder_contracts",
        "safety_invariants", "verification_requirements", "unresolved_ceo_decisions", "stale_evidence",
        "conflicting_evidence", "unknown_evidence", "review_flags", "source_provenance", "source_memory_sha",
        *AUTHORIZATION_FIELDS, "safety_decision", "semantic_envelope_digest", "generated_at",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise DispatcherEnvelopeValidationError("dispatcher envelope missing field(s): " + ", ".join(missing))
    if payload.get("schema_version") != ENVELOPE_SCHEMA or payload.get("envelope_version") != ENVELOPE_VERSION:
        raise DispatcherEnvelopeValidationError("unsupported Dispatcher Context Envelope schema/version")
    classification = str(payload.get("classification", ""))
    if classification not in CLASSIFICATIONS or classification in FORBIDDEN_CLASSIFICATIONS:
        raise DispatcherEnvelopeValidationError("classification is not an allowed context classification")
    number = payload.get("builder_number")
    if isinstance(number, bool) or number not in WORKER_BUILDER_SET:
        raise DispatcherEnvelopeValidationError("envelope worker target must be Builder 1 through Builder 4; Builder 5 is not a worker target")
    if payload.get("governed_role") != BUILDER_ROLES[int(number)]:
        raise DispatcherEnvelopeValidationError("governed_role does not match the current governed Builder roster")
    for name in ("repository_scope", "allowed_paths", "prohibited_paths", "declared_dependencies", "verification_requirements", "review_flags", "source_provenance"):
        if not isinstance(payload.get(name), list) or any(not isinstance(value, str) for value in payload[name]):
            raise DispatcherEnvelopeValidationError(f"{name} must be a deterministic list of strings")
    task = payload.get("task_identity")
    if not isinstance(task, Mapping) or not isinstance(task.get("task_id"), str) or not task["task_id"].strip():
        raise DispatcherEnvelopeValidationError("task_identity must include a task_id")
    if not isinstance(task.get("metadata", {}), Mapping):
        raise DispatcherEnvelopeValidationError("task_identity metadata must be an object")
    for name in ("authoritative_dependencies", "required_dependency_states", "non_authoritative_evidence", "active_blockers", "required_cross_builder_contracts", "safety_invariants", "unresolved_ceo_decisions", "stale_evidence", "conflicting_evidence", "unknown_evidence"):
        if not isinstance(payload.get(name), list):
            raise DispatcherEnvelopeValidationError(f"{name} must be a list")
    if not isinstance(payload.get("token_budget"), int) or payload["token_budget"] < 64 or payload.get("context_budget") != payload.get("token_budget"):
        raise DispatcherEnvelopeValidationError("token/context budget is invalid")
    if expected_budget is not None and payload["token_budget"] != expected_budget:
        raise DispatcherEnvelopeValidationError("envelope token budget does not match expected budget")
    for name, expected in REQUIRED_AUTHORIZATION_VALUES.items():
        if payload.get(name) != expected:
            raise DispatcherEnvelopeValidationError(f"{name} is immutable and must remain {expected}")
    context = payload.get("context_pack")
    if not isinstance(context, Mapping):
        raise DispatcherEnvelopeValidationError("context_pack must be an object")
    _validate_in_temp(context, validate_context_pack, payload["token_budget"])
    if any(payload.get(name) != expected for name, expected in (
        ("context_pack_digest", context.get("context_digest")),
        ("v3_pack_digest", context.get("context_digest")),
        ("context_pack_ref", _ref("context-v3", context.get("context_digest"))),
        ("v3_pack_ref", _ref("context-v3", context.get("context_digest"))),
    )):
        raise DispatcherEnvelopeValidationError("V3 context digest/reference is inconsistent")
    bootstrap = payload.get("bootstrap_pack")
    if bootstrap is not None:
        if not isinstance(bootstrap, Mapping):
            raise DispatcherEnvelopeValidationError("bootstrap_pack must be null or an object")
        _validate_in_temp(bootstrap, validate_builder_bootstrap, payload["token_budget"])
        if any(payload.get(name) != expected for name, expected in (
            ("bootstrap_digest", bootstrap.get("bootstrap_digest")),
            ("v4_bootstrap_digest", bootstrap.get("bootstrap_digest")),
            ("bootstrap_ref", _ref("bootstrap-v4", bootstrap.get("bootstrap_digest"))),
            ("v4_bootstrap_ref", _ref("bootstrap-v4", bootstrap.get("bootstrap_digest"))),
        )):
            raise DispatcherEnvelopeValidationError("V4 bootstrap digest/reference is inconsistent")
        if bootstrap.get("builder", {}).get("number") != number:
            raise DispatcherEnvelopeValidationError("V4 bootstrap Builder does not match envelope worker target")
    elif payload.get("classification") != "CONTEXT_FAILED_CLOSED":
        raise DispatcherEnvelopeValidationError("bootstrap_pack may be absent only for a failed-closed envelope")
    elif any(payload.get(name) is not None for name in ("bootstrap_digest", "bootstrap_ref", "v4_bootstrap_digest", "v4_bootstrap_ref")):
        raise DispatcherEnvelopeValidationError("failed-closed envelope cannot claim an unavailable V4 digest")
    audit = payload.get("consistency_audit")
    if not isinstance(audit, Mapping) or not isinstance(audit.get("findings"), list) or not isinstance(audit.get("semantic_digest"), str):
        raise DispatcherEnvelopeValidationError("consistency_audit is incomplete")
    if any(payload.get(name) != expected for name, expected in (
        ("consistency_audit_digest", audit.get("semantic_digest")),
        ("v5_audit_digest", audit.get("semantic_digest")),
        ("consistency_audit_ref", _ref("consistency-audit-v5", audit.get("semantic_digest"))),
        ("v5_audit_ref", _ref("consistency-audit-v5", audit.get("semantic_digest"))),
    )):
        raise DispatcherEnvelopeValidationError("V5 audit digest/reference is inconsistent")
    if audit.get("semantic_digest") != _audit_semantic_digest(audit):
        raise DispatcherEnvelopeValidationError("V5 audit semantic digest does not match its findings")
    source = payload.get("source_memory_sha")
    if not isinstance(source, str) or not source:
        raise DispatcherEnvelopeValidationError("source_memory_sha is required")
    for embedded in (context, bootstrap or {}, audit):
        if embedded and embedded.get("source_memory_sha") != source:
            raise DispatcherEnvelopeValidationError("source Memory SHA differs across V3/V4/V5")
    for identifier, statement in SAFETY_BOUNDARIES:
        text = json.dumps(payload.get("safety_invariants", []), ensure_ascii=False).upper()
        if statement.upper() not in text:
            raise DispatcherEnvelopeValidationError(f"safety boundary is not visible: {statement}")
    for item in payload.get("non_authoritative_evidence", []):
        if not isinstance(item, Mapping):
            raise DispatcherEnvelopeValidationError("non_authoritative_evidence must contain objects")
        if item.get("candidate_type") in {"SOURCE_CANDIDATE_EVENT", "CANDIDATE_OPERATIONAL_EVIDENCE"} and (item.get("canonical") is not False or item.get("promotion_required") is not True):
            raise DispatcherEnvelopeValidationError("runtime candidate authority boundary is violated")
    _assert_envelope_secret_free(payload, "dispatcher_envelope")
    if payload.get("semantic_envelope_digest") != _envelope_digest(payload):
        raise DispatcherEnvelopeValidationError("semantic_envelope_digest does not match envelope content")
    if _parse_time(payload.get("reference_time")) is None or _parse_time(payload.get("generated_at")) is None:
        raise DispatcherEnvelopeValidationError("reference_time and generated_at must be timezone-aware ISO-8601")
    return dict(payload)  # type: ignore[return-value]


def validate_dispatcher_context_envelope(path: Path, *, expected_budget: int | None = None) -> DispatcherContextEnvelope:
    path = Path(path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DispatcherEnvelopeValidationError(f"dispatcher envelope is not valid JSON: {path}") from exc
    return _validate_payload(payload, expected_budget=expected_budget)


validate_context_envelope = validate_dispatcher_context_envelope


def inspect_dispatcher_context_envelope(path: Path) -> dict[str, Any]:
    payload = validate_dispatcher_context_envelope(path)
    return {
        "schema_version": payload["schema_version"],
        "envelope_id": payload["envelope_id"],
        "classification": payload["classification"],
        "builder_number": payload["builder_number"],
        "governed_role": payload["governed_role"],
        "task_id": payload["task_identity"]["task_id"],
        "source_memory_sha": payload["source_memory_sha"],
        "context_pack_digest": payload["context_pack_digest"],
        "bootstrap_digest": payload["bootstrap_digest"],
        "consistency_audit_digest": payload["consistency_audit_digest"],
        "semantic_envelope_digest": payload["semantic_envelope_digest"],
        "review_flags": payload["review_flags"],
    }


def _ensure_external_output(root: Path, vault: Path | None, output: Path) -> tuple[Path, Path]:
    root = Path(root).resolve()
    vault = Path(vault).resolve() if vault else None
    raw = Path(output)
    resolved = raw.resolve(strict=False)
    if _inside(resolved, root):
        raise DispatcherEnvelopeError("dispatcher envelope output must be outside canonical Memory")
    if vault and _inside(resolved, vault):
        raise DispatcherEnvelopeError("dispatcher envelope output must be outside the external Vault")
    if raw.suffix.lower() == ".json":
        directory = resolved.parent
        json_path = resolved
    else:
        directory = resolved
        json_path = resolved / "DISPATCHER_CONTEXT_ENVELOPE.json"
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


def write_dispatcher_context_envelope(
    compilation: DispatcherContextEnvelopeCompilation,
    output: Path,
    *,
    root: Path,
    vault: Path | None = None,
) -> dict[str, str]:
    """Write only to an explicitly supplied external path with symlink checks."""
    json_path, markdown_path = _ensure_external_output(root, vault, Path(output))
    _atomic_write(json_path, json.dumps(compilation.envelope, indent=2, sort_keys=True, ensure_ascii=False) + "\n")
    _atomic_write(markdown_path, compilation.markdown)
    validate_dispatcher_context_envelope(json_path)
    return {"json": str(json_path), "markdown": str(markdown_path), "semantic_envelope_digest": compilation.envelope["semantic_envelope_digest"]}


write_context_envelope = write_dispatcher_context_envelope
