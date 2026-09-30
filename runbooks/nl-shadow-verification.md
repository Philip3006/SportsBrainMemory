---
id: RUNBOOK-NL-SHADOW-VERIFICATION
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: model-bound
canonical: true
---
# Nations League Shadow Verification

**TRIGGER:** A new or existing NL public shadow artifact needs verification.

**CHECK:** Schema, source/data SHAs, fixture identities, future kickoffs,
market/model coverage, digests, `SHADOW_ONLY`, `WEAK_EVIDENCE_SHADOW_ONLY`,
`no_bet`, and zero publication/ledger/scheduler mutation.

**ACTION:** Validate the immutable artifact and exact public projection once.

**ABORT CONDITION:** Missing IDs, stale fixtures, malformed coverage, or any
path that would activate/publish/bet.

**ROLLBACK:** Keep the artifact shadow-only; do not stage or publish it.

**EVIDENCE TO SAVE:** Run ID, artifact/snapshot digests, operation manifest,
counts, skip reasons, and sanitized HTTP statuses.
