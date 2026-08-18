---
id: TASK-P0C-001
type: task
title: Public / Private Serialization Boundary
status: completed
canonical: true
tier: warm
workstream: P0-C
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-18T06:56:49Z
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
evidence:
  - EVD-P0C-001-PROD-001
verified_by:
  - VER-P0C-001-PROD-001
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

## Closure

**TASK-P0C-001 is CLOSED / production verified.**

Source Release SHA: `20109387cf42c13c693e33b1642828424ce3be21` (PR #16, squash merge 2026-08-18T06:55:58Z). Post-merge CI run `32109075233` — success. Exact CI head SHA: `20109387cf42c13c693e33b1642828424ce3be21`. All required gates passed: Compile, Core smoke, Node Worker contracts, Ruff regression, Provenance truth, HARD GATE 6 Privacy serialization. Pages deployment `32109137419` success — production-served `docs/data/signals.json` and `docs/data/signals_philip.json` verified to contain zero forbidden private fields. Worker deployment `9bd2d4f0-30b1-457d-979b-610f6aa2edf2` (previous rollback identity: `01ad0f44-ed45-4b9d-a854-eba0b918f35b` — no rollback required). Production unauthenticated GET /signals.json verified HTTP 200 with zero private financial/account/identity fields. Fail-closed serializer deployed. CEO steady-state re-check confirmed latest observed main HEAD `4ab91c924a826903f6f119447d6e1f6b4fa4f509` still contains no `default_user` or `bankroll_state` in public artifacts — privacy boundary survived subsequent steady-state writer activity. Verified via [[evidence/records/EVD-P0C-001-PROD-001]].
