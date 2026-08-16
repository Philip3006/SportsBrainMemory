---
id: TASK-P0B-002
type: task
title: Schedule & Window Truth
status: draft
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T13:04:00+02:00
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
