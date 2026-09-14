---
type: meta-policy
tier: warm
status: active
---
# Generated View Policy

The following files are generated projections and MUST NOT own volatile truth:

- `00_HOME.md`
- `CURRENT_STATE.md`
- `CURRENT_TASK.md`
- `CURRENT_BLOCKERS.md`
- `CURRENT_PRIORITIES.md`
- `findings/OPEN.md`
- `findings/RESOLVED.md`
- `views/*`
- `mocs/*`
- `builder/CURRENT_CONTEXT_PACKET.md`

Memory V2 additionally generates `builder/context/*` and the separate Vault
namespace `_live/*`. `_live/*` is operational status, never canonical truth,
and may be safely regenerated or ignored by Git.

Canonical owners are first-class records under `state/records`, `tasks/records`, `findings/records`, workstreams, scorecard, evidence and verification records.
