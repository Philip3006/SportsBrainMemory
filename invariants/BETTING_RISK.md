---
type: "invariant-domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
domains:
  - Betting
  - Risk
---
# Betting Risk Invariants

Canonical definitions for 30 invariants.

## BET-001

**Severity:** P0  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Every `source=value` bet must resolve to one real canonical signal by `signal_id`.

**Canonical owner:** Canonical published signal registry

**Current evidence:** Production Worker accepts client Value payload; P0-A resolves KV signal.

**Failure mode:** Fabricated/model-unapproved bet enters production ledger.

**Production monitor target:** Value bet without canonical signal; unknown signal_id.

**Closure / next action:** Finish P0-A and verify Worker/public flow.

## BET-002

**Severity:** P0  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Canonical signal identity must bind match, market, sport and fixture identity; client may request but not redefine it.

**Canonical owner:** Canonical signal

**Current evidence:** Production Worker stores client fields; P0-A candidate validates/derives canonical identity.

**Failure mode:** Valid signal ID authorizes different proposition.

**Production monitor target:** Signal ID ↔ stored identity mismatch.

**Closure / next action:** Finish P0-A; add invariant monitor.

## BET-003

**Severity:** P0  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Only exact sources `value` and `manual` are accepted; unknown input must not normalize to `value`.

**Canonical owner:** Bet API contract

**Current evidence:** Production Worker maps every non-manual source to value.

**Failure mode:** Unknown source contaminates production population.

**Production monitor target:** Ledger source outside enum; Worker rejected-source metric.

**Closure / next action:** Finish P0-A.

## BET-004

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Manual betting must be an explicit user-selected flow; invalid Value requests cannot silently downgrade to manual.

**Canonical owner:** PWA/Worker contract

**Current evidence:** Historical paths mixed semantics; P0-A explicitly separates flows.

**Failure mode:** Model provenance becomes ambiguous.

**Production monitor target:** Value→manual reclassification count must be zero.

**Closure / next action:** Finish P0-A.

## BET-005

**Severity:** P0  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
All Value actionability surfaces must use the same semantic contract.

**Canonical owner:** Canonical actionability policy

**Current evidence:** Production `predCard()` computes independent EV>=3 rule.

**Failure mode:** Different screens disagree whether same proposition is bettable.

**Production monitor target:** Cross-surface actionability parity test.

**Closure / next action:** Finish P0-A; preserve parity tests.

## BET-006

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Value actionability requires `signal_status == ACTIVE`.

**Canonical owner:** Signal lifecycle

**Current evidence:** Top-rec style gates use status; alternate model-tip paths do not.

**Failure mode:** Stale/edge-lost signal remains bettable.

**Production monitor target:** Any non-ACTIVE Value button/request.

**Closure / next action:** Finish P0-A.

## BET-007

**Severity:** P0  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Value bet must use actual `current_odds`, never scan-time odds presented as current.

**Canonical owner:** Odds-state authority

**Current evidence:** Production UI contains scan/model-tip paths; P0-A candidate binds current odds.

**Failure mode:** Ledger entry not equal actionable market price.

**Production monitor target:** Submitted odds != canonical current_odds.

**Closure / next action:** Finish P0-A.

## BET-008

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
`current_odds` must be finite and >1.0.

**Canonical owner:** Odds-state authority

**Current evidence:** Some production gates validate; not universal.

**Failure mode:** Invalid price generates meaningless risk/EV.

**Production monitor target:** Actionable signal with invalid odds.

**Closure / next action:** Finish canonical contract.

## BET-009

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Value odds must be fresh within canonical 30-minute hard window.

**Canonical owner:** Odds-state authority

**Current evidence:** Signal status has 30m stale threshold; alternate UI path bypasses.

**Failure mode:** Stale quote presented as actionable.

**Production monitor target:** ACTIVE with odds age >30m.

**Closure / next action:** Finish P0-A + Wave3D check.

## BET-010

**Severity:** P0  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Materially future `odds_ts` must fail closed; limited clock skew only.

**Canonical owner:** Odds-state authority

**Current evidence:** Production status code lacks universal future guard; P0-A adds bounded skew.

**Failure mode:** Future timestamp makes stale data look fresh.

**Production monitor target:** Odds timestamp beyond allowed future skew.

**Closure / next action:** Finish P0-A.

## BET-011

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Value `current_ev_pct` must be finite, positive and <= canonical MAX_EV (40%).

**Canonical owner:** Canonical gate/config

**Current evidence:** Production sidecar corruption guard allows much wider range; P0-A narrows actionability.

**Failure mode:** Corrupted EV generates unsafe recommendation.

**Production monitor target:** ACTIVE EV <=0, >40%, NaN/Inf.

**Closure / next action:** Finish P0-A and monitor.

## BET-012

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Shadow signals are never actionable Value bets.

**Canonical owner:** Signal provenance

**Current evidence:** Category/shadow architecture exists; UI provenance historically inconsistent.

**Failure mode:** Experimental bets enter production.

**Production monitor target:** source=value with shadow flag/tier.

**Closure / next action:** Canonical contract + measurement provenance.

## BET-013

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Unsupported signals are never actionable Value bets.

**Canonical owner:** Signal contract

**Current evidence:** Not universal on main; P0-A candidate checks.

**Failure mode:** Unsupported market/data becomes financial action.

**Production monitor target:** Value bet with unsupported flag.

**Closure / next action:** Finish P0-A.

## BET-014

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
`edge_lost`, stale, no-bet or unrefreshable state must never remain actionable.

**Canonical owner:** Signal lifecycle

**Current evidence:** Canonical signal_status supports these; alternate paths bypass.

**Failure mode:** Known-bad signal remains clickable.

**Production monitor target:** Actionable signal with any disqualifying flag.

**Closure / next action:** Finish P0-A.

## BET-015

**Severity:** P0  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Tennis Value signals require explicit canonical event status.

**Canonical owner:** TennisEventState

**Current evidence:** Production alternate paths do not enforce; P0-A candidate sport-aware.

**Failure mode:** Unknown lifecycle treated as safe prematch.

**Production monitor target:** Tennis value with missing event_status.

**Closure / next action:** Finish P0-A.

## BET-016

**Severity:** P0  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Tennis LIVE/COMPLETED/POSTPONED/CANCELLED/UNKNOWN are non-actionable.

**Canonical owner:** TennisEventState

**Current evidence:** Event state exists; global UI/Worker enforcement absent in main.

**Failure mode:** Bet placed after/while match lifecycle invalid.

**Production monitor target:** Any actionable terminal/live/unknown Tennis signal.

**Closure / next action:** Finish P0-A.

## BET-017

**Severity:** P1  
**Domain:** Betting  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Tennis UPCOMING/AWAITING_START/qualified DELAYED may remain actionable only with fresh canonical odds.

**Canonical owner:** TennisEventState + odds state

**Current evidence:** Canonical Tennis states support semantics; P0-A aligns actionability.

**Failure mode:** Valid delayed match incorrectly blocked or unsafe delayed bet allowed.

**Production monitor target:** Status/odds freshness contradictions.

**Closure / next action:** Parity + trust monitor.

## BET-018

**Severity:** P1  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Value odds field may not be arbitrarily edited while preserving canonical `source=value`.

**Canonical owner:** Canonical current odds

**Current evidence:** Production UI paths permit loosely bound odds; P0-A candidate locks/revalidates.

**Failure mode:** Recorded price differs from evaluated price.

**Production monitor target:** Submitted value odds != canonical odds.

**Closure / next action:** Finish P0-A.

## BET-019

**Severity:** P1  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Deep links, compact cards, match detail and normal cards must not bypass canonical actionability.

**Canonical owner:** PWA action contract

**Current evidence:** Multiple production UI paths exist.

**Failure mode:** Convenience path reopens closed safety hole.

**Production monitor target:** Route-specific actionability parity.

**Closure / next action:** Browser regression suite.

## BET-020

**Severity:** P1  
**Domain:** Betting  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
No new Value bet may be created from model-tip/all-odds data without backing canonical signal.

**Canonical owner:** Canonical signal

**Current evidence:** Production `predCard` builds value from model probability+odds directly.

**Failure mode:** Informational model view becomes unapproved wager.

**Production monitor target:** Value request without registered signal.

**Closure / next action:** Finish P0-A.

## RISK-001

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Final stake must be <= 5% of authoritative current bankroll.

**Canonical owner:** Ledger-derived bankroll / hard CEO invariant

**Current evidence:** Production Worker cap €25; consumer no bankroll cap. P0-A candidate enforces 5%.

**Failure mode:** Oversized financial exposure.

**Production monitor target:** Any new stake_pct >5% or recomputed stake>5%.

**Closure / next action:** Finish P0-A + monitor.

## RISK-002

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
5% rule applies to both Value and Manual bets.

**Canonical owner:** Hard risk policy

**Current evidence:** Production manual/value share only absolute cap.

**Failure mode:** Manual flow bypasses risk policy.

**Production monitor target:** Manual stake >5%.

**Closure / next action:** Finish P0-A.

## RISK-003

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Worker must not trust client-supplied bankroll as security authority.

**Canonical owner:** Backend risk state

**Current evidence:** Production does not authoritative-cap; P0-A uses backend state.

**Failure mode:** Client spoofs bankroll upward.

**Production monitor target:** Client hint differs; server decision unchanged.

**Closure / next action:** Finish P0-A.

## RISK-004

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Consumer independently revalidates bankroll cap from live ledger state.

**Canonical owner:** Ledger

**Current evidence:** Production consumer writes submitted stake directly.

**Failure mode:** Worker-only failure reaches ledger.

**Production monitor target:** Consumer accepted >5%.

**Closure / next action:** Finish P0-A.

## RISK-005

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Maximum active bets is 3 across every placement boundary.

**Canonical owner:** Hard CEO invariant

**Current evidence:** Production config says 5; Worker does not enforce 3.

**Failure mode:** Portfolio exposure exceeds governance.

**Production monitor target:** open+pending >3.

**Closure / next action:** Finish P0-A.

## RISK-006

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Worker active-bet count comes from trusted backend state plus pending queue, never client count.

**Canonical owner:** Published risk state + KV pending

**Current evidence:** Production no canonical max3; P0-A candidate server state.

**Failure mode:** Client spoofs count.

**Production monitor target:** Server count/client count divergence test.

**Closure / next action:** Finish P0-A.

## RISK-007

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
If authoritative bankroll/open-bet state is missing or stale, new money actions fail closed.

**Canonical owner:** Backend risk state

**Current evidence:** Production lacks state gate; P0-A candidate adds freshness.

**Failure mode:** Unknown risk treated as safe.

**Production monitor target:** Placement with missing/stale risk state.

**Closure / next action:** Finish P0-A.

## RISK-008

**Severity:** P1  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Risk-state freshness heartbeat must be independent of expensive scan cadence.

**Canonical owner:** Risk-state publisher

**Current evidence:** P0-A candidate adds heartbeat; final transaction integration still under review.

**Failure mode:** Healthy system locks betting or uses stale count.

**Production monitor target:** risk published_at age and heartbeat outcome.

**Closure / next action:** Complete final P0-A queue pass.

## RISK-009

**Severity:** P0  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Security boundaries reject oversized confirmed stake; they do not silently mutate it after user confirmation.

**Canonical owner:** Worker/consumer

**Current evidence:** Production has no 5% mutation logic; P0-A candidate reject semantics.

**Failure mode:** Ledger differs from user-confirmed amount.

**Production monitor target:** Requested stake != stored stake without explicit preconfirm cap.

**Closure / next action:** Finish P0-A.

## RISK-010

**Severity:** P1  
**Domain:** Risk  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
`stake_pct` on every new non-zero bet is truthful and recomputable from bankroll-at-placement.

**Canonical owner:** Ledger provenance

**Current evidence:** Production PWA consumer writes `stake_pct=0.0`.

**Failure mode:** Risk analytics lies.

**Production monitor target:** stake_pct mismatch recomputation.

**Closure / next action:** Finish P0-A.
