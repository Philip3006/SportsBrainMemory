---
id: TASK-P0D-002
type: task
title: Financial Writer Governance
status: draft
canonical: true
tier: warm
workstream: P0-D
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T13:04:00+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-011
  - FND-20260814-017
invariants:
  - GOV-005
  - GOV-007
  - QUEUE-001
  - QUEUE-002
  - QUEUE-003
depends_on:
  - TASK-P0D-001
source_paths:
  - scripts/consume_pending_bets.py
  - src/betting/
  - tests/betting/
  - tests/scripts/test_consume_pending_bets.py
---
# TASK-P0D-002 — Financial Writer Governance

## Mission

Keep financial ledger mutation on its own durable transaction boundary; do not collapse P0-A ACK semantics into generic bot persistence.

## Primary files / boundaries

- `scripts/consume_pending_bets.py`
- `src/betting/`
- `tests/betting/`
- `tests/scripts/test_consume_pending_bets.py`

## Adjacent read-only inspection

- `scripts/_git_safe_push.sh`
- `.github/workflows/`

## Forbidden scope

- public serializer work
- AI healer
- model artifact promotion

## Deterministic gates

- ACK only after durable authoritative mutation
- per-user identity retained
- retryable failure never becomes permanent reject
- financial write cannot be incidental generic bot merge

## Production verification

- ledger mutation + ACK lifecycle remains production-equivalent to P0-A safety

## Rollback

Revert only governance wrapper around financial path; preserve P0-A durable ACK semantics.

## STOP conditions

- proposed shared primitive weakens P0-A durability
- canonical private ledger destination unresolved

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.
