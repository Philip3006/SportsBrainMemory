# SportsBrain V1 Context Packet

Task: TASK-P0C-001
Task status: approved
Budget class: complex

## Governance

Use only this scoped task. External current source/runtime evidence outranks stale Memory. STOP on missing architecture decision or stop condition.

## Task record

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


## Required invariants

- SEC-001
- SEC-002
- SEC-003
- SEC-004
- SEC-005
- DATA-013

## FND-20260814-011

---
type: "finding"
tier: "warm"
id: "FND-20260814-011"
status: "open"
severity: "P0"
domain: "security"
workstream: "P0-C"
invariants:
  - SEC-001
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-011 — Personal ledger and DB are tracked in public repository

## Problem / evidence

Current public tree includes per-user financial/betting artifacts such as ledger CSV/DB.

## Failure / impact

Personal betting history and financial state exposed publicly.

## Required closure

Migrate private durable state, stop public writes, then clean active tree/history safely.

## Related invariants

- `SEC-001`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## FND-20260814-012

---
type: "finding"
tier: "warm"
id: "FND-20260814-012"
status: "open"
severity: "P0"
domain: "security"
workstream: "P0-C"
invariants:
  - SEC-001
  - SEC-008
  - DATA-013
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-012 — Public signals snapshot contains bankroll/open-bet private state

## Problem / evidence

Static/public signals payload contains default-user bankroll and open-bet state.

## Failure / impact

Privacy remains broken even if ledger file itself is removed.

## Required closure

Split public product schema from authenticated private user schema.

## Related invariants

- `SEC-001`
- `SEC-008`
- `DATA-013`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


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
last_updated: "2026-08-14T00:03:00+02:00"
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

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


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


## TASK-P0B-004

---
id: TASK-P0B-004
type: task
title: Release & Publication Provenance
status: completed
canonical: true
tier: warm
workstream: P0-B
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-17T22:47:41Z
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
evidence:
  - EVD-P0B-004-PROD-001
verified_by:
  - VER-P0B-004-PROD-001
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


## External source scope

- `scripts/`
- `cloudflare/worker.js`
- `docs/data/signals.json`
- `docs/data/signals_philip.json`
