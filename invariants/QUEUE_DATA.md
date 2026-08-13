---
type: "invariant-domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
domains:
  - Data
  - Queue
---
# Queue Data Invariants

Canonical definitions for 27 invariants.

## QUEUE-001

**Severity:** P0  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Accepted pending bet may be ACKed/deleted only after durable ledger persistence.

**Canonical owner:** Canonical ledger persistence owner

**Current evidence:** Production deletes before non-fatal Git push; P0-A final candidate improves ordering but remote-containment edge remains.

**Failure mode:** Accepted bet disappears permanently.

**Production monitor target:** ACK timestamp before remote durable commit.

**Closure / next action:** Resolve final P0-A remote containment.

## QUEUE-002

**Severity:** P0  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Local file write/local commit is not sufficient durability for an ephemeral runner.

**Canonical owner:** Remote canonical persistence

**Current evidence:** Production treats local write then delete; candidate still needed explicit remote containment proof.

**Failure mode:** Runner dies with only local state.

**Production monitor target:** Remote branch containment check.

**Closure / next action:** Resolve final P0-A.

## QUEUE-003

**Severity:** P0  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Push/rebase/remote verification failure for accepted mutation is fatal and leaves queue item retryable.

**Canonical owner:** Consumer transaction

**Current evidence:** Production logs push failure non-fatally after ACK.

**Failure mode:** Data loss.

**Production monitor target:** Push fail + ACK occurrence must be zero.

**Closure / next action:** Resolve final P0-A.

## QUEUE-004

**Severity:** P0  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Transient infrastructure inability to validate a legitimate bet is RETRY, not permanent reject.

**Canonical owner:** Consumer classifier

**Current evidence:** Candidate review found bankroll-unavailable could be classified rejected.

**Failure mode:** Temporary outage deletes user action.

**Production monitor target:** Retry-class item ACK count = 0.

**Closure / next action:** Implement explicit ACCEPT/REJECT/RETRY.

## QUEUE-005

**Severity:** P1  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Permanent reject and retryable failure are explicit distinct states.

**Canonical owner:** Consumer queue semantics

**Current evidence:** Production collapses invalid/failure paths.

**Failure mode:** Wrong ACK policy.

**Production monitor target:** Queue decision reason metrics.

**Closure / next action:** Final P0-A.

## QUEUE-006

**Severity:** P0  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Cancellation ACK occurs only after cancellation is durably persisted.

**Canonical owner:** Ledger mutation transaction

**Current evidence:** Production cancel locally then delete queue; final candidate still under review.

**Failure mode:** Cancellation disappears/reverts.

**Production monitor target:** Cancel ACK before durable remote mutation.

**Closure / next action:** Final P0-A.

## QUEUE-007

**Severity:** P1  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Placement and cancellation can share one durable persistence boundary per consumer run.

**Canonical owner:** Consumer transaction coordinator

**Current evidence:** Not true in production; target final candidate.

**Failure mode:** Conflicting commits and partial ACKs.

**Production monitor target:** Mutations per durable transaction.

**Closure / next action:** Final P0-A design.

## QUEUE-008

**Severity:** P0  
**Domain:** Queue  
**Production status:** `partial`  
**P0-A overlay status:** `branch_partial`

### Invariant
Retry after ACK failure is idempotent and cannot duplicate ledger row.

**Canonical owner:** Stable bet identity / ledger

**Current evidence:** Production duplicate guard exists but identity is weak; P0-A improves provenance.

**Failure mode:** Duplicate stake/P&L.

**Production monitor target:** Duplicate pending ID/signal identity in ledger.

**Closure / next action:** Strengthen identity/outbox semantics.

## QUEUE-009

**Severity:** P1  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Duplicate detection should use strongest stable bet identity, not only match text/date/market.

**Canonical owner:** Canonical bet identity

**Current evidence:** Production `match_id` uses names+date and market tuple.

**Failure mode:** Different event collides or duplicate escapes.

**Production monitor target:** Duplicate canonical IDs / collision detector.

**Closure / next action:** Future identity hardening.

## QUEUE-010

**Severity:** P1  
**Domain:** Queue  
**Production status:** `partial`  
**P0-A overlay status:** `branch_partial`

### Invariant
Rejected malformed queue items have explicit reason and auditable ACK policy.

**Canonical owner:** Consumer

**Current evidence:** Production invalid items are deleted without rich durable audit.

**Failure mode:** Silent loss hides client/system defects.

**Production monitor target:** Reject reason counts.

**Closure / next action:** Add reject audit trail.

## QUEUE-011

**Severity:** P1  
**Domain:** Queue  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_partial`

### Invariant
Zero-pending heartbeat may refresh risk state but may not fabricate signal/odds freshness.

**Canonical owner:** Risk publisher

**Current evidence:** Target architecture from P0-A.

**Failure mode:** Heartbeat masks stale sports data.

**Production monitor target:** Separate risk published_at vs signal/odds timestamps.

**Closure / next action:** Final P0-A + monitoring.

## QUEUE-012

**Severity:** P1  
**Domain:** Queue  
**Production status:** `partial`  
**P0-A overlay status:** `branch_partial`

### Invariant
Queue processing must be per-user isolated; one user's failure must not mutate another user's state incorrectly.

**Canonical owner:** User-scoped KV + ledger

**Current evidence:** Per-user keys exist; error isolation not comprehensively proven.

**Failure mode:** Cross-user corruption.

**Production monitor target:** User key/ledger mismatch monitor.

**Closure / next action:** P0-C hardening.

## DATA-001

**Severity:** P0  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Every new bet has explicit supported `sport`; sport is never inferred from generic market alone.

**Canonical owner:** Bet identity schema

**Current evidence:** Production ledger lacks explicit sport field; inference used in reports.

**Failure mode:** Tennis classified as football/general.

**Production monitor target:** New bet missing sport.

**Closure / next action:** Finish P0-A.

## DATA-002

**Severity:** P1  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Every new canonical Tennis Value bet has valid league/tour/category metadata as defined by schema.

**Canonical owner:** Tennis identity

**Current evidence:** Historical blank/wm2026 contamination.

**Failure mode:** Wrong reporting/provider routing.

**Production monitor target:** Tennis value with invalid league/tour.

**Closure / next action:** Define taxonomy + enforce.

## DATA-003

**Severity:** P0  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Blank Tennis league must never default to `wm2026`.

**Canonical owner:** Ledger migration

**Current evidence:** Production `_load` fills all blank league as wm2026.

**Failure mode:** Football contamination of Tennis.

**Production monitor target:** sport=tennis + league=wm2026 default pattern.

**Closure / next action:** Finish P0-A.

## DATA-004

**Severity:** P1  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Historical compatibility behavior cannot silently rewrite semantic identity.

**Canonical owner:** Ledger migration

**Current evidence:** Production migration defaults change meaning on load.

**Failure mode:** Historical truth changes by reader version.

**Production monitor target:** Migration audit / row mutation detector.

**Closure / next action:** Use explicit UNKNOWN/legacy flags.

## DATA-005

**Severity:** P0  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
New Value bet stores explicit `signal_id`.

**Canonical owner:** Canonical signal provenance

**Current evidence:** Production ledger schema lacks it.

**Failure mode:** Cannot prove model provenance.

**Production monitor target:** Value row missing signal_id.

**Closure / next action:** Finish P0-A.

## DATA-006

**Severity:** P1  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
New bet stores `fixture_key` where canonical fixture identity exists.

**Canonical owner:** Fixture registry

**Current evidence:** Production ledger lacks it.

**Failure mode:** Cannot join event truth robustly.

**Production monitor target:** Supported row missing fixture_key.

**Closure / next action:** Finish P0-A.

## DATA-007

**Severity:** P1  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
New bet stores bankroll-at-placement and risk provenance.

**Canonical owner:** Risk/ledger

**Current evidence:** Production lacks fields.

**Failure mode:** Stake cannot be audited later.

**Production monitor target:** Missing bankroll_at_placement.

**Closure / next action:** Finish P0-A.

## DATA-008

**Severity:** P0  
**Domain:** Data  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Value `model_prob` unit in ledger is probability fraction `0<p<1`.

**Canonical owner:** Ledger/model measurement schema

**Current evidence:** Production can receive arbitrary client units; P0-A normalizes percent→fraction.

**Failure mode:** Calibration contamination or omission.

**Production monitor target:** Value model_prob outside open interval.

**Closure / next action:** Finish P0-A.

## DATA-009

**Severity:** P1  
**Domain:** Data  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Published model probability unit is explicitly documented and converted exactly once.

**Canonical owner:** Publication schema

**Current evidence:** signals publishes percentage; multiple layers historically mixed units.

**Failure mode:** 100x EV/calibration errors.

**Production monitor target:** Schema/unit contract tests.

**Closure / next action:** Keep parity tests.

## DATA-010

**Severity:** P1  
**Domain:** Data  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
CSV and SQLite represent the same canonical bet identity and risk fields.

**Canonical owner:** Ledger persistence model

**Current evidence:** Production SQLite schema omits fields/league semantics.

**Failure mode:** Different readers see different truth.

**Production monitor target:** CSV↔SQLite parity test.

**Closure / next action:** Finish P0-A.

## DATA-011

**Severity:** P1  
**Domain:** Data  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
SQLite sync failure must have defined operational consequence; silent warning cannot create indefinite divergence.

**Canonical owner:** Ledger persistence

**Current evidence:** Production logs warning and continues.

**Failure mode:** Secondary DB becomes stale.

**Production monitor target:** CSV/SQLite row-count/schema parity health.

**Closure / next action:** P0-D/monitoring.

## DATA-012

**Severity:** P1  
**Domain:** Data  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
All externally published JSON schemas are versioned or backward-compatible.

**Canonical owner:** Publication schema

**Current evidence:** Many additive fields, limited explicit schema versioning.

**Failure mode:** Old browser misreads new state.

**Production monitor target:** Schema version/required fields check.

**Closure / next action:** Introduce schema_version.

## DATA-013

**Severity:** P1  
**Domain:** Data  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
User-specific snapshots contain only that user's private financial state.

**Canonical owner:** User isolation

**Current evidence:** Per-user writer exists; Worker fallback to default snapshot remains.

**Failure mode:** Cross-user state exposure.

**Production monitor target:** Requested user vs served snapshot identity.

**Closure / next action:** P0-C.

## DATA-014

**Severity:** P1  
**Domain:** Data  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Canonical current bankroll definition is documented consistently (free/staked/equity).

**Canonical owner:** Financial accounting schema

**Current evidence:** Multiple representations exist.

**Failure mode:** 5% cap based on inconsistent denominator.

**Production monitor target:** Bankroll recomputation parity.

**Closure / next action:** Formalize accounting.

## DATA-015

**Severity:** P1  
**Domain:** Data  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Signal snapshot publication never replaces good data with structurally thin/corrupt payload.

**Canonical owner:** Publication writer / Worker guard

**Current evidence:** Worker has thin-payload guard with force bypass.

**Failure mode:** PWA wiped to empty/corrupt state.

**Production monitor target:** Payload-size/schema anomaly.

**Closure / next action:** Strengthen publisher schema validation.
