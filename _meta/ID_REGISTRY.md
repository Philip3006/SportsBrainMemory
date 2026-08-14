---
type: "id-registry"
tier: "warm"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "release-bound"
---
# ID Registry

## Findings

- `FND-20260814-001` — Remote durability is not proven by a clean staging area (open)
- `FND-20260814-002` — Retryable authoritative-bankroll failure can become permanent rejection (open)
- `FND-20260814-003` — Cancellation does not share placement durable-ACK semantics (open)
- `FND-20260814-004` — Focused Playwright submit proof can pass without an actual submit (open)
- `FND-20260814-005` — Health can report status=ok with exit_code=1 (open)
- `FND-20260814-006` — Health cadence model has drifted from actual workflow schedules (open)
- `FND-20260814-007` — Recovery maps reference inactive/nonexistent workflow filenames (open)
- `FND-20260814-008` — Windowed Bundesliga2 jobs are modeled as globally periodic (open)
- `FND-20260814-009` — Event-driven consumer is modeled as a fixed 2-minute job (open)
- `FND-20260814-010` — Odds refresher execution is missing from aggregate health coverage (open)
- `FND-20260814-011` — Personal ledger and DB are tracked in public repository (open)
- `FND-20260814-012` — Public signals snapshot contains bankroll/open-bet private state (open)
- `FND-20260814-013` — Unauthenticated Worker default-user snapshot can expose private state (open)
- `FND-20260814-014` — Privacy/legal text contradicts actual persistence architecture (open)
- `FND-20260814-015` — AI healer has autonomous source edit/commit/push capability (open)
- `FND-20260814-016` — Tennis production LIVE mode is governed by broad user override (open)
- `FND-20260814-017` — Automated Git writers use inconsistent persistence primitives (open)
- `FND-20260814-018` — Runtime-data commits continuously obscure source-release provenance (open)
- `FND-20260814-019` — Tennis non-H2H refresh can attach H2H-B odds to unrelated markets (open)
- `FND-20260814-020` — Tennis fixture identity is not globally unique across event instances (open)
- `FND-20260814-021` — Tennis LGBM train/live RollingState semantics differ (open)
- `FND-20260814-022` — Historical production measurement population is contaminated (open)
- `FND-20260814-023` — Historical Tennis rows contain blank/wm2026 identity contamination (open)
- `FND-20260814-024` — Tennis schedule authority metadata can drift across source/odds_source fields (open)
- `FND-20260814-025` — TennisExplorer parsing can leak tournament context across fixtures (open)
- `FND-20260814-026` — Closing-odds proposition parity is not fully verified (open)
- `FND-20260814-027` — Fabricated fallback odds in PWA were previously possible (resolved_production)
- `FND-20260814-028` — Elapsed-time Tennis false-LIVE behavior was materially hardened (resolved_production)
- `FND-20260814-029` — Runtime bots previously contaminated source branches (resolved_production)

## Decisions

- `DEC-0001` — CEO is strictly read-only (active)
- `DEC-0002` — Claude is the normal Builder (active)
- `DEC-0003` — No merge without explicit approval and rollback awareness (active)
- `DEC-0004` — Maximum three active bets (active)
- `DEC-0005` — Five-percent bankroll hard cap (active)
- `DEC-0006` — No auto-betting (active)
- `DEC-0007` — Failed required gate never production (active)
- `DEC-0008` — One concept has one canonical truth owner (active)
- `DEC-0009` — Source Release SHA is distinct from Runtime/Data HEAD (active)
- `DEC-0010` — Production score and projected score are separate (active)
- `DEC-0011` — Queue ACK follows durable canonical mutation (active)
- `DEC-0012` — Public product data and private user state must be separated (active)
- `DEC-0013` — Plan early, finalize Builder prompt late (active)
- `DEC-0014` — Selective shared-memory retrieval (active)
- `DEC-0015` — 10.0 means effectively flawless (active)
- `DEC-0016` — P0 implementation order is A → B → C → D (active)
- `DEC-0017` — Actionable current odds must match exact market proposition (active)
- `DEC-0018` — Tennis LIVE requires authoritative evidence (active)
- `DEC-0019` — Production measurement requires explicit provenance (active)
- `DEC-0020` — AI healer becomes diagnosis/recovery-only (approved_target)
- `DEC-0021` — Shared Memory is private Markdown/Git; Obsidian is UI (active)
- `DEC-0022` — No MCP in Shared Memory V1 (active)

## Incidents

- `INC-0001` — Branch contamination by runtime bots
- `INC-0002` — PWA fabricated/fallback odds
- `INC-0003` — False Tennis LIVE
- `INC-0004` — Absurd EV / stale actionability
- `INC-0005` — P0-A end-to-end betting safety bypass
- `INC-0006` — P0-A review-loop findings
- `INC-0007` — Health false-green
- `INC-0008` — Public private-state exposure

## Current task

- `TASK-P0A-009`


## P0-A CEO review additions — 2026-08-14T01:06:00+02:00

- `FND-20260814-030` — Consumer exact-source gap (open)
- `FND-20260814-031` — Legacy PWA action-contract/browser gap (open)
- `TASK-P0A-010` — Final Closure Correction


## P0-A CEO review additions — 2026-08-14T01:31:00+02:00

- `TASK-P0A-011` — Queue Identity + Final Recommendation Actionability


## P0-A CEO review addition — 2026-08-14T01:57:00+02:00

- `TASK-P0A-012` — Final Queue Atomicity + Compact-Mode Closure
