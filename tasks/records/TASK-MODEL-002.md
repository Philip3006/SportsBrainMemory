---
id: TASK-MODEL-002
type: task
title: Model Promotion Gate
status: draft
canonical: true
tier: warm
workstream: MODEL_INTEGRITY
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T13:04:00+02:00
freshness_class: release-bound
budget_class: complex
findings:
  - FND-20260814-016
  - FND-20260814-021
  - FND-20260814-022
invariants:
  - MOD-003
  - MOD-004
  - GOV-006
depends_on:
  - TASK-MEAS-001
source_paths:
  - scripts/tennis_lgbm_retrain.py
  - src/tennis/
  - models/
  - .github/workflows/tennis_lgbm_retrain.yml
---
# TASK-MODEL-002 — Model Promotion Gate

## Mission

Separate retraining from promotion and require parity, evaluation, calibration and provenance evidence before production artifact activation.

## Primary files / boundaries

- `scripts/tennis_lgbm_retrain.py`
- `src/tennis/`
- `models/`
- `.github/workflows/tennis_lgbm_retrain.yml`

## Adjacent read-only inspection

- `measurement reports`
- `tests/tennis/`

## Forbidden scope

- automatic promotion solely because retrain succeeded
- manual all_live bypass

## Deterministic gates

- retrain creates candidate only
- promotion requires chronological/walk-forward evaluation
- feature/model/schema compatibility gate
- calibration/measurement evidence referenced
- degradation keeps prior artifact active
- no approval => shadow

## Production verification

- production predictor loads only approved artifact with approval/model/data/schema provenance

## Rollback

Rollback pointer/manifest to previously approved artifact; candidate remains retained for audit.

## STOP conditions

- MODEL-001 parity or MEAS-001 population not closed
- current production artifact identity cannot be proven

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.

## Related

- [[domains/MODEL_RESEARCH]]
- [[domains/TENNIS]]
- [[models/MOD-TENNIS-LGBM]]
- [[tasks/records/TASK-MEAS-001]]
- [[decisions/records/DEC-0029]]
