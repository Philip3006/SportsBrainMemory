---
id: RUNBOOK-INDEX
type: runbook-index
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: stable
canonical: true
graph_domain: production
graph_role: support
---
# Runbook Index

Every runbook follows `TRIGGER → CHECK → ACTION → ABORT CONDITION →
ROLLBACK → EVIDENCE TO SAVE`. Read the applicable runbook before touching a
provider, deployment, publication, scheduler, or ledger boundary.

- [[runbooks/top5-canary-preflight]]
- [[runbooks/top5-rollback]]
- [[runbooks/quota-evidence-failure]]
- [[runbooks/provider-auth-failure]]
- [[runbooks/stale-odds]]
- [[runbooks/worker-public-mismatch]]
- [[runbooks/pwa-publication-issue]]
- [[runbooks/nl-shadow-verification]]
- [[runbooks/historical-research-data-ingestion]]
- [[runbooks/production-activation]]
- [[runbooks/incident-triage]]
- [[runbooks/post-deploy-verification]]
- [[runbooks/AUTOMATIC_MEMORY_OBSIDIAN_SYNC]]
