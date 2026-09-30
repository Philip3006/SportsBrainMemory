---
id: EVD-P0C-002-PROD-001
type: evidence
title: P0-C2 Authenticated Private State & Dual Fetch production closure evidence
status: current
canonical: true
graph_domain: production
graph_role: evidence
tier: warm
created_at: 2026-08-18T12:00:00Z
updated_at: 2026-08-18T12:00:00Z
freshness_class: release-bound
evidence_type: production-source
sha: 635566bb6f993dae2f937e43fd7c5a9e411fb89a
environment: production
scope: P0-C2 Authenticated Private State & Dual Fetch — authenticated /me endpoint; exact per-user token owner routing; no DEFAULT_USER fallback; master token 403 fail-closed; PWA dual-fetch; session race isolation; private_serializer.py allowlist; HARD GATE 7
workstream: P0-C
verified_by:
  - VER-P0C-002-PROD-001
findings:
  - FND-20260814-013
---
# P0-C2 Authenticated Private State & Dual Fetch — Production Closure Evidence

## Source release

- Source Release SHA: `635566bb6f993dae2f937e43fd7c5a9e411fb89a`
- PR #17, squash merge to main: `2026-08-18`
- Post-merge CI run: `32133192040` — **success**

## CI gates passed

- Gate 5 Provenance: **PASS**
- Gate 6 P0C-001 Privacy: **PASS**
- Gate 7 P0C-002 Authenticated Private State: **PASS**

## Worker production evidence

- Previous Worker deployment (rollback identity): `2e3b3888-6731-43ae-8b39-dc39ee2956b9`
- New TASK-P0C-002 Worker deployment: `8b4f5ad5-c10d-402e-8636-16d0c5b00c97`
- No rollback was required

## Production endpoint verification

- GET /signals.json anonymous → HTTP 200, zero private fields — **VERIFIED**
- GET /me no token → 401 — **VERIFIED**
- GET /me master token → 403 (fail-closed) — **VERIFIED**
- GET /me Philip per-user token → exact owner routing — **VERIFIED** (CI Suite 16 T3/T6; skipped in local env — no per-user token)
- P0C-001 privacy regression: 26/26 PASS — **VERIFIED**
- PWA smoke public logged-out: 4/4 PASS — **VERIFIED**

## What P0C-002 delivered

- GET /me endpoint: per-user Bearer required; master token → 403; missing state → 404 (no DEFAULT_USER fallback)
- Exact owner routing: Philip token reads signals_json as explicit owner key (not generic fallback)
- Alice token cannot reach Bob's state
- Cross-user auth fixes: rotate_token and token_status reject A-targeting-B
- PWA dual-fetch: public /signals.json (no auth) + private /me (Bearer), independent failure handling
- _authenticatedOwner sourced only from /me payload.owner
- sb_user removed as authorization authority
- Master token removed from all browser paths; scripts/create_invite.py admin CLI added
- ?token= long-lived auth ingestion removed from browser
- Session race isolation: monotonic _privateFetchGen prevents stale Alice response overwriting Bob
- private_serializer.py (explicit allowlist)
- HARD GATE 7 added

## Known open baseline (not introduced by P0C-002)

- test_fnd004_mandatory_submit_delivers_canonical_payload — pre-existing issue, not introduced by P0C-002. Still open.

## FND-20260814-013 closure basis

Authenticated /me endpoint deployed with exact per-user token owner routing; no DEFAULT_USER fallback; master token → 403 fail-closed; Alice cannot access Bob; public /signals.json zero private fields; PWA dual-fetch independent. FND-20260814-013 is fully resolved by P0C-002 production evidence.

## Related

- [[domains/PRODUCTION_OPERATIONS]]
- [[domains/PWA_AND_WORKER]]
- [[domains/SECURITY_AND_PRIVACY]]
- [[components/CMP-BETTING]]
- [[workstreams/P0-C]]
- [[verifications/records/VER-P0C-002-PROD-001]]
