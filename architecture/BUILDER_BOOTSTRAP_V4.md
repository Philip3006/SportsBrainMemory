# Memory Builder Bootstrap V4

Builder Bootstrap V4 is a deterministic, noncanonical delivery layer over
Context Compiler V3. It turns a dispatcher-supplied builder and task request
into a machine-readable JSON package and a human-readable Markdown handoff.
It does not launch a Builder, decide whether execution is safe, grant CEO
authorization, merge, deploy, or promote evidence.

## Supported Builder identities

The accepted identity is an explicit `BUILDER: N` value for N in 1 through 7.

| Builder | Governance role |
| --- | --- |
| 1 | Research / Shadow / Evidence Lifecycle |
| 2 | Independent Qualification / Authority |
| 3 | Memory / Context / Observability |
| 4 | Provider Cascade / Controlled Shadow Infrastructure |
| 5 | Live App Delivery / PWA Integration |
| 6 | Bug / Regression |
| 7 | Runtime Reliability / Product Observability |

The governance role is a baseline label. Current operational status and any
current evidence-derived role are taken from Context Compiler V3 evidence; an
absent handoff is shown as `UNKNOWN / NO CURRENT HANDOFF EVIDENCE`.

## Package contract

Every package includes the request identity, embedded V3 context pack,
authoritative dependencies, missing dependencies, active blockers,
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

## CLI

Build an in-memory package:

```text
python3 tools/memory.py builder-bootstrap build \
  --builder 7 \
  --task-id TASK-EXAMPLE \
  --task "Inspect runtime reliability context" \
  --workstream "Runtime Reliability" \
  --json
```

Use `--vault /external/vault` to atomically write the JSON and Markdown
artifacts under `_live/builder-bootstrap`. The output must be outside the
canonical Memory checkout. Existing output is restored if validation or
promotion fails.

```text
python3 tools/memory.py builder-bootstrap validate /external/vault/_live/builder-bootstrap/BOOT-....json
python3 tools/memory.py builder-bootstrap inspect /external/vault/_live/builder-bootstrap/BOOT-....json
```

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
