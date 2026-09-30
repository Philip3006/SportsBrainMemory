---
id: EVD-P0B-002-PROD-001
type: evidence
title: P0-B2 Schedule & Window Truth production closure evidence
status: current
canonical: true
graph_domain: production
graph_role: evidence
tier: warm
created_at: 2026-08-17T17:00:00+02:00
updated_at: 2026-08-17T17:00:00+02:00
freshness_class: release-bound
evidence_type: production-source
sha: bb59d180e9d6f8df7a2c78d2d4e82e71e12751c9
environment: production
scope: P0-B2 Schedule & Window Truth — machine-readable JobExpectation semantics with timezone-correct cron evaluation
workstream: P0-B
verified_by:
  - VER-P0B-002-PROD-001
findings:
  - FND-20260814-006
  - FND-20260814-008
  - FND-20260814-009
  - FND-20260814-010
---
# P0-B2 Schedule & Window Truth — Production Closure Evidence

## Source release

- Source release SHA: `bb59d180e9d6f8df7a2c78d2d4e82e71e12751c9`
- PR #12, approved head: `0e774f5619eb141b340b10a5265f140a0b191097`
- Post-merge CI run: `32040431271` — **success**

## Publication

- Publication runtime/data HEAD: `f95b372607b7ccd6cf5caae244f48cbec3132d69`
- Publication scope: `docs/data/health.json` only
- Generated at: `2026-08-17T14:55:30Z`
- GitHub Pages run `32040828663` — **success**

## Production proofs

### MON-002 / FND-20260814-008 — BL2 windowed jobs not false-stale off-window

- `bundesliga2_live_push`: status=ok / reported_status=ok / expectation_state=not_expected
- `bundesliga2_scan`: ok + not_expected
- `bundesliga2_closing_odds`: ok + not_expected
- `bundesliga2_retrain`: ok + not_expected
- `bundesliga2_settle`: error + exit_code=1 + not_expected — execution failure visible; not false-stale

### MON-012 / FND-20260814-006 — Cadence model matches active schedulers

- `tennis_scan` cadence: `8×/Tag 02/06/09/12/15/18/21/23 UTC` (was 4×/day — schedule drift closed)
- `daily_scan` cadence: `1×/Tag 07:00 Europe/Berlin (launchd)` — DST-correct
- `auto_retrain` cadence: `2×/Tag 06:00 + 18:00 Europe/Berlin (launchd)` — 04:00+16:00 UTC during CEST
- `closing_odds` cadence: `2×/Tag 14:00 + 18:00 Europe/Berlin (launchd)`
- `settle` cadence: `stündlich :30 Europe/Berlin (launchd, 24h)`
- All launchd calendar jobs use `tz="Europe/Berlin"` — DST-correct zoneinfo evaluation

### FND-20260814-009 — Event-driven consumer modeled correctly

- `consume_pending_bets` uses `EventWithFallbackExpectation(fallback_interval_s=1800, grace_s=600)`
- No-event periods do not trigger false stale (fallback window semantics applied)

### FND-20260814-010 — Odds refresher now registered in aggregate health

- `odds_refresh` registered as `IntervalExpectation(interval_s=300, grace_s=300)` in JOB_EXPECTATIONS
- Execution-plane visibility gap closed; job now surfaces in published health output
- Never-run gap (no health snapshot) is pre-existing operational state, not a coverage gap — recorded as remaining risk, does not reopen this finding

### MON-001 — No ok/degraded with nonzero or unknown exit (P0-B1 invariant preserved)

- Zero MON-001 contradictions in published health output

### reported_status round-trip (P0-B2 aggregate extension)

- All snapshot-derived job entries contain `reported_status` field
- `reported_status` captures pre-schedule execution truth after MON-001 coercions
- Second merge-from-committed generation is status-idempotent (verified)

## Remaining non-B2 operational risks

- `odds_refresh` has no health snapshot / never-run gap — pre-existing, does not reopen FND-20260814-010
- Tennis scan/retrain/settle/closing_odds have real exit=1 failures — operational, not P0-B2 regressions
- `tennis_retrain` health key shared by LGBM daily and Elo weekly — pre-existing gap
- Cloud publication endpoint not configured locally — unavailable / not independently verified

## OPS-006 scope note

OPS-006 (full execution-plane provenance) is partially addressed by odds_refresh coverage. Full OPS-006 closure spans multiple workstream tasks and is not marked fully closed by this evidence.

## Related

- [[domains/PRODUCTION_OPERATIONS]]
- [[domains/MONITORING_AND_RECOVERY]]
- [[domains/DATA_AND_PROVIDERS]]
- [[workstreams/P0-B]]
- [[verifications/records/VER-P0B-002-PROD-001]]
