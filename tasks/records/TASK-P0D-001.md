---
id: TASK-P0D-001
type: task
title: Standard Runtime Writer Governance
status: completed
canonical: true
tier: warm
workstream: P0-D
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-18T19:36:30Z
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-017
  - FND-20260814-018
invariants:
  - GOV-002
  - GOV-003
  - GOV-005
  - GOV-006
  - REL-004
depends_on:
  - TASK-P0C-002
source_paths:
  - scripts/_git_safe_push.sh
  - scripts/_bot_commit_push.sh
  - .github/workflows/
  - tests/monitoring/test_writer_governance.py
evidence:
  - EVD-P0D-001-PROD-001
verified_by:
  - VER-P0D-001-PROD-001
---
# TASK-P0D-001 — Standard Runtime Writer Governance

## Mission

Route normal automated Git/runtime-data writers through one governed persistence primitive with path allowlists and source/runtime provenance.

## Primary files / boundaries

- `scripts/_git_safe_push.sh`
- `.github/workflows/`

## Adjacent read-only inspection

- `scripts/consume_pending_bets.py`
- `model artifact writers`

## Forbidden scope

- financial writer semantics
- AI healer source mutation
- model promotion

## Deterministic gates

- bot path allowlist enforced
- source path staged by runtime writer => fail closed
- concurrent data commits retry safely
- source release SHA remains separate

## Production verification

- representative runtime workflows publish without source mutation
- writer identity/provenance visible

## Rollback

Restore per-workflow persistence only for affected runtime workflows if shared primitive regresses; retain source path fail-closed guard.

## STOP conditions

- workflow requires source mutation
- writer path set cannot be classified

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.
