---
id: DOMAIN-MODEL-RESEARCH
type: domain
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: model-bound
canonical: true
---
# Model & Research

## CURRENT FACT

Model promotion requires walk-forward/PIT-safe evaluation, calibration, Brier
and log-loss evidence, confidence intervals where applicable, clean holdouts,
and a reproducible artifact. A research result is not a production signal.

## Promotion gates

1. Dataset and cohort are frozen and provenance is explicit.
2. Temporal leakage and feature availability are tested.
3. Baseline comparison is honest and reproducible.
4. Calibration and uncertainty are reported.
5. Negative results are registered and not silently retried.
6. Promotion is separately approved from research completion.

The negative-result registry is [[findings/NEGATIVE_EVIDENCE]]. Existing model
notes remain historical unless linked to a current evidence record.
