---
type: "meta-policy"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
---
# Memory Rules

## Canonical-owner rule

Every volatile truth has exactly one canonical owner.

| Truth | Owner |
|---|---|
| Current project status | `CURRENT_STATE.md` |
| Current Builder task | `CURRENT_TASK.md` |
| Active blockers | `CURRENT_BLOCKERS.md` |
| Invariant definition/status | domain file under `invariants/` |
| Finding | its finding record |
| Decision | its decision record |
| Product score | `product/SCORECARD.md` |
| Architecture | `architecture/` |
| Historical audit | `history/archive/` |

Other files may link to the owner but should not maintain competing volatile values.

## Confirmed-finding rule

Every confirmed CEO finding must be persisted in shared memory.

If it affects the active Builder workstream, before the next Builder run:
1. create/update Finding record;
2. link affected invariant(s);
3. update `CURRENT_BLOCKERS.md`;
4. update `CURRENT_TASK.md`;
5. rebuild current context packet;
6. supersede any obsolete prompt/task version.

## No auto-closure

Claude reports do not change CEO truth automatically.
Only independent CEO verification can mark a finding/invariant closed.

## Freshness

Memory can be stale. Current source/runtime evidence outranks Memory.

## Security

Never store:
- API keys
- bearer/user/master tokens
- secrets
- full private ledger rows
- private push endpoints
- credentials.

Store the existence and architecture of sensitive data, not the sensitive payload itself.
