---
id: RUNBOOK-PRODUCTION-ACTIVATION
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
---
# Production Activation

**TRIGGER:** Explicit CEO request to activate a governed production path.

**CHECK:** Exact source release, runtime evidence, provider authority, quota,
model/market/identity, freshness, canary, publication, ledger, scheduler,
rollback, and observation gates.

**ACTION:** Execute only the reviewed activation contract with a lock/fence.

**ABORT CONDITION:** Any missing gate, changed source, stale evidence, or
ambiguous authority.

**ROLLBACK:** Use the recorded last-known-good deployment/artifact and fence
new work.

**EVIDENCE TO SAVE:** CEO gate, exact SHAs, gate matrix, deployment ID,
traffic, audit chain, and post-activation health.
