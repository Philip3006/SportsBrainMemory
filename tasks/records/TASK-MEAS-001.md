---
id: TASK-MEAS-001
type: task
title: Canonical Measurement Population
status: draft
canonical: true
tier: warm
workstream: MODEL_INTEGRITY
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T13:04:00+02:00
freshness_class: release-bound
budget_class: complex
findings:
  - FND-20260814-022
  - FND-20260814-023
  - FND-20260814-026
invariants:
  - MEAS-001
  - MEAS-002
  - DATA-012
depends_on:
  - TASK-MODEL-001
source_paths:
  - src/measurement/
  - scripts/
  - results/
---
# TASK-MEAS-001 — Canonical Measurement Population

## Mission

Define one provenance-explicit production measurement population so ROI/Brier/logloss/ECE/CLV cannot mix contaminated or incomparable rows.

## Primary files / boundaries

- `src/measurement/`
- `scripts/`
- `results/`

## Adjacent read-only inspection

- `src/tennis/`
- `tests/`

## Forbidden scope

- model promotion until canonical population exists
- historical row rewriting without manifest

## Deterministic gates

- explicit sport/dataset/provenance/epoch inclusion criteria
- exclusions recorded
- historical contamination cannot silently enter new epoch
- CLV coverage denominator explicit
- backfill manifest required

## Production verification

- new reports carry population_id + dataset/version + sample counts

## Rollback

Keep historical reports labeled historical/non-canonical; do not delete them.

## STOP conditions

- population cannot be separated from contaminated rows deterministically

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.
