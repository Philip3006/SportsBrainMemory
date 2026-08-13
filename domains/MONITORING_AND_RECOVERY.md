---
type: "domain"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# Monitoring & Recovery

## Current problem

Monitoring combines caller-reported health, fixed cadence assumptions and limited outcome checks. It has produced impossible `ok + exit_code=1` states and stale false positives for windowed jobs.

## P0-B target

Separate:
- execution_status
- expectation state
- service status
- execution plane
- trigger type
- source/runtime release provenance.

## Recovery

Deterministic allowlisted retries can be automated.
Source repair is a different operation and belongs to controlled Builder governance.

Current healer mappings include inactive/nonexistent workflow targets; recovery must verify target capability and emit `RECOVERY_UNAVAILABLE` when it cannot act.
