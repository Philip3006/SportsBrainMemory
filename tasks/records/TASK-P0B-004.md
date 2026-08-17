---
id: TASK-P0B-004
type: task
title: Release & Publication Provenance
status: approved
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-17T21:07:18+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-018
invariants:
  - REL-004
  - REL-009
depends_on:
  - TASK-P0B-003
source_paths:
  - src/monitoring/aggregate_health.py
  - docs/data/
  - scripts/
---
# TASK-P0B-004 — Release & Publication Provenance

## Mission

Publish source release, exact CI, runtime-data head and publication/build provenance as separate truths.

## Primary files / boundaries

- `src/monitoring/aggregate_health.py`
- `docs/data/`
- `scripts/`

## Adjacent read-only inspection

- `.github/workflows/pages*.yml`
- `.github/workflows/*publish*.yml`
- `cloudflare/`

## Forbidden scope

- privacy payload redesign except provenance fields
- model promotion

## Deterministic gates

- source_release_sha does not move on data-only commits
- runtime_data_sha can move independently
- published artifact carries schema/build timestamp
- provenance serialization tests

## Production verification

- public artifact exposes exact source release and runtime data provenance
- Pages/Worker provenance agrees with deployed evidence

## Rollback

Remove new provenance fields/readers together if incompatible; retain prior public schema.

## STOP conditions

- current deployment identity cannot be resolved
- provenance field would expose secrets/private state

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.
