---
id: WS-P0-B
type: "workstream"
tier: "warm"
status: "active"
workstream: "P0-B"
last_updated: "2026-08-16T14:00:00+02:00"
freshness_class: "release-bound"
---
# P0-B — Monitoring Truth

## Objective

Make monitoring describe execution, expectation windows, recovery capability and release provenance truthfully.

## Packets

### B1 Execution Truth
Close MON-001/MON-011/OPS-006:
- impossible `ok + exit_code!=0` eliminated
- explicit execution plane/status
- malformed/unknown execution cannot look green.

### B2 Schedule / Window Truth
Close MON-002/MON-012:
- machine-readable JobExpectation
- cron-set, interval, windowed, event-with-fallback semantics
- off-window job = inactive/not_expected, not stale.

### B3 Recovery Truth
- verified active recovery targets
- disabled/nonexistent workflows never dispatched
- `RECOVERY_UNAVAILABLE` when recovery cannot execute.

### B4 Release/Publication Provenance
Publish:
- source_release_sha
- source CI run
- runtime_data_sha
- worker release provenance
- schema/build timestamp.

## Known findings

- FND-20260814-005 through FND-20260814-010.

## Dependency

Do not implement until P0-A closes.


## V1 readiness note

Next product implementation workstream after Memory V1 acceptance.
