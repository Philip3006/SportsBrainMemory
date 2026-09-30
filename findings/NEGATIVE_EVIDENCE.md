---
id: NEGATIVE-EVIDENCE-REGISTRY
type: finding-index
tier: warm
status: current
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: model-bound
canonical: true
graph_domain: model-research
graph_role: evidence
---
# Negative Evidence Registry

This registry prevents future builders from rebuilding rejected or unsupported
ideas. A row is only a current fact when its exact artifact is linked and the
artifact is on the applicable source/evidence path.

| Item | Method / cohort | Result or current posture | Status | Evidence boundary |
|---|---|---|---|---|
| NL causal GBT | Nations League research branch | The requested `NL_CAUSAL_GBT_NO_CLEAR_GAIN` marker was not found in current main or fetched branch trees during this audit; do not promote the claim from memory alone. | UNVERIFIED | Reconcile exact artifact before reuse |
| NL competition context | Competition-state branch | The requested `NL_SAFE_CONTEXT_FINAL_REGRESSION` marker was not found in current main or fetched branch trees; the branch is not production truth. | BRANCH CANDIDATE / UNVERIFIED | `origin/feat/nl-causal-competition-state`, latest `eb6b2d85a3c119afeeabc0e0b3fe88ffc3295394` |
| Historical squad features | Historical PIT availability | Historical point-in-time squad evidence is a known limitation; no production feature promotion follows. | UNSUPPORTED | Research limitation, not a runtime blocker |
| Historical odds executor | Reproducible historical market ingestion | The requested `NL_HISTORICAL_ODDS_EXECUTOR_RECONCILED` marker was not found in current main or fetched refs; keep the plan separate from execution authority. | UNVERIFIED | No exact artifact found |
| PostHog PWA analytics | Frontend/unit/browser implementation | PR #221 head passed exact-head CI and controlled test ingestion, but is not in `origin/main`; no production traffic claim. | BRANCH CANDIDATE | `b67fde78e82ce169f9b23f109818ffca0ce0db20`, PR #221 |
| Top-5 route/storage rollback | Controlled activation routing | Main contains the routing contract at `5f8523d7f5801ad9c5f9f4217699ea63ba54ed6e`; the requested readiness marker was not found, so activation remains gated. | MERGED / NOT ACTIVATION AUTHORITY | Current `origin/main`, CEO gate still required |

## Rule

`UNVERIFIED` and `BRANCH CANDIDATE` rows may guide investigation but may not
close a blocker, promote a model, change provider authority, or activate a
production path.
