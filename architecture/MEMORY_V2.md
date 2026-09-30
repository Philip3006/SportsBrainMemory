---
type: architecture
tier: warm
status: active
canonical: true
last_updated: 2026-09-13T23:04:08+02:00
freshness_class: stable
---
# Memory V2 Architecture

Memory V2 has two intentionally separate layers:

1. **Canonical Memory** — reviewed Markdown records, append-only event JSON,
   generated projections, and Git history in `Philip3006/SportsBrainMemory`.
2. **Near-live operational view** — generated `_live/` Markdown/JSON in the
   local Obsidian Vault. It reports source/runtime/CI/sync observations and
   does not own canonical truth.

The update path is:

```text
structured event -> canonical event/record -> generated projections
-> bounded context packets -> validator -> reviewed Git commit
```

The live path fetches the Memory remote, checks the local worktree, pulls only
with `git merge --ff-only`, checks the Vault manifest for local edits, copies
only safe canonical changes, and regenerates `_live/`. Any conflict stops the
copy and writes `SYNC BLOCKED` visibly. No hard reset, production mutation,
Cloudflare operation, financial ledger access, or sealed research outcome is
allowed.

## Related

- [[architecture/OPERATIONAL_KNOWLEDGE_BASE]]
- [[domains/GOVERNANCE]]
- [[domains/PRODUCTION_OPERATIONS]]
- [[runbooks/incident-triage]]
