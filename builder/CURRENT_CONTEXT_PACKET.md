# SportsBrain V1 Context Packet

Task: TASK-P0B-003
Task status: approved
Budget class: standard

## Governance

Use only this scoped task. External current source/runtime evidence outranks stale Memory. STOP on missing architecture decision or stop condition.

## Task record

---
id: TASK-P0B-003
type: task
title: Recovery Truth
status: approved
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-17T17:00:00+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-007
invariants:
  - MON-008
  - OPS-006
depends_on:
  - TASK-P0B-002
source_paths:
  - scripts/cloud_healer.py
  - scripts/auto_heal_ai.py
  - src/monitoring/aggregate_health.py
  - tests/monitoring/
---
# TASK-P0B-003 — Recovery Truth

## Mission

Make recovery capability fail closed and require post-dispatch execution/output evidence before declaring recovered.

## Primary files / boundaries

- `scripts/cloud_healer.py`
- `scripts/auto_heal_ai.py`
- `src/monitoring/aggregate_health.py`
- `tests/monitoring/`

## Adjacent read-only inspection

- `.github/workflows/cloud_healer.yml`
- `.github/workflows/*.disabled`
- `.github/workflows/`

## Forbidden scope

- AI source mutation policy implementation
- P0-C
- model promotion

## Deterministic gates

- inactive/nonexistent workflow target => RECOVERY_UNAVAILABLE
- dispatch alone never equals RECOVERED
- fresh execution + output evidence required
- unsupported action fails closed

## Production verification

- recovery dashboard distinguishes requested/dispatched/observed/verified/recovered

## Rollback

Restore prior recovery mapping while preserving fail-closed unknown target behavior.

## STOP conditions

- active recovery target identity cannot be established
- recovery requires source mutation to succeed

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.


## Required invariants

- MON-008
- OPS-006

## FND-20260814-007

---
type: "finding"
tier: "warm"
id: "FND-20260814-007"
status: "open"
severity: "P1"
domain: "monitoring"
workstream: "P0-B"
invariants:
  - MON-011
  - GOV-003
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-007 — Recovery maps reference inactive/nonexistent workflow filenames

## Problem / evidence

Healer mappings include workflow names for which current repo contains only `.disabled` variants.

## Failure / impact

Recovery can claim action while target cannot execute.

## Required closure

Verified recovery registry; unavailable target emits RECOVERY_UNAVAILABLE.

## Related invariants

- `MON-011`
- `GOV-003`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## TASK-P0B-002

---
id: TASK-P0B-002
type: task
title: Schedule & Window Truth
status: completed
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-17T17:00:00+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-006
  - FND-20260814-008
  - FND-20260814-009
  - FND-20260814-010
invariants:
  - MON-002
  - MON-012
depends_on:
  - TASK-P0B-001
source_paths:
  - src/monitoring/health_writer.py
  - src/monitoring/aggregate_health.py
  - tests/monitoring/test_health_truth.py
evidence:
  - EVD-P0B-002-PROD-001
verified_by:
  - VER-P0B-002-PROD-001
---
# TASK-P0B-002 — Schedule & Window Truth

## Mission

Replace global fixed-interval stale logic with machine-readable JobExpectation semantics for cron sets, windows, intervals and event-with-fallback jobs.

## Primary files / boundaries

- `src/monitoring/health_writer.py`
- `src/monitoring/aggregate_health.py`
- `tests/monitoring/test_health_truth.py`

## Adjacent read-only inspection

- `.github/workflows/tennis*.yml`
- `.github/workflows/*bundesliga2*.yml`
- `.github/workflows/*pending*.yml`
- `launchd/`

## Forbidden scope

- recovery dispatch logic
- privacy
- financial durability

## Deterministic gates

- Tennis scan exact cron-set expectation
- Tennis retrain daily 05 UTC expectation
- BL2 live push off-window => not_expected
- BL2 closing odds weekly points do not false-stale
- event-driven consumer models event + 30m fallback
- odds_refresh covered

## Production verification

- off-window jobs publish inactive/not_expected, never false stale
- schedule view matches active workflow source

## Rollback

Revert expectation registry and aggregate evaluation as one change.

## STOP conditions

- active workflow schedule cannot be reconciled read-only
- same logical job has unresolved conflicting active schedulers

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.


## External source scope

- `scripts/cloud_healer.py`
- `scripts/auto_heal_ai.py`
- `src/monitoring/aggregate_health.py`
- `tests/monitoring/`
