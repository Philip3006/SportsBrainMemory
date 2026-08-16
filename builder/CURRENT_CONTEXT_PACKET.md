# SportsBrain V1 Context Packet

Task: TASK-P0B-002
Task status: approved
Budget class: standard

## Governance

Use only this scoped task. External current source/runtime evidence outranks stale Memory. STOP on missing architecture decision or stop condition.

## Task record

---
id: TASK-P0B-002
type: task
title: Schedule & Window Truth
status: approved
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T23:00:00+02:00
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


## Required invariants

- MON-002
- MON-012

## FND-20260814-006

---
type: "finding"
tier: "warm"
id: "FND-20260814-006"
status: "open"
severity: "P1"
domain: "monitoring"
workstream: "P0-B"
invariants:
  - MON-002
  - MON-012
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-006 — Health cadence model has drifted from actual workflow schedules

## Problem / evidence

Examples include Tennis Scan expected 4x/day while active workflow runs 8x/day, and Tennis retrain expected weekly while active workflow runs daily.

## Failure / impact

False stale/healthy classifications and recurring configuration drift.

## Required closure

Introduce machine-readable JobExpectation with trigger/window semantics and workflow parity tests.

## Related invariants

- `MON-002`
- `MON-012`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## FND-20260814-008

---
type: "finding"
tier: "warm"
id: "FND-20260814-008"
status: "open"
severity: "P1"
domain: "monitoring"
workstream: "P0-B"
invariants:
  - MON-002
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-008 — Windowed Bundesliga2 jobs are modeled as globally periodic

## Problem / evidence

BL2 live/closing jobs are active only in specific weekly windows but current stale logic uses global intervals.

## Failure / impact

Correctly inactive jobs appear stale for most of the week.

## Required closure

Model expected windows and use inactive/not_expected outside them.

## Related invariants

- `MON-002`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## FND-20260814-009

---
type: "finding"
tier: "warm"
id: "FND-20260814-009"
status: "open"
severity: "P1"
domain: "monitoring"
workstream: "P0-B"
invariants:
  - MON-002
  - OPS-006
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-009 — Event-driven consumer is modeled as a fixed 2-minute job

## Problem / evidence

Primary consume trigger is Worker event dispatch with a 30-minute GitHub fallback.

## Failure / impact

No-event periods can be misclassified as job failure.

## Required closure

Model event_with_fallback trigger semantics.

## Related invariants

- `MON-002`
- `OPS-006`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## FND-20260814-010

---
type: "finding"
tier: "warm"
id: "FND-20260814-010"
status: "open"
severity: "P1"
domain: "monitoring"
workstream: "P0-B"
invariants:
  - MON-005
  - OPS-006
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-010 — Odds refresher execution is missing from aggregate health coverage

## Problem / evidence

A local launchd odds-refresh process is a core actionability dependency but is not a dedicated aggregate-health job.

## Failure / impact

Odds freshness infrastructure can fail without explicit process health signal.

## Required closure

Add execution-plane visibility; semantic odds trust remains Wave3D.

## Related invariants

- `MON-005`
- `OPS-006`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## TASK-P0B-001

---
id: TASK-P0B-001
type: task
title: Execution Truth
status: completed
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T23:00:00+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-005
invariants:
  - MON-001
  - MON-011
  - OPS-006
source_paths:
  - src/monitoring/health_writer.py
  - src/monitoring/aggregate_health.py
  - tests/monitoring/test_health_truth.py
evidence:
  - EVD-P0B-001-PROD-001
verified_by:
  - VER-P0B-001-PROD-001
---
# TASK-P0B-001 — Execution Truth

## Mission

Make execution status derive from execution evidence so `exit_code != 0` can never publish success.

## Primary files / boundaries

- `src/monitoring/health_writer.py`
- `src/monitoring/aggregate_health.py`
- `tests/monitoring/test_health_truth.py`

## Adjacent read-only inspection

- `.github/workflows/*health*`
- `.github/workflows/*retrain*`
- `.github/workflows/*closing*`

## Forbidden scope

- schedule redesign
- privacy migration
- writer governance
- model changes

## Deterministic gates

- non-zero exit cannot serialize execution success
- malformed/unknown execution fails closed
- existing valid success/degraded cases remain deterministic
- focused + full monitoring tests

## Production verification

- published health contains no `ok + exit_code!=0` state
- exact source SHA and runtime-data SHA reported separately

## Rollback

Revert execution-truth helper/writer changes together; do not roll back unrelated runtime data.

## STOP conditions

- runner context cannot supply truthful exit evidence
- required workflow semantics differ materially from scoped model

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.


## External source scope

- `src/monitoring/health_writer.py`
- `src/monitoring/aggregate_health.py`
- `tests/monitoring/test_health_truth.py`
