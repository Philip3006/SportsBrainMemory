---
id: RUNBOOK-INCIDENT-TRIAGE
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
graph_domain: production
graph_role: operational
---
# Incident Triage

**TRIGGER:** User-visible failure, safety alarm, mismatch, or unexpected
mutation.

**CHECK:** Scope, timestamp, source/runtime identity, logs/health, recent
deployments, locks/fences, provider requests, ledger, and public artifacts.

**ACTION:** Stabilize read-only first, fence affected work, preserve evidence,
and classify the incident.

**ABORT CONDITION:** Destructive cleanup, secret inspection, or speculative
repair without an approved boundary.

**ROLLBACK:** Apply the incident-specific rollback only after target identity
and authority are confirmed.

**EVIDENCE TO SAVE:** Timeline, exact commands, statuses, IDs/digests,
mutations (or zero-mutation proof), and follow-up finding.
