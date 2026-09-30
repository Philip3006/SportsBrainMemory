---
id: RUNBOOK-PWA-PUBLICATION-ISSUE
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
graph_domain: product
graph_role: operational
---
# PWA Publication Issue

**TRIGGER:** GitHub Pages/PWA does not reflect an accepted public artifact.

**CHECK:** Pages source SHA, static payload digest, Worker payload, browser
cache, and public/private field boundary.

**ACTION:** Perform one bounded read-only browser/network check; use the
approved publication path only after the artifact is validated.

**ABORT CONDITION:** Provider call, betting action, KV mutation, or fallback
fabrication would be required.

**ROLLBACK:** Restore the previous validated public artifact through the
approved change path.

**EVIDENCE TO SAVE:** Page URL, source SHA, digest, browser result, and
publication/deployment ID.
