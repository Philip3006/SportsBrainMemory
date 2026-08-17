---
id: EVD-P0B-004-PROD-001
type: evidence
title: P0-B4 Release & Publication Provenance production closure evidence
status: current
canonical: true
tier: warm
created_at: 2026-08-17T22:20:43Z
updated_at: 2026-08-17T22:47:41Z
freshness_class: release-bound
evidence_type: production-source
sha: 7cd6c6793419ab1f89c4b3c8e446f7764e84387a
environment: production
scope: P0-B4 Release & Publication Provenance — source_release_sha and runtime_data_sha published as separate truths; full-history checkout (C5) ensures _check_source_runtime_consistency() succeeds
workstream: P0-B
verified_by:
  - VER-P0B-004-PROD-001
findings:
  - FND-20260814-018
---
# P0-B4 Release & Publication Provenance — Production Closure Evidence

## Source release

- Source Release SHA: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a`
- PR #15, squash merge to main: `2026-08-17T22:20:43Z`
- Post-merge CI run: `32075583343` — **success**
- Exact CI head SHA: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a`
- Three-way SHA agreement: source_release_sha == source_ci.head_sha == squash commit SHA — **PASS**
- Provenance record commit: `9f90ac1cfb4d59710921579cec0f30bb64a198bc`

## provenance_meta.json (production)

- `source_release_sha`: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a`
- `source_ci.run_id`: `32075583343`
- `source_ci.status`: `success`
- `source_ci.head_sha`: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a`
- `source_ci.workflow`: `CI Gates (compile + smoke tests + lint)`
- `recorded_at`: `2026-08-17T22:21:27Z`

## Natural post-release production execution (C5 fix verified)

- Workflow: Consume Pending Bets (`consume_pending_bets.yml`)
- Run ID: `32077550579`
- Start: `2026-08-17T22:46:53Z` / Completion: `2026-08-17T22:47:41Z`
- Conclusion: **success**
- Checkout SHA (runtime/data): `b81d606641baaf3765dfbb77a93170023a3ee496`
- Full-history checkout (`fetch-depth: 0`): **confirmed active** — C5 fix operational
- Cloud upload: **confirmed** (`[health] cloud upload: ok` at `22:47:36Z`)

## Published repository artifact (docs/data/health.json)

- `generated_at`: `2026-08-17T22:47:35Z`
- `source_release_sha`: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a`
- `runtime_data_sha`: `b81d606641baaf3765dfbb77a93170023a3ee496`
- `source_runtime_consistent`: **true**
- `source_ci.run_id`: `32075583343`
- `source_ci.head_sha`: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a`
- `errors`: none

## Data-only source stability

- `git log 7cd6c679..b81d6066 -- src/ scripts/ tests/ requirements.txt .github/workflows/` returned empty
- Zero source-changing commits between Source Release and runtime-data SHA
- Source Release remained stable while runtime/data HEAD advanced independently — **PASS**

## GitHub Pages production evidence

- Pages deployment run: `32077608783` — **success**
- Deployment SHA: `e0f9c2924`
- Served `source_release_sha`: `7cd6c6793419ab1f89c4b3c8e446f7764e84387a`
- Served `runtime_data_sha`: `b81d606641baaf3765dfbb77a93170023a3ee496`
- Served `source_runtime_consistent`: `true`
- Cross-surface agreement: **PASS**

## Worker / Cloudflare health surface

- CI log confirms health cloud upload at `22:47:36Z`
- No dedicated persistent Worker `/health` endpoint exists (pre-existing architecture)
- Health KV key is transient; subsequent signals uploads from other workflows overwrite signals.json without health key
- This pre-dates P0-B4 and is **not a P0-B4 regression** — documented deferred risk (P0-D scope)

## Observed repository main HEAD after publication

- `e0f9c2924` (`auto: consume health 2026-08-17 22:47 UTC`)
- Distinct from Source Release SHA, runtime/data SHA, and provenance-record commit

## Absence of regressions

- No P0-B4 attributable regression
- No provenance exception, no malformed health.json, no aggregate_health crash
- No `source_runtime_consistent=null` (C5 fix confirmed active)
- No `source_runtime_consistent=false` under valid data movement
- No false source_release advancement
- No private/secret exposure caused by provenance
- Production source files unchanged during verification

## Effective P0-B4 source files

- `src/monitoring/release_provenance.py`
- `src/monitoring/aggregate_health.py`
- `scripts/record_source_release.py`
- `tests/monitoring/test_release_provenance.py` (33 tests, +1 C5 static gate)
- `.github/workflows/ci_gates.yml` (HARD GATE 5, `fetch-depth: 0`)
- `.github/workflows/consume_pending_bets.yml` (`fetch-depth: 0` added — C5 fix)
- `docs/data/provenance_meta.json`

## Remaining risks (deferred, NOT P0-B4 blockers)

1. Worker/Cloudflare health provenance is transient — no dedicated persistent `/health` endpoint. Canonical upload succeeded; KV field may be overwritten by subsequent signals writes. Pre-existing behavior. Deferred to P0-D/P0-C architecture.
2. OPS-007 runtime-main churn architecture — P0-B4 separates Source Release identity from runtime/data identity in the published artifact, but does not eliminate the frequency of data-only commits to main. P0-D scope.
