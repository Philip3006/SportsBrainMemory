---
id: RUNBOOK-WORKER-PUBLIC-MISMATCH
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
graph_domain: production
graph_role: operational
---
# Worker / Public Mismatch

**TRIGGER:** Worker and Pages/static payloads disagree.

**CHECK:** Read-only GETs, deployment/version, payload digest, updated time,
public serializer, KV key, and cache headers.

**ACTION:** Record the mismatch and compare exact source/deployment evidence;
do not upload or deploy as a diagnostic shortcut.

**ABORT CONDITION:** Any request would mutate KV, secrets, traffic, or
production data without an explicit approved recovery task.

**ROLLBACK:** None during diagnosis; preserve both payloads.

**EVIDENCE TO SAVE:** URLs, statuses, digests, timestamps, deployment ID, and
sanitized response shape.
