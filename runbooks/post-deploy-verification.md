---
id: RUNBOOK-POST-DEPLOY-VERIFICATION
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
graph_domain: production
graph_role: operational
---
# Post-Deploy Verification

**TRIGGER:** An approved deployment reports success.

**CHECK:** Deployment/version ID, source SHA, traffic, bindings, secrets names,
cron schedules, health/logs, public response, and code parity.

**ACTION:** Perform one bounded harmless GET and the required observability
checks; compare against the pre-deploy contract.

**ABORT CONDITION:** Code drift, unexpected config/binding/traffic change,
5xx, exception, or any mutation outside the deployment.

**ROLLBACK:** Use the approved previous deployment only with explicit
authority; do not redeploy automatically.

**EVIDENCE TO SAVE:** Before/after metadata, response status/digest,
observability event, parity result, and zero-unrelated-mutation record.
