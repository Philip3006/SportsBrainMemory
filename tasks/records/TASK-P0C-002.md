---
id: TASK-P0C-002
type: task
title: Authenticated Private State & Dual Fetch
status: draft
canonical: true
tier: warm
workstream: P0-C
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-16T13:04:00+02:00
freshness_class: release-bound
budget_class: complex
findings:
  - FND-20260814-013
  - FND-20260814-014
invariants:
  - SEC-004
  - SEC-005
  - SEC-006
  - SEC-008
  - SEC-009
  - SEC-010
depends_on:
  - TASK-P0C-001
source_paths:
  - cloudflare/worker.js
  - docs/js/
  - scripts/
---
# TASK-P0C-002 — Authenticated Private State & Dual Fetch

## Mission

Add authenticated per-user private state with no default-user fallback and move PWA to independent public + private fetch channels.

## Primary files / boundaries

- `cloudflare/worker.js`
- `docs/js/`
- `scripts/`

## Adjacent read-only inspection

- `results/ledger_*.csv`
- `results/ledger_*.db`
- `docs/data/`

## Forbidden scope

- big-bang deletion before dual-fetch verification
- backend master token in browser

## Deterministic gates

- no token -> private 401
- A token cannot read/mutate B
- missing A state never falls back to Philip
- public works while private unavailable
- private failure disables betting/history clearly
- browser master-token absence test

## Production verification

- authenticated /me owner assertion
- logged-out public product works
- no private static fallback

## Rollback

Revert PWA private reader to compatibility channel only while keeping new private endpoint dark; never restore public private-state exposure.

## STOP conditions

- identity cannot be derived uniquely from user token
- private persistence owner cannot be established

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding evidence; exact test counts; CI evidence; production verification state; rollback note; remaining risks. Do not merge or broaden scope.
