---
id: RUNBOOK-STALE-ODDS
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
---
# Stale Odds

**TRIGGER:** Odds age exceeds the applicable freshness contract.

**CHECK:** Capture time, kickoff, market identity, fixture identity, provider
authority, and whether a refresh is authorized.

**ACTION:** Mark the candidate non-actionable and preserve the stale evidence.

**ABORT CONDITION:** Attempt to reuse stale odds, substitute a different
market/provider, or refresh without provider authorization.

**ROLLBACK:** Remove only the non-actionable candidate from the pending path;
do not rewrite history.

**EVIDENCE TO SAVE:** Fixture/market IDs, timestamps, age calculation, and
blocked decision.
