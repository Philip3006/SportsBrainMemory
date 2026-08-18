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
**Production status:** `enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
User-specific signal/financial state never falls back to another user's private state.

**Canonical owner:** User isolation

**Current evidence:** P0C-002 production verified (2026-08-18): authenticated /me endpoint deployed with exact per-user token owner routing; no DEFAULT_USER fallback; master token → 403 fail-closed; Alice token cannot reach Bob's state; GET /me no token → 401; GET /me Philip per-user token → exact owner (CI Suite 16 T3/T6); public /signals.json zero private fields (26/26 regression PASS); Worker `8b4f5ad5-c10d-402e-8636-16d0c5b00c97`. Note: physical KV key migration deferred — Philip's exact-owner key still maps to legacy signals_json, which is exact routing not fallback. This is acceptable for enforced status. Evidence: EVD-P0C-002-PROD-001.

**Failure mode:** Cross-user disclosure.

**Production monitor target:** Requested user != payload owner.

**Closure / next action:** Preserve enforcement; monitor via /me exact-owner routing and HARD GATE 7.

## SEC-004

**Severity:** P1  
**Domain:** Security  
**Production status:** `enforced`  
**P0-A overlay status:** `partial`

### Invariant
User tokens are scoped, revocable and never exposed in URLs/loggable query strings.

**Canonical owner:** Auth boundary

**Current evidence:** P0C-002 production verified (2026-08-18): ?token= long-lived auth ingestion removed from browser; tokens transmitted only via Authorization header Bearer; per-user token scoping and rotation preserved; master token removed from all browser paths (scripts/create_invite.py admin CLI replaces browser flow). Worker `8b4f5ad5-c10d-402e-8636-16d0c5b00c97`, CI `32133192040` Gate 7 PASS. Evidence: EVD-P0C-002-PROD-001.

**Failure mode:** Credential leakage.

**Production monitor target:** Token-location audit; no ?token= parameter in any browser-facing URL.

**Closure / next action:** Preserve enforcement; monitor via HARD GATE 7 on every release.

## SEC-005

**Severity:** P1  
**Domain:** Security  
**Production status:** `enforced`  
**P0-A overlay status:** `partial`

### Invariant
Master token is never exposed to browser clients.

**Canonical owner:** Worker auth

**Current evidence:** P0C-002 production verified (2026-08-18): _createInvite() and all browser master-token paths removed; scripts/create_invite.py admin CLI replaces browser invite flow; GET /me master token → 403 fail-closed (live production); master token absent from all browser-facing code paths. Worker `8b4f5ad5-c10d-402e-8636-16d0c5b00c97`, CI `32133192040` Gate 7 PASS. Evidence: EVD-P0C-002-PROD-001.

**Failure mode:** Total backend compromise.

**Production monitor target:** Secret exposure scan; master token path exclusion in browser bundle.

**Closure / next action:** Preserve enforcement; monitor via HARD GATE 7 on every release.

## SEC-006

**Severity:** P1  
**Domain:** Security  
**Production status:** `enforced`  
**P0-A overlay status:** `partial`

### Invariant
Per-user authorization controls every read/write queue and signal operation.

**Canonical owner:** Worker auth

**Current evidence:** P0C-002 production verified (2026-08-18): exact per-user token owner routing on /me; cross-user auth fixes — rotate_token and token_status reject A-targeting-B; Alice cannot reach Bob's state; master token → 403 on /me; no DEFAULT_USER fallback; sb_user removed as authorization authority. Worker `8b4f5ad5-c10d-402e-8636-16d0c5b00c97`, CI `32133192040` Gate 7 PASS. Evidence: EVD-P0C-002-PROD-001.

**Failure mode:** Cross-user mutation/read.

**Production monitor target:** Authorization matrix tests; HARD GATE 7 on every release.

**Closure / next action:** Preserve enforcement; monitor via HARD GATE 7.

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
**Production status:** `enforced`  
**P0-A overlay status:** `partial`

### Invariant
Public Pages contains no secrets/private operational artifacts.

**Canonical owner:** Static publication boundary

**Current evidence:** P0C-001 production verified (2026-08-18): explicit public serializer allowlist deployed with recursive fail-closed private-key assertion. HARD GATE 6 Privacy serialization enforced in CI. Production Pages deployment `32109137419` confirmed `docs/data/signals.json` and `docs/data/signals_philip.json` contain zero forbidden private fields (`bankroll_state`, `open_bets`, `settled_bets`, `default_user`, user identity, private financial state). CEO steady-state re-check confirmed sanitized artifacts survived subsequent bot activity at runtime/data HEAD `4ab91c924a826903f6f119447d6e1f6b4fa4f509`. Deterministic publication scan is now CI-gated. Note: SEC-001 (personal ledger/DB artifacts in public *repository*) remains not_enforced — SEC-008 covers the *Pages publication tree*, not the repository file tree. Evidence: EVD-P0C-001-PROD-001. P0C-002 no regression: P0C-001 privacy regression 26/26 PASS; HARD GATE 6 passed in CI `32133192040`; public /signals.json zero private fields confirmed. Evidence: EVD-P0C-002-PROD-001.

**Failure mode:** Credential/data exposure.

**Production monitor target:** Public artifact allowlist scan (now CI-gated via HARD GATE 6 and HARD GATE 7).

**Closure / next action:** Preserve enforcement; monitor via HARD GATE 6 and HARD GATE 7 on every release.

## SEC-009

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Changing repository visibility cannot silently break public PWA availability.

**Canonical owner:** Deployment/privacy migration

**Current evidence:** P0C-002 partial mitigation: PWA dual-fetch deployed — public /signals.json and private /me are now independent failure channels. PWA smoke public logged-out 4/4 PASS (CI `32133192040`). Physical Pages/repo migration and visibility change rehearsal remain deferred. Evidence: EVD-P0C-002-PROD-001.

**Failure mode:** Privacy fix causes outage.

**Production monitor target:** Migration rehearsal; dual-fetch independence in production.

**Closure / next action:** P0-D or later — requires Pages/repo decoupling and visibility rehearsal.

## SEC-010

**Severity:** P1  
**Domain:** Security  
**Production status:** `partial`  
**P0-A overlay status:** `not_enforced`

### Invariant
Multi-user identity has explicit owner metadata in every private snapshot/ledger.

**Canonical owner:** Identity schema

**Current evidence:** P0C-002 production verified (2026-08-18): /me payload.owner is the sole authorization authority; _authenticatedOwner sourced only from /me payload.owner; private_serializer.py explicit allowlist enforces owner-scoped serialization; sb_user removed as authorization authority. Physical KV key migration and owner field in every historical ledger artifact deferred. Evidence: EVD-P0C-002-PROD-001.

**Failure mode:** Misrouting undetectable.

**Production monitor target:** owner/user_id field parity across all private artifacts.

**Closure / next action:** P0-D — requires owner metadata in every private snapshot/ledger artifact (physical KV key migration).

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
**Production status:** `partial`  
**P0-A overlay status:** `not_enforced`

### Invariant
Claude/authorized Builder is sole normal source-code mutator.

**Canonical owner:** Builder governance

**Current evidence:** P0D-001 (2026-08-18): `_git_safe_push.sh` path allowlist enforced fail-closed via `bot_assert_staged_safe()` — runtime bot writers cannot stage source files (HARD GATE 8). All 8 Class A writers use governed primitive. Source/runtime SHA separation verified in production. Remaining gap: `auto_heal_ai.py` can still autonomously edit/commit/push scripts (AI healer source mutation) → P0D-003.

**Failure mode:** Unreviewed autonomous source mutation via AI healer path.

**Production monitor target:** Source commit actor/path audit.

**Closure / next action:** P0D-003 (AI healer source mutation removal).

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
