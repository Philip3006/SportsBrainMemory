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
reference report. A canonical-only graph can be built on demand under
`views/graph/`; that directory is not a committed current-state snapshot.
The current operational graph is generated in the Obsidian Vault at
`_live/graph/`.

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

The graph has one live writer: the Semantic Graph engine. It reads canonical
Memory plus the current `_live` observer outputs and writes only Vault
`_live/graph/`. It never writes generated runtime files into the Memory Git
checkout, so the next fast-forward sync cannot be blocked by graph output.

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

Builder identities 1–5 are supported. The graph may show the governed identity
of a Builder without asserting a current workstream. Current role, branch,
head, PR, status, blocker, tests/CI, observed time, and freshness come only
from the latest valid explicit handoff when runtime evidence is included. The
Source Observer's FRESH (≤6h), AGING (>6h), and STALE (>24h) policy remains the
authority for operational freshness; a stale handoff is visibly stale.

## Determinism, health, and rollback

`GRAPH_MANIFEST.json` contains the semantic digest, canonical input digests,
entity/edge registry, namespaces, runtime inclusion flag, selected projection
location, and health metrics. `generated_at` and performance measurements are
excluded from the semantic digest. Rebuilding the same source snapshot is
byte-stable and idempotent.

Runtime rebuilds are atomic: output is rendered into a temporary sibling of
`_live/graph/`, validated completely, and promoted with same-filesystem
renames. A failed build leaves the previous valid graph in place and writes a
visible `_live/SEMANTIC_GRAPH_STATUS.json` failure record. Canonical Memory is
untouched in both cases.

Health reports baseline canonical nodes with no materialized Graph V2 edges
against the generated graph: entity/node count, typed edge count, isolated
nodes and percentage, connected components, largest component, unresolved
references, edge relation counts, node types, and top hubs.

Commands:

```text
python3 tools/memory.py graph build
python3 tools/memory.py graph build --vault /path/to/Obsidian-Vault
python3 tools/memory.py graph validate
python3 tools/memory.py graph validate --vault /path/to/Obsidian-Vault
python3 tools/memory.py graph health --vault /path/to/Obsidian-Vault
```

The existing 90-second synchronizer keeps its cadence and fast-forward-only
rules. After canonical Memory fast-forward and Vault canonical sync, the
current `_live` observer outputs are projected into `_live/graph/`, validated,
and then surfaced in live status. Source Observer remains the upstream
runtime evidence producer; the graph does not create or promote evidence.

The canonical-only projection rolls back by removing its selected output root.
The live projection rolls back to the previous valid graph automatically when
generation or validation fails. Canonical Memory remains unchanged in either
case.
