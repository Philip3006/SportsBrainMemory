---
id: RUNBOOK-TOP5-CANARY-PREFLIGHT
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
graph_domain: top5
graph_role: operational
---
# Top-5 Canary Preflight

**TRIGGER:** A reviewed canary proposal exists.

**CHECK:** Fresh main SHA; clean runtime; source/runtime identity; provider
authority; quota; fixture identity; odds age ≤900s; model/evidence; activation,
publication, ledger, and rollback gates.

**ACTION:** Produce a read-only evidence bundle and exact-head CI result.

**ABORT CONDITION:** Any missing, stale, conflicting, or unapproved gate.

**ROLLBACK:** No activation. If already activated, use [[runbooks/top5-rollback]].

**EVIDENCE TO SAVE:** Source/runtime SHAs, timestamps, provider order, fixture
IDs, odds/model digests, gate results, and CEO decision reference.
