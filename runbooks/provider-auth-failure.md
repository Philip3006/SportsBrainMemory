---
id: RUNBOOK-PROVIDER-AUTH-FAILURE
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: runtime-sensitive
canonical: true
---
# Provider Auth Failure

**TRIGGER:** Credential resolution or provider auth check fails.

**CHECK:** Existence and permissions only in the exact operator context; no
secret output; request count and circuit state.

**ACTION:** Restore the existing protected source if available, then verify a
non-empty key locally without an HTTP call.

**ABORT CONDITION:** Missing credential, suspected secret exposure, or any
need to probe the provider to diagnose locally.

**ROLLBACK:** Leave circuit/state unchanged; do not create a new secret.

**EVIDENCE TO SAVE:** Boolean availability, redacted source type, zero-request
confirmation, and sanitized failure stage.
