---
id: RUNBOOK-TOP5-ROLLBACK
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
graph_domain: top5
graph_role: operational
---
# Top-5 Rollback

**TRIGGER:** Failed canary, invalid evidence, or explicit rollback decision.

**CHECK:** Identify exact deployed source/runtime version and last-known-good
artifact; verify rollback authority and lock ownership.

**ACTION:** Stop new work, fence the affected execution, and use the approved
rollback path only.

**ABORT CONDITION:** Unknown version, missing fence, destructive ambiguity, or
no approved rollback target.

**ROLLBACK:** Restore only the recorded last-known-good state; never reset the
repository or delete historical records.

**EVIDENCE TO SAVE:** Trigger, version IDs, fence/lock, commands, result,
post-rollback health, and preserved delivery evidence.
