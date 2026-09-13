---
type: meta-protocol
tier: warm
status: active
last_updated: 2026-09-13T23:04:08+02:00
freshness_class: stable
---
# Events

`records/` contains verified canonical Memory V2 events. `pending/` contains
Builder handoffs or unresolved evidence and is explicitly noncanonical. Use
`python tools/update_memory.py payload.json` to validate and ingest structured
events; do not hand-edit generated projections as truth.
