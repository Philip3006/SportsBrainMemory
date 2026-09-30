---
id: EVD-P0C-001-PROD-001
type: evidence
title: P0-C1 Public / Private Serialization Boundary production closure evidence
status: current
canonical: true
tier: warm
created_at: 2026-08-18T06:56:49Z
updated_at: 2026-08-18T06:56:49Z
freshness_class: release-bound
evidence_type: production-source
sha: 20109387cf42c13c693e33b1642828424ce3be21
environment: production
scope: P0-C1 Public / Private Serialization Boundary — explicit public serializer allowlist; recursive fail-closed private-key assertion; HARD GATE 6 Privacy serialization; production Pages and Worker public response verified zero private fields; steady-state public artifacts remain sanitized after later bot activity
workstream: P0-C
verified_by:
  - VER-P0C-001-PROD-001
findings:
  - FND-20260814-012
---
# P0-C1 Public / Private Serialization Boundary — Production Closure Evidence

## Source release

- Source Release SHA: `20109387cf42c13c693e33b1642828424ce3be21`
- PR #16, squash merge to main: `2026-08-18T06:55:58Z`
- Post-merge CI run: `32109075233` — **success**
- Exact CI head SHA: `20109387cf42c13c693e33b1642828424ce3be21`
- Three-way SHA agreement: source_release_sha == source_ci.head_sha == squash commit SHA — **PASS**

## Provenance record

- Provenance commit: `ca493fb35646182b4699222801fc74c40c44d233`
- `provenance_meta.json` canonical records:
  - `source_release_sha`: `20109387cf42c13c693e33b1642828424ce3be21`
  - `source_ci.run_id`: `32109075233`
  - `source_ci.head_sha`: `20109387cf42c13c693e33b1642828424ce3be21`
  - `source_ci.status`: `success`
  - `recorded_at`: `2026-08-18T06:56:49Z`

## CI gates passed

- Compile: **PASS**
- Core smoke: **PASS**
- Node Worker contracts: **PASS**
- Ruff regression: **PASS**
- Provenance truth: **PASS**
- HARD GATE 6 Privacy serialization: **PASS**

## GitHub Pages production evidence

- Pages deployment run: `32109137419` — **success**
- Deployment source: `ca493fb35646182b4699222801fc74c40c44d233`
- Production-served `docs/data/signals.json`: zero forbidden private fields — **VERIFIED**
- Production-served `docs/data/signals_philip.json`: zero forbidden private fields — **VERIFIED**
- Forbidden fields absent: `bankroll_state`, `open_bets`, `settled_bets`, `default_user`, user identity, private financial state
- Public product remained useful after serializer boundary enforcement

## Worker production evidence

- Previous Worker deployment (rollback identity): `01ad0f44-ed45-4b9d-a854-eba0b918f35b`
- New TASK-P0C-001 Worker deployment: `9bd2d4f0-30b1-457d-979b-610f6aa2edf2`
- Rollback readiness before deploy: **PASS**
- No rollback was required
- Production unauthenticated GET /signals.json: HTTP 200, recursively zero private financial/account/identity fields — **VERIFIED**
- Deployed Worker serializer: **fail-closed**
- Private/internal KV risk state remained structurally available for: bankroll cap, active-bet count, risk freshness, canonical signal validation, odds validation, identity validation
- `aggregate_health merge_health=1` preserved the private internal snapshot

## PWA production smoke

- PWA loads: **PASS**
- Public product remains usable: **PASS**
- Public signals network payload: zero private fields — **VERIFIED**
- No `default_user` identity leak in public response: **VERIFIED**
- No `TypeError` / `ReferenceError` attributable to P0C-001: **VERIFIED**
- Logged-out/private UI degrades safely: **VERIFIED**
- No real wager was placed

## Steady-state CEO verification

- CEO independently re-checked repository after additional runtime bots ran
- Later main HEAD observed: `4ab91c924a826903f6f119447d6e1f6b4fa4f509`
- This is NOT the Source Release SHA — tracked separately
- Source Release = `20109387cf42c13c693e33b1642828424ce3be21`
- Later Runtime/Data Main = `4ab91c924a826903f6f119447d6e1f6b4fa4f509`
- Public artifacts after later bot activity: no `default_user`, no `bankroll_state` — **VERIFIED**
- Privacy boundary survived subsequent steady-state writer activity — **PASS**

## FND-20260814-012 closure basis

Explicit public serializer allowlist; recursive fail-closed private-key assertion; HARD GATE 6; production Pages sanitized; production Worker public response sanitized; steady-state public artifacts remain sanitized after later bot activity. FND-20260814-012 is fully resolved by production evidence.

## FND-20260814-013 partial mitigation

P0C-001 has materially mitigated the unauthenticated Worker default-user exposure: unauthenticated public response is sanitized; private financial state is no longer exposed through public GET. The deployed P0C-001 architecture still internally sources the public container from the legacy DEFAULT_USER KV snapshot. Remaining closure (separate authenticated private /me state; no default-user private fallback semantics) is TASK-P0C-002 scope. FND-20260814-013 remains open.

## Remaining risks (deferred)

1. FND-20260814-011: Personal ledger/DB artifacts remain tracked in the public repository. Not addressed by P0C-001. P0-C/later scope.
2. FND-20260814-013: Default-user KV snapshot is still the internal source for public container. Full isolation requires TASK-P0C-002 authenticated dual-fetch.
3. FND-20260814-014: Privacy/legal text not updated. P0C-001 did not update legal copy. P0-C/legal scope.
4. SEC-001: Ledger/DB still tracked publicly — not_enforced until P0-C ledger migration.
5. SEC-003: Authenticated/private dual-fetch and removal of remaining DEFAULT_USER dependency not complete — partial only until TASK-P0C-002.

## Related

- [[domains/PRODUCTION_OPERATIONS]]
- [[domains/PWA_AND_WORKER]]
- [[domains/SECURITY_AND_PRIVACY]]
- [[components/CMP-PUBLICATION]]
- [[workstreams/P0-C]]
- [[verifications/records/VER-P0C-001-PROD-001]]
