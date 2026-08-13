---
type: "builder-contract"
tier: "hot"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
---
# Claude Context Contract

## Goal

Keep Builder prompts precise while minimizing repeated context.

## Loading order

1. `BOOTSTRAP.md`
2. `CURRENT_STATE.md`
3. `CURRENT_TASK.md`
4. `builder/CURRENT_CONTEXT_PACKET.md`
5. only current source files/direct callers/tests.

## Hard rule

Do not recursively read the vault.

## Evidence

Builder output is not CEO approval. A green suite is necessary but not sufficient; tests must exercise the real claimed boundary.

## Failure semantics

- PERMANENT_REJECT → invalid as submitted; ACK only with auditable reason.
- RETRYABLE → temporary authority/infrastructure failure; keep intent.
- DEGRADED → safe reduced-quality information.
- UNSAFE → hard invariant cannot be established; block money action.
- UNKNOWN → for P0 money actions, fail closed/retry.

## Model routing

- Sonnet + High: precise scoped implementation/tests.
- Opus + Medium: choose architecture/contracts when multiple legitimate designs exist.
