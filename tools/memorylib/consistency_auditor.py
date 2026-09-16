"""Read-only Memory Consistency / Governance Auditor V5.

The auditor compares current Memory contracts and explicitly supplied runtime
artifacts.  It is intentionally not a writer, promoter, scheduler, dispatcher,
or authorization boundary.  All projection reads are performed in memory;
reports are written only when the caller explicitly supplies an external path.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import subprocess
from typing import Any, Iterable, Mapping

from . import builder_bootstrap, context_compiler, governance, observer, semantic_graph
from .builder_bootstrap import validate_builder_bootstrap
from .context_compiler import validate_context_pack
from .frontmatter import parse_frontmatter
from .observer import _age_state, _latest_builder_evidence, validate_blocker, validate_candidate, validate_handoff_evidence


AUDIT_SCHEMA = 5
AUDIT_VERSION = "memory-consistency-auditor-v5.0"
GOVERNED_BUILDERS = (1, 2, 3, 4, 5)
GOVERNED_ROLES = {
    1: "Research / Shadow / Evidence Lifecycle",
    2: "Independent Qualification / Authority",
    3: "Memory / Context / Observability",
    4: "Provider Cascade / Controlled Shadow Infrastructure",
    5: "Autonomous Development / Night Shift Dispatcher Owner",
}
PROFILE_PARTNERS = {1: (2, 4), 2: (4,), 3: (), 4: (1, 2), 5: (1, 2, 3, 4)}
CONSUMERS = {"CEO", *(f"BUILDER_{n}" for n in GOVERNED_BUILDERS), "GENERIC_REVIEW"}
FRESHNESS_STATES = {"FRESH", "AGING", "STALE"}
STATUS_VALUES = {
    "CONSISTENT", "WARNING", "STALE", "UNKNOWN", "NONAUTHORITATIVE_ONLY",
    "CONFLICT", "GOVERNANCE_DRIFT", "SAFETY_INVARIANT_MISSING", "FAILED_CLOSED",
}
SEVERITY_RANK = {"ERROR": 3, "WARNING": 2, "INFO": 1}

CURRENT_GOVERNANCE_PATHS = (
    "README.md",
    "CURRENT_STATE.md",
    "architecture/CONTEXT_COMPILER_V3.md",
    "architecture/BUILDER_BOOTSTRAP_V4.md",
    "architecture/SOURCE_OBSERVER.md",
    "architecture/SEMANTIC_GRAPH_V2.md",
)
SAFETY_PATHS = (
    "README.md", "CURRENT_STATE.md", "CURRENT_PRIORITIES.md", "CURRENT_BLOCKERS.md",
    "CURRENT_TASK.md", "architecture/CONTEXT_COMPILER_V3.md",
    "architecture/BUILDER_BOOTSTRAP_V4.md", "architecture/SOURCE_OBSERVER.md",
    "architecture/SEMANTIC_GRAPH_V2.md", "architecture/EXECUTION_AND_RELEASE.md",
    "workstreams/TOP5-RESEARCH.md", "workstreams/TOP5-PRODUCTION.md",
    "workstreams/TOP5-SHADOW-READINESS.md", "workstreams/TOP5-SHADOW-INTEGRATION.md",
    "workstreams/TOP5-ACTIVATION-READINESS.md", "domains/LEDGER_AND_MEASUREMENT.md",
    "invariants/SAFETY.md",
)
RUNTIME_FILENAMES = (
    "SOURCE_OBSERVER.json", "SOURCE_CANDIDATES.json", "BUILDER_HANDOFFS.json",
    "BLOCKERS.json", "SEMANTIC_GRAPH_STATUS.json",
)


def _normal(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _stable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _stable(value[key]) for key in sorted(value, key=lambda item: str(item))}
    if isinstance(value, (list, tuple, set)):
        values = [_stable(item) for item in value]
        return sorted(values, key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
    return value


def _digest(value: Any) -> str:
    encoded = json.dumps(_stable(value), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _read_json(path: Path) -> tuple[bool, Any, str | None]:
    if not path.exists() and not path.is_symlink():
        return False, None, None
    try:
        return True, json.loads(path.read_text(encoding="utf-8")), None
    except (OSError, json.JSONDecodeError) as exc:
        return True, None, str(exc)


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(parent.resolve(strict=False))
        return True
    except ValueError:
        return False


def _source_sha(root: Path) -> str:
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
    return "UNCOMMITTED-" + semantic_graph.canonical_input_digest(root)


def _reference_time(value: str | None) -> str:
    if value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
        return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _field(value: Mapping[str, Any], name: str) -> Any:
    aliases = {
        "head_sha": ("head_sha", "head", "source_sha"),
        "source_pr": ("source_pr", "pr", "pull_request"),
        "status": ("status", "reported_status", "source_state", "state"),
        "blockers": ("blockers", "blocker", "blocker_state"),
        "tests": ("tests", "tests_passed", "test_summary"),
        "ci": ("ci", "ci_state"),
    }
    for key in aliases.get(name, (name,)):
        if key in value and value[key] not in (None, "", [], {}):
            return value[key]
    return None


def _compare_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        if "summary" in value or "classification" in value or "status" in value:
            return {
                "summary": _normal(value.get("summary")),
                "classification": _normal(value.get("classification")).upper(),
                "status": _normal(value.get("status")).upper(),
            }
        return _stable(value)
    if isinstance(value, list):
        return sorted((_compare_value(item) for item in value), key=lambda item: json.dumps(item, sort_keys=True, ensure_ascii=True))
    if isinstance(value, str):
        return _normal(value).casefold()
    return value


SECRET_VALUE_RE = re.compile(r"(?i)(?:bearer\s+|gh[pousr]_[A-Za-z0-9._-]{20,}|(?:api[_ -]?key|access[_ -]?token|refresh[_ -]?token|password|private[_ -]?key|client[_ -]?secret)\s*[:=]\s*[^\s,;]+)")


def _builder_number(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    match = re.fullmatch(r"(?:BUILDER(?:[-_: ]*)?)?([0-9]+)", _normal(value), re.IGNORECASE)
    return int(match.group(1)) if match else None


@dataclass(frozen=True)
class Finding:
    severity: str
    domain: str
    status: str
    summary: str
    affected_entities: tuple[str, ...] = ()
    evidence: tuple[Mapping[str, Any], ...] = ()
    authority_classes: tuple[str, ...] = ()
    source_paths: tuple[str, ...] = ()
    recommended_human_action: str = "Review the evidence and make any required governance decision manually."

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "severity": self.severity,
            "domain": self.domain,
            "status": self.status,
            "summary": self.summary,
            "affected_entities": list(self.affected_entities),
            "evidence": [_stable(item) for item in self.evidence],
            "authority_classes": list(self.authority_classes),
            "source_paths": list(self.source_paths),
            "recommended_human_action": self.recommended_human_action,
        }
        payload["finding_id"] = "AUDIT-FINDING-" + _digest(payload)[:24]
        return payload


@dataclass
class ConsistencyAudit:
    source_memory_sha: str
    reference_time: str
    overall_status: str
    findings: list[dict[str, Any]]
    semantic_digest: str
    generated_at: str
    runtime_available: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": AUDIT_SCHEMA,
            "audit_version": AUDIT_VERSION,
            "read_only": True,
            "source_memory_sha": self.source_memory_sha,
            "reference_time": self.reference_time,
            "generated_at": self.generated_at,
            "overall_status": self.overall_status,
            "runtime_available": self.runtime_available,
            "semantic_digest": self.semantic_digest,
            "summary": {
                "finding_count": len(self.findings),
                "error_count": sum(1 for item in self.findings if item["severity"] == "ERROR"),
                "warning_count": sum(1 for item in self.findings if item["severity"] == "WARNING"),
                "statuses": {status: sum(1 for item in self.findings if item["status"] == status) for status in sorted(STATUS_VALUES) if any(item["status"] == status for item in self.findings)},
            },
            "findings": self.findings,
        }

    def markdown(self) -> str:
        lines = [
            "# Memory Consistency Auditor V5",
            "",
            f"- Overall status: **{self.overall_status}**",
            f"- Source Memory SHA: `{self.source_memory_sha}`",
            f"- Reference time: `{self.reference_time}`",
            f"- Runtime available: **{str(self.runtime_available).lower()}**",
            f"- Semantic digest: `{self.semantic_digest}`",
            "- Read-only audit: **true**",
            "",
            "## Findings",
            "",
        ]
        if not self.findings:
            lines.append("- CONSISTENT — no findings.")
        else:
            for finding in self.findings:
                entities = ", ".join(finding["affected_entities"]) or "none"
                lines.append(f"- **{finding['severity']} / {finding['status']}** `{finding['finding_id']}` — {finding['summary']} (entities: {entities})")
                if finding["source_paths"]:
                    lines.append(f"  - sources: {', '.join(finding['source_paths'])}")
                lines.append(f"  - action: {finding['recommended_human_action']}")
        return "\n".join(lines).rstrip() + "\n"


class _AuditBuilder:
    def __init__(self, root: Path, vault: Path | None, reference_time: str) -> None:
        self.root = root.resolve()
        self.vault = vault.resolve() if vault else None
        self.reference_time = reference_time
        self.findings: dict[str, dict[str, Any]] = {}
        self.runtime_available = False
        self.latest_handoffs: dict[int, dict[str, Any]] = {}
        self.runtime_snapshots: dict[int, list[tuple[str, dict[str, Any]]]] = {number: [] for number in GOVERNED_BUILDERS}
        self.graph: semantic_graph.SemanticGraph | None = None
        self.runtime_payloads: dict[str, dict[str, Any]] = {}

    def add(
        self,
        severity: str,
        domain: str,
        status: str,
        summary: str,
        *,
        entities: Iterable[Any] = (),
        evidence: Iterable[Mapping[str, Any]] = (),
        authorities: Iterable[str] = (),
        paths: Iterable[Any] = (),
        action: str = "Review the evidence and make any required governance decision manually.",
    ) -> None:
        if status not in STATUS_VALUES:
            status = "FAILED_CLOSED"
        finding = Finding(
            severity=severity,
            domain=domain,
            status=status,
            summary=_normal(summary),
            affected_entities=tuple(sorted({_normal(item) for item in entities if _normal(item)})),
            evidence=tuple(_stable(item) for item in evidence if isinstance(item, Mapping)),
            authority_classes=tuple(sorted({_normal(item).upper() for item in authorities if _normal(item)})),
            source_paths=tuple(sorted({_normal(item) for item in paths if _normal(item)})),
            recommended_human_action=action,
        )
        payload = finding.to_dict()
        self.findings[payload["finding_id"]] = payload

    def governance(self) -> None:
        if tuple(governance.BUILDER_NUMBERS) != GOVERNED_BUILDERS:
            self.add("ERROR", "governance", "GOVERNANCE_DRIFT", "central governed Builder roster differs from Builder 1–5", entities=["BUILDER_ROSTER"], evidence=[{"actual": list(governance.BUILDER_NUMBERS), "expected": list(GOVERNED_BUILDERS)}], paths=["tools/memorylib/governance.py"])
        if dict(governance.BUILDER_ROLES) != GOVERNED_ROLES:
            self.add("ERROR", "governance", "GOVERNANCE_DRIFT", "central Builder role baseline differs from the governed roster", entities=["BUILDER_ROLES"], evidence=[{"actual": governance.BUILDER_ROLES, "expected": GOVERNED_ROLES}], paths=["tools/memorylib/governance.py"])
        if dict(getattr(governance, "BUILDER_PROFILE_PARTNERS", {})) != PROFILE_PARTNERS or tuple(getattr(governance, "CEO_PROFILE_PARTNERS", ())) != GOVERNED_BUILDERS:
            self.add("ERROR", "governance", "GOVERNANCE_DRIFT", "central Builder profile partner mapping differs from the governed visibility contract", entities=["BUILDER_PROFILE_PARTNERS"], evidence=[{"actual": getattr(governance, "BUILDER_PROFILE_PARTNERS", {}), "expected": PROFILE_PARTNERS}], paths=["tools/memorylib/governance.py"])

        expected_profiles = {"CEO", *(f"BUILDER_{number}" for number in GOVERNED_BUILDERS), "GENERIC_REVIEW"}
        if set(context_compiler.CONSUMER_TYPES) != expected_profiles:
            self.add("ERROR", "context_compiler", "GOVERNANCE_DRIFT", "Context Compiler consumer types do not match the governed Builder roster", entities=["CONSUMER_TYPES"], evidence=[{"actual": sorted(context_compiler.CONSUMER_TYPES), "expected": sorted(expected_profiles)}], paths=["tools/memorylib/context_compiler.py"])
        if set(context_compiler.PROFILES) != expected_profiles:
            self.add("ERROR", "context_compiler", "GOVERNANCE_DRIFT", "Context Compiler profiles do not cover exactly the governed consumers", entities=["PROFILES"], evidence=[{"actual": sorted(context_compiler.PROFILES), "expected": sorted(expected_profiles)}], paths=["tools/memorylib/context_compiler.py"])
        for number in GOVERNED_BUILDERS:
            profile = context_compiler.PROFILES.get(f"BUILDER_{number}", {})
            actual = tuple(profile.get("partners", ())) if isinstance(profile, Mapping) else ()
            if actual != PROFILE_PARTNERS[number]:
                self.add("ERROR", "context_compiler", "GOVERNANCE_DRIFT", f"Builder {number} Context Compiler partner mapping drifted", entities=[f"BUILDER_{number}"], evidence=[{"actual": list(actual), "expected": list(PROFILE_PARTNERS[number])}], paths=["tools/memorylib/context_compiler.py"])
            try:
                function_partners = tuple(context_compiler._profile_partners(f"BUILDER_{number}"))
            except Exception:
                function_partners = ()
            if function_partners != PROFILE_PARTNERS[number]:
                self.add("ERROR", "context_compiler", "GOVERNANCE_DRIFT", f"Builder {number} Context Compiler partner function drifted", entities=[f"BUILDER_{number}"], evidence=[{"actual": list(function_partners), "expected": list(PROFILE_PARTNERS[number])}], paths=["tools/memorylib/context_compiler.py"])
        if tuple(context_compiler.PROFILES.get("CEO", {}).get("partners", ())) != GOVERNED_BUILDERS:
            self.add("ERROR", "context_compiler", "GOVERNANCE_DRIFT", "CEO Context Compiler profile does not cover exactly Builders 1–5", entities=["CEO_PROFILE"], paths=["tools/memorylib/context_compiler.py"])
        try:
            ceo_function_partners = tuple(context_compiler._profile_partners("CEO"))
        except Exception:
            ceo_function_partners = ()
        if ceo_function_partners != GOVERNED_BUILDERS:
            self.add("ERROR", "context_compiler", "GOVERNANCE_DRIFT", "CEO Context Compiler partner function does not cover exactly Builders 1–5", entities=["CEO_PROFILE"], paths=["tools/memorylib/context_compiler.py"])
        b5_focus = set(context_compiler.PROFILES.get("BUILDER_5", {}).get("focus", ()))
        if not {"dispatcher", "orchestration"}.issubset(b5_focus):
            self.add("ERROR", "context_compiler", "GOVERNANCE_DRIFT", "Builder 5 profile is missing dispatcher/orchestration context", entities=["BUILDER_5"], paths=["tools/memorylib/context_compiler.py"])

        regex_checks = ((observer.BUILDER_HEADER_RE, "observer"), (semantic_graph.BUILDER_RE, "semantic_graph"))
        for regex, domain in regex_checks:
            if any(regex.fullmatch(f"BUILDER: {number}") is None for number in GOVERNED_BUILDERS) and domain == "observer":
                self.add("ERROR", domain, "GOVERNANCE_DRIFT", "Source Observer does not accept every governed Builder header", entities=["BUILDER_HANDOFF_HEADER"], paths=["tools/memorylib/observer.py"])
            if any(regex.fullmatch(f"Builder {number}") is None for number in GOVERNED_BUILDERS) and domain == "semantic_graph":
                self.add("ERROR", domain, "GOVERNANCE_DRIFT", "Semantic Graph does not recognize every governed Builder identity", entities=["BUILDER_GRAPH_IDENTITY"], paths=["tools/memorylib/semantic_graph.py"])
            invalid_values = ("BUILDER: 6", "BUILDER: 7", "BUILDER: 8", "BUILDER: 1/4") if domain == "observer" else ("Builder 6", "Builder 7", "Builder 8", "Builder 1/4")
            if any(regex.fullmatch(value) is not None for value in invalid_values):
                self.add("ERROR", domain, "GOVERNANCE_DRIFT", "unsupported or ambiguous Builder identity is accepted", entities=["UNSUPPORTED_BUILDER_IDENTITY"], evidence=[{"accepted": value} for value in invalid_values if regex.fullmatch(value) is not None], paths=["tools/memorylib/observer.py" if domain == "observer" else "tools/memorylib/semantic_graph.py"])
        if set(observer.BUILDER_NUMBER_SET) != set(GOVERNED_BUILDERS):
            self.add("ERROR", "observer", "GOVERNANCE_DRIFT", "Source Observer allowed Builder set differs from Builder 1–5", entities=["BUILDER_HANDOFF_VALIDATOR"], paths=["tools/memorylib/observer.py"])
        if tuple(builder_bootstrap.BUILDER_NUMBERS) != GOVERNED_BUILDERS or dict(builder_bootstrap.BUILDER_ROLES) != GOVERNED_ROLES:
            self.add("ERROR", "bootstrap", "GOVERNANCE_DRIFT", "Builder Bootstrap accepted identities or roles differ from Builder 1–5", entities=["BUILDER_BOOTSTRAP_VALIDATOR"], paths=["tools/memorylib/builder_bootstrap.py"])

        self._current_documentation()

    def _current_documentation(self) -> None:
        stale_patterns = (
            r"\bBUILDER\s*:\s*[678]\b", r"\bBuilders?\s+6\b", r"\bBuilders?\s+7\b",
            r"Builder[s]?\s+1\s*[–-]\s*7\b", r"Live App Delivery\s*/\s*PWA Integration",
            r"Bug\s*/\s*Regression", r"Runtime Reliability\s*/\s*Product Observability",
        )
        for relative in CURRENT_GOVERNANCE_PATHS:
            path = self.root / relative
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for pattern in stale_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    self.add("ERROR", "documentation", "GOVERNANCE_DRIFT", f"current governance documentation retains obsolete Builder roster or role text: {match.group(0)}", entities=[relative], evidence=[{"match": match.group(0)}], paths=[relative])
            if relative == "CURRENT_STATE.md":
                numbers = {int(value) for value in re.findall(r"\bBuilder\s*:?\s*([1-9])\b", text, re.IGNORECASE)}
                for start, end in re.findall(r"\bBuilders?\s+([1-9])\s*[–-]\s*([1-9])\b", text, re.IGNORECASE):
                    numbers.update(range(int(start), int(end) + 1))
                if numbers and numbers != set(GOVERNED_BUILDERS):
                    self.add("WARNING", "documentation", "GOVERNANCE_DRIFT", "current Builder State view names an incomplete or unsupported governed Builder roster", entities=[relative], evidence=[{"mentioned_builders": sorted(numbers), "governed_builders": list(GOVERNED_BUILDERS)}], paths=[relative], action="Regenerate the current operational view from governed evidence; preserve historical records and do not invent a current workstream.")
            if "BUILDER_BOOTSTRAP_V4" in relative:
                if "Autonomous Development / Night Shift Dispatcher Owner" not in text:
                    self.add("WARNING", "documentation", "GOVERNANCE_DRIFT", "current documentation does not state Builder 5's governed Dispatcher Owner role", entities=["BUILDER_5"], paths=[relative])

    def graph_audit(self) -> None:
        try:
            self.graph = semantic_graph.SemanticGraph(self.root).build()
        except Exception as exc:
            self.add("ERROR", "semantic_graph", "FAILED_CLOSED", f"Semantic Graph could not be read in memory: {exc}", entities=["SEMANTIC_GRAPH"], paths=["tools/memorylib/semantic_graph.py"])
            return
        graph_keys = {key for key, entity in self.graph.entities.items() if entity.namespace == "BUILDER"}
        expected_keys = {f"BUILDER:BUILDER-{number}" for number in GOVERNED_BUILDERS}
        if graph_keys != expected_keys:
            self.add("ERROR", "semantic_graph", "GOVERNANCE_DRIFT", "Semantic Graph seeded Builder identities do not match Builder 1–5", entities=sorted(graph_keys ^ expected_keys), evidence=[{"actual": sorted(graph_keys), "expected": sorted(expected_keys)}], paths=["tools/memorylib/semantic_graph.py"])
        if self.graph.issues:
            errors = [issue.as_dict() for issue in self.graph.issues if issue.severity in {"ERROR", "FATAL"}]
            if errors:
                self.add("ERROR", "semantic_graph", "FAILED_CLOSED", "Semantic Graph contains source-read errors", entities=["SEMANTIC_GRAPH"], evidence=errors, paths=[item.get("path") for item in errors if item.get("path")])
        for unresolved in self.graph.unresolved:
            if str(unresolved.get("field", "")).casefold() in {"depends_on", "dependencies", "required_dependencies"}:
                self.add("ERROR", "dependencies", "MISSING", "a canonical dependency reference is unresolved", entities=[unresolved.get("raw_target")], evidence=[unresolved], authorities=["CANONICAL"], paths=[unresolved.get("source_path")])
        self._dependency_cycles()

    def _dependency_cycles(self) -> None:
        if not self.graph:
            return
        adjacency: dict[str, set[str]] = {}
        for edge in self.graph.edges.values():
            if edge.relation == "depends_on":
                adjacency.setdefault(edge.source, set()).add(edge.target)
        visiting: set[str] = set()
        visited: set[str] = set()
        cycles: set[tuple[str, ...]] = set()

        def visit(node: str, path: list[str]) -> None:
            if node in visiting:
                cycle = tuple(path[path.index(node):] + [node]) if node in path else (node,)
                cycles.add(tuple(sorted(cycle)))
                return
            if node in visited:
                return
            visiting.add(node)
            for target in sorted(adjacency.get(node, ())):
                visit(target, path + [target])
            visiting.remove(node)
            visited.add(node)

        for node in sorted(adjacency):
            visit(node, [node])
        for cycle in sorted(cycles):
            self.add("ERROR", "dependencies", "CONFLICT", "circular dependency detected", entities=cycle, authorities=["CANONICAL"], paths=["events/records", "workstreams"])

    def external_output_audit(self) -> None:
        expected = (
            (context_compiler.CONTEXT_DIR, "context"),
            (builder_bootstrap.BOOTSTRAP_DIR, "builder-bootstrap"),
            (semantic_graph.GRAPH_RELATIVE_ROOT if semantic_graph.GRAPH_RELATIVE_ROOT.startswith("_live/") else "_live/graph", "graph"),
        )
        if context_compiler.CONTEXT_DIR != "_live/context" or builder_bootstrap.BOOTSTRAP_DIR != "_live/builder-bootstrap":
            self.add("ERROR", "external_output", "FAILED_CLOSED", "runtime output contract no longer targets the external Vault live layer", entities=["RUNTIME_OUTPUT_ROOT"], paths=["tools/memorylib/context_compiler.py", "tools/memorylib/builder_bootstrap.py"])
        if not self.vault:
            return
        for relative, label in expected:
            target = self.vault / relative
            resolved = target.resolve(strict=False)
            if _inside(resolved, self.root):
                self.add("ERROR", "external_output", "FAILED_CLOSED", f"{label} runtime output resolves inside canonical Memory", entities=[f"_live/{label}"], evidence=[{"configured": str(target), "resolved": str(resolved), "canonical_root": str(self.root)}], paths=[str(target)], action="Move the runtime output outside canonical Memory; do not write until the path is corrected.")

    def _runtime_file(self, filename: str) -> tuple[bool, dict[str, Any] | None]:
        if not self.vault:
            return False, None
        path = self.vault / "_live" / filename
        exists, payload, error = _read_json(path)
        if error:
            self.add("ERROR", "runtime", "FAILED_CLOSED", f"runtime artifact {filename} is unreadable JSON", entities=[filename], evidence=[{"error": error}], authorities=["RUNTIME_DERIVED"], paths=[f"_live/{filename}"])
            return True, None
        if not exists:
            return False, None
        if not isinstance(payload, dict):
            self.add("ERROR", "runtime", "FAILED_CLOSED", f"runtime artifact {filename} must be a JSON object", entities=[filename], authorities=["RUNTIME_DERIVED"], paths=[f"_live/{filename}"])
            return True, None
        self.runtime_payloads[filename] = payload
        return True, payload

    def runtime_audit(self) -> None:
        if not self.vault:
            self.add("WARNING", "runtime", "UNKNOWN", "no external Vault was supplied; runtime-derived state cannot be audited", entities=["RUNTIME_STATE"], paths=["_live"], action="Supply the external Vault path for a runtime consistency audit; no runtime state is inferred.")
            for number in GOVERNED_BUILDERS:
                self.add("WARNING", "builder_status", "UNKNOWN", f"Builder {number} has no current handoff evidence in this audit", entities=[f"Builder {number}"], authorities=["RUNTIME_DERIVED"], paths=["_live/BUILDER_HANDOFFS.json"])
            return
        present = False
        for filename in RUNTIME_FILENAMES:
            exists, payload = self._runtime_file(filename)
            present = present or exists
            if payload is not None:
                self._validate_runtime_payload(filename, payload)
                self._scan_unsupported_builder_payload(filename, payload)
                self._scan_authority_claims(filename, payload)
        self.runtime_available = present and bool(self.runtime_payloads.get("SEMANTIC_GRAPH_STATUS.json", {}).get("status") in {"ONLINE", "STALE"} or (self.vault / "_live" / "graph" / "GRAPH_MANIFEST.json").is_file())
        if not present:
            self.add("WARNING", "runtime", "UNKNOWN", "external Vault has no current runtime artifacts", entities=["RUNTIME_STATE"], authorities=["RUNTIME_DERIVED"], paths=["_live"])
        elif not (self.vault / "_live" / "graph" / "GRAPH_MANIFEST.json").is_file():
            self.add("WARNING", "semantic_graph", "UNKNOWN", "runtime Semantic Graph is unavailable; graph-current consistency cannot be claimed", entities=["GRAPH_MANIFEST"], authorities=["RUNTIME_DERIVED"], paths=["_live/graph/GRAPH_MANIFEST.json"], action="Rebuild and validate the external runtime graph before treating context or bootstrap projections as graph-current.")
        handoff_payload = self.runtime_payloads.get("BUILDER_HANDOFFS.json", {})
        raw_handoffs = handoff_payload.get("candidates", []) if isinstance(handoff_payload, Mapping) else []
        valid_handoffs: list[dict[str, Any]] = []
        for item in raw_handoffs if isinstance(raw_handoffs, list) else []:
            if not isinstance(item, Mapping):
                continue
            try:
                validate_handoff_evidence(dict(item))
                valid_handoffs.append(dict(item))
            except Exception:
                continue
        try:
            self.latest_handoffs = _latest_builder_evidence(valid_handoffs)
        except Exception:
            self.latest_handoffs = {}
        for number in GOVERNED_BUILDERS:
            evidence = self.latest_handoffs.get(number)
            if evidence is None:
                self.add("WARNING", "builder_status", "UNKNOWN", f"Builder {number} has no current valid handoff evidence", entities=[f"Builder {number}"], authorities=["RUNTIME_DERIVED"], paths=["_live/BUILDER_HANDOFFS.json"], action="Obtain an explicit valid handoff; do not infer a current workstream or resolve an earlier blocker.")
                continue
            self.runtime_snapshots[number].append(("_live/BUILDER_HANDOFFS.json", evidence))
            try:
                freshness = _age_state(str(evidence["observed_at"]), self.reference_time)
            except (TypeError, ValueError):
                freshness = "STALE"
            if freshness not in FRESHNESS_STATES:
                freshness = "STALE"
            if freshness == "STALE":
                self.add("WARNING", "builder_status", "STALE", f"Builder {number} handoff is STALE and cannot be treated as unquestionably current", entities=[f"Builder {number}"], evidence=[{"observed_at": evidence.get("observed_at"), "reference_time": self.reference_time}], authorities=["CANDIDATE_OPERATIONAL_EVIDENCE"], paths=["_live/BUILDER_HANDOFFS.json"], action="Obtain a newer explicit handoff and require CEO review for any state transition.")
            elif freshness == "AGING":
                self.add("WARNING", "builder_status", "WARNING", f"Builder {number} handoff is AGING", entities=[f"Builder {number}"], evidence=[{"observed_at": evidence.get("observed_at"), "reference_time": self.reference_time}], authorities=["CANDIDATE_OPERATIONAL_EVIDENCE"], paths=["_live/BUILDER_HANDOFFS.json"])
        self._runtime_projection_snapshots()

    def _validate_runtime_payload(self, filename: str, payload: Mapping[str, Any]) -> None:
        if filename in {"SOURCE_CANDIDATES.json", "BUILDER_HANDOFFS.json"}:
            if payload.get("schema") != 1 or not isinstance(payload.get("candidates"), list):
                self.add("ERROR", "runtime", "FAILED_CLOSED", f"{filename} violates its runtime candidate-store contract", entities=[filename], authorities=["RUNTIME_DERIVED"], paths=[f"_live/{filename}"])
        if filename == "BLOCKERS.json":
            blockers = payload.get("blockers")
            if not isinstance(blockers, list):
                self.add("ERROR", "runtime", "FAILED_CLOSED", "BLOCKERS.json blockers must be a list", entities=[filename], paths=["_live/BLOCKERS.json"])
            else:
                for index, blocker in enumerate(blockers):
                    try:
                        validate_blocker(blocker)
                    except Exception as exc:
                        self.add("ERROR", "runtime", "FAILED_CLOSED", f"invalid runtime blocker at index {index}: {exc}", entities=[filename], paths=["_live/BLOCKERS.json"])
        candidates = payload.get("candidates", [])
        if isinstance(candidates, list):
            for index, candidate in enumerate(candidates):
                if not isinstance(candidate, Mapping):
                    continue
                try:
                    if candidate.get("candidate_type") == "CANDIDATE_OPERATIONAL_EVIDENCE":
                        validate_handoff_evidence(dict(candidate))
                    elif candidate.get("candidate_type") == "SOURCE_CANDIDATE_EVENT":
                        validate_candidate(dict(candidate))
                except Exception as exc:
                    self.add("ERROR", "runtime", "FAILED_CLOSED", f"invalid runtime candidate at index {index}: {exc}", entities=[filename], authorities=["RUNTIME_DERIVED"], paths=[f"_live/{filename}"])

    def _scan_unsupported_builder_payload(self, filename: str, payload: Mapping[str, Any]) -> None:
        source_path = filename if filename.startswith("_live/") else f"_live/{filename}"
        def walk(value: Any, path: str) -> None:
            if isinstance(value, Mapping):
                number = None
                if "builder_number" in value:
                    number = _builder_number(value.get("builder_number"))
                elif "builder" in value:
                    number = _builder_number(value.get("builder"))
                identity_key_present = "builder_number" in value or "builder" in value
                identity_value = value.get("builder_number", value.get("builder")) if identity_key_present else None
                identity_text = _normal(identity_value)
                has_builder_identity = identity_key_present or bool(re.search(r"\bBUILDER\b", identity_text, re.IGNORECASE))
                if has_builder_identity and number is None:
                    self.add("ERROR", "governance", "GOVERNANCE_DRIFT", "runtime artifact contains an ambiguous or malformed Builder identity", entities=[identity_text or filename], evidence=[{"identity": identity_text}], authorities=["RUNTIME_DERIVED"], paths=[source_path])
                if number is not None and number not in GOVERNED_BUILDERS:
                    self.add("ERROR", "governance", "GOVERNANCE_DRIFT", f"runtime artifact contains unsupported Builder {number} identity", entities=[f"Builder {number}"], evidence=[{"builder_number": number}], authorities=["RUNTIME_DERIVED"], paths=[source_path])
                for key, child in value.items():
                    walk(child, f"{path}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")
        walk(payload, filename)

    def _scan_authority_claims(self, filename: str, payload: Mapping[str, Any]) -> None:
        source_path = filename if filename.startswith("_live/") else f"_live/{filename}"
        def walk(value: Any, path: str) -> None:
            if isinstance(value, str) and SECRET_VALUE_RE.search(value):
                self.add("ERROR", "security", "FAILED_CLOSED", "runtime artifact contains secret-like material", entities=[filename], authorities=["RUNTIME_DERIVED"], paths=[source_path], action="Remove secret material from the runtime artifact and regenerate it through the existing secret-safe boundary.")
                return
            if isinstance(value, Mapping):
                metadata = value.get("metadata") if isinstance(value.get("metadata"), Mapping) else {}
                candidate_type = value.get("candidate_type") or metadata.get("candidate_type")
                if candidate_type in {"SOURCE_CANDIDATE_EVENT", "CANDIDATE_OPERATIONAL_EVIDENCE"} or path.endswith("candidates"):
                    if "canonical" in value and value.get("canonical") is not False:
                        self.add("ERROR", "authority", "FAILED_CLOSED", "runtime candidate is presented as canonical", entities=[value.get("candidate_id") or filename], evidence=[{"canonical": value.get("canonical")}], authorities=["RUNTIME_DERIVED"], paths=[source_path], action="Keep runtime candidates canonical=false and promotion_required=true; require explicit human promotion.")
                    if "promotion_required" in value and value.get("promotion_required") is not True and candidate_type in {"SOURCE_CANDIDATE_EVENT", "CANDIDATE_OPERATIONAL_EVIDENCE"}:
                        self.add("ERROR", "authority", "FAILED_CLOSED", "runtime candidate does not require explicit promotion", entities=[value.get("candidate_id") or filename], evidence=[{"promotion_required": value.get("promotion_required")}], paths=[source_path])
                if "execution_authorization" in value and str(value.get("execution_authorization")).upper() != "NOT_PROVIDED":
                    self.add("ERROR", "authority", "FAILED_CLOSED", "Memory artifact claims execution authorization", entities=[value.get("bootstrap_id") or filename], evidence=[{"execution_authorization": value.get("execution_authorization")}], paths=[source_path], action="Remove the authorization claim and keep the bootstrap layer informational only.")
                if "safety_decision" in value and str(value.get("safety_decision")).upper() != "NOT_EVALUATED":
                    self.add("ERROR", "authority", "FAILED_CLOSED", "Memory artifact claims a safety decision", entities=[value.get("bootstrap_id") or filename], evidence=[{"safety_decision": value.get("safety_decision")}], paths=[source_path])
                for key, child in value.items():
                    lowered = str(key).casefold()
                    if lowered in {"ceo_authorized", "execution_authorized", "authorized_to_execute", "merge_authorized", "deploy_authorized"} and child is True:
                        self.add("ERROR", "authority", "FAILED_CLOSED", "runtime artifact contains an execution or CEO authorization claim", entities=[filename], evidence=[{"field": key, "value": child}], paths=[source_path])
                    walk(child, f"{path}.{key}")
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, f"{path}[{index}]")
        walk(payload, filename)

    def _runtime_projection_snapshots(self) -> None:
        if not self.vault:
            return
        graph_path = self.vault / "_live" / "graph" / "GRAPH_MANIFEST.json"
        exists, manifest, error = _read_json(graph_path)
        if error:
            self.add("ERROR", "semantic_graph", "FAILED_CLOSED", "runtime Semantic Graph manifest is unreadable", entities=["GRAPH_MANIFEST"], evidence=[{"error": error}], paths=["_live/graph/GRAPH_MANIFEST.json"])
        if exists and isinstance(manifest, Mapping):
            try:
                validation = semantic_graph.validate_semantic_graph(self.root, graph_path.parent, vault=self.vault, link_base=self.vault)
                if validation.errors:
                    self.add("ERROR", "semantic_graph", "FAILED_CLOSED", "runtime Semantic Graph fails validation", entities=["GRAPH_MANIFEST"], evidence=[issue.as_dict() for issue in validation.issues], authorities=["RUNTIME_DERIVED"], paths=["_live/graph/GRAPH_MANIFEST.json"])
                elif validation.warnings:
                    self.add("WARNING", "semantic_graph", "WARNING", "runtime Semantic Graph validation has warnings", entities=["GRAPH_MANIFEST"], evidence=[issue.as_dict() for issue in validation.issues], authorities=["RUNTIME_DERIVED"], paths=["_live/graph/GRAPH_MANIFEST.json"])
            except Exception as exc:
                self.add("ERROR", "semantic_graph", "FAILED_CLOSED", f"runtime Semantic Graph validation could not complete: {exc}", entities=["GRAPH_MANIFEST"], paths=["_live/graph/GRAPH_MANIFEST.json"])
        if exists and isinstance(manifest, Mapping):
            self._scan_authority_claims("graph/GRAPH_MANIFEST.json", manifest)
            for entity in manifest.get("entities", []) if isinstance(manifest.get("entities"), list) else []:
                if not isinstance(entity, Mapping) or entity.get("namespace") != "BUILDER":
                    continue
                number = _builder_number(entity.get("stable_id"))
                current = entity.get("metadata", {}).get("current_evidence") if isinstance(entity.get("metadata"), Mapping) else None
                if number in GOVERNED_BUILDERS and isinstance(current, Mapping):
                    self.runtime_snapshots[number].append(("_live/graph/GRAPH_MANIFEST.json", dict(current)))
        for filename, payload in self.runtime_payloads.items():
            if filename not in {"SOURCE_OBSERVER.json", "BUILDER_HANDOFFS.json"}:
                continue
            values = payload.get("builder_handoffs", []) if filename == "SOURCE_OBSERVER.json" else payload.get("candidates", [])
            if not isinstance(values, list):
                continue
            for value in values:
                if not isinstance(value, Mapping):
                    continue
                number = _builder_number(value.get("builder_number", value.get("builder")))
                if number in GOVERNED_BUILDERS and value.get("candidate_type") == "CANDIDATE_OPERATIONAL_EVIDENCE":
                    self.runtime_snapshots[number].append((f"_live/{filename}", dict(value)))

        for number, snapshots in self.runtime_snapshots.items():
            if len(snapshots) < 2:
                continue
            baseline_path, baseline = snapshots[0]
            for other_path, other in snapshots[1:]:
                for field_name in ("role", "branch", "head_sha", "source_pr", "status", "blockers", "tests", "ci"):
                    left, right = _compare_value(_field(baseline, field_name)), _compare_value(_field(other, field_name))
                    if left in (None, "", [], {}) or right in (None, "", [], {}) or left == right:
                        continue
                    self.add("WARNING", "builder_status", "CONFLICT", f"Builder {number} {field_name} differs between current evidence projections", entities=[f"Builder {number}"], evidence=[{"field": field_name, "left": left, "right": right}], authorities=["CANDIDATE_OPERATIONAL_EVIDENCE", "RUNTIME_DERIVED"], paths=[baseline_path, other_path], action="Keep both observations, do not auto-resolve, and require CEO review of the state transition.")

    def canonical_runtime_consistency(self) -> None:
        canonical = self._canonical_builder_snapshots()
        for number, handoff in self.latest_handoffs.items():
            for field_name in ("role", "branch", "head_sha", "source_pr", "status", "blockers"):
                observed = _compare_value(_field(handoff, field_name))
                for path, record in canonical.get(number, []):
                    expected = _compare_value(_field(record, field_name))
                    if observed in (None, "", [], {}) or expected in (None, "", [], {}) or observed == expected:
                        continue
                    self.add("WARNING", "builder_status", "CONFLICT", f"Builder {number} {field_name} differs between canonical and latest handoff evidence", entities=[f"Builder {number}"], evidence=[{"field": field_name, "canonical": expected, "handoff": observed}], authorities=["CANONICAL", "CANDIDATE_OPERATIONAL_EVIDENCE"], paths=[path, "_live/BUILDER_HANDOFFS.json"], action="Do not overwrite either source; review the conflicting current-state evidence explicitly.")

    def _canonical_builder_snapshots(self) -> dict[int, list[tuple[str, dict[str, Any]]]]:
        result: dict[int, list[tuple[str, dict[str, Any]]]] = {number: [] for number in GOVERNED_BUILDERS}
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or any(part in {".git", "history", "views", "_live", "__pycache__"} for part in path.relative_to(self.root).parts):
                continue
            if path.suffix not in {".md", ".json"}:
                continue
            rel = path.relative_to(self.root).as_posix()
            try:
                raw = path.read_text(encoding="utf-8")
                if path.suffix == ".json":
                    payload = json.loads(raw)
                    payload = payload if isinstance(payload, dict) else {}
                else:
                    payload, _ = parse_frontmatter(raw)
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            number = _builder_number(payload.get("builder_number", payload.get("builder")))
            if number in GOVERNED_BUILDERS:
                result[number].append((rel, dict(payload)))
        return result

    def dependency_and_authority_audit(self) -> None:
        if not self.vault:
            return
        root = self.vault / "_live" / "builder-bootstrap"
        if root.is_dir():
            for path in sorted(root.glob("*.json")):
                exists, payload, error = _read_json(path)
                rel = path.relative_to(self.vault).as_posix()
                if error or not isinstance(payload, Mapping):
                    self.add("ERROR", "bootstrap", "FAILED_CLOSED", "Builder Bootstrap artifact is unreadable", entities=[path.name], paths=[rel])
                    continue
                try:
                    validate_builder_bootstrap(path)
                except Exception as exc:
                    self.add("ERROR", "bootstrap", "FAILED_CLOSED", f"Builder Bootstrap artifact fails validation: {exc}", entities=[payload.get("bootstrap_id") or path.name], paths=[rel])
                self._scan_unsupported_builder_payload(rel, payload)
                self._audit_bootstrap(payload, rel)
        context_root = self.vault / "_live" / "context"
        if context_root.is_dir():
            for path in sorted(context_root.glob("*.json")):
                exists, payload, error = _read_json(path)
                rel = path.relative_to(self.vault).as_posix()
                if error or not isinstance(payload, Mapping):
                    self.add("ERROR", "context_compiler", "FAILED_CLOSED", "Context Compiler artifact is unreadable", entities=[path.name], paths=[rel])
                    continue
                try:
                    validate_context_pack(path)
                except Exception as exc:
                    self.add("ERROR", "context_compiler", "FAILED_CLOSED", f"Context Compiler artifact fails validation: {exc}", entities=[path.name], paths=[rel])
                self._scan_unsupported_builder_payload(rel, payload)
                self._audit_context(payload, rel)

    def _audit_context(self, payload: Mapping[str, Any], rel: str) -> None:
        self._scan_authority_claims(rel, payload)
        for item in payload.get("included_entities", []) if isinstance(payload.get("included_entities"), list) else []:
            if not isinstance(item, Mapping):
                continue
            number = _builder_number(item.get("stable_id")) if item.get("namespace") == "BUILDER" else None
            current = item.get("runtime_status")
            if number in GOVERNED_BUILDERS and isinstance(current, Mapping):
                self.runtime_snapshots[number].append((rel, dict(current)))
                if str(current.get("state", "")).upper() == "UNKNOWN" and number in self.latest_handoffs:
                    self.add("WARNING", "builder_status", "CONFLICT", f"Builder {number} context reports UNKNOWN despite a newer valid handoff", entities=[f"Builder {number}"], evidence=[{"context_state": current.get("state"), "handoff_candidate_id": self.latest_handoffs[number].get("candidate_id")}], authorities=["CANDIDATE_OPERATIONAL_EVIDENCE", "RUNTIME_DERIVED"], paths=[rel, "_live/BUILDER_HANDOFFS.json"], action="Preserve the evidence and require review of the context refresh; do not auto-resolve the state conflict.")
                if str(current.get("freshness", "")).upper() == "STALE" and str(payload.get("freshness_state", "")).upper() == "FRESH":
                    self.add("ERROR", "builder_status", "CONFLICT", f"Builder {number} context presents stale evidence as FRESH", entities=[f"Builder {number}"], evidence=[{"context_freshness": payload.get("freshness_state"), "evidence_freshness": current.get("freshness")}], authorities=["RUNTIME_DERIVED"], paths=[rel])
            authority = str(item.get("authority_class", "")).upper()
            if authority in {"CANDIDATE", "RUNTIME_DERIVED"} and item.get("canonical") is not False:
                self.add("ERROR", "authority", "FAILED_CLOSED", "context projection presents non-authoritative evidence as canonical", entities=[item.get("entity_id")], evidence=[{"authority_class": authority, "canonical": item.get("canonical")}], paths=[rel])
            if item.get("freshness") == "STALE" and authority in {"CANDIDATE", "RUNTIME_DERIVED"}:
                self.add("WARNING", "authority", "STALE", "context projection contains stale runtime evidence", entities=[item.get("entity_id")], authorities=[authority], paths=[rel])

    def _audit_bootstrap(self, payload: Mapping[str, Any], rel: str) -> None:
        builder = payload.get("builder") if isinstance(payload.get("builder"), Mapping) else {}
        number = _builder_number(builder.get("number"))
        current = builder.get("current_evidence")
        if number in GOVERNED_BUILDERS and isinstance(current, Mapping):
            self.runtime_snapshots[number].append((rel, dict(current)))
        if payload.get("execution_authorization") != "NOT_PROVIDED" or payload.get("safety_decision") != "NOT_EVALUATED":
            self.add("ERROR", "authority", "FAILED_CLOSED", "Builder Bootstrap claims execution or safety authority", entities=[payload.get("bootstrap_id") or rel], evidence=[{"execution_authorization": payload.get("execution_authorization"), "safety_decision": payload.get("safety_decision")}], paths=[rel])
        context = payload.get("context_pack") if isinstance(payload.get("context_pack"), Mapping) else {}
        items = [item for item in context.get("included_entities", []) if isinstance(item, Mapping)]
        for status in payload.get("required_dependency_status", []) if isinstance(payload.get("required_dependency_status"), list) else []:
            if not isinstance(status, Mapping):
                continue
            dependency = status.get("dependency")
            state = str(status.get("status", "")).upper()
            matches = [item for item in items if _normal(dependency).casefold() in {_normal(item.get("entity_id")).casefold(), _normal(item.get("stable_id")).casefold(), _normal(item.get("label")).casefold()}]
            auth = {str(item.get("authority_class", "")).upper() for item in matches}
            if re.search(r"BUILDER[-_ ]?[678]\b", _normal(dependency), re.IGNORECASE):
                self.add("ERROR", "dependencies", "GOVERNANCE_DRIFT", "bootstrap dependency names an unsupported Builder", entities=[dependency], paths=[rel])
            if state == "MISSING":
                self.add("ERROR", "dependencies", "MISSING", f"required dependency {dependency} is missing", entities=[dependency], authorities=["CANONICAL"], paths=[rel])
            elif state == "PRESENT_NONAUTHORITATIVE":
                self.add("WARNING", "dependencies", "NONAUTHORITATIVE_ONLY", f"required dependency {dependency} is present only as candidate/runtime evidence", entities=[dependency], authorities=auth or ["CANDIDATE"], paths=[rel])
            elif state == "SATISFIED_AUTHORITATIVE" and not (auth & {"CANONICAL", "VERIFIED"}):
                self.add("ERROR", "dependencies", "NONAUTHORITATIVE_ONLY", f"required dependency {dependency} is marked authoritative without authoritative evidence", entities=[dependency], authorities=auth or ["CANDIDATE", "RUNTIME_DERIVED"], paths=[rel], action="Rebuild the package from canonical or verified evidence; candidate/runtime evidence must not satisfy an authoritative dependency.")
            if state == "SATISFIED_AUTHORITATIVE" and any(str(item.get("freshness", "")).upper() in {"STALE", "UNKNOWN"} for item in matches):
                self.add("ERROR", "dependencies", "STALE", f"required dependency {dependency} is satisfied by stale or unknown evidence", entities=[dependency], paths=[rel])
            for item in matches:
                if item.get("superseded") or item.get("superseded_by") or "SUPERSEDED_HISTORY" in {str(reason) for reason in item.get("selection_reasons", [])}:
                    self.add("WARNING", "dependencies", "STALE", f"required dependency {dependency} is superseded evidence", entities=[dependency], authorities=[str(item.get("authority_class", "UNKNOWN"))], paths=[rel], action="Use the current authoritative dependency or require explicit human review of the supersession chain.")
        self._scan_authority_claims(rel, payload)

    def compare_runtime_snapshots(self) -> None:
        """Compare every current projection after context/bootstrap artifacts load."""
        for number, snapshots in self.runtime_snapshots.items():
            if len(snapshots) < 2:
                continue
            for index, (left_path, left) in enumerate(snapshots):
                for right_path, right in snapshots[index + 1:]:
                    for field_name in ("role", "branch", "head_sha", "source_pr", "status", "blockers", "tests", "ci"):
                        left_value = _compare_value(_field(left, field_name))
                        right_value = _compare_value(_field(right, field_name))
                        if left_value in (None, "", [], {}) or right_value in (None, "", [], {}) or left_value == right_value:
                            continue
                        self.add("WARNING", "builder_status", "CONFLICT", f"Builder {number} {field_name} differs between current evidence projections", entities=[f"Builder {number}"], evidence=[{"field": field_name, "left": left_value, "right": right_value}], authorities=["CANDIDATE_OPERATIONAL_EVIDENCE", "RUNTIME_DERIVED"], paths=[left_path, right_path], action="Keep both observations, do not auto-resolve, and require CEO review of the state transition.")
            for path, snapshot in snapshots:
                state = str(snapshot.get("freshness", "")).upper()
                if state == "STALE" and path != "_live/BUILDER_HANDOFFS.json":
                    self.add("WARNING", "builder_status", "STALE", f"Builder {number} runtime projection is STALE", entities=[f"Builder {number}"], evidence=[{"path": path, "observed_at": snapshot.get("observed_at")}], authorities=["RUNTIME_DERIVED"], paths=[path], action="Obtain a newer handoff and do not present this runtime projection as unquestionably current.")

    def safety_audit(self) -> None:
        chunks: list[tuple[str, str]] = []
        for relative in SAFETY_PATHS:
            path = self.root / relative
            if path.is_file():
                chunks.append((relative, path.read_text(encoding="utf-8", errors="replace")))
        text = "\n".join(value for _, value in chunks)
        checks = (
            ("NO_BET", re.compile(r"\bNO[- ]BET\b", re.IGNORECASE), "NO-BET invariant is missing from current safety sources"),
            ("NO_LIVE_ACTIVATION", re.compile(r"no[- ]live[- ]activation|live activation[^.\n]*(?:not approved|disabled|prohibited|not permitted)", re.IGNORECASE), "no-live-activation invariant is missing from current safety sources"),
            ("SEALED_RESEARCH", re.compile(r"2425", re.IGNORECASE), "sealed 2425/2526 research boundary is missing"),
            ("SEALED_HOLDOUT", re.compile(r"2526", re.IGNORECASE), "sealed 2425/2526 research boundary is missing"),
            ("SEALED_MARKER", re.compile(r"SEALED", re.IGNORECASE), "SEALED marker is missing from current safety sources"),
            ("CLOSING_ODDS_BENCHMARK", re.compile(r"closing odds.{0,180}(?:benchmark|CLV)|(?:benchmark|CLV).{0,180}closing odds", re.IGNORECASE | re.DOTALL), "closing odds benchmark-only boundary is missing"),
            ("NO_EXECUTION_AUTHORITY", re.compile(r"(?:does not|never|no|not)\b.{0,140}\b(?:grant CEO authorization|merge|deploy|production|activation)\b", re.IGNORECASE | re.DOTALL), "automatic production/execution authority boundary is missing"),
            ("NO_CEO_AUTH_ARTIFACT", re.compile(r"does not[^.\n]{0,140}grant\s+CEO\s+authorization|execution authorization[^.\n]{0,40}NOT PROVIDED", re.IGNORECASE), "Memory artifacts must not grant CEO authorization"),
        )
        for name, pattern, summary in checks:
            if not pattern.search(text):
                self.add("ERROR", "safety", "SAFETY_INVARIANT_MISSING", summary, entities=[name], authorities=["CANONICAL"], paths=[relative for relative, _ in chunks], action="Restore the mandatory safety invariant in canonical governance sources before treating the system as consistent.")
        if "2425" in text and "2526" in text and not re.search(r"2425.{0,80}2526.{0,80}SEALED|2526.{0,80}2425.{0,80}SEALED", text, re.IGNORECASE | re.DOTALL):
            self.add("ERROR", "safety", "SAFETY_INVARIANT_MISSING", "2425 and 2526 are not visibly tied to SEALED status", entities=["2425", "2526"], paths=[relative for relative, _ in chunks])

    def verification_conflicts(self) -> None:
        canonical_records: list[tuple[str, dict[str, Any]]] = []
        verified_records: list[tuple[str, dict[str, Any]]] = []
        for path in sorted(self.root.rglob("*")):
            if not path.is_file() or path.suffix not in {".json", ".md"}:
                continue
            parts = path.relative_to(self.root).parts
            if any(part in {"history", "views", "_live", ".git"} for part in parts):
                continue
            try:
                raw = path.read_text(encoding="utf-8")
                payload = json.loads(raw) if path.suffix == ".json" else parse_frontmatter(raw)[0]
            except (OSError, ValueError, json.JSONDecodeError):
                continue
            if not isinstance(payload, dict):
                continue
            rel = path.relative_to(self.root).as_posix()
            if parts[0] == "events" and (payload.get("canonical") is not False):
                canonical_records.append((rel, payload))
            if parts[0] == "verifications" or str(payload.get("verification_state", "")).casefold() in {"verified", "ceo_verified", "merged_source"}:
                verified_records.append((rel, payload))
        for canonical_path, canonical in canonical_records:
            for verified_path, verified in verified_records:
                same_pr = canonical.get("source_pr") and canonical.get("source_pr") == verified.get("source_pr") and canonical.get("source_repository") == verified.get("source_repository")
                same_event = canonical.get("event_id") and canonical.get("event_id") in {verified.get("event_id"), verified.get("source_event"), verified.get("record_id"), verified.get("canonical_event")}
                if not same_pr and not same_event:
                    continue
                for field_name in ("status", "state", "source_state", "head_sha", "source_sha"):
                    left, right = _compare_value(canonical.get(field_name)), _compare_value(verified.get(field_name))
                    if left in (None, "") or right in (None, "") or left == right:
                        continue
                    self.add("ERROR", "authority", "CONFLICT", f"canonical and verified evidence disagree on {field_name}", entities=[canonical.get("event_id") or canonical_path, verified.get("id") or verified_path], evidence=[{"field": field_name, "canonical": left, "verified": right}], authorities=["CANONICAL", "VERIFIED"], paths=[canonical_path, verified_path], action="Preserve both records and require human review; do not promote, resolve, or rewrite either record automatically.")

    def finish(self) -> ConsistencyAudit:
        ordered = sorted(self.findings.values(), key=lambda item: (-SEVERITY_RANK.get(item["severity"], 0), item["domain"], item["status"], item["finding_id"]))
        statuses = {item["status"] for item in ordered}
        if "SAFETY_INVARIANT_MISSING" in statuses:
            overall = "SAFETY_INVARIANT_MISSING"
        elif "CONFLICT" in statuses:
            overall = "CONFLICT"
        elif "GOVERNANCE_DRIFT" in statuses:
            overall = "GOVERNANCE_DRIFT"
        elif "FAILED_CLOSED" in statuses:
            overall = "FAILED_CLOSED"
        elif any(item["severity"] == "WARNING" for item in ordered):
            overall = "WARNING"
        elif "UNKNOWN" in statuses:
            overall = "UNKNOWN"
        else:
            overall = "CONSISTENT"
        semantic = {
            "schema_version": AUDIT_SCHEMA,
            "source_memory_sha": _source_sha(self.root),
            "reference_time": self.reference_time,
            "overall_status": overall,
            "runtime_available": self.runtime_available,
            "findings": ordered,
        }
        return ConsistencyAudit(
            source_memory_sha=semantic["source_memory_sha"],
            reference_time=self.reference_time,
            overall_status=overall,
            findings=ordered,
            semantic_digest=_digest(semantic),
            generated_at=datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            runtime_available=self.runtime_available,
        )


def audit_consistency(root: Path, *, vault: Path | None = None, reference_time: str | None = None) -> ConsistencyAudit:
    """Audit current Memory and optional external runtime projections read-only."""
    root = Path(root).resolve()
    builder = _AuditBuilder(root, Path(vault) if vault else None, _reference_time(reference_time))
    builder.governance()
    builder.graph_audit()
    builder.external_output_audit()
    builder.runtime_audit()
    builder.dependency_and_authority_audit()
    builder.compare_runtime_snapshots()
    builder.canonical_runtime_consistency()
    builder.safety_audit()
    builder.verification_conflicts()
    return builder.finish()


def _ensure_external_report_path(root: Path, vault: Path | None, output: Path) -> Path:
    resolved = output.resolve(strict=False)
    if _inside(resolved, root):
        raise ValueError("consistency audit output must be outside canonical Memory")
    if vault and _inside(resolved, vault):
        raise ValueError("consistency audit output must be outside the external Vault runtime root")
    return resolved


def write_audit_report(audit: ConsistencyAudit, output: Path, *, root: Path, vault: Path | None = None) -> dict[str, str]:
    """Write JSON and Markdown only to an explicitly requested external path."""
    target = _ensure_external_report_path(Path(root).resolve(), Path(vault).resolve() if vault else None, Path(output))
    if target.suffix.lower() in {".json", ".md"}:
        json_path = target.with_suffix(".json")
        markdown_path = target.with_suffix(".md")
    else:
        target.mkdir(parents=True, exist_ok=True)
        json_path = target / "MEMORY_CONSISTENCY_AUDIT_V5.json"
        markdown_path = target / "MEMORY_CONSISTENCY_AUDIT_V5.md"
    for path in (json_path, markdown_path):
        _ensure_external_report_path(Path(root).resolve(), Path(vault).resolve() if vault else None, path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(audit.to_dict(), indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(audit.markdown(), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}


__all__ = ["AUDIT_SCHEMA", "AUDIT_VERSION", "ConsistencyAudit", "Finding", "audit_consistency", "write_audit_report"]
