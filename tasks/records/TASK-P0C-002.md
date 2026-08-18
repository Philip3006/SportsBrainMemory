---
id: TASK-P0C-002
type: task
title: Authenticated Private State & Dual Fetch
status: completed
canonical: true
tier: warm
workstream: P0-C
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-18T12:00:00Z
freshness_class: release-bound
budget_class: complex
findings:
  - FND-20260814-013
  - FND-20260814-014
invariants:
  - SEC-003
  - SEC-004
  - SEC-005
  - SEC-006
  - SEC-008
  - SEC-009
  - SEC-010
  - DATA-013
depends_on:
  - TASK-P0C-001
source_paths:
  - cloudflare/worker.js
  - docs/js/
  - scripts/
evidence:
  - EVD-P0C-002-PROD-001
verified_by:
  - VER-P0C-002-PROD-001
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

## Closure

**TASK-P0C-002 is CLOSED / production verified.**

Source Release SHA: `635566bb6f993dae2f937e43fd7c5a9e411fb89a` (PR #17, squash merge 2026-08-18). Post-merge CI run `32133192040` — success. All required gates passed: Gate 5 Provenance, Gate 6 P0C-001 Privacy, Gate 7 P0C-002 Authenticated Private State. Worker deployment `8b4f5ad5-c10d-402e-8636-16d0c5b00c97` (rollback identity: `2e3b3888-6731-43ae-8b39-dc39ee2956b9`). Production verified: GET /signals.json anonymous → 200, zero private fields; GET /me no token → 401; GET /me master token → 403 (fail-closed); GET /me Philip per-user token → exact owner (CI Suite 16 T3/T6); P0C-001 privacy regression 26/26 PASS; PWA smoke public logged-out 4/4 PASS. Verified via [[evidence/records/EVD-P0C-002-PROD-001]].
