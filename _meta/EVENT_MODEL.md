---
type: meta-protocol
tier: warm
status: active
last_updated: 2026-09-13T23:04:08+02:00
freshness_class: stable
---
# Memory V2 Event Model

Canonical events are append-only JSON records under `events/records/`. They
are durable project history, not a stream of runtime bot updates. The allowed
event types are `CEO_DECISION`, `PR_MERGED`, `WORKSTREAM_STARTED`,
`WORKSTREAM_COMPLETED`, `RESEARCH_GATE`, `PRODUCTION_VERIFIED`,
`BLOCKER_OPENED`, `BLOCKER_RESOLVED`, `ARCHITECTURE_CHANGED`, `ROLLBACK`, and
`DEFERRED_DEPENDENCY`.

Every event has a stable `event_id`, timezone-aware `timestamp`, `domain`,
`summary`, source repository and optional source SHA/PR, builder, CEO gate
state, affected workstreams, findings, invariants, supersession, evidence,
and an explicit `verification_state`.

`ceo_approved`, `independently_verified`, and `merged_source` may be
canonical. Builder reports are written to `events/pending/` and remain
noncanonical until promoted by a separate verified event. The updater rejects
duplicate IDs with changed payloads, path traversal, secret-like material,
missing evidence, and invalid timestamps. Reapplying an identical event is
idempotent.

Runtime-only status belongs in `_live/` and must not create a canonical event
or Memory commit on every bot run.
