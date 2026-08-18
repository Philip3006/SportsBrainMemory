# SportsBrain V1 Context Packet

Task: TASK-P0C-002
Task status: approved
Budget class: complex

## Governance

Use only this scoped task. External current source/runtime evidence outranks stale Memory. STOP on missing architecture decision or stop condition.

## Task record

---
id: TASK-P0C-002
type: task
title: Authenticated Private State & Dual Fetch
status: approved
canonical: true
tier: warm
workstream: P0-C
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-18T06:56:49Z
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


## Required invariants

- SEC-004
- SEC-005
- SEC-006
- SEC-008
- SEC-009
- SEC-010

## FND-20260814-013

---
type: "finding"
tier: "warm"
id: "FND-20260814-013"
status: "open"
severity: "P0"
domain: "security"
workstream: "P0-C"
invariants:
  - SEC-003
  - SEC-006
discovered_by: "CEO"
last_updated: "2026-08-18T06:56:49Z"
freshness_class: "release-bound"
---
# FND-20260814-013 — Unauthenticated Worker default-user snapshot can expose private state

## Problem / evidence

Public Worker signals path resolves/falls back to default user's combined snapshot.

## Failure / impact

Missing auth or missing per-user state can reveal another user's private state.

## Required closure

Separate public endpoint and authenticated /me state; never private fallback.

## Related invariants

- `SEC-003`
- `SEC-006`

## P0C-001 partial mitigation (2026-08-18)

TASK-P0C-001 production verified (Source Release SHA `20109387cf42c13c693e33b1642828424ce3be21`, PR #16, CI `32109075233`). Mitigation delivered:
- Unauthenticated public response is now sanitized: recursively zero private financial/account/identity fields in production GET /signals.json.
- Private financial state is no longer exposed through the public GET boundary.
- Fail-closed public serializer is deployed (Worker `9bd2d4f0-30b1-457d-979b-610f6aa2edf2`).

Remaining exposure:
- Deployed P0C-001 architecture still internally sources the public container from the legacy DEFAULT_USER KV snapshot.
- Canonical required closure also calls for: separate authenticated private /me state; no default-user private fallback semantics.
- These are TASK-P0C-002 scope.

## Verification

Current status: **open** — P0C-001 production mitigation complete; remaining closure dependency = TASK-P0C-002 (authenticated private state and removal of default-user dependency/fallback semantics).

For full closure, independent CEO review required against TASK-P0C-002 implementation boundary.


## FND-20260814-014

---
type: "finding"
tier: "warm"
id: "FND-20260814-014"
status: "open"
severity: "P0"
domain: "security"
workstream: "P0-C"
invariants:
  - SEC-002
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-014 — Privacy/legal text contradicts actual persistence architecture

## Problem / evidence

Current privacy text says bankroll/bet log are local-only while backend/public ledger persistence exists.

## Failure / impact

Users receive materially inaccurate storage description.

## Required closure

Fix architecture first; update text to deployed reality after migration.

## Related invariants

- `SEC-002`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## TASK-P0C-001

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


## External source scope

- `cloudflare/worker.js`
- `docs/js/`
- `scripts/`
