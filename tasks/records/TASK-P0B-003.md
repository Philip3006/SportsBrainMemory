---
id: TASK-P0B-003
type: task
title: Recovery Truth
status: completed
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-17T21:07:18+02:00
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
  - scripts/_health.sh
  - scripts/auto_heal_ai.py
  - src/monitoring/health_writer.py
  - src/monitoring/recovery_truth.py
  - src/notifications/health_push.py
  - tests/monitoring/test_recovery_truth.py
evidence:
  - EVD-P0B-003-PROD-001
verified_by:
  - VER-P0B-003-PROD-001
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
