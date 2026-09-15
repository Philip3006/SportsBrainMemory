---
type: architecture
status: active
last_updated: 2026-09-16T00:00:00Z
freshness_class: stable
---
# Memory Semantic Link Graph V2

The Semantic Link Graph V2 is a deterministic, noncanonical projection of
SportsBrainMemory. It materializes a typed entity registry, explicit relations,
Obsidian links, typed backlinks, MOCs, health metrics, and an unresolved
reference report under `views/graph/`.

## Truth boundary

Canonical events, decisions, findings, evidence, verifications, tasks,
workstreams, provider/model/dataset records, invariants, and history are
read-only inputs. The graph builder never writes `events/records/`, never
promotes a candidate, never resolves a blocker, and never changes the Vault,
runtime, LaunchAgent, Cloudflare, ledger, Research, or sealed data.

When `--vault` is supplied, `_live/SOURCE_OBSERVER.json`,
`SOURCE_CANDIDATES.json`, `BUILDER_HANDOFFS.json`, and `BLOCKERS.json` are read
as `RUNTIME_DERIVED` evidence. Runtime entities always retain
`canonical: false`; source candidates retain `promotion_required: true` in
their evidence metadata. Missing handoffs do not create operational status.

## Entity registry and relations

Every entity has a stable `(namespace, stable_id)` key. The required
namespaces are `EVENT`, `DECISION`, `EVIDENCE`, `FINDING`, `VERIFICATION`,
`TASK`, `WORKSTREAM`, `BUILDER`, `PROVIDER`, `MODEL`, `DATASET`, `PR`,
`COMMIT`, `INVARIANT`, `BLOCKER`, `REPOSITORY`, and `DOMAIN`; state, component,
job, writer, architecture, and metadata records are also represented where
they have authoritative source records.

Relations come only from explicit structured fields, explicit PR/commit
references in structured evidence arrays, or authored wikilinks. Examples are
`source_pr`, `source_commit`, `evidence`, `finding`, `decision`, `verification`,
`workstream`, `builder`, `provider`, `model`, `dataset`, `invariant`,
`blocked_by`, `blocks`, `supersedes`, and `explicit_link`. Keyword matching is
not a relation source.

Generated entity pages are the only graph link targets. A typed link is emitted
only after its target is in the registry, so a missing target appears in
`UNRESOLVED_REFERENCES.json` rather than becoming a silent broken wikilink.
Backlinks are derived from the outgoing typed edge set and are not separately
authored.

## Builder governance

Builder identities 1–4 are supported. The graph may show the governed identity
of a Builder without asserting a current workstream. Current role, branch,
head, PR, status, blocker, tests/CI, observed time, and freshness come only
from the latest valid explicit handoff when runtime evidence is included. The
Source Observer's FRESH (≤6h), AGING (>6h), and STALE (>24h) policy remains the
authority for operational freshness; a stale handoff is visibly stale.

## Determinism, health, and rollback

`GRAPH_MANIFEST.json` contains the semantic digest, canonical input digests,
entity/edge registry, namespaces, runtime inclusion flag, and health metrics.
`generated_at` and performance measurements are excluded from the semantic
digest. Rebuilding the same source snapshot is byte-stable and idempotent.

Health reports baseline canonical nodes with no materialized Graph V2 edges
against the generated graph: entity/node count, typed edge count, isolated
nodes and percentage, connected components, largest component, unresolved
references, edge relation counts, node types, and top hubs.

Commands:

```text
python3 tools/memory.py graph build --vault /path/to/Obsidian-Vault
python3 tools/memory.py graph validate
python3 tools/memory.py graph health
```

The projection rolls back by removing `views/graph/` or reverting this graph
change. Canonical Memory remains unchanged in either case.
