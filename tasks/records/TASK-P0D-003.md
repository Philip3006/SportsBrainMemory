---
id: TASK-P0D-003
type: task
title: AI Healer Boundary
status: draft
canonical: true
graph_domain: governance
graph_role: operational
tier: warm
workstream: P0-D
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T13:04:00+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-015
invariants:
  - GOV-002
  - GOV-003
  - GOV-008
  - OPS-007
depends_on:
  - TASK-P0D-002
source_paths:
  - scripts/auto_heal_ai.py
  - tests/
---
# TASK-P0D-003 — AI Healer Boundary

## Mission

Remove autonomous LLM source edit/commit/push authority; retain diagnosis, recommendation and deterministic allowlisted operational recovery.

## Primary files / boundaries

- `scripts/auto_heal_ai.py`
- `tests/`

## Adjacent read-only inspection

- `scripts/cloud_healer.py`
- `scripts/_git_safe_push.sh`

## Forbidden scope

- Builder source authority
- unrelated monitoring redesign

## Deterministic gates

- no source write/git add/git commit/git push path reachable
- diagnosis still emitted
- deterministic recovery only through allowlist
- SOURCE_FIX_PROPOSED output tested

## Production verification

- production healer can diagnose without source mutation
- fix proposal contains evidence and bounded recommendation

## Rollback

Disable AI healer entirely if diagnosis-only mode cannot be safely isolated.

## STOP conditions

- source mutation is entangled with required monitoring availability

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.

## Related

- [[domains/GOVERNANCE]]
- [[domains/MONITORING_AND_RECOVERY]]
- [[domains/PRODUCTION_OPERATIONS]]
- [[workstreams/P0-D]]
- [[writers/WRT-RECOVERY]]
