---
id: RUNBOOK-QUOTA-EVIDENCE-FAILURE
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
---
# Quota Evidence Failure

**TRIGGER:** A provider/AI operation reports a conservative quota condition.

**CHECK:** Authoritative quota evidence, retry-after/reset time, operation
class, and whether the error is actually quota rather than auth/rate-limit/code.

**ACTION:** Persist `PAUSED_QUOTA` with bounded backoff or explicit reset;
preserve evidence and do not consume normal attempt/dead-letter budgets.

**ABORT CONDITION:** No authoritative evidence, ambiguous error, or request to
expand quota/spend.

**ROLLBACK:** Automatic `PAUSED_QUOTA → READY` only after eligibility; never
revive `FAILED_SAFE`/dead-letter history.

**EVIDENCE TO SAVE:** Sanitized error class, state transition, reset time,
attempt counters, and audit-chain entry.
