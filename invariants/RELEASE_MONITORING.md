---
type: "invariant-domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
domains:
  - Monitoring
  - Operations
  - Release
---
# Release Monitoring Invariants

Canonical definitions for 30 invariants.

## REL-001

**Severity:** P0  
**Domain:** Release  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Source-changing production commit must have relevant green CI.

**Canonical owner:** CI gate

**Current evidence:** `require_green_ci.py` fail-closed exact/inherited logic.

**Failure mode:** Untested source runs production.

**Production monitor target:** Source SHA without green run.

**Closure / next action:** Preserve.

## REL-002

**Severity:** P0  
**Domain:** Release  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Failed/active/missing ambiguous CI is not treated as green.

**Canonical owner:** CI gate

**Current evidence:** Explicit decision logic.

**Failure mode:** Red build deployed.

**Production monitor target:** Guard failure metrics.

**Closure / next action:** Preserve.

## REL-003

**Severity:** P1  
**Domain:** Release  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Path-excluded data-only HEAD may inherit green source ancestor only when ancestry is proven.

**Canonical owner:** CI gate

**Current evidence:** Compare API ancestor check.

**Failure mode:** Runtime commit hides unrelated source change.

**Production monitor target:** Source/runtime classifier.

**Closure / next action:** Preserve.

## REL-004

**Severity:** P1  
**Domain:** Release  
**Production status:** `enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Source Release SHA is published separately from Runtime/Data HEAD.

**Canonical owner:** Build provenance

**Current evidence:** P0-B4 production verified 2026-08-17T22:47:41Z. `provenance_meta.json` written by `scripts/record_source_release.py` on each ci_gates success. `docs/data/health.json` publishes `source_release_sha`, `runtime_data_sha`, and `source_runtime_consistent` as separate truths. Natural post-release consume run `32077550579` confirmed `source_runtime_consistent: true` with SHA `b81d606641...` independent of source release SHA `7cd6c679...`. Pages deployment `32077608783` served correct provenance. Evidence: EVD-P0B-004-PROD-001. P0D-001 (2026-08-18): source_release_sha `c79603efcc...` (PR #18 squash-merge) correctly recorded; 3 runtime SHAs (d980d04, fd6e6f3, 5117817) advance independently; provenance_meta.json not overwritten by runtime commits. Evidence: EVD-P0D-001-PROD-001.

**Failure mode:** Users/monitor cannot identify validated source.

**Production monitor target:** Public health.json with both SHAs.

**Closure / next action:** Preserve. OPS-007 (runtime-main churn architecture) remains P0-D scope.

## REL-005

**Severity:** P1  
**Domain:** Release  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Rollback target is explicit and tested for source releases.

**Canonical owner:** Rollback governance

**Current evidence:** Rollback script exists; full deploy-unit verification not complete.

**Failure mode:** Incident recovery uncertain.

**Production monitor target:** Rollback drill outcome.

**Closure / next action:** P0-D.

## REL-006

**Severity:** P1  
**Domain:** Release  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Worker deploy version is tied to source release SHA.

**Canonical owner:** Worker release provenance

**Current evidence:** No comprehensive evidence in current map.

**Failure mode:** Worker/main semantic drift.

**Production monitor target:** Worker version endpoint/hash.

**Closure / next action:** P0-B/3D.

## REL-007

**Severity:** P1  
**Domain:** Release  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Pages/public PWA version is tied to source release SHA.

**Canonical owner:** PWA provenance

**Current evidence:** Build info exists but runtime HEAD confusion remains.

**Failure mode:** Browser runs unknown source.

**Production monitor target:** Public build SHA verification.

**Closure / next action:** Wave3D.

## REL-008

**Severity:** P1  
**Domain:** Release  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Critical deterministic betting safety tests are hard CI gates.

**Canonical owner:** CI

**Current evidence:** Production main CI lacks Node Worker contract; P0-A adds it.

**Failure mode:** Safety regression passes CI.

**Production monitor target:** CI job contains Worker contract.

**Closure / next action:** Merge P0-A.

## REL-009

**Severity:** P1  
**Domain:** Release  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Browser-contract tests cover PWA safety semantics; actual browser smoke required before release closure.

**Canonical owner:** Release validation

**Current evidence:** Node pure-function tests not Playwright; real Playwright exists but final P0-A run outstanding.

**Failure mode:** UI wiring bug escapes.

**Production monitor target:** Focused real-browser result.

**Closure / next action:** Final P0-A.

## REL-010

**Severity:** P1  
**Domain:** Release  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Runtime data bots cannot mutate source paths.

**Canonical owner:** Git writer governance

**Current evidence:** Safe-push/path controls exist; architecture historically had contamination incidents.

**Failure mode:** Bot changes code unintentionally.

**Production monitor target:** Bot commit changed path outside allowlist.

**Closure / next action:** P0-D/Wave3D.

## MON-001

**Severity:** P0  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
`status=ok` and non-zero execution exit code cannot coexist.

**Canonical owner:** Health writer

**Current evidence:** Health writer trusts caller; known workflow contradiction.

**Failure mode:** False green.

**Production monitor target:** Health rows with ok + exit!=0.

**Closure / next action:** P0-B.

## MON-002

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Expected cadence definitions match actual active workflows/launchd schedules.

**Canonical owner:** Health schedule authority

**Current evidence:** Hardcoded JOB_SCHEDULE can drift from workflows.

**Failure mode:** Healthy job marked stale or dead job marked fine.

**Production monitor target:** Schedule source parity.

**Closure / next action:** P0-B.

## MON-003

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Aggregate health cannot overwrite/erase valid signal payload when cloud upload fails.

**Canonical owner:** Health publisher

**Current evidence:** Guard/merge logic exists.

**Failure mode:** Monitoring damages product data.

**Production monitor target:** Payload integrity after health upload.

**Closure / next action:** Preserve/test.

## MON-004

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Outcome checks verify product outcomes, not only cron execution.

**Canonical owner:** Outcome monitoring

**Current evidence:** Stuck bets, stale signals, push, silent settle exist.

**Failure mode:** Jobs green while product broken.

**Production monitor target:** Outcome symptom coverage.

**Closure / next action:** Expand.

## MON-005

**Severity:** P0  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Production Trust detects actionable signal with stale/missing/wrong-market odds.

**Canonical owner:** Future Trust monitor

**Current evidence:** Not in current health.

**Failure mode:** Unsafe bet despite green jobs.

**Production monitor target:** Semantic signal sweep.

**Closure / next action:** Wave3D.

## MON-006

**Severity:** P0  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Production Trust detects stake >5% or >3 active bets.

**Canonical owner:** Future Trust monitor

**Current evidence:** No current semantic monitor.

**Failure mode:** Risk invariant violated silently.

**Production monitor target:** Recompute ledger risk.

**Closure / next action:** Wave3D.

## MON-007

**Severity:** P0  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Production Trust detects false Tennis LIVE / open Tennis bet missing from live system.

**Canonical owner:** Future Trust monitor

**Current evidence:** Current live system stronger but no universal trust assertion.

**Failure mode:** Incorrect live UX/settlement.

**Production monitor target:** Event state vs evidence/open bet join.

**Closure / next action:** Wave3D.

## MON-008

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Production Trust detects source-release/CI/runtime-head mismatch.

**Canonical owner:** Release monitor

**Current evidence:** P0-B4 production verified 2026-08-17T22:47:41Z. Public `docs/data/health.json` carries `source_release_sha`, `runtime_data_sha`, `source_runtime_consistent`, and `source_ci` identity fields. `_check_source_runtime_consistency()` classifies SOURCE..RUNTIME git log against canonical source paths; `source_runtime_consistent: true` confirms no source-changing commits exist between source release and runtime/data HEAD. C5 fix (`fetch-depth: 0` in `consume_pending_bets.yml`) ensures classification succeeds on shallow-clone-free full-history checkout. Evidence: EVD-P0B-004-PROD-001.

**Failure mode:** Unknown production source.

**Production monitor target:** source_runtime_consistent field in published health.json.

**Closure / next action:** Preserve. OPS-007 runtime-main architecture remains P0-D scope.

## MON-009

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Production Trust detects fixture identity collisions.

**Canonical owner:** Identity monitor

**Current evidence:** No global collision monitor.

**Failure mode:** Wrong event state reused.

**Production monitor target:** Duplicate registry key with incompatible event metadata.

**Closure / next action:** Wave3D.

## MON-010

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Monitoring distinguishes DEGRADED from UNSAFE.

**Canonical owner:** Trust policy

**Current evidence:** Current aggregate has ok/degraded/down, not safety semantics.

**Failure mode:** Money-risk condition treated like cosmetic staleness.

**Production monitor target:** Severity policy tests.

**Closure / next action:** Wave3D.

## MON-011

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Health check failure itself becomes visible, not silently empty-good.

**Canonical owner:** Monitoring engine

**Current evidence:** Outcome checks emit checker_error warning; other readers may return empty.

**Failure mode:** Blind spot looks healthy.

**Production monitor target:** Checker execution coverage.

**Closure / next action:** P0-B.

## MON-012

**Severity:** P1  
**Domain:** Monitoring  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Freshness heartbeats do not masquerade as semantic data freshness.

**Canonical owner:** Trust timestamps

**Current evidence:** Multiple updated/heartbeat timestamps exist.

**Failure mode:** Stale odds/signals hidden by unrelated heartbeat.

**Production monitor target:** Timestamp provenance checks.

**Closure / next action:** P0-B/Wave3D.

## OPS-001

**Severity:** P0  
**Domain:** Operations  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
PWA remains continuously usable during refactor/deployment.

**Canonical owner:** Product operations

**Current evidence:** Explicit CEO rule; not every release path has live browser proof.

**Failure mode:** User-facing outage.

**Production monitor target:** Public PWA availability check.

**Closure / next action:** Release gate.

## OPS-002

**Severity:** P1  
**Domain:** Operations  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Atomic file writes protect shared JSON/ledger artifacts against partial writes.

**Canonical owner:** Persistence utilities

**Current evidence:** Atomic IO/file locks exist in key paths.

**Failure mode:** Corrupt JSON/CSV.

**Production monitor target:** Parse failure/atomic writer coverage.

**Closure / next action:** Expand.

## OPS-003

**Severity:** P1  
**Domain:** Operations  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Concurrent Git/runtime writers have path-scoped conflict policy.

**Canonical owner:** Git operations

**Current evidence:** Safe-push logic and workflow concurrency exist after incidents.

**Failure mode:** Lost/overwritten runtime state.

**Production monitor target:** Conflict/retry telemetry.

**Closure / next action:** P0-D.

## OPS-004

**Severity:** P1  
**Domain:** Operations  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Cloud publication failure is observable and does not silently claim success.

**Canonical owner:** Publisher

**Current evidence:** Various paths log failures, some non-fatal.

**Failure mode:** PWA stale despite green job.

**Production monitor target:** Publish outcome health.

**Closure / next action:** P0-B.

## OPS-005

**Severity:** P1  
**Domain:** Operations  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Every critical external provider has explicit timeout/retry/fallback/fail-closed policy.

**Canonical owner:** Provider layer

**Current evidence:** Retry helpers/provider chains exist; full inventory not verified.

**Failure mode:** Hang or bad fallback.

**Production monitor target:** Provider latency/error/fallback monitor.

**Closure / next action:** Provider reliability workstream.

## OPS-006

**Severity:** P1  
**Domain:** Operations  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Local launchd runtime state is separately observable from GitHub Actions state.

**Canonical owner:** Runtime monitoring

**Current evidence:** P0-B3 production verification confirms `com.sportsbrain.auto-heal-ai` loaded (StartInterval=900) with natural post-release run at `2026-08-17T19:25:02Z`. P0-B4 production verified 2026-08-17T22:47:41Z: per-job runtime/cloud separation now operational via `source_runtime_consistent` field in published health.json. Evidence: EVD-P0B-003-PROD-001, EVD-P0B-004-PROD-001.

**Failure mode:** Local job dead while cloud healthy.

**Production monitor target:** Runtime source field / heartbeat origin.

**Closure / next action:** Preserve. OPS-007 runtime-writer architecture scope remains P0-D.

## OPS-007

**Severity:** P1  
**Domain:** Operations  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
No single bot can continuously move `main` in a way that invalidates source-release provenance.

**Canonical owner:** Git runtime architecture

**Current evidence:** Frequent tennis runtime commits move HEAD every minutes.

**Failure mode:** PR mergeability/source identity noise.

**Production monitor target:** Runtime commit rate/source release marker.

**Closure / next action:** P0-D architecture decision.

## OPS-008

**Severity:** P1  
**Domain:** Operations  
**Production status:** `unverified`  
**P0-A overlay status:** `unverified`

### Invariant
Disaster recovery identifies durable sources for ledger, model, config, Worker and public assets separately.

**Canonical owner:** Recovery

**Current evidence:** Partial rollback tooling; full DR model not audited.

**Failure mode:** Recovery restores inconsistent components.

**Production monitor target:** DR drill/manifests.

**Closure / next action:** Future ops workstream.
