---
type: meta-policy
tier: warm
status: active
last_updated: 2026-09-13T23:34:53+02:00
freshness_class: stable
---
# Builder Handoff Schema

Every builder completion handoff must begin with an explicit identity line:

```text
BUILDER: 1
```

or `BUILDER: 2` / `BUILDER: 3`. The number must match the structured event's
`builder_number` and the current role ownership. A handoff without a builder
number is formally incomplete and cannot be promoted to CEO-accepted truth.

Current ownership:

- Builder 1 — Top-5 Shadow Integration Owner.
- Builder 2 — Top-5 Production / Activation Readiness Owner.
- Builder 3 — Memory / Obsidian / Observability Owner.

CEO and system events are not builder completion handoffs and use the explicit
non-builder actor values `CEO` or `SYSTEM` in `builder_number`.
