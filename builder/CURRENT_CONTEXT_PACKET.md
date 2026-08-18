# SportsBrain V1 Context Packet

Task: TASK-P0D-001
Task status: approved
Budget class: standard

## Governance

Use only this scoped task. External current source/runtime evidence outranks stale Memory. STOP on missing architecture decision or stop condition.

## Task record

---
id: TASK-P0D-001
type: task
title: Standard Runtime Writer Governance
status: approved
canonical: true
tier: warm
workstream: P0-D
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-08-18T00:00:00+02:00
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
  - .github/workflows/
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


## Required invariants

- GOV-002
- GOV-003
- GOV-005
- GOV-006
- REL-004

## FND-20260814-017

---
type: "finding"
tier: "warm"
id: "FND-20260814-017"
status: "open"
severity: "P1"
domain: "governance"
workstream: "P0-D"
invariants:
  - OPS-003
  - REL-010
discovered_by: "CEO"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# FND-20260814-017 — Automated Git writers use inconsistent persistence primitives

## Problem / evidence

Several workflows perform their own add/commit/rebase/push rather than the shared safe-push governance.

## Failure / impact

Path authority, conflict behavior and durability differ by writer.

## Required closure

Introduce writer classes and one governed persistence primitive/equivalent tested implementations.

## Related invariants

- `OPS-003`
- `REL-010`

## Verification

Current status: **open**.

For open findings, closure requires independent CEO review against the actual implementation boundary.


## FND-20260814-018

---
type: "finding"
tier: "warm"
id: "FND-20260814-018"
status: "resolved_production"
severity: "P1"
domain: "release"
workstream: "P0-B"
invariants:
  - REL-004
  - OPS-007
discovered_by: "CEO"
last_updated: "2026-08-17T22:47:41Z"
freshness_class: "release-bound"
resolved_by: "VER-P0B-004-PROD-001"
evidence:
  - EVD-P0B-004-PROD-001
---
# FND-20260814-018 — Runtime-data commits continuously obscure source-release provenance

## Problem / evidence

Frequent Tennis/runtime commits move main even though source code did not change.

## Failure / impact

HEAD can be misinterpreted as validated release; PR bases churn.

## Required closure

Publish source_release_sha separately from runtime_data_sha; evaluate moving high-frequency runtime data.

## Related invariants

- `REL-004`
- `OPS-007`

## Verification

Current status: **resolved_production** — 2026-08-17T22:20:43Z.

Source Release SHA: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a` (PR #15, post-merge CI `32075583343` success). `source_release_sha` is now published separately from `runtime_data_sha` in the canonical public artifact (`docs/data/health.json` and GitHub Pages). Natural post-release `consume_pending_bets` run `32077550579` confirmed `source_runtime_consistent: true` with runtime/data SHA `b81d606641baaf3765dfbb77a93170023a3ee496` independent of the Source Release SHA. Pages deployment `32077608783` served correct provenance. Three-way SHA agreement PASS.

**Note:** OPS-007 (no single bot can continuously move main in a way that _invalidates_ source-release provenance) remains `not_enforced` at the architecture level — runtime-main churn itself is not eliminated. P0-B4 solved the publication identity separation; the broader runtime-writer architecture is P0-D scope. Verified via [[verifications/records/VER-P0B-004-PROD-001]].


## TASK-P0C-002

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


## External source scope

- `scripts/_git_safe_push.sh`
- `.github/workflows/`
