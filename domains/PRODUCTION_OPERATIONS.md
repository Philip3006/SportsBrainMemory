---
id: DOMAIN-PRODUCTION-OPERATIONS
type: domain
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
---
# Production Operations

## CURRENT FACT

The production surface is split into the GitHub Pages/PWA layer, the
Cloudflare Worker, its KV-backed public/private boundary, scheduled/runtime
writers, provider adapters, and monitoring. The current source main is
`cdcfa2d57266cd3089d2910e6aa9d1a623a8300b`; the latest meaningful merged
configuration source is `c6a7b7ed0c0824276650f241ec41ca53a27e63b7`.

## Boundaries

- Read-only verification precedes any mutation.
- Public Worker/PWA evidence does not prove private runtime or ledger state.
- Cloudflare/KV writes, deployments, scheduler changes, provider authority,
  betting, and ledger mutation each require their own approved path.
- Workers Logs configuration is merged in PR #210; production deployment state
  must still be read from Cloudflare evidence rather than inferred from Git.
- PostHog PR #221 is implementation-ready but not production-live.

## Operations map

- [[runbooks/top5-canary-preflight]]
- [[runbooks/worker-public-mismatch]]
- [[runbooks/pwa-publication-issue]]
- [[runbooks/post-deploy-verification]]
- [[runbooks/incident-triage]]
- [[domains/MONITORING_AND_RECOVERY]]

## Related

- [[providers/PRV-WORKER]]
- [[components/CMP-PUBLICATION]]
- [[components/CMP-MONITORING]]
- [[components/CMP-BETTING]]
- [[domains/PWA_AND_WORKER]]
- [[domains/DATA_AND_PROVIDERS]]
- [[domains/GOVERNANCE]]
- [[decisions/records/DEC-0031]]
- [[evidence/PR_EVIDENCE_INDEX]]
