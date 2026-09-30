---
id: VER-P0B-004-PROD-001
type: verification
title: P0-B4 Release & Publication Provenance production verification
status: verified
canonical: true
graph_domain: production
graph_role: evidence
tier: warm
created_at: 2026-08-17T22:47:41Z
updated_at: 2026-08-17T22:47:41Z
freshness_class: release-bound
verification_status: verified
evidence:
  - EVD-P0B-004-PROD-001
workstream: P0-B
findings:
  - FND-20260814-018
---
# P0-B4 Release & Publication Provenance — Production Verification

**TASK-P0B-004 is CLOSED / production verified.**

Source Release SHA (`7cd6c6793419ab1f89c4b3c8e446f7764e84387a`) is now published as a distinct truth from Runtime/Data HEAD in the canonical public artifact. The public `docs/data/health.json` carries `source_release_sha`, `runtime_data_sha`, `source_runtime_consistent`, and `source_ci` identity fields. The C5 fix (`fetch-depth: 0` in `consume_pending_bets.yml`) ensures `_check_source_runtime_consistency()` performs a real `git log SOURCE..RUNTIME` classification rather than failing closed on a shallow clone. Verified via natural post-release run `32077550579` (`2026-08-17T22:46:53Z`), which produced `source_runtime_consistent: true` and successful cloud upload. Three-way SHA agreement confirmed. Pages deployment `32077608783` served correct provenance. No regressions. Verified via [[evidence/records/EVD-P0B-004-PROD-001]].
