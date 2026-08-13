---
type: "builder-task"
tier: "hot"
status: "current"
task_id: "TASK-P0A-009"
workstream: "P0-A"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "runtime-sensitive"
invariants:
  - QUEUE-001
  - QUEUE-002
  - QUEUE-003
  - QUEUE-004
  - QUEUE-005
  - QUEUE-006
  - QUEUE-007
  - QUEUE-008
  - REL-009
  - UX-008
findings:
  - FND-20260814-001
  - FND-20260814-002
  - FND-20260814-003
  - FND-20260814-004
required_context:
  - workstreams/P0-A.md
  - invariants/QUEUE_DATA.md#QUEUE-001
  - invariants/QUEUE_DATA.md#QUEUE-002
  - invariants/QUEUE_DATA.md#QUEUE-003
  - invariants/QUEUE_DATA.md#QUEUE-004
  - invariants/QUEUE_DATA.md#QUEUE-005
  - invariants/QUEUE_DATA.md#QUEUE-006
  - invariants/QUEUE_DATA.md#QUEUE-007
  - invariants/QUEUE_DATA.md#QUEUE-008
  - invariants/RELEASE_MONITORING.md#REL-009
  - invariants/SECURITY_GOVERNANCE.md#UX-008
  - architecture/DATA_AND_PERSISTENCE.md
---
# TASK-P0A-009 — Final P0-A Closure

## Mission

Close the final four verified P0-A blockers on the existing PR #10 without expanding into P0-B/C/D.

## Current reviewed state

- Reviewed PR head: `f2f7831fdaead6667b6eb53c0021a7bc0377eebf`
- Exact-head CI is green, but semantic approval is withheld.
- Runtime/data main moves frequently; safely re-fetch/sync at execution time.

## Required findings to close

1. **FND-20260814-001 — Remote durability**
   - clean staging area is not proof of `origin/main` durability.
   - accepted queue ACK requires remote containment/exact durable-state proof.
   - test local-ahead clean-tree retry, remote-contained retry, push failure, ACK failure idempotency.

2. **FND-20260814-002 — ACCEPT / REJECT / RETRY**
   - explicit decision semantics.
   - authoritative bankroll/open-state outage is RETRY.
   - RETRY is never ACKed.

3. **FND-20260814-003 — Cancellation durability**
   - cancellation uses the same durable mutation boundary.
   - push failure leaves cancel request queued.
   - ACK failure retries idempotently.
   - mixed placement+cancellation cannot ACK before durability.

4. **FND-20260814-004 — mandatory browser submit**
   - valid fixture must enable confirm.
   - click must happen.
   - exactly one `/pending_bets` request captured.
   - assert `source=value`, canonical `signal_id`, `odds=current_odds`, stake≤5%, no JS errors.
   - no conditional pass if submit/request does not occur.

## Primary expected files

- `scripts/consume_pending_bets.py`
- `tests/scripts/test_consume_pending_bets.py`
- `tests/frontend/test_pwa_smoke.py`

Inspect direct callers/workflow only as necessary.

## Forbidden scope

Do not start:
- P0-B monitoring redesign
- P0-C privacy migration
- P0-D governance/model rollout
- Model Integrity
- Wave 3D
- unrelated cleanup.

## Git safety

- isolated clean worktree
- preserve original dirty worktree
- no force push
- no destructive reset
- no history rewrite
- do not merge.

## Required gates

- focused new durability tests
- full relevant Python suite
- actual Playwright browser tests
- Node Worker contract tests
- Ruff regression
- exact new PR-head CI after push.

## Report

Return only:
- Status
- task/invariant IDs
- branch + exact head
- current main/runtime-data SHA
- changed files
- evidence for Findings 001–004
- exact test counts
- exact PR-head CI
- remaining risks
- merge recommendation
- STOP; do not merge.
