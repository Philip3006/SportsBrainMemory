---
id: EVD-P0B-003-PROD-001
type: evidence
title: P0-B3 Recovery Truth production closure evidence
status: current
canonical: true
tier: warm
created_at: 2026-08-17T21:07:18+02:00
updated_at: 2026-08-17T21:07:18+02:00
freshness_class: release-bound
evidence_type: production-source
sha: 71d952d852ff11077dea2ac05ac82c49a6115d49
environment: production
scope: P0-B3 Recovery Truth — fail-closed recovery with post-dispatch execution/output evidence requirement
workstream: P0-B
verified_by:
  - VER-P0B-003-PROD-001
findings:
  - FND-20260814-007
---
# P0-B3 Recovery Truth — Production Closure Evidence

## Source release

- Source release SHA: `71d952d852ff11077dea2ac05ac82c49a6115d49`
- PR #14, exact-head SHA: `e48cf436d19c3ba1941fa1eb867db08317619b86`
- Exact-head CI run: `32058083032` — **success**
- Squash merge to main: `2026-08-17T19:07:18Z`
- Post-merge CI run: `32058588474` — **success**

## Runtime/Data HEAD

- Observed runtime/data HEAD after merge: `408f44af5`
- Tracked separately from source release SHA (data-only commits advance this independently)

## Production proofs

### Matching attempt probe — PASS

Recovery correctly identifies and executes against the matching recovery target.

### Wrong attempt probe — PASS / fail-closed

Recovery emits RECOVERY_UNAVAILABLE for unrecognised/wrong targets. Dispatch alone does not produce RECOVERED status.

### Missing attempt probe — PASS / fail-closed

Recovery emits RECOVERY_UNAVAILABLE when target is inactive/nonexistent (`.disabled` workflow variants cannot execute).

### Process-exit enforcement D1/D2/D3 — PASS

Post-dispatch execution evidence is required before declaring recovered; three distinct process-exit scenarios all enforced.

### Healthy terminology migration — PASS

Monitoring terminology migrated; no healthy-state regression observed.

### launchd runtime

- `com.sportsbrain.auto-heal-ai` loaded with `StartInterval=900`
- Natural post-release run observed: `2026-08-17T19:25:02Z`
- No P0-B3 runtime errors

### Absence of regressions

- No public health regression
- No production files mutated during verification
- Product source unchanged during verification

### FND-20260814-007 / GOV-003 — Recovery maps reference inactive/nonexistent workflow filenames

**RESOLVED**: Recovery registry now emits `RECOVERY_UNAVAILABLE` for inactive/nonexistent workflow targets. Verified via matching/wrong/missing attempt probes above.

## Effective P0-B3 source files

- `scripts/_health.sh`
- `scripts/auto_heal_ai.py`
- `src/monitoring/health_writer.py`
- `src/monitoring/recovery_truth.py`
- `src/notifications/health_push.py`
- `tests/monitoring/test_recovery_truth.py`

## Remaining risks (deferred, NOT P0-B3 blockers)

1. Pre-existing JSONDecodeError race on `docs/data/health.json` during concurrent bot writes — deferred
2. `re-test-vapid` and `force-refresh-signals` remain process-exit-only recovery bindings — deferred to P0-D3
