---
id: TASK-MODEL-001
type: task
title: Tennis Train / Live Feature Parity
status: draft
canonical: true
graph_domain: model-research
graph_role: operational
tier: warm
workstream: MODEL_INTEGRITY
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T13:04:00+02:00
freshness_class: release-bound
budget_class: complex
findings:
  - FND-20260814-021
invariants:
  - MOD-001
  - MOD-002
  - DATA-011
depends_on:
  - TASK-P0D-003
source_paths:
  - src/tennis/
  - scripts/tennis_lgbm_retrain.py
  - tests/tennis/
---
# TASK-MODEL-001 — Tennis Train / Live Feature Parity

## Mission

Prove and enforce semantic parity between Tennis LGBM training/backtest RollingState/features and live serving before any promotion decision.

## Primary files / boundaries

- `src/tennis/`
- `scripts/tennis_lgbm_retrain.py`
- `tests/tennis/`

## Adjacent read-only inspection

- `model artifacts`
- `historical datasets`

## Forbidden scope

- promotion of new model
- measurement score claims before parity

## Deterministic gates

- same fixture sequence yields equivalent train/live features
- RollingState initialization/update ordering parity
- feature schema/version asserted
- live mismatch fails closed or shadow

## Production verification

- production serving records model + feature schema provenance

## Rollback

Keep current approved artifact and serving path active; new parity code can remain shadow-only.

## STOP conditions

- live feature state source cannot be reconstructed
- training data semantics are ambiguous

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.

## Related

- [[domains/TENNIS]]
- [[domains/MODEL_RESEARCH]]
- [[models/MOD-TENNIS-LGBM]]
- [[components/CMP-TENNIS-MODEL]]
- [[workstreams/MODEL_INTEGRITY]]
