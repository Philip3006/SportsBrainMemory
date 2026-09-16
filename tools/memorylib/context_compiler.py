"""Deterministic, auditable Context Compiler V3.

This module selects context from canonical Memory, the Semantic Graph V2
registry, and explicitly requested runtime observations. It never writes
canonical Memory or promotes runtime evidence.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any, Iterable, Mapping, TypedDict

from .frontmatter import parse_frontmatter
from .observer import _latest_builder_evidence, _valid_handoffs
from .semantic_graph import (
    Entity,
    GraphEdge,
    GraphIssue,
    SemanticGraph,
    canonical_input_digest,
    validate_semantic_graph,
)


CONTEXT_SCHEMA = 3
COMPILER_VERSION = "memory-context-compiler-v3.1"
SELECTION_POLICY_VERSION = "v3-deterministic-authority-first-20260916"
CONTEXT_DIR = "_live/context"
CONSUMER_TYPES = {"CEO", "BUILDER_1", "BUILDER_2", "BUILDER_3", "BUILDER_4", "GENERIC_REVIEW"}
FRESHNESS_REQUIREMENTS = {"ANY", "FRESH_ONLY", "FRESH_OR_AGING"}
BUILDER_NUMBERS = {1, 2, 3, 4}

RELATION_PRIORITY: dict[str, int] = {
    "invariant": 110, "blocked_by": 100, "blocks": 100,
    "verified_by": 98, "verification": 98, "implements": 96,
    "supersedes": 95, "superseded_by": 95, "governed_by": 94,
    "constrained_by": 94, "depends_on": 92, "validates": 90,
    "produces_evidence_for": 90, "owned_by": 88, "builder": 88,
    "workstream": 86, "affected_workstream": 86, "evidence_reference": 80,
    "related": 70, "explicit_link": 68, "source_pr": 66,
    "evidence_pr": 64, "merge_commit": 62, "source_commit": 62, "domain": 45,
}

AUTHORITY_RANK = {"CANONICAL": 4, "VERIFIED": 3, "CANDIDATE": 2, "RUNTIME_DERIVED": 1}
REASON_PRIORITY = {
    "SAFETY_INVARIANT": 1200, "ACTIVE_BLOCKER": 1150, "GOVERNING_DECISION": 1100,
    "EXPLICIT_SEED": 1080, "REQUIRED_CROSS_BUILDER_CONTRACT": 1060,
    "OWNER_CONTEXT": 1040, "DIRECT_DEPENDENCY": 980, "RECENT_VERIFICATION": 940,
    "RECENT_EVIDENCE": 900, "SECOND_HOP_RELATION": 700, "SUPERSEDED_HISTORY": 200,
}

PROFILES = {
    "CEO": {"focus": ("objective", "progress", "blockers", "risks", "decisions", "builders", "critical_path", "next_safe_action"), "partners": (1, 2, 3, 4)},
    "BUILDER_1": {"focus": ("task", "workstream", "decisions", "contracts", "dependencies", "safety", "blockers", "verification"), "partners": (2, 4)},
    "BUILDER_2": {"focus": ("task", "workstream", "decisions", "contracts", "dependencies", "safety", "blockers", "verification"), "partners": (4,)},
    "BUILDER_3": {"focus": ("task", "workstream", "memory", "graph", "sync", "safety", "blockers", "verification"), "partners": ()},
    "BUILDER_4": {"focus": ("task", "workstream", "decisions", "contracts", "dependencies", "safety", "blockers", "verification"), "partners": (1, 2)},
    "GENERIC_REVIEW": {"focus": ("objective", "verified_state", "dependencies", "provenance"), "partners": ()},
}

SAFE_METADATA_FIELDS = {
    "status", "type", "title", "name", "summary", "domain", "workstream",
    "builder", "builder_number", "source_repository", "source_pr", "source_sha",
    "source_merge_sha", "merge_sha", "verification_state", "ceo_gate_state",
    "canonical", "promotion_required", "candidate_type", "classification", "severity",
    "freshness_class", "last_updated", "updated_at", "created_at", "timestamp",
    "observed_at", "head_sha", "branch", "role", "tests", "ci", "tests_passed",
    "blocker_id", "auto_resolve", "latest_for_builder",
}
SECRET_KEY_RE = re.compile(r"(?i)(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|authorization|password|private[_ -]?key|client[_ -]?secret|secret[_ -]?key)")
SECRET_VALUE_RE = re.compile(r"(?i)(?:bearer\s+|gh[pousr]_)[A-Za-z0-9._-]{20,}")
SECRET_ASSIGNMENT_RE = re.compile(r"(?i)\b(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|password|authorization|private[_ -]?key|client[_ -]?secret|secret[_ -]?key)\s*[:=]\s*([^\s,;]+)")


class ContextCompilerError(ValueError):
    """A request, source, or generated pack failed a fail-closed contract."""


class ContextValidationError(ContextCompilerError):
    """A generated or supplied context pack is invalid."""


class ContextPack(TypedDict, total=False):
    """JSON contract for a noncanonical V3 context pack."""

    schema_version: int
    compiler_version: str
    request: dict[str, Any]
    request_id: str
    consumer: str
    source_memory_sha: str
    semantic_graph_digest: str
    runtime_digest: str | None
    selection_policy_version: str
    profile: dict[str, Any]
    seed_entities: list[str]
    graph_available: bool
    included_entities: list[dict[str, Any]]
    included_edges: list[dict[str, Any]]
    candidate_entity_count: int
    included_entity_count: int
    omitted_entity_count: int
    canonical_count: int
    runtime_count: int
    truncated: bool
    token_budget: int
    estimated_tokens: int
    freshness_state: str
    warnings: list[str]
    conflicts: list[dict[str, Any]]
    unresolved_references: list[dict[str, Any]]
    metrics: dict[str, Any]
    generated_at: str
    cache_key: str
    context_digest: str


def _normal_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _parse_time(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _stable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _stable(value[key]) for key in sorted(value, key=str)}
    if isinstance(value, (list, tuple, set)):
        values = [_stable(item) for item in value]
        return sorted(values, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True))
    return value


def _semantic_value(value: Any) -> Any:
    """Remove observation bookkeeping that must not alter semantic output."""
    if isinstance(value, Mapping):
        ignored = {"generated_at", "first_observed_at", "last_observed_at", "observation_count"}
        return {str(key): _semantic_value(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0])) if key not in ignored}
    if isinstance(value, (list, tuple)):
        return [_semantic_value(item) for item in value]
    return value


def _digest(value: Any) -> str:
    encoded = json.dumps(_stable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _assert_secret_free(value: Any, path: str = "context") -> None:
    """Reject secret-bearing fields while allowing safe boolean presence flags."""
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            if SECRET_KEY_RE.search(key_text) and not (key_text.casefold() == "credentials_present" and isinstance(item, bool)):
                raise ContextCompilerError(f"secret-bearing field rejected at {path}.{key_text}")
            _assert_secret_free(item, f"{path}.{key_text}")
        return
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            _assert_secret_free(item, f"{path}[{index}]")
        return
    text = str(value)
    if SECRET_VALUE_RE.search(text):
        raise ContextCompilerError(f"secret-like value rejected at {path}")
    match = SECRET_ASSIGNMENT_RE.search(text)
    if match and match.group(1).strip().casefold() not in {"true", "false", "none", "null", "unknown", "redacted"}:
        raise ContextCompilerError(f"secret-like assignment rejected at {path}")


def _list_value(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, (list, tuple, set)):
        return [_normal_text(item) for item in value if _normal_text(item)]
    return [_normal_text(value)] if _normal_text(value) else []


def _safe_request_id(value: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    if not normalized or normalized in {".", ".."} or len(normalized) > 120:
        raise ContextCompilerError("request_id must be a short filesystem-safe identifier")
    return normalized


@dataclass(frozen=True)
class ContextRequest:
    request_id: str
    consumer_type: str
    builder_number: int | None = None
    task: str = ""
    workstream: str = ""
    repository_scope: tuple[str, ...] = ()
    entity_seeds: tuple[str, ...] = ()
    requested_domains: tuple[str, ...] = ()
    token_budget: int = 6000
    max_entity_count: int = 80
    freshness_requirement: str = "ANY"
    include_runtime: bool = False
    generated_at: str = ""

    def __post_init__(self) -> None:
        consumer = str(self.consumer_type).upper().replace("-", "_")
        object.__setattr__(self, "consumer_type", consumer)
        if consumer not in CONSUMER_TYPES:
            raise ContextCompilerError(f"unsupported consumer_type: {consumer!r}")
        number = self.builder_number
        if number is not None and (isinstance(number, bool) or number not in BUILDER_NUMBERS):
            raise ContextCompilerError("builder_number must be exactly 1, 2, 3, or 4")
        expected = int(consumer.split("_", 1)[1]) if consumer.startswith("BUILDER_") else None
        if expected is not None and number not in (None, expected):
            raise ContextCompilerError("builder_number must match consumer_type")
        if expected is not None:
            object.__setattr__(self, "builder_number", expected)
        freshness = str(self.freshness_requirement).upper()
        if freshness not in FRESHNESS_REQUIREMENTS:
            raise ContextCompilerError(f"unsupported freshness_requirement: {freshness!r}")
        object.__setattr__(self, "freshness_requirement", freshness)
        if not isinstance(self.token_budget, int) or isinstance(self.token_budget, bool) or self.token_budget < 64:
            raise ContextCompilerError("token_budget must be an integer >= 64")
        if not isinstance(self.max_entity_count, int) or isinstance(self.max_entity_count, bool) or self.max_entity_count < 1:
            raise ContextCompilerError("max_entity_count must be a positive integer")
        timestamp = self.generated_at or _iso_now()
        if _parse_time(timestamp) is None:
            raise ContextCompilerError("generated_at must be timezone-aware ISO-8601")
        object.__setattr__(self, "generated_at", timestamp)
        object.__setattr__(self, "request_id", _safe_request_id(self.request_id))
        for field_name in ("repository_scope", "entity_seeds", "requested_domains"):
            object.__setattr__(self, field_name, tuple(sorted(set(_list_value(getattr(self, field_name))))))

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "ContextRequest":
        if not isinstance(value, Mapping):
            raise ContextCompilerError("context request must be an object")
        consumer = str(value.get("consumer_type") or value.get("consumer") or "").upper().replace("-", "_")
        if not consumer:
            raise ContextCompilerError("context request requires consumer_type")
        number = value.get("builder_number")
        if number is None and consumer.startswith("BUILDER_"):
            try:
                number = int(consumer.split("_", 1)[1])
            except (TypeError, ValueError):
                number = None
        provisional: dict[str, Any] = {
            "request_id": str(value.get("request_id") or ""),
            "consumer_type": consumer,
            "builder_number": number,
            "task": _normal_text(value.get("task")),
            "workstream": _normal_text(value.get("workstream")),
            "repository_scope": tuple(_list_value(value.get("repository_scope") or value.get("repository"))),
            "entity_seeds": tuple(_list_value(value.get("entity_seeds") or value.get("seeds"))),
            "requested_domains": tuple(_list_value(value.get("requested_domains") or value.get("domains"))),
            "token_budget": value.get("token_budget", value.get("budget_tokens", 6000)),
            "max_entity_count": value.get("max_entity_count", 80),
            "freshness_requirement": value.get("freshness_requirement", "ANY"),
            "include_runtime": bool(value.get("include_runtime", False)),
            "generated_at": str(value.get("generated_at") or _iso_now()),
        }
        if not provisional["request_id"]:
            semantic = dict(provisional)
            semantic.pop("generated_at", None)
            provisional["request_id"] = "CTX-" + _digest(semantic)[:16]
        return cls(**provisional)

    def semantic_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "consumer_type": self.consumer_type,
            "builder_number": self.builder_number,
            "task": self.task,
            "workstream": self.workstream,
            "repository_scope": list(self.repository_scope),
            "entity_seeds": list(self.entity_seeds),
            "requested_domains": list(self.requested_domains),
            "token_budget": self.token_budget,
            "max_entity_count": self.max_entity_count,
            "freshness_requirement": self.freshness_requirement,
            "include_runtime": self.include_runtime,
        }

    def to_dict(self) -> dict[str, Any]:
        result = self.semantic_dict()
        result["generated_at"] = self.generated_at
        return result


@dataclass
class _Candidate:
    key: str
    reasons: set[str] = field(default_factory=set)
    score: int = 0
    hops: int = 0
    relation_paths: list[dict[str, Any]] = field(default_factory=list)
    explicit: bool = False
    synthetic: dict[str, Any] | None = None


@dataclass
class ContextCompilation:
    pack: ContextPack
    markdown: str


def _authority(entity: Entity | None, synthetic: Mapping[str, Any] | None = None) -> str:
    if synthetic:
        if synthetic.get("candidate_type") in {"CANDIDATE_OPERATIONAL_EVIDENCE", "SOURCE_CANDIDATE_EVENT"}:
            return "CANDIDATE"
        return "RUNTIME_DERIVED"
    if entity is None:
        return "RUNTIME_DERIVED"
    if entity.provenance == "GOVERNED_IDENTITY":
        return "CANONICAL"
    if entity.provenance in {"RUNTIME_DERIVED", "PRESERVED_LAST_KNOWN"} or not entity.canonical:
        if entity.metadata.get("candidate_type") in {"CANDIDATE_OPERATIONAL_EVIDENCE", "SOURCE_CANDIDATE_EVENT"}:
            return "CANDIDATE"
        return "RUNTIME_DERIVED"
    if entity.namespace == "VERIFICATION" or "verified" in entity.provenance.casefold():
        return "VERIFIED"
    return "CANONICAL"


def _entity_timestamp(entity: Entity | None, synthetic: Mapping[str, Any] | None = None) -> str | None:
    source = synthetic or (entity.metadata if entity else {})
    if not isinstance(source, Mapping):
        return None
    for field_name in ("observed_at", "timestamp", "updated_at", "last_updated", "created_at"):
        if source.get(field_name):
            return str(source[field_name])
    return None


def _freshness(value: Any, reference: datetime) -> str:
    timestamp = _parse_time(value)
    if timestamp is None:
        return "STALE"
    hours = max(0.0, (reference - timestamp).total_seconds() / 3600.0)
    if hours <= 6:
        return "FRESH"
    if hours <= 24:
        return "AGING"
    return "STALE"


def _git_head(root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=3,
        )
        value = result.stdout.strip()
        if re.fullmatch(r"[0-9a-f]{40}", value):
            return value
    except (OSError, subprocess.SubprocessError):
        pass
    return "UNCOMMITTED-" + canonical_input_digest(root)


def _runtime_json(vault: Path | None, filename: str) -> Any:
    if vault is None:
        return None
    path = vault / "_live" / filename
    try:
        return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None
    except (OSError, json.JSONDecodeError):
        return None


def _runtime_snapshot(vault: Path | None) -> dict[str, Any]:
    if vault is None:
        return {}
    names = ("SOURCE_OBSERVER.json", "SOURCE_CANDIDATES.json", "BUILDER_HANDOFFS.json", "BLOCKERS.json")
    result: dict[str, Any] = {}
    for name in names:
        payload = _runtime_json(vault, name)
        if isinstance(payload, dict):
            _assert_secret_free(payload, f"_live/{name}")
            result[name] = payload
    return result


def _runtime_digest(snapshot: Mapping[str, Any]) -> str | None:
    return _digest(_semantic_value(snapshot)) if snapshot else None


def _graph_semantic_digest(graph: SemanticGraph) -> str:
    return _digest(_semantic_value(graph.semantic_payload()))


def _runtime_candidate_records(snapshot: Mapping[str, Any]) -> tuple[dict[str, Any], dict[int, dict[str, Any]], list[dict[str, Any]]]:
    handoff_payload = snapshot.get("BUILDER_HANDOFFS.json", {})
    raw_handoffs = handoff_payload.get("candidates", []) if isinstance(handoff_payload, dict) else []
    valid_handoffs = _valid_handoffs(raw_handoffs)
    latest = _latest_builder_evidence(valid_handoffs)
    records: dict[str, Any] = {}
    for item in valid_handoffs:
        value = dict(item)
        value["source_path"] = "_live/BUILDER_HANDOFFS.json"
        records[f"EVIDENCE:{item['candidate_id']}"] = value
        for blocker in item.get("blockers", []) if isinstance(item.get("blockers"), list) else []:
            if not isinstance(blocker, dict) or not blocker.get("blocker_id"):
                continue
            blocker_value = dict(blocker)
            blocker_value["source_path"] = "_live/BUILDER_HANDOFFS.json"
            blocker_value.setdefault("observed_at", item.get("observed_at"))
            records.setdefault(f"BLOCKER:{blocker['blocker_id']}", blocker_value)
    for payload_name in ("SOURCE_CANDIDATES.json", "SOURCE_OBSERVER.json"):
        payload = snapshot.get(payload_name, {})
        for item in payload.get("candidates", []) if isinstance(payload, dict) else []:
            if isinstance(item, dict) and item.get("candidate_id"):
                value = dict(item)
                value["source_path"] = f"_live/{payload_name}"
                records[f"EVIDENCE:{item['candidate_id']}"] = value
    blockers: list[dict[str, Any]] = []
    for item in valid_handoffs:
        for blocker in item.get("blockers", []) if isinstance(item.get("blockers"), list) else []:
            if isinstance(blocker, dict) and blocker.get("blocker_id") and not any(existing.get("blocker_id") == blocker["blocker_id"] for existing in blockers):
                blockers.append(dict(blocker))
    blocker_payload = snapshot.get("BLOCKERS.json", {})
    if isinstance(blocker_payload, dict):
        blockers.extend(item for item in blocker_payload.get("blockers", []) if isinstance(item, dict) and item.get("blocker_id"))
    observer = snapshot.get("SOURCE_OBSERVER.json", {})
    if isinstance(observer, dict):
        blockers.extend(item for item in observer.get("blockers", []) if isinstance(item, dict) and item.get("blocker_id"))
    for blocker in blockers:
        value = dict(blocker)
        value["source_path"] = "_live/BLOCKERS.json"
        records.setdefault(f"BLOCKER:{blocker['blocker_id']}", value)
    return records, latest, blockers


def _runtime_graph_available(root: Path, vault: Path | None) -> bool:
    if not vault:
        return False
    path = vault / "_live" / "graph" / "GRAPH_MANIFEST.json"
    if not path.is_file():
        return False
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(manifest, dict) or manifest.get("noncanonical_view") is not True:
        return False
    try:
        validation = validate_semantic_graph(root, path.parent, vault=vault, link_base=vault)
    except Exception:
        return False
    return validation.errors == 0 and validation.warnings == 0


def _seed_match(graph: SemanticGraph, seed: str) -> list[str]:
    needle = _normal_text(seed).casefold()
    if not needle:
        return []
    matches: list[str] = []
    for key, entity in graph.entities.items():
        values = {key, entity.stable_id, entity.label, *entity.source_paths}
        values.update(str(value) for value in entity.metadata.values() if isinstance(value, (str, int)))
        if any(needle == str(value).casefold() for value in values):
            matches.append(key)
    if matches:
        return sorted(set(matches))
    tokens = {token for token in re.findall(r"[a-z0-9][a-z0-9_-]+", needle) if len(token) > 2}
    if not tokens:
        return []
    scored: list[tuple[int, str]] = []
    for key, entity in graph.entities.items():
        haystack = " ".join([key, entity.stable_id, entity.label, *entity.source_paths]).casefold()
        overlap = sum(1 for token in tokens if token in haystack)
        if overlap:
            scored.append((overlap, key))
    if not scored:
        return []
    best = max(score for score, _ in scored)
    return sorted(key for score, key in scored if score == best)


def _entity_text(entity: Entity) -> str:
    values = [entity.key, entity.stable_id, entity.label, *entity.source_paths]
    for key in ("title", "name", "summary", "status", "workstream", "domain", "builder", "builder_number", "type", "source_repository"):
        value = entity.metadata.get(key)
        if value not in (None, "", []):
            values.append(str(value))
    return " ".join(values).casefold()


def _is_safety(entity: Entity) -> bool:
    if entity.namespace != "INVARIANT":
        return False
    text = _entity_text(entity)
    return any(token in text for token in ("no-bet", "sealed", "no-live", "no_production", "research", "closing"))


def _is_blocker_entity(entity: Entity) -> bool:
    return entity.namespace == "BLOCKER" or str(entity.source_type or "").casefold() == "blocker" or str(entity.metadata.get("type", "")).casefold() == "blocker"


def _is_active_blocker(entity: Entity) -> bool:
    if not _is_blocker_entity(entity):
        return False
    status = str(entity.metadata.get("status", "")).upper()
    return status not in {"RESOLVED", "CLOSED", "REPORTED_CHANGED", "PRESERVED_UNVERIFIED"}


def _is_governing_decision(entity: Entity) -> bool:
    return entity.namespace == "DECISION" and str(entity.metadata.get("status", "")).casefold() in {"active", "current", "approved", "approved_target"}


def _is_superseded(graph: SemanticGraph, key: str) -> bool:
    return any(edge.target == key and edge.relation == "supersedes" for edge in graph.edges.values())


def _profile_partners(consumer: str) -> tuple[int, ...]:
    return {
        "BUILDER_1": (2, 4), "BUILDER_2": (4,), "BUILDER_3": (),
        "BUILDER_4": (1, 2), "CEO": (1, 2, 3, 4), "GENERIC_REVIEW": (),
    }.get(consumer, ())


def _entity_for_builder(graph: SemanticGraph, number: int) -> str:
    return f"BUILDER:BUILDER-{number}"


def _read_source(root: Path, vault: Path | None, path_text: str) -> tuple[dict[str, Any], str]:
    path = (vault / path_text) if path_text.startswith("_live/") and vault else (root / path_text)
    if not path.is_file():
        return {}, ""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError:
        return {}, ""
    _assert_secret_free(raw, path_text)
    if path.suffix == ".json":
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return {}, ""
        return value if isinstance(value, dict) else {}, ""
    try:
        frontmatter, body = parse_frontmatter(raw)
    except ValueError:
        frontmatter, body = {}, raw
    lines = [line.strip() for line in body.splitlines() if line.strip()]
    return frontmatter, " ".join(lines[:12])[:1200]


def _safe_metadata(entity: Entity | None, source: Mapping[str, Any]) -> dict[str, Any]:
    values = dict(entity.metadata) if entity else {}
    values.update({key: source.get(key) for key in SAFE_METADATA_FIELDS if key in source})
    result: dict[str, Any] = {}
    for key in SAFE_METADATA_FIELDS:
        value = values.get(key)
        if value not in (None, "", [], {}):
            if isinstance(value, (str, int, float, bool)):
                result[key] = value
    _assert_secret_free(result)
    return result


def _current_builder_status(entity: Entity | None, handoff: Mapping[str, Any] | None, reference: datetime) -> dict[str, Any] | None:
    if not handoff and not entity:
        return None
    current = dict(handoff or (entity.metadata.get("current_evidence", {}) if entity else {}))
    if not current:
        return None
    current["freshness"] = _freshness(current.get("observed_at"), reference)
    allowed = {
        "candidate_id", "role", "branch", "head_sha", "source_pr", "status", "blocker_count",
        "tests", "tests_passed", "ci", "observed_at", "freshness", "canonical",
        "promotion_required", "candidate_type",
    }
    return {key: current[key] for key in sorted(current) if key in allowed}


def _entity_item(
    root: Path,
    vault: Path | None,
    graph: SemanticGraph,
    candidate: _Candidate,
    latest_handoffs: Mapping[int, dict[str, Any]],
    reference: datetime,
) -> dict[str, Any]:
    entity = graph.entities.get(candidate.key)
    synthetic = candidate.synthetic
    if entity is None and synthetic is None:
        raise ContextCompilerError(f"selected entity is unavailable: {candidate.key}")
    source_excerpt = ""
    if synthetic is not None:
        namespace = "EVIDENCE" if candidate.key.startswith("EVIDENCE:") else "BLOCKER" if candidate.key.startswith("BLOCKER:") else "RUNTIME"
        stable_id = candidate.key.split(":", 1)[1] if ":" in candidate.key else candidate.key
        label = _normal_text(synthetic.get("summary") or synthetic.get("role") or stable_id)
        paths = [str(synthetic.get("source_path"))] if synthetic.get("source_path") else []
        source = synthetic
        source_sha = synthetic.get("source_sha")
        observed_at = _entity_timestamp(None, synthetic)
        authority = _authority(None, synthetic)
        canonical = False
        source_type = synthetic.get("candidate_type")
        current_status = None
    else:
        namespace = "BLOCKER" if _is_blocker_entity(entity) else entity.namespace
        stable_id = entity.stable_id
        label = entity.label
        paths = sorted(entity.source_paths)
        source: Mapping[str, Any] = {}
        for source_path in paths:
            loaded, excerpt = _read_source(root, vault, source_path)
            if loaded:
                source = loaded
                source_excerpt = excerpt
                break
        source_sha = entity.metadata.get("source_sha") or entity.metadata.get("source_latest_meaningful_sha")
        observed_at = _entity_timestamp(entity)
        authority = _authority(entity)
        canonical = entity.canonical
        source_type = entity.source_type
        current_status = None
        if namespace == "BUILDER":
            try:
                number = int(stable_id.split("-", 1)[1])
            except (ValueError, IndexError):
                number = None
            current_status = _current_builder_status(entity, latest_handoffs.get(number) if number else None, reference)
    safe = _safe_metadata(entity, source)
    excerpt = ""
    if source_excerpt:
        excerpt = source_excerpt
    elif source:
        compact = {key: source[key] for key in SAFE_METADATA_FIELDS if key in source and source[key] not in (None, "", [], {})}
        excerpt = json.dumps(_stable(compact), ensure_ascii=False, sort_keys=True)[:1200]
    item: dict[str, Any] = {
        "entity_id": candidate.key,
        "namespace": namespace,
        "stable_id": stable_id,
        "label": label or stable_id,
        "canonical": bool(canonical),
        "authority_class": authority,
        "source_type": source_type,
        "status": safe.get("status") if entity else synthetic.get("status"),
        "summary": safe.get("summary") if entity else _normal_text(synthetic.get("summary")),
        "source_excerpt": excerpt,
        "selection_reason": sorted(candidate.reasons, key=lambda reason: (-REASON_PRIORITY.get(reason, 0), reason))[0],
        "selection_reasons": sorted(candidate.reasons),
        "freshness": _freshness(observed_at, reference) if observed_at else ("CANONICAL" if authority in {"CANONICAL", "VERIFIED"} else "STALE"),
        "runtime_status": current_status,
        "provenance": {
            "entity_id": candidate.key,
            "source_paths": paths,
            "authority_class": authority,
            "source_sha": source_sha,
            "record_identity": stable_id,
            "observed_at": observed_at,
            "graph_relations": sorted(candidate.relation_paths, key=lambda value: json.dumps(value, sort_keys=True)),
        },
    }
    if synthetic is not None:
        item["candidate_type"] = synthetic.get("candidate_type")
        item["promotion_required"] = synthetic.get("promotion_required")
        item["canonical"] = False
    if namespace == "BLOCKER":
        item["blocker"] = {
            key: (synthetic or source).get(key)
            for key in ("blocker_id", "status", "classification", "summary", "auto_resolve", "owner", "dependency", "last_observed_at", "provenance")
            if (synthetic or source).get(key) not in (None, "", [], {})
        }
    if namespace == "BUILDER" and current_status is None:
        item["runtime_status"] = {"state": "UNKNOWN", "message": "NO CURRENT HANDOFF EVIDENCE"}
        item["freshness"] = "UNKNOWN"
    _assert_secret_free(item)
    return item


def _edge_items(graph: SemanticGraph, selected: set[str]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for edge in sorted(graph.edges.values(), key=lambda item: (item.source, item.relation, item.target, item.source_path)):
        if edge.source not in selected or edge.target not in selected:
            continue
        item = edge.as_dict()
        item["relation_priority"] = RELATION_PRIORITY.get(edge.relation, 40)
        result.append(item)
    return result


def _source_conflicts(snapshot: Mapping[str, Any]) -> list[dict[str, Any]]:
    observer = snapshot.get("SOURCE_OBSERVER.json", {})
    if not isinstance(observer, dict):
        return []
    return [dict(item) for item in observer.get("conflicts", []) if isinstance(item, dict)]


def _freshness_state(items: Iterable[dict[str, Any]], include_runtime: bool, conflicts: list[dict[str, Any]]) -> str:
    if not include_runtime:
        return "CANONICAL_ONLY"
    if conflicts:
        return "CONFLICTING"
    states = {str(item.get("freshness")) for item in items if item.get("authority_class") in {"CANDIDATE", "RUNTIME_DERIVED"}}
    if not states:
        return "UNKNOWN"
    if "STALE" in states:
        return "STALE"
    if "AGING" in states:
        return "AGING"
    if "FRESH" in states:
        return "FRESH"
    return "UNKNOWN"


def _estimate_tokens(markdown: str) -> int:
    return max(1, math.ceil(len(markdown.encode("utf-8")) / 4))


def _section(lines: list[str], title: str, values: Iterable[str]) -> None:
    content = [value for value in values if _normal_text(value)]
    if not content:
        return
    lines.extend([f"## {title}", ""])
    lines.extend(content)
    lines.append("")


def _render_markdown(request: ContextRequest, pack: Mapping[str, Any], items: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    lines = [
        "<!-- GENERATED BY SportsBrain Memory Context Compiler V3: NONCANONICAL DERIVED CONTEXT -->",
        "# SportsBrain Context Pack V3", "",
        f"- Request: `{request.request_id}`",
        f"- Consumer: **{request.consumer_type}**",
        f"- Context digest: `{pack.get('context_digest', '0' * 64)}`",
        f"- Graph available: **{str(pack.get('graph_available', False)).lower()}**",
        f"- Freshness state: **{pack.get('freshness_state', 'UNKNOWN')}**",
        f"- Estimated tokens: **{pack.get('estimated_tokens', 'pending')} / {request.token_budget}**", "",
    ]
    by_ns: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in items:
        by_ns[item["namespace"]].append(item)
    objective = request.task or request.workstream or "No narrower task supplied; use the selected governance scope."
    _section(lines, "CURRENT OBJECTIVE", [f"- {objective}"])
    current_state: list[str] = []
    for item in items:
        status = item.get("status") or ""
        runtime = item.get("runtime_status")
        if item["namespace"] == "BUILDER":
            if isinstance(runtime, dict) and runtime.get("state") == "UNKNOWN":
                current_state.append(f"- {item['label']}: **UNKNOWN / NO CURRENT HANDOFF EVIDENCE**")
            elif isinstance(runtime, dict):
                current_state.append(f"- {item['label']}: **{runtime.get('status') or status or 'UNKNOWN'}** ({runtime.get('freshness', 'UNKNOWN')})")
        elif status and item["authority_class"] in {"CANONICAL", "VERIFIED"}:
            current_state.append(f"- `{item['entity_id']}` — {status} ({item['authority_class']})")
    _section(lines, "CURRENT VERIFIED STATE", current_state)
    _section(lines, "ACTIVE WORKSTREAM", [f"- `{item['entity_id']}` — {item['label']}" for item in by_ns.get("WORKSTREAM", [])])
    _section(lines, "RELEVANT DECISIONS", [f"- `{item['entity_id']}` — {item['label']} [{item['authority_class']}]" for item in by_ns.get("DECISION", []) if "SUPERSEDED_HISTORY" not in item.get("selection_reasons", [])])
    _section(lines, "HARD INVARIANTS", [f"- `{item['entity_id']}` — {item['label']}" for item in by_ns.get("INVARIANT", [])])
    _section(lines, "OPEN BLOCKERS", [
        f"- `{item['entity_id']}` — {item.get('blocker', {}).get('summary') or item['label']} [{item.get('blocker', {}).get('status') or item.get('status') or 'UNKNOWN'}; {item['authority_class']}]"
        for item in items if item["namespace"] == "BLOCKER"
    ])
    dependencies = [
        f"- `{edge['source']}` — `{edge['relation']}` → `{edge['target']}`"
        for edge in edges if edge.get("relation") in {"depends_on", "blocked_by", "implements", "verification", "verified_by", "builder", "workstream"}
    ]
    _section(lines, "DEPENDENCIES", dependencies)
    _section(lines, "RECENT VERIFIED EVIDENCE", [
        f"- `{item['entity_id']}` — {item['label']} ({item.get('freshness', 'UNKNOWN')})"
        for item in items if item["authority_class"] == "VERIFIED" or item.get("selection_reason") == "RECENT_VERIFICATION"
    ])
    _section(lines, "RELEVANT PR / COMMIT STATE", [
        f"- `{item['entity_id']}` — {item['summary'] or item['label']}"
        for item in items if item["namespace"] in {"PR", "COMMIT"} or item.get("source_type") in {"PR_MERGED", "PR_OPEN"}
    ])
    _section(lines, "OWNERSHIP BOUNDARIES", [
        f"- {item['label']}: role/status comes from current valid handoff only; freshness **{item.get('freshness', 'UNKNOWN')}**."
        for item in by_ns.get("BUILDER", [])
    ])
    _section(lines, "UNRESOLVED CEO DECISIONS", [
        f"- `{item['entity_id']}` — {item['label']} requires explicit CEO interpretation; it is not a technical default."
        for item in by_ns.get("DECISION", []) if "CEO" in (item.get("source_excerpt") or "").upper() and item.get("status") in {"active", "current", "open"}
    ])
    _section(lines, "NEXT SAFE ACTION", ["- Stop on CONFLICTING, STALE, or UNKNOWN runtime evidence; verify included provenance before taking action."])
    provenance_lines = []
    for item in items:
        provenance = item["provenance"]
        provenance_lines.append(
            f"- `{item['entity_id']}` — reason `{item['selection_reason']}`; authority `{provenance['authority_class']}`; source `{', '.join(provenance['source_paths']) or 'runtime/derived'}`; relation `{len(provenance['graph_relations'])} graph relation(s)`."
        )
    _section(lines, "PROVENANCE", provenance_lines)
    if pack.get("warnings"):
        _section(lines, "WARNINGS", [f"- {warning}" for warning in pack["warnings"]])
    return "\n".join(lines).rstrip() + "\n"


def _pack_without_digest(pack: Mapping[str, Any]) -> dict[str, Any]:
    value = json.loads(json.dumps(pack, ensure_ascii=False))
    value.pop("context_digest", None)
    # Cache identity is an operational reuse key, not semantic context.
    value.pop("cache_key", None)
    value.pop("generated_at", None)
    value.pop("markdown", None)
    return _semantic_value(value)


def _priority_class(candidate: _Candidate) -> int:
    """Return the governance priority class, independent of authority."""
    if "SAFETY_INVARIANT" in candidate.reasons:
        return 4
    if "ACTIVE_BLOCKER" in candidate.reasons:
        return 3
    if "GOVERNING_DECISION" in candidate.reasons:
        return 2
    if candidate.explicit or "REQUIRED_CROSS_BUILDER_CONTRACT" in candidate.reasons:
        return 1
    return 0


def _rank_candidate(graph: SemanticGraph, candidate: _Candidate, item: Mapping[str, Any]) -> tuple[Any, ...]:
    priority = _priority_class(candidate)
    authority = AUTHORITY_RANK.get(str(item.get("authority_class")), 0)
    safety = 1 if "SAFETY_INVARIANT" in candidate.reasons else 0
    blocker = 1 if "ACTIVE_BLOCKER" in candidate.reasons else 0
    reason_score = max((REASON_PRIORITY.get(reason, 0) for reason in candidate.reasons), default=0)
    relation_score = max((RELATION_PRIORITY.get(str(edge.get("relation")), 0) for edge in candidate.relation_paths), default=0)
    timestamp = _parse_time(item.get("provenance", {}).get("observed_at"))
    recency = timestamp.timestamp() if timestamp else 0
    superseded = 1 if "SUPERSEDED_HISTORY" in candidate.reasons else 0
    return (-priority, -authority, -safety, -blocker, superseded, -reason_score, -relation_score, -recency, candidate.hops, candidate.key)


def _build_graph(root: Path, vault: Path | None, include_runtime: bool, graph_available: bool, reference_time: str) -> SemanticGraph:
    graph = SemanticGraph(
        root,
        vault=vault if include_runtime and graph_available else None,
        include_runtime=include_runtime and graph_available,
        reference_time=reference_time,
    )
    try:
        return graph.build()
    except Exception as exc:
        if include_runtime and graph_available:
            fallback = SemanticGraph(root, reference_time=reference_time)
            fallback.build()
            # Keep the fallback usable while making the degraded source visible.
            fallback.issues.append(GraphIssue("ERROR", "RUNTIME_GRAPH_BUILD_FAILED", str(exc), None))
            return fallback
        raise


def compile_context(root: Path, request: ContextRequest | Mapping[str, Any], *, vault: Path | None = None) -> ContextCompilation:
    """Compile a deterministic context pack in memory; this function does not write files."""
    root = Path(root).resolve()
    request = request if isinstance(request, ContextRequest) else ContextRequest.from_mapping(request)
    vault = Path(vault).resolve() if vault else None
    snapshot = _runtime_snapshot(vault) if request.include_runtime else {}
    runtime_available = _runtime_graph_available(root, vault) if request.include_runtime else False
    warnings: list[str] = []
    if request.include_runtime and not runtime_available:
        warnings.append("graph_available=false: runtime context withheld because the runtime Semantic Graph projection is unavailable or failed validation; canonical-only context used")
    runtime_records, latest_handoffs, blockers = _runtime_candidate_records(snapshot) if runtime_available else ({}, {}, [])
    graph = _build_graph(root, vault, request.include_runtime, runtime_available, request.generated_at)
    if graph.issues:
        warnings.extend(f"{issue.code}: {issue.message}" for issue in graph.issues if issue is not None)
    if request.include_runtime and runtime_available and any(issue and issue.code == "RUNTIME_GRAPH_BUILD_FAILED" for issue in graph.issues):
        runtime_available = False
        runtime_records, latest_handoffs, blockers = {}, {}, []
        warnings.append("graph_available=false: runtime context withheld because the runtime Semantic Graph build failed; canonical-only context used")
    conflicts = _source_conflicts(snapshot)
    if conflicts:
        warnings.append("CONFLICTING EVIDENCE: runtime source conflicts require CEO review")
    reference = _parse_time(request.generated_at) or datetime.now(timezone.utc)
    for number, handoff in latest_handoffs.items():
        state = _freshness(handoff.get("observed_at"), reference)
        if state == "STALE":
            warnings.append(f"Builder {number} runtime handoff is STALE and is not unquestionably current")
        elif state == "AGING":
            warnings.append(f"Builder {number} runtime handoff is AGING")
    candidates = _select_candidates(graph, request, runtime_records, latest_handoffs, blockers)
    if not candidates:
        warnings.append("no matching graph/runtime evidence; context selection is empty")
    raw_items: dict[str, dict[str, Any]] = {}
    for key, candidate in candidates.items():
        raw_items[key] = _entity_item(root, vault, graph, candidate, latest_handoffs, reference)
    ranked = sorted(candidates.values(), key=lambda candidate: _rank_candidate(graph, candidate, raw_items[candidate.key]))
    eligible: list[_Candidate] = []
    for candidate in ranked:
        item = raw_items[candidate.key]
        if request.freshness_requirement == "FRESH_ONLY" and item["authority_class"] in {"CANDIDATE", "RUNTIME_DERIVED"} and item.get("freshness") != "FRESH":
            continue
        if request.freshness_requirement == "FRESH_OR_AGING" and item["authority_class"] in {"CANDIDATE", "RUNTIME_DERIVED"} and item.get("freshness") == "STALE":
            continue
        eligible.append(candidate)
    mandatory = [candidate for candidate in ranked if _priority_class(candidate) >= 2]
    eligible_ids = {candidate.key for candidate in eligible}
    freshness_excluded_mandatory = [candidate.key for candidate in mandatory if candidate.key not in eligible_ids]
    if freshness_excluded_mandatory:
        raise ContextCompilerError(
            "mandatory safety/blocker/decision evidence was excluded by freshness policy: "
            + ", ".join(sorted(freshness_excluded_mandatory))
        )

    base: dict[str, Any] = {
        "schema_version": CONTEXT_SCHEMA,
        "compiler_version": COMPILER_VERSION,
        "request": request.to_dict(),
        "request_id": request.request_id,
        "consumer": request.consumer_type,
        "source_memory_sha": _git_head(root),
        "semantic_graph_digest": _graph_semantic_digest(graph),
        "runtime_digest": _runtime_digest(snapshot) if request.include_runtime and runtime_available else None,
        "selection_policy_version": SELECTION_POLICY_VERSION,
        "profile": PROFILES.get(request.consumer_type, PROFILES["GENERIC_REVIEW"]),
        "seed_entities": list(request.entity_seeds),
        "graph_available": bool(not request.include_runtime or runtime_available),
        "warnings": sorted(set(warnings)),
        "conflicts": conflicts,
        "unresolved_references": [],
    }
    base["cache_key"] = _digest({
        "source_memory_sha": base["source_memory_sha"],
        "semantic_graph_digest": base["semantic_graph_digest"],
        "runtime_digest": base["runtime_digest"],
        "freshness_reference": (_parse_time(request.generated_at) or reference).isoformat(),
        "request": request.semantic_dict(),
        "compiler_version": COMPILER_VERSION,
    })

    def draft_for(proposed: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        proposed_edges = _edge_items(graph, {entry["entity_id"] for entry in proposed})
        draft = dict(base)
        draft.update({
            "included_entities": proposed,
            "included_edges": proposed_edges,
            "canonical_count": sum(1 for entry in proposed if entry["authority_class"] in {"CANONICAL", "VERIFIED"}),
            "runtime_count": sum(1 for entry in proposed if entry["authority_class"] in {"CANDIDATE", "RUNTIME_DERIVED"}),
            "truncated": False,
            "candidate_entity_count": len(candidates),
            "included_entity_count": len(proposed),
            "omitted_entity_count": max(0, len(candidates) - len(proposed)),
            "token_budget": request.token_budget,
            "freshness_state": _freshness_state(proposed, request.include_runtime, conflicts),
            "metrics": {},
        })
        draft["estimated_tokens"] = _estimate_tokens(_render_markdown(request, draft, proposed, proposed_edges))
        return draft, proposed_edges

    def fits(proposed: list[dict[str, Any]]) -> bool:
        draft, _ = draft_for(proposed)
        return len(proposed) <= request.max_entity_count and draft["estimated_tokens"] <= request.token_budget

    selected: list[_Candidate] = []
    selected_items: list[dict[str, Any]] = []
    mandatory_ids = {candidate.key for candidate in mandatory}
    for candidate in mandatory:
        item = raw_items[candidate.key]
        proposed = selected_items + [item]
        if not fits(proposed):
            raise ContextCompilerError(
                "mandatory safety/blocker/decision evidence cannot fit the requested "
                f"token/entity budget: {candidate.key}"
            )
        selected.append(candidate)
        selected_items.append(item)

    for candidate in eligible:
        if candidate.key in mandatory_ids:
            continue
        item = raw_items[candidate.key]
        proposed = selected_items + [item]
        if not fits(proposed):
            continue
        selected.append(candidate)
        selected_items.append(item)

    truncated = len(selected_items) < len(candidates)
    selected_ids = {item["entity_id"] for item in selected_items}
    edges = _edge_items(graph, selected_ids)
    unresolved = [item for item in graph.unresolved if item.get("source_entity") in selected_ids]
    metrics = {
        "candidate_entities": len(candidates),
        "selected_entities": len(selected_items),
        "selected_edges": len(edges),
        "canonical_runtime_ratio": {
            "canonical": sum(1 for item in selected_items if item["authority_class"] in {"CANONICAL", "VERIFIED"}),
            "runtime": sum(1 for item in selected_items if item["authority_class"] in {"CANDIDATE", "RUNTIME_DERIVED"}),
        },
        "direct_relation_count": sum(1 for item in selected if item.hops <= 1),
        "second_hop_count": sum(1 for item in selected if item.hops > 1),
        "active_blockers_included": sum(1 for item in selected_items if item["namespace"] == "BLOCKER"),
        "governing_decisions_included": sum(1 for item in selected_items if item["namespace"] == "DECISION" and "SUPERSEDED_HISTORY" not in item.get("selection_reasons", [])),
        "unresolved_refs": len(unresolved),
        "conflicts": len(conflicts),
        "budget_utilization": 0.0,
        "truncated_entities": max(0, len(candidates) - len(selected_items)),
    }
    pack = dict(base)
    pack.update({
        "included_entities": selected_items,
        "included_edges": edges,
        "canonical_count": sum(1 for item in selected_items if item["authority_class"] in {"CANONICAL", "VERIFIED"}),
        "runtime_count": sum(1 for item in selected_items if item["authority_class"] in {"CANDIDATE", "RUNTIME_DERIVED"}),
        "truncated": truncated,
        "candidate_entity_count": len(candidates),
        "included_entity_count": len(selected_items),
        "omitted_entity_count": max(0, len(candidates) - len(selected_items)),
        "token_budget": request.token_budget,
        "freshness_state": _freshness_state(selected_items, request.include_runtime, conflicts),
        "unresolved_references": unresolved,
        "metrics": metrics,
        "generated_at": request.generated_at,
    })
    markdown = _render_markdown(request, pack, selected_items, edges)
    estimated = _estimate_tokens(markdown)
    if estimated > request.token_budget:
        for item in selected_items:
            item["source_excerpt"] = item.get("source_excerpt", "")[:240]
        markdown = _render_markdown(request, pack, selected_items, edges)
        estimated = _estimate_tokens(markdown)
    if estimated > request.token_budget:
        raise ContextCompilerError(f"context cannot fit requested token budget: estimated {estimated} > {request.token_budget}")
    pack["estimated_tokens"] = estimated
    metrics["budget_utilization"] = round(estimated / request.token_budget, 4)
    pack["context_digest"] = _digest(_pack_without_digest(pack))
    markdown = _render_markdown(request, pack, selected_items, edges)
    _assert_secret_free(pack)
    _assert_secret_free(markdown)
    return ContextCompilation(pack=pack, markdown=markdown)


def build_context_pack(root: Path, request: ContextRequest | Mapping[str, Any], *, vault: Path | None = None) -> dict[str, Any]:
    return compile_context(root, request, vault=vault).pack


def _pack_json_path(path: Path) -> Path:
    return path if path.suffix == ".json" else path.with_suffix(".json")


def validate_context_pack(path: Path, *, expected_budget: int | None = None) -> dict[str, Any]:
    """Validate a JSON context pack and return its normalized payload."""
    path = _pack_json_path(Path(path))
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextValidationError(f"context pack is not valid JSON: {path}") from exc
    if not isinstance(payload, dict):
        raise ContextValidationError("context pack must be an object")
    required = {
        "schema_version", "compiler_version", "request", "request_id", "consumer", "source_memory_sha", "semantic_graph_digest", "runtime_digest",
        "selection_policy_version", "profile", "seed_entities", "included_entities", "included_edges",
        "candidate_entity_count", "included_entity_count", "omitted_entity_count",
        "canonical_count", "runtime_count", "truncated", "token_budget", "estimated_tokens",
        "freshness_state", "warnings", "conflicts", "unresolved_references", "metrics", "generated_at", "graph_available", "cache_key", "context_digest",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ContextValidationError("context pack missing field(s): " + ", ".join(missing))
    if payload.get("schema_version") != CONTEXT_SCHEMA:
        raise ContextValidationError("unsupported context schema_version")
    if payload.get("consumer") not in CONSUMER_TYPES:
        raise ContextValidationError("invalid context consumer")
    request = payload.get("request")
    if not isinstance(request, dict):
        raise ContextValidationError("request must be an object")
    try:
        normalized_request = ContextRequest.from_mapping(request)
    except ContextCompilerError as exc:
        raise ContextValidationError(f"invalid context request: {exc}") from exc
    if normalized_request.request_id != payload.get("request_id") or normalized_request.consumer_type != payload.get("consumer"):
        raise ContextValidationError("request identity does not match context pack")
    expected_profile = json.loads(json.dumps(PROFILES.get(payload.get("consumer")), ensure_ascii=False))
    if payload.get("profile") != expected_profile:
        raise ContextValidationError("context profile does not match consumer")
    budget = expected_budget if expected_budget is not None else payload.get("token_budget")
    if not isinstance(budget, int) or payload.get("estimated_tokens", 0) > budget:
        raise ContextValidationError("context pack exceeds token budget")
    entities = payload.get("included_entities")
    edges = payload.get("included_edges")
    if not isinstance(entities, list) or not isinstance(edges, list):
        raise ContextValidationError("included_entities and included_edges must be lists")
    candidate_count = payload.get("candidate_entity_count")
    if not isinstance(candidate_count, int) or candidate_count < len(entities):
        raise ContextValidationError("candidate_entity_count must cover included entities")
    if payload.get("truncated") != (candidate_count > len(entities)):
        raise ContextValidationError("truncated flag does not match candidate/included counts")
    ids: set[str] = set()
    canonical_count = runtime_count = 0
    for index, entity in enumerate(entities):
        if not isinstance(entity, dict):
            raise ContextValidationError(f"included_entities[{index}] must be an object")
        for field_name in ("entity_id", "authority_class", "selection_reason", "provenance"):
            if field_name not in entity:
                raise ContextValidationError(f"included_entities[{index}] missing {field_name}")
        if entity["entity_id"] in ids:
            raise ContextValidationError(f"duplicate included entity: {entity['entity_id']}")
        ids.add(entity["entity_id"])
        if entity.get("namespace") == "BUILDER" and entity.get("stable_id") not in {f"BUILDER-{number}" for number in BUILDER_NUMBERS}:
            raise ContextValidationError("invalid Builder identity in context pack")
        if entity["authority_class"] in {"CANONICAL", "VERIFIED"}:
            canonical_count += 1
        elif entity["authority_class"] in {"CANDIDATE", "RUNTIME_DERIVED"}:
            runtime_count += 1
        else:
            raise ContextValidationError(f"invalid authority class: {entity['authority_class']}")
        provenance = entity["provenance"]
        if not isinstance(provenance, dict) or provenance.get("entity_id") != entity["entity_id"] or "source_paths" not in provenance:
            raise ContextValidationError(f"invalid provenance for {entity['entity_id']}")
        if entity.get("candidate_type") in {"CANDIDATE_OPERATIONAL_EVIDENCE", "SOURCE_CANDIDATE_EVENT"}:
            if entity.get("canonical") is not False or entity.get("promotion_required") is not True:
                raise ContextValidationError(f"candidate promotion boundary violated for {entity['entity_id']}")
    if payload.get("canonical_count") != canonical_count or payload.get("runtime_count") != runtime_count:
        raise ContextValidationError("canonical/runtime counts do not match included entities")
    for index, edge in enumerate(edges):
        if not isinstance(edge, dict) or edge.get("source") not in ids or edge.get("target") not in ids:
            raise ContextValidationError(f"included_edges[{index}] has a dangling endpoint")
    if payload.get("included_entity_count") != len(entities):
        raise ContextValidationError("included_entity_count does not match")
    if payload.get("omitted_entity_count") != max(0, int(payload.get("candidate_entity_count", len(entities))) - len(entities)):
        raise ContextValidationError("omitted_entity_count does not match")
    _assert_secret_free(payload)
    expected_digest = _digest(_pack_without_digest(payload))
    if payload.get("context_digest") != expected_digest:
        raise ContextValidationError("context_digest does not match semantic pack content")
    return payload


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, ensure_ascii=False)
        handle.write("\n")


def _ensure_external_context_output(root: Path, vault: Path) -> None:
    """Reject any resolved Vault/output path inside the active Memory checkout."""
    root = root.resolve()
    vault = vault.resolve()
    output_dir = (vault / CONTEXT_DIR).resolve()
    for label, path in (("Vault", vault), ("context output", output_dir)):
        try:
            path.relative_to(root)
        except ValueError:
            continue
        raise ContextCompilerError(
            f"{label} must be outside the canonical Memory checkout: {path}"
        )


def build_context_atomic(root: Path, request: ContextRequest | Mapping[str, Any], *, vault: Path) -> dict[str, Any]:
    """Build and atomically promote one noncanonical pack into Vault _live/context."""
    root = Path(root).resolve()
    vault = Path(vault).resolve()
    _ensure_external_context_output(root, vault)
    compilation = compile_context(root, request, vault=vault)
    request_obj = request if isinstance(request, ContextRequest) else ContextRequest.from_mapping(request)
    output_dir = vault / CONTEXT_DIR
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{request_obj.request_id}.json"
    md_path = output_dir / f"{request_obj.request_id}.md"
    temp_dir = Path(tempfile.mkdtemp(prefix=".context-build-", dir=str(output_dir.parent)))
    previous: dict[Path, bytes | None] = {path: path.read_bytes() if path.exists() else None for path in (json_path, md_path)}
    try:
        temp_json = temp_dir / json_path.name
        temp_md = temp_dir / md_path.name
        _write_json(temp_json, compilation.pack)
        temp_md.write_text(compilation.markdown, encoding="utf-8")
        validate_context_pack(temp_json, expected_budget=compilation.pack["token_budget"])
        output_dir.mkdir(parents=True, exist_ok=True)
        os.replace(temp_json, json_path)
        os.replace(temp_md, md_path)
        return {"status": "ONLINE", "json": str(json_path), "markdown": str(md_path), "context_digest": compilation.pack["context_digest"], "pack": compilation.pack}
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


def inspect_context_pack(path: Path) -> dict[str, Any]:
    payload = validate_context_pack(path)
    return {
        "schema_version": payload["schema_version"],
        "request_id": payload["request_id"],
        "consumer": payload["consumer"],
        "context_digest": payload["context_digest"],
        "graph_available": payload.get("graph_available", False),
        "freshness_state": payload["freshness_state"],
        "included_entities": [
            {"entity_id": item["entity_id"], "authority_class": item["authority_class"], "selection_reason": item["selection_reason"], "freshness": item.get("freshness")}
            for item in payload["included_entities"]
        ],
        "metrics": payload.get("metrics", {}),
        "warnings": payload.get("warnings", []),
    }


compile_context_pack = compile_context
build_context_pack_atomic = build_context_atomic


def _select_candidates(
    graph: SemanticGraph,
    request: ContextRequest,
    runtime_records: Mapping[str, Any],
    latest_handoffs: Mapping[int, dict[str, Any]],
    blockers: Iterable[dict[str, Any]],
) -> dict[str, _Candidate]:
    candidates: dict[str, _Candidate] = {}

    def add(
        key: str,
        reason: str,
        score: int,
        hops: int = 0,
        explicit: bool = False,
        relation_path: dict[str, Any] | None = None,
        synthetic: dict[str, Any] | None = None,
    ) -> None:
        if key not in graph.entities and key not in runtime_records and synthetic is None:
            return
        item = candidates.setdefault(key, _Candidate(key=key, synthetic=synthetic))
        if synthetic is not None and item.synthetic is None:
            item.synthetic = synthetic
        item.reasons.add(reason)
        item.score = max(item.score, score)
        item.hops = min(item.hops, hops) if item.relation_paths else hops
        item.explicit = item.explicit or explicit
        if relation_path and relation_path not in item.relation_paths:
            item.relation_paths.append(relation_path)

    seed_keys: set[str] = set()
    for seed in request.entity_seeds:
        matched = _seed_match(graph, seed)
        if not matched:
            candidate_key = seed if seed in runtime_records else f"EVIDENCE:{seed}"
            if candidate_key in runtime_records:
                add(candidate_key, "EXPLICIT_SEED", 1080, explicit=True, synthetic=runtime_records[candidate_key])
                seed_keys.add(candidate_key)
                continue
        for key in matched:
            add(key, "EXPLICIT_SEED", 1080, explicit=True)
            seed_keys.add(key)

    for query in (request.task, request.workstream):
        for key in _seed_match(graph, query):
            add(key, "EXPLICIT_SEED", 1060, explicit=True)
            seed_keys.add(key)

    if request.builder_number:
        key = _entity_for_builder(graph, request.builder_number)
        add(key, "OWNER_CONTEXT", 1040)
        seed_keys.add(key)

    for domain in request.requested_domains:
        for key in _seed_match(graph, domain):
            add(key, "EXPLICIT_SEED", 1000, explicit=True)
            seed_keys.add(key)

    if request.consumer_type == "CEO":
        for number in BUILDER_NUMBERS:
            add(_entity_for_builder(graph, number), "OWNER_CONTEXT", 960)
        for key, entity in graph.entities.items():
            if _is_active_blocker(entity):
                add(key, "ACTIVE_BLOCKER", 1150)
            elif _is_governing_decision(entity):
                add(key, "GOVERNING_DECISION", 1100)
            elif _is_safety(entity):
                add(key, "SAFETY_INVARIANT", 1200)
            elif entity.namespace == "WORKSTREAM" and str(entity.metadata.get("status", "")).casefold() in {"active", "current", "planned_ready"}:
                add(key, "OWNER_CONTEXT", 720)

    operational_request = request.consumer_type.startswith("BUILDER_") or any(
        token in f"{request.task} {request.workstream}".casefold()
        for token in ("top-5", "top5", "shadow", "provider", "activation")
    )
    if operational_request:
        for key, entity in graph.entities.items():
            if _is_safety(entity):
                add(key, "SAFETY_INVARIANT", 1200)

    for number in _profile_partners(request.consumer_type):
        add(_entity_for_builder(graph, number), "REQUIRED_CROSS_BUILDER_CONTRACT", 1060)
        for key, entity in graph.entities.items():
            if key == _entity_for_builder(graph, number):
                continue
            metadata_builder = str(entity.metadata.get("builder", "")).casefold()
            builder_number = entity.metadata.get("builder_number")
            owned = metadata_builder == f"builder {number}" or builder_number == number or any(
                edge.source == key and edge.target == _entity_for_builder(graph, number) and edge.relation == "builder"
                for edge in graph.edges.values()
            )
            text = _entity_text(entity)
            if owned and any(token in text for token in ("contract", "interface", "seam", "validation", "quality", "observation", "provider", "reliability")):
                add(key, "REQUIRED_CROSS_BUILDER_CONTRACT", 850)

    for key, entity in graph.entities.items():
        if _is_active_blocker(entity):
            add(key, "ACTIVE_BLOCKER", 1150)

    selected_numbers = set(BUILDER_NUMBERS if request.consumer_type == "CEO" else ([request.builder_number] if request.builder_number else []))
    for number in selected_numbers:
        handoff = latest_handoffs.get(number)
        if handoff:
            key = f"EVIDENCE:{handoff['candidate_id']}"
            add(key, "RECENT_EVIDENCE", 900, synthetic=runtime_records.get(key, handoff))
            add(_entity_for_builder(graph, number), "OWNER_CONTEXT", 1040)
    for blocker in blockers:
        status = str(blocker.get("status", "")).upper()
        if status in {"RESOLVED", "CLOSED", "REPORTED_CHANGED", "PRESERVED_UNVERIFIED"}:
            continue
        key = f"BLOCKER:{blocker.get('blocker_id')}"
        if key in runtime_records:
            add(key, "ACTIVE_BLOCKER", 1150, synthetic=runtime_records[key])

    adjacency: dict[str, list[GraphEdge]] = defaultdict(list)
    for edge in graph.edges.values():
        adjacency[edge.source].append(edge)
        adjacency[edge.target].append(edge)
    for edges in adjacency.values():
        edges.sort(key=lambda edge: (edge.source, edge.relation, edge.target, edge.source_path))
    scopes = tuple(scope.casefold() for scope in request.repository_scope)

    def in_scope(key: str) -> bool:
        if not scopes or key not in graph.entities:
            return True
        entity = graph.entities[key]
        if entity.namespace in {"BUILDER", "INVARIANT", "DECISION"}:
            return True
        text = _entity_text(entity)
        return any(scope in text for scope in scopes)

    frontier = sorted(seed_keys)
    seen_depth = {key: 0 for key in frontier}
    for depth in range(0, 2):
        next_frontier: list[str] = []
        for source in frontier:
            for edge in adjacency.get(source, []):
                target = edge.target if edge.source == source else edge.source
                if not in_scope(target):
                    continue
                relation_score = RELATION_PRIORITY.get(edge.relation, 40)
                if depth == 0 or relation_score >= 80:
                    reason = "DIRECT_DEPENDENCY" if depth == 0 else "SECOND_HOP_RELATION"
                    add(
                        target, reason, relation_score + (920 if depth == 0 else 680), depth + 1,
                        relation_path={
                            "source": edge.source, "relation": edge.relation, "target": edge.target,
                            "source_path": edge.source_path, "field": edge.field,
                        },
                    )
                if target not in seen_depth:
                    seen_depth[target] = depth + 1
                    next_frontier.append(target)
        frontier = sorted(set(next_frontier))

    for key, item in candidates.items():
        if key in graph.entities and _is_superseded(graph, key) and not item.explicit:
            item.reasons.add("SUPERSEDED_HISTORY")
            item.score = min(item.score, REASON_PRIORITY["SUPERSEDED_HISTORY"])
    return candidates
