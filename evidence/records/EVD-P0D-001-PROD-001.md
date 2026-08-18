---
id: EVD-P0D-001-PROD-001
type: evidence
title: P0-D1 Standard Runtime Writer Governance production closure evidence
status: current
canonical: true
tier: warm
created_at: 2026-08-18T19:30:42Z
updated_at: 2026-08-18T19:36:30Z
freshness_class: release-bound
evidence_type: production-source
sha: c79603efcc69891e38433d9e9e15123711c00938
environment: production
scope: TASK-P0D-001 Standard Runtime Writer Governance — path allowlist fail-closed, governed persistence primitive, writer identity, Class A classification, failure-masking gate
workstream: P0-D
verified_by:
  - VER-P0D-001-PROD-001
findings:
  - FND-20260814-017
  - FND-20260814-018
---
# P0-D1 Standard Runtime Writer Governance — Production Closure Evidence

## Source release

- Source Release SHA: `c79603efcc69891e38433d9e9e15123711c00938`
- PR #18 (`task/TASK-P0D-001`), pre-merge head: `f37e15b72ae1f9c582d0a6e9251bcce16ff820ba`
- Squash-merge to main: `2026-08-18T19:30:42Z`
- Post-merge CI run: `32177012250` — **success**

## CI gates passed

- HARD GATE 8 (Runtime Writer Governance): **16/16 PASS**
- All prior hard gates (compile, smoke, lint, provenance, privacy, P0C-002): **PASS**
- `source_release_sha` written to `docs/data/provenance_meta.json` by CI: `c79603efcc69891e38433d9e9e15123711c00938`
- `recorded_at`: `2026-08-18T19:31:44Z`

## Provenance meta (post-merge)

```json
{
  "schema_version": "1",
  "source_release_sha": "c79603efcc69891e38433d9e9e15123711c00938",
  "source_ci": {
    "run_id": "32177012250",
    "workflow": "CI Gates (compile + smoke tests + lint)",
    "status": "success",
    "head_sha": "c79603efcc69891e38433d9e9e15123711c00938"
  },
  "recorded_at": "2026-08-18T19:31:44Z"
}
```

## Production writer verification

### tennis_live_scan (Class A) — run 32177254238

- Workflow: `tennis_live_scan.yml`
- Head SHA on main: runtime commit (post-source-release, distinct SHA)
- Primitive used: `bash scripts/_bot_commit_push.sh "auto: tennis live ..."` — **VERIFIED**
- No `|| true` masking: **VERIFIED** (CEO-final fix)
- Identity: `git config user.name "SportsBrain Bot"` — **VERIFIED**
- Provenance annotation: `[run=32177254238]` in commit message — **VERIFIED**
- Push: `push ok (attempt 1)` — **VERIFIED**
- Runtime commit SHA: `d980d0493` (distinct from source_release_sha) — **VERIFIED**

### tennis_scan (Class A) — run 32177257124

- Workflow: `tennis_scan.yml`
- Primitive used: `bash scripts/_bot_commit_push.sh "auto: tennis scan ..."` — **VERIFIED**
- Identity: `SportsBrain Bot` — **VERIFIED**
- Provenance annotation: `[run=32177257124]` — **VERIFIED**
- Push: `push ok (attempt 1)` — **VERIFIED**
- Runtime commit SHA: `fd6e6f3ba` (distinct) — **VERIFIED**

### bundesliga2_scan (Class A) — run 32177264550

- Workflow: `bundesliga2_scan.yml`
- Primitive used: `bash scripts/_bot_commit_push.sh "auto: bl2 scan ..."` — **VERIFIED**
- Identity: `SportsBrain Bot` — **VERIFIED**
- Provenance annotation: `[run=32177264550]` — **VERIFIED**
- Push: `push ok (attempt 1)` — **VERIFIED**
- Runtime commit SHA: `511781703` (distinct) — **VERIFIED**

## Source/runtime SHA separation

Main log post-merge (descending):
- `d980d0493` — `auto: tennis live 19:36 [run=32177254238]` (runtime)
- `fd6e6f3ba` — `auto: tennis scan 2026-08-18 [run=32177257124]` (runtime)
- `511781703` — `auto: bl2 scan 2026-08-18T19:34 [run=32177264550]` (runtime)
- `b699ccb32` — `auto: record source release c79603efcc...` (provenance annotation)
- `c79603efc` — `feat(P0D-001): runtime writer governance...` ← **source_release_sha**

Runtime SHAs are distinct from and advance independently of `source_release_sha`. `provenance_meta.json` was not overwritten by runtime commits. **SEPARATION INTACT.**

## What P0D-001 delivered

- `scripts/_git_safe_push.sh`: `_bot_permitted()` POSIX case-pattern allowlist; `bot_assert_staged_safe()` fail-closed validator
- `scripts/_bot_commit_push.sh`: governed persistence primitive with path validation, identity enforcement, `GITHUB_RUN_ID` annotation, 5× retry push
- All 8 Class A runtime writers routed through `_bot_commit_push.sh` (tennis_scan, tennis_live_scan, tennis_stats_snapshot, tennis_recalibrate, tennis_odds_snapshot, bundesliga2_closing_odds, bundesliga2_live_push, bundesliga2_scan)
- `bundesliga2_closing_odds.yml`, `bundesliga2_live_push.yml`, `bundesliga2_scan.yml`: converted from inline retry loops to Class A
- `tennis_live_scan.yml`: `|| true` failure-masking removed
- `tests/monitoring/test_writer_governance.py`: 16 governance tests (HARD GATE 8) including shell allowlist bridge via subprocess, integration tests for `bot_assert_staged_safe()`, complete writer classification, failure-masking regression gate
- SportsBrainMemory `workstreams/P0-D.md`: `started_at` field removed (validator compliance)

## Rollback identity

Pre-merge PR head: `f37e15b72ae1f9c582d0a6e9251bcce16ff820ba`  
To revert: `git revert c79603efcc69891e38433d9e9e15123711c00938` (restore per-workflow persistence; retain source path fail-closed guard from `_git_safe_push.sh`)

## Remaining deferred risks

- **Class B** (tennis_settle, tennis_closing_odds, bundesliga2_settle, consume_pending_bets): retain inline retry without path validation → P0D-002
- **Class C** (tennis_lgbm_retrain, tennis_elo_refresh, bundesliga2_retrain): model promotion governance → MODEL_INTEGRITY (TASK-MODEL-002), not P0D-003
- **Class D** (cloud_healer): AI healer source mutation removal → P0D-003
- **Local launchd cron jobs**: call `_git_safe_push.sh` directly, not through `_bot_commit_push.sh` → P0D-002 scope
- Pre-existing: `test_fnd004_mandatory_submit_delivers_canonical_payload` — not introduced by P0D-001
