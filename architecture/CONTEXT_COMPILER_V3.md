---
type: architecture
status: active
last_updated: 2026-09-16T00:00:00Z
freshness_class: stable
---
# Memory Context Compiler V3

Context Compiler V3 is a deterministic selection layer over canonical Memory,
Semantic Graph V2, and explicitly requested noncanonical runtime observations.
It produces an auditable context pack for a named consumer. It is not a source
of truth, decision maker, status fabricator, LLM inference engine, or canonical
Memory writer.

## Architecture and storage

The compiler builds the Semantic Graph V2 registry in memory. Canonical records
are read-only inputs. If `include_runtime=true`, the compiler reads validated
`_live/SOURCE_OBSERVER.json`, `SOURCE_CANDIDATES.json`, `BUILDER_HANDOFFS.json`,
`BLOCKERS.json`, and the current `_live/graph/GRAPH_MANIFEST.json` when present.
Runtime evidence remains `CANDIDATE` or `RUNTIME_DERIVED`, noncanonical, and
freshness-bounded.

Generated JSON and Markdown packs belong in Vault `_live/context/`. They are
temporary operational artifacts and must not be committed to Memory `main`.
The compiler is callable on demand; it does not add a scheduler or change the
existing 90-second LaunchAgent.

## Request contract

`ContextRequest` contains:

```json
{
  "request_id": "CTX-example",
  "consumer_type": "BUILDER_4",
  "builder_number": 4,
  "task": "continue provider cascade implementation",
  "workstream": "",
  "repository_scope": ["Philip3006/sportsbrain"],
  "entity_seeds": ["WS-TOP5-PRODUCTION"],
  "requested_domains": ["production-shadow"],
  "token_budget": 6000,
  "max_entity_count": 80,
  "freshness_requirement": "ANY",
  "include_runtime": true,
  "generated_at": "2026-09-16T00:00:00Z"
}
```

Consumers are `CEO`, `BUILDER_1` through `BUILDER_4`, and `GENERIC_REVIEW`.
Builder identities are fail-closed to exactly 1–4; ambiguous or unknown
identities are rejected.

## Pack contract and provenance

Every pack includes schema/compiler versions, request identity, source Memory
SHA, semantic graph digest, optional runtime digest, selection policy, seeds,
selected entities and edges, canonical/runtime counts, freshness, warnings,
conflicts, unresolved references, metrics, truncation accounting, token budget,
estimated tokens, cache key, and a stable `context_digest`.

Every entity includes a short factual selection reason and provenance containing
the entity ID, source paths, authority class, source SHA where available,
record identity, observed/created timestamp, and graph relations used. This
answers “why was this included?” without storing hidden reasoning.

## Authority and retrieval policy

Priority classes are safety invariants, active blockers, governing decisions,
and explicit required task/contract context, in that order. Within a priority
class, authority is `CANONICAL`, `VERIFIED`, `CANDIDATE`, then
`RUNTIME_DERIVED`, followed by deterministic relevance and recency. Explicit
seeds, task/workstream matches, owner identities, high-value relations, recent
verification, and a bounded second hop are selected deterministically. The
compiler never dumps the full graph and does not use embeddings or LLM guesses.

Relation priorities include `invariant`, `BLOCKED_BY`/`blocked_by`, `VERIFIED_BY`,
`IMPLEMENTS`, `SUPERSEDES`, `GOVERNED_BY`, `DEPENDS_ON`, `VALIDATES`, ownership,
workstream, evidence, PR, commit, and authored-link edges. Node degree alone is
never treated as importance.

Builder profiles preserve the operational boundaries: Builder 1 receives
relevant Builder 2 validation and Builder 4 observation contracts; Builder 2
receives the relevant Builder 4 seam; Builder 3 receives Memory/graph context;
Builder 4 receives relevant Builder 1/2 contracts. Profile metadata guides
selection but never supplies current status.

Superseded decisions remain provenance-available but are ranked as history;
explicitly selected history is labeled as such. `SUPERSEDES`, `RESOLVES`, and
`REPLACES` are not silently ignored.

## Human-readable sections

Markdown includes only non-empty useful sections: CURRENT OBJECTIVE, CURRENT
VERIFIED STATE, ACTIVE WORKSTREAM, RELEVANT DECISIONS, HARD INVARIANTS, OPEN
BLOCKERS, DEPENDENCIES, RECENT VERIFIED EVIDENCE, RELEVANT PR / COMMIT STATE,
OWNERSHIP BOUNDARIES, UNRESOLVED CEO DECISIONS, NEXT SAFE ACTION, PROVENANCE,
and WARNINGS when applicable.

Conflicts are preserved as `CONFLICTING EVIDENCE` with source, authority,
timestamps, and reason. Technical blockers and unresolved CEO decisions are
separate categories. No technical default is promoted into CEO policy.

## Freshness and runtime safety

Runtime handoffs use the existing policy: FRESH through 6 hours, AGING above 6
hours, and STALE above 24 hours. A stale handoff is labeled stale and is not
presented as current. `UNKNOWN`, `STALE`, and `CONFLICTING` remain visible.
When the materialized runtime graph is unavailable or fails validation, V3 uses
a canonical-only graph fallback, sets `graph_available=false`, withholds all
runtime handoffs/candidates/blockers, and explains the withholding in warnings.
If mandatory safety, blocker, or governing-decision material cannot fit the
requested entity/token budget, compilation fails closed.

Candidates keep `canonical=false` and `promotion_required=true`. The compiler
does not auto-promote candidates, resolve blockers, rewrite events, access or
unlock sealed 2425/2526 data, or change NO-BET/no-live-activation invariants.

## Token budgeting and truncation

The estimate is deterministic UTF-8 bytes divided by four, rounded up. Entities
are ranked before selection and added only while both `max_entity_count` and
`token_budget` remain satisfied. Safety invariants, active blockers, and
governing decisions are mandatory and outrank explicit task context and
optional history. If material is omitted, `truncated=true` and the pack reports
`candidate_entity_count`, `included_entity_count`, `omitted_entity_count`, and
metrics for truncated entities and budget utilization. The compiler never
silently exceeds the requested budget.

## Digests and cache

`context_digest` is calculated from semantic pack content, excluding
`generated_at`, the operational `cache_key`, and observation bookkeeping
(`first_observed_at`, `last_observed_at`, `observation_count`). A changed
decision, blocker, verification, request, graph relationship, or substantive
runtime state changes the digest. `cache_key` combines source Memory SHA, graph
digest, runtime digest, semantic request, compiler version, and the normalized
freshness reference time. Thus an unchanged semantic result can retain its
digest while freshness-reference changes cannot reuse an old cache entry.

## CLI

```text
python3 tools/memory.py context build --consumer builder-4 \
  --task "continue provider cascade implementation" --budget-tokens 6000 \
  --include-runtime --vault /path/to/Obsidian-Vault
python3 tools/memory.py context validate /path/to/Obsidian-Vault/_live/context/CTX.json
python3 tools/memory.py context inspect /path/to/Obsidian-Vault/_live/context/CTX.json
```

Build output is atomically written through a temporary sibling and validated
before promotion. If promotion fails, prior JSON/Markdown files are restored.
Resolved Vault and `_live/context` output paths inside or resolving into the
Memory checkout are rejected before any output operation.

## Secrets, rollback, and non-proofs

Known secret-bearing fields and token-like values are rejected. Safe presence
booleans such as `credentials_present=true` remain allowed. Context packs never
contain private chain-of-thought or hidden reasoning transcripts.

Rollback removes compiler integration and `_live/context` output only. It does
not alter canonical Memory, Semantic Graph V2, Source Observer evidence, or
historical events.

A context pack does **not** prove provider authority, a model edge, production
readiness, activation approval, or current truth when source evidence is stale.
Consumers must verify the supplied provenance and stop on safety conflicts.
