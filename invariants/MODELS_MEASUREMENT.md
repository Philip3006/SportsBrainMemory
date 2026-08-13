---
type: "invariant-domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
domains:
  - Measurement
  - Model
---
# Models Measurement Invariants

Canonical definitions for 20 invariants.

## MODEL-001

**Severity:** P0  
**Domain:** Model  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Only models with passed production gate may be used in live ensemble.

**Canonical owner:** Model metadata

**Current evidence:** Tennis ensemble requires `gate_passed`.

**Failure mode:** Failed model silently deployed.

**Production monitor target:** Live model metadata gate check.

**Closure / next action:** Preserve.

## MODEL-002

**Severity:** P0  
**Domain:** Model  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Training/validation feature semantics must match live-serving feature semantics or documented domain shift must be validated.

**Canonical owner:** Feature pipeline

**Current evidence:** Live Tennis ensemble uses fresh `RollingState()`; historical training uses progressed state.

**Failure mode:** Holdout quality overstates live model quality.

**Production monitor target:** Feature distribution parity monitor.

**Closure / next action:** Model Integrity workstream.

## MODEL-003

**Severity:** P1  
**Domain:** Model  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Model probability is finite and bounded before signal generation.

**Canonical owner:** Model output contract

**Current evidence:** Calibrators clip some probabilities; P0-A rejects invalid bet probability.

**Failure mode:** NaN/extreme model output.

**Production monitor target:** Model output domain check.

**Closure / next action:** Unify contracts.

## MODEL-004

**Severity:** P1  
**Domain:** Model  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Unknown/insufficient-history player cannot generate falsely confident Tennis Value signal.

**Canonical owner:** Tennis ensemble

**Current evidence:** Known-player min-match gate returns low_confidence.

**Failure mode:** Default Elo produces fake edge.

**Production monitor target:** Unknown-player actionable signal count.

**Closure / next action:** Preserve.

## MODEL-005

**Severity:** P1  
**Domain:** Model  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Calibration artifacts are applied only when sample/gate requirements are met.

**Canonical owner:** Calibration loader

**Current evidence:** Meta calibrator min samples; surface calibrators optional.

**Failure mode:** Overfit calibrator distorts probabilities.

**Production monitor target:** Calibrator metadata/age/sample monitor.

**Closure / next action:** Preserve.

## MODEL-006

**Severity:** P1  
**Domain:** Model  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Symmetric prediction removes player-order positional bias.

**Canonical owner:** Tennis ensemble

**Current evidence:** AB/BA predictions averaged.

**Failure mode:** Order artifact changes outcome.

**Production monitor target:** Swap invariance test.

**Closure / next action:** Preserve.

## MODEL-007

**Severity:** P1  
**Domain:** Model  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Every model artifact records feature version/training metadata.

**Canonical owner:** Model metadata

**Current evidence:** Tennis LGBM writes feature_version/trained_at; coverage across all models not verified.

**Failure mode:** Unknown artifact provenance.

**Production monitor target:** Artifact metadata completeness.

**Closure / next action:** Expand to all models.

## MODEL-008

**Severity:** P1  
**Domain:** Model  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Retraining cannot promote a model solely because it trained successfully; evaluation gate controls promotion.

**Canonical owner:** Model governance

**Current evidence:** Gate concept exists; all retrain paths not fully audited.

**Failure mode:** Regression deployed.

**Production monitor target:** Promotion audit trail.

**Closure / next action:** P0-D.

## MODEL-009

**Severity:** P1  
**Domain:** Model  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Rule-based post-model adjustments require measured evidence and versioned provenance.

**Canonical owner:** Ensemble adjustments

**Current evidence:** Bayesian/altitude/style adjustments exist with comments/backtests.

**Failure mode:** Silent heuristic drift.

**Production monitor target:** Adjustment version + ablation report.

**Closure / next action:** Formalize.

## MODEL-010

**Severity:** P1  
**Domain:** Model  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Live feature fetch failure degrades to explicit neutral/fallback state and is observable.

**Canonical owner:** Tennis live features

**Current evidence:** Serve stats failures fall to neutral prior, mostly debug log.

**Failure mode:** Silent feature loss shifts model.

**Production monitor target:** Feature availability telemetry.

**Closure / next action:** Monitoring/model integrity.

## MEAS-001

**Severity:** P0  
**Domain:** Measurement  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Production metrics include only provably canonical production Value bets.

**Canonical owner:** Measurement provenance

**Current evidence:** Production report equates non-manual/non-Challenger source with value.

**Failure mode:** ROI/Brier population contaminated.

**Production monitor target:** Production row without canonical signal provenance.

**Closure / next action:** New schema + historical cohorting.

## MEAS-002

**Severity:** P0  
**Domain:** Measurement  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Manual bets are excluded from model-approved ROI/calibration metrics.

**Canonical owner:** Source/provenance

**Current evidence:** Report separates source=manual; historical source ambiguity remains.

**Failure mode:** Manual judgment credited to model.

**Production monitor target:** Manual in production population.

**Closure / next action:** P0-A future rows + backfill segmentation.

## MEAS-003

**Severity:** P1  
**Domain:** Measurement  
**Production status:** `not_enforced`  
**P0-A overlay status:** `not_enforced`

### Invariant
Shadow bets are excluded from production metrics based on explicit provenance, not one league heuristic.

**Canonical owner:** Signal tier/provenance

**Current evidence:** Production shadow classification only Challenger league.

**Failure mode:** Other shadow experiments leak into production.

**Production monitor target:** Shadow provenance field.

**Closure / next action:** Measurement redesign.

## MEAS-004

**Severity:** P0  
**Domain:** Measurement  
**Production status:** `not_enforced`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Sport classification for metrics uses explicit sport, not market-name inference.

**Canonical owner:** Ledger identity

**Current evidence:** `_is_tennis_row()` infers from market/source/league.

**Failure mode:** Tennis Match Winner pollutes football/general stats.

**Production monitor target:** Rows where inferred sport != explicit sport.

**Closure / next action:** P0-A new data + historical cohort.

## MEAS-005

**Severity:** P1  
**Domain:** Measurement  
**Production status:** `partial`  
**P0-A overlay status:** `branch_candidate`

### Invariant
Calibration metrics use only valid `0<p<1` model probabilities and track exclusion reasons.

**Canonical owner:** Measurement schema

**Current evidence:** Report filters valid p but doesn't prove why invalid rows exist.

**Failure mode:** Bad rows silently disappear.

**Production monitor target:** Calibration exclusion counts by reason.

**Closure / next action:** Add audit fields/report.

## MEAS-006

**Severity:** P1  
**Domain:** Measurement  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
CLV coverage is reported with denominator and source/market validity.

**Canonical owner:** CLV pipeline

**Current evidence:** Season report reports coverage/hit/mean.

**Failure mode:** Sparse CLV misread as strong evidence.

**Production monitor target:** Coverage threshold + market match.

**Closure / next action:** Improve coverage.

## MEAS-007

**Severity:** P1  
**Domain:** Measurement  
**Production status:** `unverified`  
**P0-A overlay status:** `unverified`

### Invariant
Closing-line comparison uses same proposition and bookmaker/source semantics.

**Canonical owner:** CLV

**Current evidence:** Needs dedicated audit.

**Failure mode:** CLV sign/size meaningless.

**Production monitor target:** Market/selection/source join validation.

**Closure / next action:** Dedicated CLV workstream.

## MEAS-008

**Severity:** P1  
**Domain:** Measurement  
**Production status:** `enforced`  
**P0-A overlay status:** `enforced`

### Invariant
Historical cohorts remain separable by calibration/model epoch.

**Canonical owner:** Report

**Current evidence:** Calibration epoch split exists.

**Failure mode:** Before/after changes mixed.

**Production monitor target:** Epoch metadata completeness.

**Closure / next action:** Preserve/extend.

## MEAS-009

**Severity:** P1  
**Domain:** Measurement  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
No backfill silently changes historical model provenance.

**Canonical owner:** Historical data governance

**Current evidence:** Several backfill scripts exist.

**Failure mode:** Retrospective metrics become unauditable.

**Production monitor target:** Backfill manifest.

**Closure / next action:** P0-D.

## MEAS-010

**Severity:** P1  
**Domain:** Measurement  
**Production status:** `partial`  
**P0-A overlay status:** `partial`

### Invariant
Every published performance claim includes sample size and population definition.

**Canonical owner:** Reporting

**Current evidence:** Core report includes n; population definition currently weak.

**Failure mode:** Small/contaminated sample overinterpreted.

**Production monitor target:** Report contract.

**Closure / next action:** Measurement redesign.
