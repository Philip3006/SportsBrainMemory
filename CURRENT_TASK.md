---
type: "builder-task"
tier: "hot"
status: "current"
task_id: "TASK-P0A-010"
workstream: "P0-A"
last_updated: "2026-08-14T01:06:00+02:00"
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
  - BET-003
  - BET-004
  - BET-005
  - BET-019
  - BET-020
  - REL-009
  - UX-008
findings:
  - FND-20260814-001
  - FND-20260814-002
  - FND-20260814-003
  - FND-20260814-004
  - FND-20260814-030
  - FND-20260814-031
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
  - invariants/BETTING_RISK.md#BET-003
  - invariants/BETTING_RISK.md#BET-004
  - invariants/BETTING_RISK.md#BET-005
  - invariants/BETTING_RISK.md#BET-019
  - invariants/BETTING_RISK.md#BET-020
  - invariants/RELEASE_MONITORING.md#REL-009
  - architecture/DATA_AND_PERSISTENCE.md
---
# TASK-P0A-010 — Final Closure Correction

## Mission

Close all six remaining P0-A blockers on existing PR #10. Do not merge or start downstream work.

## Reviewed state

- PR head: `08b63f8a14fb64021f79277e7069e9aee11327f9`
- exact-head CI: GREEN (`31752148258`)
- full frontend smoke is not green
- runtime/data main moves independently.

## Required closure

### FND-20260814-001 — fail closed on Git durability-command errors
- `git add` nonzero → failure/no accepted ACK.
- current `fetch origin main` required before containment claim.
- merge-base: 0=contained, 1=not-contained push path, >1=verification failure.
- failed pull/rebase cannot be ignored before push.
- deterministic add/fetch/merge-base/local-ahead/contained/push/ACK-retry tests.

### FND-20260814-002 — correct decision semantics
- `bankroll is None` / lookup failure → RETRY.
- finite authoritative `bankroll <= 0` → permanent risk REJECT.
- open-count exception remains RETRY.
- tests for None/zero/negative/positive.

### FND-20260814-003 — prove mixed cancellation + placement
Use real orchestration/call-order tests for one run containing both mutation types, failure ordering and ACK-retry idempotency. Do not redesign if current ordering is safe.

### FND-20260814-004 — exactly one submit
- assert exactly one `/pending_bets` request (`== 1`);
- assert POST;
- preserve source=value, signal_id, current odds, <=5% stake and JS assertions;
- no conditional pass.

### FND-20260814-030 — exact consumer source
- exact string `value` or `manual` only;
- no default, trim or case normalization;
- malformed/missing source permanent REJECT;
- deterministic consumer tests.

### FND-20260814-031 — legacy recommendation stays non-actionable
CEO contract: a legacy/incomplete recommendation that fails canonical Value actionability must not automatically become a Manual action on that recommendation card. Manual betting remains only via a clearly explicit separate manual-entry flow.
- smallest safe UI change;
- do not weaken/delete `test_p0a_legacy_signal_cannot_open_value_modal`;
- preserve explicit Manual flow elsewhere;
- complete `tests/frontend/test_pwa_smoke.py` must be green.

## Expected files

- `scripts/consume_pending_bets.py`
- `tests/scripts/test_consume_pending_bets.py`
- `tests/frontend/test_pwa_smoke.py`
- `docs/js/views.js`
- `docs/js/bets.js` only if directly required.

## Forbidden scope

No P0-B/C/D, Model Integrity, Wave 3D, privacy migration, monitoring redesign or unrelated cleanup.

## Git safety

Re-fetch remote first. Use isolated clean worktree. Preserve original dirty worktree. No force push, destructive reset/history rewrite, or merge.

## Required gates

Focused durability/consumer tests; full relevant Python suite; **complete frontend Playwright suite**; Node Worker contract; Ruff; push same PR branch; exact new-head CI green.

If CI is not completed, report WAITING, not COMPLETE.

## Report

Status; task/findings; exact head; current runtime-data main; changed files; evidence for six findings; exact test counts including full Playwright; exact new-head CI; residual risk; merge recommendation; STOP.
