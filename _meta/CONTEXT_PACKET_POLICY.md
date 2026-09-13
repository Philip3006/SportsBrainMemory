---
type: meta-policy
tier: warm
status: active
last_updated: 2026-09-13T23:04:08+02:00
freshness_class: stable
---
# Context Packet Policy

Memory V2 generates four bounded packets:

- `builder/context/BUILDER_A_RESEARCH.md`
- `builder/context/BUILDER_B_PRODUCTION.md`
- `builder/context/BUILDER_C_MEMORY.md`
- `builder/context/CEO_SUMMARY.md`

Each packet declares its exact canonical paths and is deterministic. Builders
must load the packet for their logical role and only the source files it
references. No builder should recursively load the full Obsidian Vault.
