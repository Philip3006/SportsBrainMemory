---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Models

## Tennis LGBM

Historical holdout evidence is positive versus Elo, but live-serving feature parity is not proven because RollingState-dependent features differ between historical training/holdout and live prediction path.

## Tennis ensemble

Uses Elo, LGBM when gate-passed, calibration and rule/feature adjustments. Unknown/insufficient-history players should degrade rather than fabricate confidence.

## Governance

Model artifact existence is not production approval. Candidate retrain and production promotion must remain distinct.

## Calibration

Accepted Value `model_prob` should be stored as fraction strictly in `(0,1)`. Published percent and ledger fraction units must be converted exactly once.

See [[workstreams/MODEL_INTEGRITY]].
