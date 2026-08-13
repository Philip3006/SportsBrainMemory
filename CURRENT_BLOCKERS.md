---
type: "current-blockers"
tier: "hot"
status: "current"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "runtime-sensitive"
workstream: "P0-A"
---
# Current Blockers

These are the **merge-blocking** findings for the active P0-A workstream.

## FND-20260814-001 — Remote durability clean-tree gap

**Severity:** P0  
**Status:** OPEN  
**Workstream:** P0-A

`_durable_push()` can treat no staged diff as proof of remote durability even if a previous local commit was never pushed.

See `findings/records/FND-20260814-001.md`.

## FND-20260814-002 — Retryable bankroll failure can be permanently ACKed

**Severity:** P0  
**Status:** OPEN  
**Workstream:** P0-A

Authoritative bankroll unavailable can flow through generic rejection and delete an otherwise valid pending intent.

See `findings/records/FND-20260814-002.md`.

## FND-20260814-003 — Cancellation lacks the same durable ACK boundary

**Severity:** P0  
**Status:** OPEN  
**Workstream:** P0-A

Cancel request can mutate local ledger and clear queue before canonical remote durability is proven.

See `findings/records/FND-20260814-003.md`.

## FND-20260814-004 — Focused Playwright submit proof is conditional

**Severity:** P0  
**Status:** OPEN  
**Workstream:** P0-A

The current submit test can pass without proving an actual `/pending_bets` request if confirm remains disabled.

See `findings/records/FND-20260814-004.md`.

## Rule

Any new confirmed CEO finding in the active workstream must be added here and to [[CURRENT_TASK]] before the next Builder execution.
