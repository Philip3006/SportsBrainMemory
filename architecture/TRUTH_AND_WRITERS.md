---
type: "architecture"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Truth Owners & Writer Governance

## Core architecture principle

> One concept → one canonical owner. Replicas are not authorities.

## Writer classes

- **SOURCE_WRITER:** controlled Builder/human review.
- **RUNTIME_DATA_WRITER:** allowlisted data/cache/public runtime paths only.
- **FINANCIAL_WRITER:** canonical private ledger transaction path.
- **MODEL_ARTIFACT_WRITER:** candidate/approved model artifacts with gate metadata.
- **RECOVERY_ACTOR:** deterministic allowlisted operational retries.

## Known current governance gaps

- Automated workflows do not universally use one governed Git-persistence primitive.
- `auto_heal_ai.py` has a source-edit→test→commit→push capability.
- production config still mixes hard policy, strategy tuning and user overrides.
- frequent runtime-data writes continuously move `main`.

## Canonical target

- Source code can be mutated only through controlled Builder governance.
- Runtime bots have testable path authority.
- Financial mutation has transactional durable ACK semantics.
- Model retraining is distinct from production promotion.
- Recovery and repair are separate concepts.

## Full planning evidence

The original detailed writer-governance audit is preserved under `history/archive/2026-08-13/SPORTSBRAIN_P0D_WRITER_GOVERNANCE_MATRIX_2026-08-13.md`.
