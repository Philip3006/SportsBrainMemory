---
type: "invariant-domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
domains:
  - Odds
  - Tennis
---
# Odds Tennis Invariants

Canonical definitions for 24 invariants.

## ODDS-001

**Severity:** P0  
**Domain:** Odds  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
`odds_state.json` remains sole writer authority for refreshed odds.

**Canonical owner:** Odds state sidecar

**Current evidence:** Explicit module contract.

**Failure mode:** Concurrent writers create race/divergence.

**Production monitor target:** Writer audit.

**Closure / next action:** Preserve.

## ODDS-002

**Severity:** P0  
**Domain:** Odds  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Every market refresh retrieves the quote for the exact same market/selection.

**Canonical owner:** Market taxonomy + provider quote

**Current evidence:** Production Tennis refresher maps almost every non-home market to H2H-B.

**Failure mode:** Wrong current odds/EV.

**Production monitor target:** Market vs provider-field contract test.

**Closure / next action:** Fix Tennis market mapping before trust score increase.

## ODDS-003

**Severity:** P0  
**Domain:** Odds  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
No model-implied/WebSearch-only price may be authoritative for actionable current odds unless explicitly approved by policy.

**Canonical owner:** Provider authority

**Current evidence:** Football refresher fails closed on WebSearch; Tennis scanner has fallback/display mechanisms.

**Failure mode:** Synthetic/non-market quote treated as executable.

**Production monitor target:** Actionable odds source whitelist.

**Closure / next action:** Wave3D.

## ODDS-004

**Severity:** P1  
**Domain:** Odds  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Odds source and source tier are preserved with every refreshed quote.

**Canonical owner:** Odds state

**Current evidence:** Sidecar stores source/tier.

**Failure mode:** Cannot audit quality.

**Production monitor target:** Missing source on ACTIVE.

**Closure / next action:** Preserve + monitor.

## ODDS-005

**Severity:** P1  
**Domain:** Odds  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Initial odds are immutable historical observation; refresh never overwrites scan entry price semantics.

**Canonical owner:** Odds state

**Current evidence:** Sidecar seeds/preserves initial odds.

**Failure mode:** CLV/line movement corrupted.

**Production monitor target:** Initial odds mutation detector.

**Closure / next action:** Preserve.

## ODDS-006

**Severity:** P1  
**Domain:** Odds  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Odds history is timestamped, deduplicated and market-specific.

**Canonical owner:** Odds state

**Current evidence:** History exists/dedups; market identity relies on signal_id correctness.

**Failure mode:** Line history cross-market contamination.

**Production monitor target:** History signal/market parity.

**Closure / next action:** Strengthen identity.

## ODDS-007

**Severity:** P0  
**Domain:** Odds  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Odds freshness is computed from trusted fetch timestamp, not UI/render time.

**Canonical owner:** Odds state

**Current evidence:** Sidecar odds_ts from refresher.

**Failure mode:** Stale quote appears fresh.

**Production monitor target:** Timestamp origin/schema check.

**Closure / next action:** Preserve.

## ODDS-008

**Severity:** P1  
**Domain:** Odds  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Provider outage degrades to non-actionable state, never fabricated ACTIVE.

**Canonical owner:** Signal lifecycle

**Current evidence:** UNREFRESHABLE/STALE states exist; alternate UI bypasses on main.

**Failure mode:** Outage creates fake value.

**Production monitor target:** Provider failure + actionable count.

**Closure / next action:** P0-A + Wave3D.

## ODDS-009

**Severity:** P1  
**Domain:** Odds  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Refresh cadence becomes faster near kickoff and is not slower than freshness guarantee.

**Canonical owner:** Odds refresher

**Current evidence:** 5/10/15/20/30m cadence, hard stale 30m.

**Failure mode:** Freshness window breached systematically.

**Production monitor target:** Due-but-not-refreshed signals.

**Closure / next action:** Preserve/monitor.

## ODDS-010

**Severity:** P1  
**Domain:** Odds  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
EV recomputation uses model probability in correct unit exactly once.

**Canonical owner:** Signal status

**Current evidence:** Helper divides published percent by 100; historical bugs existed.

**Failure mode:** 100x EV artifact.

**Production monitor target:** EV recomputation parity.

**Closure / next action:** P0-A + invariant test.

## ODDS-011

**Severity:** P1  
**Domain:** Odds  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Absurd/NaN EV in sidecar/published signal is sanitized and ACTIVE revoked.

**Canonical owner:** Odds state

**Current evidence:** Production corruption guard exists but loose ±500%; P0-A actionable max40.

**Failure mode:** Corrupt data actionability.

**Production monitor target:** Sanitized EV counter.

**Closure / next action:** Tighten trust monitor.

## ODDS-012

**Severity:** P1  
**Domain:** Odds  
**Production status:** `unverified`  
**P0-A overlay status:** `unverified`

### Invariant
Closing odds correspond to the same market/selection as entry bet.

**Canonical owner:** Closing-odds subsystem

**Current evidence:** Not exhaustively re-audited in this session.

**Failure mode:** CLV becomes meaningless.

**Production monitor target:** Entry market vs closing source field.

**Closure / next action:** Dedicated CLV audit.

## TEN-001

**Severity:** P0  
**Domain:** Tennis  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Elapsed time alone never creates LIVE.

**Canonical owner:** TennisEventState

**Current evidence:** Explicit event_state authority rule.

**Failure mode:** False LIVE.

**Production monitor target:** LIVE state with no qualified evidence.

**Closure / next action:** Preserve.

## TEN-002

**Severity:** P0  
**Domain:** Tennis  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
LIVE requires qualified authoritative evidence.

**Canonical owner:** TennisEventState authority matrix

**Current evidence:** ESPN primary; TE informational for live.

**Failure mode:** False LIVE.

**Production monitor target:** LIVE evidence source whitelist.

**Closure / next action:** Preserve + Wave3D.

## TEN-003

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Initial scheduled start becomes immutable after authoritative creation.

**Canonical owner:** TennisEventState

**Current evidence:** Separate scheduled_start_initial/current.

**Failure mode:** Historical schedule truth overwritten.

**Production monitor target:** Initial-start mutation.

**Closure / next action:** Preserve.

## TEN-004

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Current scheduled start changes only through authorized source rules.

**Canonical owner:** TennisEventState

**Current evidence:** Authority matrix exists; source metadata integration remains audit concern.

**Failure mode:** Fallback source silently becomes primary.

**Production monitor target:** Schedule update source violation.

**Closure / next action:** Audit TE source/odds_source path.

## TEN-005

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Schedule truth and lifecycle truth remain separate fields.

**Canonical owner:** TennisEventState

**Current evidence:** Explicit architecture.

**Failure mode:** Delay/reschedule conflated with LIVE.

**Production monitor target:** State/schedule contradiction checks.

**Closure / next action:** Preserve.

## TEN-006

**Severity:** P0  
**Domain:** Tennis  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Terminal authoritative state dominates stale kickoff heuristics.

**Canonical owner:** TennisEventState / signal lifecycle

**Current evidence:** COMPLETED/CANCELLED handled; broader cross-layer parity was P0-A focus.

**Failure mode:** Completed match still active.

**Production monitor target:** Terminal event + ACTIVE signal.

**Closure / next action:** P0-A + Wave3D.

## TEN-007

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Fixture identity survives cross-midnight/reschedule without generating new logical bet identity.

**Canonical owner:** Fixture registry

**Current evidence:** Registry specifically introduced for this.

**Failure mode:** Duplicate signal/bet.

**Production monitor target:** Same provider event -> multiple fixture keys.

**Closure / next action:** Preserve.

## TEN-008

**Severity:** P0  
**Domain:** Tennis  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Fixture identity is globally unique across event instances, years, rounds and repeat meetings.

**Canonical owner:** Fixture identity

**Current evidence:** Current key lacks year/round/event-instance.

**Failure mode:** Wrong event inherits old state/signal.

**Production monitor target:** Fixture-key collision detector.

**Closure / next action:** Future provider-native ID migration.

## TEN-009

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Provider-native stable event ID is preferred primary identity when available.

**Canonical owner:** Fixture identity target

**Current evidence:** Current fallback pair+sport_key dominates.

**Failure mode:** Heuristic collisions.

**Production monitor target:** Native ID coverage.

**Closure / next action:** Design workstream.

## TEN-010

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
TennisExplorer fallback cannot be promoted to stronger schedule authority through missing/mismatched metadata.

**Canonical owner:** Source authority

**Current evidence:** Known source-vs-odds_source concern not yet fully closed.

**Failure mode:** Wrong kickoff overwrites canonical schedule.

**Production monitor target:** Authority field consistency.

**Closure / next action:** Re-audit and test.

## TEN-011

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Tournament/category metadata is tied to each parsed fixture, not leaked from page-wide regex context.

**Canonical owner:** TE parser

**Current evidence:** Historical suspicious metadata clusters.

**Failure mode:** Wrong surface/category/model gate.

**Production monitor target:** Tournament-player plausibility checks.

**Closure / next action:** Parser hardening.

## TEN-012

**Severity:** P1  
**Domain:** Tennis  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Open Tennis bet classification uses explicit sport identity, not market/source guessing.

**Canonical owner:** Ledger identity

**Current evidence:** Production live monitor has historical inference weakness; P0-A adds sport for new bets.

**Failure mode:** Bet invisible to live/settlement pipeline.

**Production monitor target:** Open Tennis row with missing sport.

**Closure / next action:** P0-A + historical segmentation.
