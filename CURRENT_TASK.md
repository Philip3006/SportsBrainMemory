---
type: "builder-task"
tier: "hot"
status: "current"
task_id: "TASK-P0A-012"
workstream: "P0-A"
last_updated: "2026-08-14T01:57:00+02:00"
freshness_class: "runtime-sensitive"
invariants:
  - QUEUE-006
  - QUEUE-007
  - QUEUE-008
  - BET-004
  - BET-005
  - BET-019
  - BET-020
  - REL-009
findings:
  - FND-20260814-003
  - FND-20260814-031
required_context:
  - workstreams/P0-A.md
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
# TASK-P0A-012 — Final Queue Atomicity + Compact-Mode Closure

## Mission

Close the final two verified P0-A merge blockers on existing PR #10. Do not merge or start downstream work.

## Reviewed state

- CEO-reviewed PR head: `fd52d1b858dc08caae355de7ed9fab3a36ed47a9`
- exact-head CI: GREEN (`31755460760`)
- FND-001 is now resolved.
- two blockers remain: FND-003 and FND-031.

## FND-20260814-003 — cancellation storage must be truly per-intent

Current stable IDs are correct, but `DELETE /cancel_requests/{id}` still performs whole-array KV read-modify-write and can overwrite a concurrently queued cancellation.

Required:
- one cancellation ACK must not rewrite/drop unrelated concurrent intents;
- prefer one KV key per cancel ID (or a truly atomic equivalent);
- exact per-ID delete;
- remove/disable normal clear-all `DELETE /cancel_requests`;
- preserve unresolved retry, durable-push-before-ACK and ACK-retry idempotency;
- tests must prove a concurrent/new request survives deletion of an older ID.

Do not broaden into general queue redesign beyond what is required for this cancellation safety invariant.


### CEO correction after review of `5aeae738b`

The per-intent storage design is accepted, but one final namespace defect remains:
- `_cancelIntentPrefix(DEFAULT_USER)` must not be the broad `cancel_intent:` prefix because it also matches `cancel_intent:{other_user}:...` keys.
- namespace the default user explicitly (`cancel_intent:philip:` or equivalent stable canonical user namespace);
- add a Worker test proving default-user listing cannot see another user's cancel intent.

This is the only newly required correction. Do not reopen already-closed compact-mode work.

## FND-20260814-031 — compact mode must not bypass actionability

Current normal card/model-tip paths are fixed. Compact mode still creates a clickable bet control and `source=manual` when `_cIsValueActionable` is false.

Required:
- compact recommendation row has a bet action only when fully canonical/actionable Value;
- non-actionable compact rows are informational, no modal opener and no Manual fallback;
- add focused regression for non-actionable compact mode;
- preserve canonical actionable Value submit.

## Expected files

Likely:
- `cloudflare/worker.js`
- Worker tests
- `scripts/consume_pending_bets.py` only if cancellation retrieval contract changes
- `docs/js/views.js`
- frontend/JS tests

## Forbidden scope

No P0-B/C/D, Model Integrity, Wave 3D, privacy/monitoring redesign or unrelated cleanup.

## Git safety

Re-fetch current state. Use isolated clean worktree. No force push, destructive reset, history rewrite or merge.

## Required gates

Focused cancellation storage tests; consumer tests if touched; Node Worker contract; compact-mode browser/JS regression; full Playwright; full relevant Python; Ruff; push same PR branch; exact new-head CI green.

If exact new-head CI is not complete, report WAITING.

## Report

Very short: status, exact head, tests, CI, residual blockers. STOP; do not merge.
