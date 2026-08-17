---
id: TASK-P0C-001
type: task
title: Public / Private Serialization Boundary
status: approved
canonical: true
tier: warm
workstream: P0-C
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-17T22:47:41Z
freshness_class: release-bound
budget_class: complex
findings:
  - FND-20260814-011
  - FND-20260814-012
  - FND-20260814-013
  - FND-20260814-014
invariants:
  - SEC-001
  - SEC-002
  - SEC-003
  - SEC-004
  - SEC-005
  - DATA-013
depends_on:
  - TASK-P0B-004
source_paths:
  - scripts/
  - cloudflare/worker.js
  - docs/data/signals.json
  - docs/data/signals_philip.json
---
# TASK-P0C-001 — Public / Private Serialization Boundary

## Mission

Create explicit public product serialization that contains no user bankroll, bets, history or default-user identity.

## Primary files / boundaries

- `scripts/`
- `cloudflare/worker.js`
- `docs/data/signals.json`
- `docs/data/signals_philip.json`

## Adjacent read-only inspection

- `docs/js/`
- `src/`
- `results/ledger_philip.csv`
- `results/ledger_philip.db`

## Forbidden scope

- destructive ledger deletion
- unrelated PWA redesign
- model changes

## Deterministic gates

- public serializer allowlist schema
- recursive forbidden-private-key test
- unauth public path contains no default_user/user private state
- legacy compatibility path explicit

## Production verification

- public Pages and Worker payload remain useful without authentication and contain zero private fields

## Rollback

Keep legacy serializer available behind explicit compatibility path until dual-fetch verification.

## STOP conditions

- cannot enumerate all public serializer writers/readers
- public UI requires a private field with no replacement plan

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.
