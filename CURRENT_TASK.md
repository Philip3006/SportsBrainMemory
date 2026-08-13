---
type: "builder-task"
tier: "hot"
status: "current"
task_id: "TASK-P0A-011"
workstream: "P0-A"
last_updated: "2026-08-14T01:31:00+02:00"
freshness_class: "runtime-sensitive"
invariants:
  - QUEUE-001
  - QUEUE-002
  - QUEUE-003
  - QUEUE-006
  - QUEUE-007
  - QUEUE-008
  - BET-004
  - BET-005
  - BET-019
  - BET-020
  - REL-009
findings:
  - FND-20260814-001
  - FND-20260814-003
  - FND-20260814-031
required_context:
  - workstreams/P0-A.md
  - invariants/QUEUE_DATA.md#QUEUE-001
  - invariants/QUEUE_DATA.md#QUEUE-002
  - invariants/QUEUE_DATA.md#QUEUE-003
  - invariants/QUEUE_DATA.md#QUEUE-006
  - invariants/QUEUE_DATA.md#QUEUE-007
  - invariants/QUEUE_DATA.md#QUEUE-008
  - invariants/BETTING_RISK.md#BET-004
  - invariants/BETTING_RISK.md#BET-005
  - invariants/BETTING_RISK.md#BET-019
  - invariants/BETTING_RISK.md#BET-020
  - invariants/RELEASE_MONITORING.md#REL-009
  - architecture/DATA_AND_PERSISTENCE.md
---
# TASK-P0A-011 — Queue Identity + Final Recommendation Actionability

## Mission

Close the final three verified P0-A blockers on PR #10. Do not merge or start P0-B/C/D.

## Reviewed state

- CEO-reviewed PR head: `a90be4c492b736b348dba9b3847c3b1d9823031a`
- exact-head CI: GREEN (`31753905213`)
- runtime/data main moves independently
- builder reports local consumer 48/48, Playwright 12/12, Python 1528/1528 green
- production remains unchanged/uncredited until merge.

## 1. FND-20260814-001 — staged-diff command errors fail closed

In `_durable_push()` handle `git diff --cached --quiet` explicitly:
- rc 0 = no staged changes;
- rc 1 = staged changes;
- rc >1 = Git verification error → return False / no ACK.

Add deterministic rc>1 test. Preserve all other newly-correct Git error handling.

## 2. FND-20260814-003 — cancellation queue must have exact-intent ACK semantics

Current clear-all `DELETE /cancel_requests` is unsafe.

Required invariants:
- ACK/deletion may remove only the exact cancellation intent whose durable outcome is proven;
- an unresolved/not-found cancel remains retryable;
- a cancellation for a placement fetched in the same run cannot be lost;
- a new cancellation arriving after consumer GET cannot be erased by ACK of older requests;
- push failure leaves affected cancel intents queued;
- ACK failure retry is idempotent;
- placement and cancellation may share one durable push if the final remote state for both is proven before either ACK.

Preferred implementation: stable cancel request IDs + per-item DELETE endpoint analogous to pending bets. An equally safe transactional design is acceptable, but clear-all ACK is not.

Deterministic tests must include:
1. same bet has pending placement + cancel request in the same run;
2. two cancel requests where one succeeds and one is unresolved/retryable;
3. newly/concurrently queued cancel survives ACK of an older one (test Worker/per-item deletion semantics);
4. cancel push failure → no cancel ACK;
5. cancel ACK failure → retry idempotent;
6. mixed placement+cancel ordering proves exact corresponding durability before ACK, not merely counts of pushes/deletes.

Expected files may now include `cloudflare/worker.js` and Node Worker tests because cancellation identity lives at the queue boundary.

## 3. FND-20260814-031 — no recommendation→Manual downgrade

CEO contract:
- recommendation/model-tip surfaces may place a bet only when backed by a fully actionable canonical Value signal;
- failure/missing canonical actionability makes the recommendation informational/non-actionable;
- changing hidden `source` to `manual` is not an acceptable bypass.

Required:
- `sigCard`: missing/stale current data or otherwise non-actionable Value recommendation must not render a Manual fallback bet button;
- `predCard` / model-tip / all-odds recommendation buttons with no canonical signal must not directly open a Manual bet flow;
- do not build a new manual-entry feature in this task;
- if an already-existing genuinely separate user-selected manual-entry UI exists, preserve it; otherwise no Manual path is preferable to recommendation auto-downgrade;
- update Playwright/JS tests so legacy, missing-current-data and model-tip noncanonical recommendation surfaces prove no bet action;
- canonical actionable Value submit remains green.

## Forbidden scope

No P0-B monitoring redesign, P0-C privacy, P0-D governance/model rollout, Model Integrity, Wave 3D, unrelated cleanup or feature work.

## Git safety

Re-fetch remote. Isolated clean worktree. Preserve original dirty worktree. No force push, destructive reset, history rewrite or merge.

## Required gates

- focused new durability/cancellation identity tests;
- Worker cancellation endpoint tests if Worker changes;
- full consumer suite;
- full relevant Python suite;
- complete frontend Playwright suite;
- Node Worker contract tests;
- Ruff regression;
- push same PR branch;
- exact new-head CI green.

If exact new-head CI is not complete, report WAITING, not COMPLETE.

## Report

Return only Status; task/finding IDs; exact head; runtime-data main; changed files; evidence for all three findings; exact test counts; exact new-head CI; residual risks; merge recommendation; STOP.
