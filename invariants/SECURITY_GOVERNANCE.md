---
type: "invariant-domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
domains:
  - Governance
  - Product
  - Security
---
# Security Governance Invariants

Canonical definitions for 28 invariants.

## SEC-001

**Severity:** P0  
**Domain:** Security  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Personal betting ledger is not publicly exposed.

**Canonical owner:** Private financial datastore

**Current evidence:** Repo is public and per-user ledger is tracked.

**Failure mode:** Privacy breach.

**Production monitor target:** Public path scanner for ledger/user financial files.

**Closure / next action:** P0-C.

## SEC-002

**Severity:** P0  
**Domain:** Security  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Legal/privacy text matches actual persistence behavior.

**Canonical owner:** Legal/data architecture

**Current evidence:** Legal says bankroll/bet log localStorage-only while backend ledger exists.

**Failure mode:** Misleading privacy disclosure.

**Production monitor target:** Policy-vs-data-map review.

**Closure / next action:** P0-C + legal review.

## SEC-003

**Severity:** P0  
**Domain:** Security  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
User-specific signal/financial state never falls back to another user's private state.

**Canonical owner:** User isolation

**Current evidence:** Worker can fallback missing per-user snapshot to default user.

**Failure mode:** Cross-user disclosure.

**Production monitor target:** Requested user != payload owner.

**Closure / next action:** P0-C.

## SEC-004

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
User tokens are scoped, revocable and never exposed in URLs/loggable query strings.

**Canonical owner:** Auth boundary

**Current evidence:** Token rotation exists; complete browser transport audit not finished.

**Failure mode:** Credential leakage.

**Production monitor target:** Token-location audit.

**Closure / next action:** P0-C.

## SEC-005

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Master token is never exposed to browser clients.

**Canonical owner:** Worker auth

**Current evidence:** Architecture distinguishes master/per-user; live secret handling not reverified tonight.

**Failure mode:** Total backend compromise.

**Production monitor target:** Secret exposure scan.

**Closure / next action:** P0-C.

## SEC-006

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Per-user authorization controls every read/write queue and signal operation.

**Canonical owner:** Worker auth

**Current evidence:** Per-user KV routing exists; fallback semantics weaken isolation.

**Failure mode:** Cross-user mutation/read.

**Production monitor target:** Authorization matrix tests.

**Closure / next action:** P0-C.

## SEC-007

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Push subscriptions are user/privacy scoped and have deletion lifecycle.

**Canonical owner:** Push subsystem

**Current evidence:** KV push_subs exists; expiry pruning/outcome checks exist.

**Failure mode:** Persistent endpoint exposure.

**Production monitor target:** Subscription ownership/expiry monitor.

**Closure / next action:** P0-C.

## SEC-008

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Public Pages contains no secrets/private operational artifacts.

**Canonical owner:** Static publication boundary

**Current evidence:** No known secret claim from current audit, but privacy data coupling exists.

**Failure mode:** Credential/data exposure.

**Production monitor target:** Public artifact allowlist scan.

**Closure / next action:** P0-C.

## SEC-009

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Changing repository visibility cannot silently break public PWA availability.

**Canonical owner:** Deployment/privacy migration

**Current evidence:** Pages/repo coupling requires planned migration.

**Failure mode:** Privacy fix causes outage.

**Production monitor target:** Migration rehearsal.

**Closure / next action:** P0-C.

## SEC-010

**Severity:** P1  
**Domain:** Security  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Multi-user identity has explicit owner metadata in every private snapshot/ledger.

**Canonical owner:** Identity schema

**Current evidence:** Filename/KV key imply user; payload ownership metadata not universal.

**Failure mode:** Misrouting undetectable.

**Production monitor target:** owner/user_id field parity.

**Closure / next action:** P0-C.

## GOV-001

**Severity:** P0  
**Domain:** Governance  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
ChatGPT/CEO is read-only to GitHub/project; no mutations.

**Canonical owner:** Human governance

**Current evidence:** Explicit operating rule.

**Failure mode:** Auditor independence lost.

**Production monitor target:** Audit tool usage policy.

**Closure / next action:** Preserve.

## GOV-002

**Severity:** P0  
**Domain:** Governance  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Claude/authorized Builder is sole normal source-code mutator.

**Canonical owner:** Builder governance

**Current evidence:** `auto_heal_ai.py` can autonomously edit/commit/push scripts.

**Failure mode:** Unreviewed autonomous source mutation.

**Production monitor target:** Source commit actor/path audit.

**Closure / next action:** P0-D.

## GOV-003

**Severity:** P0  
**Domain:** Governance  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Autonomous healer may not bypass code review/release governance for source changes.

**Canonical owner:** Recovery governance

**Current evidence:** AI healer applies FIX then commits/pushes after pytest.

**Failure mode:** AI-generated production mutation.

**Production monitor target:** Auto-heal source commit detector.

**Closure / next action:** P0-D.

## GOV-004

**Severity:** P0  
**Domain:** Governance  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
No auto-betting / implicit logging of real bets without explicit user action.

**Canonical owner:** CEO rule

**Current evidence:** No broad proof of active autobetting; historical auto-log mechanisms governed by tests.

**Failure mode:** Unapproved financial record/action.

**Production monitor target:** New ledger source without user/approved scanner semantics.

**Closure / next action:** Keep hard regression.

## GOV-005

**Severity:** P1  
**Domain:** Governance  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Hard CEO safety invariants are not ordinary user-overridable tuning flags.

**Canonical owner:** Policy architecture

**Current evidence:** Config mixes rollout/user modes and policy; `--all-live` exists.

**Failure mode:** Operator bypasses safety.

**Production monitor target:** Override use audit.

**Closure / next action:** P0-D.

## GOV-006

**Severity:** P1  
**Domain:** Governance  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Tennis live/shadow rollout must be justified by gate evidence, not one-off user override.

**Canonical owner:** Model/rollout governance

**Current evidence:** Production config broadly forces live categories.

**Failure mode:** Unvalidated category bets enter production.

**Production monitor target:** Live category without gate artifact.

**Closure / next action:** P0-D.

## GOV-007

**Severity:** P1  
**Domain:** Governance  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Every production source change has explicit rollback reference.

**Canonical owner:** Release governance

**Current evidence:** Rollback rule/process exists but not universal artifact.

**Failure mode:** Slow unsafe rollback.

**Production monitor target:** Release manifest completeness.

**Closure / next action:** P0-D.

## GOV-008

**Severity:** P1  
**Domain:** Governance  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Backfills/migrations are auditable, reversible or explicitly immutable-preserving.

**Canonical owner:** Data governance

**Current evidence:** Many backfill scripts; no single migration ledger.

**Failure mode:** Historical truth silently changed.

**Production monitor target:** Migration manifest.

**Closure / next action:** P0-D.

## GOV-009

**Severity:** P1  
**Domain:** Governance  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
CEO score increases only for production evidence; branch work is projected separately.

**Canonical owner:** CEO governance

**Current evidence:** New canonical scorecard rule.

**Failure mode:** Score inflation hides risk.

**Production monitor target:** Scorecard audit.

**Closure / next action:** Preserve.

## GOV-010

**Severity:** P1  
**Domain:** Governance  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Builder reports are evidence inputs, never substitutes for independent CEO verification.

**Canonical owner:** CEO/Builder process

**Current evidence:** Repeated P0-A reviews caught report/code mismatches.

**Failure mode:** False completion accepted.

**Production monitor target:** Independent SHA/diff/CI review.

**Closure / next action:** Preserve.

## UX-001

**Severity:** P0  
**Domain:** Product  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
UI labels distinguish scan odds from current executable odds.

**Canonical owner:** PWA

**Current evidence:** Some displays distinguish; production model-tip actions blur semantics.

**Failure mode:** User believes stale scan price is current.

**Production monitor target:** Rendered label vs payload odds.

**Closure / next action:** P0-A.

## UX-002

**Severity:** P0  
**Domain:** Product  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Disabled/non-actionable signal remains informative without misleading Value CTA.

**Canonical owner:** PWA

**Current evidence:** P0-A target manual/informational fallback.

**Failure mode:** Fail-closed becomes unusable or misleading.

**Production monitor target:** CTA semantics browser test.

**Closure / next action:** P0-A.

## UX-003

**Severity:** P1  
**Domain:** Product  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Manual action is clearly labeled as manual and not model-approved.

**Canonical owner:** PWA

**Current evidence:** P0-A explicit flow candidate.

**Failure mode:** User confuses judgment bet with SportsBrain signal.

**Production monitor target:** Manual badge/source.

**Closure / next action:** P0-A.

## UX-004

**Severity:** P1  
**Domain:** Product  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Zero actionable signals is a valid usable app state, not an error/fail-open trigger.

**Canonical owner:** PWA

**Current evidence:** P0-A tests target zero-signal usability.

**Failure mode:** System fabricates action to avoid empty UI.

**Production monitor target:** Zero-signal browser smoke.

**Closure / next action:** P0-A.

## UX-005

**Severity:** P1  
**Domain:** Product  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
User sees meaningful degraded/stale state rather than silent outdated data.

**Canonical owner:** PWA/health

**Current evidence:** Stale banner exists; semantic trust incomplete.

**Failure mode:** User acts on stale system.

**Production monitor target:** Degraded banner tied to trust state.

**Closure / next action:** Wave3D.

## UX-006

**Severity:** P1  
**Domain:** Product  
**Production status:** `partial`  
**P0-A overlay status:** `branch_partial`

### Invariant
Open/pending/settled/cancelled bet lifecycle is clearly represented and consistent with backend.

**Canonical owner:** PWA + ledger

**Current evidence:** Pending UI exists; durability semantics still being hardened.

**Failure mode:** UI says synced when not durable.

**Production monitor target:** Lifecycle state parity.

**Closure / next action:** P0-A/P0-B.

## UX-007

**Severity:** P1  
**Domain:** Product  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Browser error paths never silently convert Value action into another semantic.

**Canonical owner:** PWA

**Current evidence:** Historical alternate paths/coercions; P0-A improves.

**Failure mode:** User intent changes invisibly.

**Production monitor target:** Browser request source/identity assertion.

**Closure / next action:** P0-A.

## UX-008

**Severity:** P1  
**Domain:** Product  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Public PWA release gets real-browser verification on final deployed assets.

**Canonical owner:** Release UX

**Current evidence:** Real Playwright exists locally; final P0-A focused run pending and public fetch historically limited.

**Failure mode:** Repo tests pass but deployed PWA broken.

**Production monitor target:** Public smoke evidence.

**Closure / next action:** Release closure.
