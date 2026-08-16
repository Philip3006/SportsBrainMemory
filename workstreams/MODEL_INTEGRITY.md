---
id: WS-MODEL
type: "workstream"
tier: "warm"
status: "planned_ready"
workstream: "MODEL-INTEGRITY"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Model Integrity

Primary target: [[findings/records/FND-20260814-021]].

## Mission

Prove that the live-serving Tennis feature distribution matches the training/holdout semantics, especially RollingState-dependent form/surface/H2H/rest/fatigue features.

## Closure

- exact live-path feature reconstruction
- historical replay through live-serving code path
- distribution parity report
- Brier/logloss/calibration comparison
- gate outcome based on serving path, not only historical trainer path.


## V1 readiness note

Execute Train/Live parity → Measurement population → Promotion gate in order.
