# SportsBrain — P0-B Execution Plane & Schedule Matrix

**Date:** 2026-08-13  
**Purpose:** Pre-build audit for P0-B Monitoring Truth.  
**Status:** Planning artifact only — no repository changes.  
**Key invariants:** MON-001, MON-002, MON-011, MON-012, OPS-006, MON-008, REL-004.

---

# 1. Core finding

The present monitoring model assumes that most jobs can be represented as:

```text
last_run_at + fixed interval + grace
```

That assumption is already false.

SportsBrain currently contains jobs that are:
- fixed-interval launchd jobs;
- exact cron-set GitHub jobs;
- windowed high-frequency jobs;
- event-driven jobs with scheduled fallback;
- manual workflows;
- recovery/meta-jobs.

Therefore P0-B should not “update the cadence constants”. It should replace the cadence abstraction with a machine-readable **execution expectation model**.

---

# 2. Observed execution matrix

| Logical job | Execution plane | Active trigger observed | Current health expectation | Audit verdict |
|---|---|---|---|---|
| `tennis_scan` | GitHub Actions | 8 cron times/day: 02, 06, 09, 12, 15, 18, 21, 23 UTC + manual | Health registry says 4x/day / 6h | **Wrong schedule model** |
| `tennis_settle` | GitHub Actions | every 2h, 06–22 UTC (`15 6-22/2`) + manual | 2h | cadence roughly aligned, execution truth still weak |
| `tennis_closing_odds` | GitHub Actions | every 30 min + manual | 30 min | cadence aligned, but `ok + exit=1` exists in published health |
| `tennis_retrain` | GitHub Actions (`tennis_lgbm_retrain.yml`) | daily 05:00 UTC + manual | health registry says weekly Monday 03:00 | **Severe schedule drift** |
| `bundesliga2_scan` | GitHub Actions | daily 06:00 UTC + Fri/Sat/Sun prematch cron points | “2x/day + pre-match” / 12h | oversimplified and not equivalent |
| `bundesliga2_settle` | GitHub Actions | explicit weekly cron set around match slots | fixed 3h age model | **wrong outside expected match slots** |
| `bundesliga2_live_push` | GitHub Actions | every 2 min only Fri/Sat/Sun live windows | global 2m expectation | **false stale outside windows** |
| `bundesliga2_retrain` | GitHub Actions | daily 05:00 UTC | daily | schedule aligned; workflow hardcodes exit-code 0 |
| `bundesliga2_closing_odds` | GitHub Actions | four weekly pre-kickoff cron points | global 15m interval | **false stale almost all week** |
| `consume_pending_bets` | Worker event → GitHub repository_dispatch + GH 30m fallback | primary conditional event; fallback every 30m | global 2m | **wrong trigger abstraction** |
| `live_score_push` | local launchd | every 120 sec; internal smart-skip | 2m | cadence aligned if launchd actually loaded |
| `odds_refresh` | local launchd | every 300 sec; internal per-signal due logic | not present in current aggregate health registry | **coverage gap** |
| `auto_heal_ai` | local launchd | every 900 sec | not a normal service health row | governance/recovery plane; should be separately observable |
| `cloud_healer` | GitHub Actions + Worker trigger | Worker primary health trigger; GHA 2h fallback | not represented as normal job health | recovery plane should expose ability to act |

---

# 3. Execution Truth defects

## 3.1 Caller-controlled status

`health_writer` currently persists caller-provided:
- `status`
- `exit_code`

without enforcing their semantic relationship.

Known impossible public states already occurred:

```text
status = ok
exit_code = 1
```

for multiple Tennis jobs.

### P0-B rule
For a completed execution:
- `exit_code != 0` cannot produce `execution_status=success`;
- a service may only be `ok` when execution evidence supports it;
- fallback may yield `degraded`, not fake success.

---

## 3.2 Hardcoded zero exit codes in workflows

Observed examples:

### Bundesliga2 retrain
Workflow derives `STATUS` from job status but calls:

```text
--exit-code 0
```

unconditionally.

### Bundesliga2 closing odds
Health step also calls:

```text
--exit-code 0
```

even though prior step could have failed.

This proves P0-B cannot depend on every YAML author remembering to manually pass a correct exit code.

### Target
Prefer one wrapper/action/helper that derives execution truth from the runner context rather than free-form status strings.

---

# 4. Schedule Truth defects

## 4.1 Tennis Scan
Actual active schedule:
- 02 UTC
- 06 UTC
- 09 UTC
- 12 UTC
- 15 UTC
- 18 UTC
- 21 UTC
- 23 UTC.

Current health registry:
- “4x/day 06/11/16/21 UTC”
- interval 21600 seconds.

This is direct configuration drift.

## 4.2 Tennis Retrain
Actual active workflow:
- daily 05:00 UTC.

Current health registry:
- weekly Monday 03:00 UTC.

This is not a small grace error; it represents a different job contract.

## 4.3 Bundesliga2 Live Push
Actual GitHub trigger:
- Fri: every 2 min, 18–22 UTC
- Sat: every 2 min, 11–22 UTC
- Sun: every 2 min, 11–22 UTC.

Current aggregate stale logic treats it as if a run is expected every 2 minutes throughout the week.

Correct off-window state:
`inactive` / `not_expected`.

## 4.4 Bundesliga2 Closing Odds
Actual workflow runs only at four specific weekly pre-kickoff points.

A global 15-minute stale threshold is structurally invalid.

## 4.5 Event-driven Consumer
Primary trigger is not a schedule at all:
- Worker checks pending state and dispatches GitHub job when needed.
- GitHub has a 30-minute fallback.

Correct monitor questions are:
1. Was the event dispatcher healthy?
2. If pending work existed, was dispatch/run latency acceptable?
3. Is the fallback schedule healthy?

“Did consumer run in the last 2 minutes?” is not the correct invariant.

---

# 5. Proposed `JobExpectation` model

P0-B should use a machine-readable representation conceptually equivalent to:

```python
JobExpectation(
    job="...",
    execution_planes=("github_actions",),
    trigger_type="cron_set",  # interval | cron_set | windowed_interval | event_with_fallback
    cron_utc=(...),
    interval_s=None,
    windows=None,
    event_condition=None,
    fallback_cron=None,
    grace_s=...,
    required=True,
)
```

For a windowed job:

```python
JobExpectation(
    job="bundesliga2_live_push",
    execution_planes=("github_actions",),
    trigger_type="windowed_interval",
    interval_s=120,
    windows=(
        "Fri 18:00-22:59 UTC",
        "Sat 11:00-22:59 UTC",
        "Sun 11:00-22:59 UTC",
    ),
    grace_s=300,
)
```

For event-driven consumer:

```python
JobExpectation(
    job="consume_pending_bets",
    execution_planes=("worker", "github_actions"),
    trigger_type="event_with_fallback",
    event_condition="pending_bets_or_cancel_requests_exist",
    fallback_cron="*/30 * * * *",
)
```

The exact Python/YAML form is a Builder design decision. The semantics are not.

---

# 6. Required state vocabulary

Recommended separation:

## Execution state
- `success`
- `failure`
- `running`
- `skipped`
- `unknown`.

## Expectation state
- `expected_now`
- `not_expected`
- `event_pending`
- `unknown`.

## Service state
- `ok`
- `degraded`
- `error`
- `stale`
- `inactive`
- `unknown`.

This avoids using `stale` for “the job correctly had nothing to do”.

---

# 7. Recovery-plane audit

The recovery subsystem must be monitored as a capability.

Current healer mappings include workflow filenames that are not active because current repo contains `.disabled` variants for several names.

Examples include mappings to:
- `daily_scan.yml`
- `auto_retrain.yml`
- `closing_odds.yml`
- `settle.yml`
- `prematch_scan.yml`
- `live_score_push.yml`

while active workflow directory contains their `.disabled` variants.

### Required invariant
Before a healer reports a retry:
- target exists;
- target is active;
- dispatch method is supported;
- target is not already running;
- action is allowlisted.

Otherwise:
`RECOVERY_UNAVAILABLE`.

---

# 8. Monitoring coverage gaps

## Odds refresher
Tracked launchd plist runs every 5 minutes, but current aggregate health does not expose a dedicated `odds_refresh` job row.

Given refreshed odds are a core actionability dependency, this is an important gap.

Future monitoring should distinguish:
- refresher process health;
- refreshed-odds semantic freshness.

The second belongs to Wave 3D; the first belongs to P0-B.

## AI healer
The 15-minute AI healer is operational/recovery infrastructure, not normal product health. It should still expose:
- loaded/enabled state;
- last diagnostic execution;
- whether code-write capability is disabled under governance;
- last recovery action.

---

# 9. P0-B implementation packets

## B1 — Execution Truth
Primary:
- `src/monitoring/health_writer.py`
- `src/monitoring/aggregate_health.py`
- health-writing workflow/wrapper callsites
- `tests/monitoring/*`

Close:
- MON-001
- MON-011
- OPS-006.

## B2 — Schedule Truth
Primary:
- new canonical expectation registry
- aggregate health
- parity tests against `.github/workflows/` and tracked launchd plists.

Close:
- MON-002
- MON-012.

## B3 — Recovery Truth
Primary:
- `cloud_healer.yml`
- Worker recovery mapping
- deterministic recovery registry/tests.

Do not mix AI source-mutation removal here; that is P0-D D1.

## B4 — Provenance
Primary:
- health/publication build info
- source release resolver
- Worker release provenance.

Close:
- REL-004
- REL-006 partial
- REL-007
- MON-008.

---

# 10. Acceptance tests that should exist

1. `ok + exit_code=1` is impossible.
2. `error + exit_code=0` cannot be silently normalized to ok.
3. malformed/missing execution evidence becomes unknown/error.
4. Tennis Scan next expected occurrence is computed from actual 8-point cron.
5. Tennis Retrain expected daily at 05 UTC.
6. BL2 Live Push is not stale Tuesday at noon.
7. BL2 Live Push can become stale inside active Fri/Sat/Sun window.
8. BL2 Closing Odds is inactive between scheduled kickoff snapshots.
9. Consumer is not stale solely because no pending event existed.
10. Consumer fallback schedule health is separately tested.
11. Disabled workflow is never treated as active recovery target.
12. Recovery target missing → `RECOVERY_UNAVAILABLE`.
13. Odds refresher execution is visible as its own job.
14. source release SHA differs correctly from runtime/data HEAD after a data-only bot commit.

---

# 11. CEO recommendation

Do not patch the current `JOB_SCHEDULE` dictionary with new numbers.

That would fix today's symptoms and recreate the same class of failure later.

P0-B should introduce a **first-class execution expectation model** and make monitoring derive truth from:
- real execution evidence;
- real trigger semantics;
- real active windows;
- explicit recovery capability.

That is the difference between a dashboard that looks healthy and an operational truth system.
