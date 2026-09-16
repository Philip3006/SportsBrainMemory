# Memory Builder Bootstrap V4

Builder Bootstrap V4 is a deterministic, noncanonical delivery layer over
Context Compiler V3. It turns a dispatcher-supplied builder and task request
into a machine-readable JSON package and a human-readable Markdown handoff.
It does not launch a Builder, decide whether execution is safe, grant CEO
authorization, merge, deploy, or promote evidence.

## Supported Builder identities

The accepted identity is an explicit `BUILDER: N` value for N in 1 through 5.

| Builder | Governance role |
| --- | --- |
| 1 | Research / Shadow / Evidence Lifecycle |
| 2 | Independent Qualification / Authority |
| 3 | Memory / Context / Observability |
| 4 | Provider Cascade / Controlled Shadow Infrastructure |
| 5 | Autonomous Development / Night Shift Dispatcher Owner |

The governance role is a baseline label. Current operational status and any
current evidence-derived role are taken from Context Compiler V3 evidence; an
absent handoff is shown as `UNKNOWN / NO CURRENT HANDOFF EVIDENCE`.

## Package contract

Every package includes the request identity, embedded V3 context pack,
authoritative dependencies, required dependency status, missing or
non-authoritative dependencies, active blockers,
cross-Builder contracts, safety invariants, optional repository/path scope,
prohibited operations, verification requirements, unresolved CEO decisions,
stale/conflicting/unknown evidence, the exact source Memory SHA, the V3
semantic digest, the graph digest, and a bootstrap digest.

The bootstrap digest excludes generated time and other observation bookkeeping.
Identical semantic input therefore produces identical semantic and bootstrap
digests. Source SHA and graph provenance remain explicit and auditable.

Canonical and verified evidence outrank candidate and runtime-derived
evidence. Runtime candidates remain `canonical=false` and
`promotion_required=true`. Mandatory conflicts fail closed and require CEO
review; stale, unknown, missing, and non-mandatory conflicting evidence is
retained and surfaced through review flags. No automatic resolution or
canonical rewrite occurs.

Required dependencies are classified as `SATISFIED_AUTHORITATIVE`, `MISSING`,
or `PRESENT_NONAUTHORITATIVE`. Only canonical or verified matches enter the
authoritative dependency section. Candidate and runtime-derived matches are
preserved but raise `DEPENDENCY_AUTHORITY_MISSING` and never satisfy the
requirement.

## CLI

Build an in-memory package:

```text
python3 tools/memory.py builder-bootstrap build \
  --builder 5 \
  --task-id TASK-EXAMPLE \
  --task "Request dispatcher bootstrap context" \
  --workstream "Night Shift Dispatcher" \
  --json
```

Use `--vault /external/vault` to atomically write the JSON and Markdown
artifacts under `_live/builder-bootstrap`. The resolved
`vault/_live/builder-bootstrap` target is checked directly, including symlink
resolution, and must be outside the canonical Memory checkout. Existing
output is restored if validation or promotion fails.

```text
python3 tools/memory.py builder-bootstrap validate /external/vault/_live/builder-bootstrap/BOOT-....json
python3 tools/memory.py builder-bootstrap inspect /external/vault/_live/builder-bootstrap/BOOT-....json
```

Validation re-derives the evidence-facing sections from the embedded V3 pack
and preserved request provenance. Removing or altering a blocker, dependency
status, review flag, current Builder evidence, scope, or CEO decision is
rejected even if a caller recomputes the non-authenticating bootstrap digest.

The interface accepts future dispatcher metadata for task identity, scopes,
dependencies, prohibited operations, verification requirements, freshness,
token budget, and runtime inclusion. It remains a packaging boundary: it does
not launch Codex or any agent and does not implement dispatcher policy.

## Safety boundaries

Bootstrap generation does not modify canonical events/history, generated
canonical views, Research, SportsBrain production/runtime, Cloudflare, the
ledger, the LaunchAgent, or the 90-second cadence. NO-BET, no-live-activation,
and sealed 2425/2526 invariants are carried as required verification
boundaries. `_live/builder-bootstrap` is an external noncanonical projection.
Future Builder numbers require an explicit governance update before they become
valid identities; unsupported numbers currently fail closed.
