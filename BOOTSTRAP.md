---
type: "bootstrap"
tier: "hot"
status: "active"
last_updated: "2026-08-14T00:03:00+02:00"
freshness_class: "stable"
token_target: "<1200"
---
# SportsBrain Bootstrap

## What SportsBrain is

SportsBrain is a hybrid sports-analysis, betting-signal and PWA system spanning Football and Tennis, predictive models, odds providers, signal generation, Cloudflare Worker/KV, GitHub Actions, local launchd jobs, a per-user betting ledger, settlement/CLV/calibration and monitoring.

## Roles

- **Owner** — final authority.
- **ChatGPT / CEO** — architecture, prioritization, independent read-only audit, scorecard and merge approval.
- **Claude / Builder** — scoped implementation, testing, commit/push/PR work.
- **Bots / workflows** — only their explicitly governed runtime/data responsibilities.

## Hard rules

1. Final stake ≤ **5%** of authoritative current bankroll.
2. Maximum **3 active bets**.
3. No auto-betting.
4. No silent Value→Manual downgrade.
5. Client state is never financial/security authority.
6. Value requires canonical signal provenance and market-correct current odds.
7. Stale, LIVE or terminal prematch Value action is blocked.
8. Tennis LIVE requires authoritative evidence; time alone is insufficient.
9. Queue ACK only after durable canonical mutation.
10. Retryable infrastructure failure is never permanent rejection.
11. Failed required gate never reaches production.
12. Source Release SHA ≠ Runtime/Data HEAD.
13. Personal betting/financial state must not be public.
14. Autonomous AI must not mutate/commit/push source.
15. ChatGPT/CEO remains read-only.

## Evidence hierarchy

1. Current production source + runtime evidence
2. Real deterministic boundary test
3. Exact-SHA CI
4. Current published data
5. Real-browser behavior
6. Builder report
7. Current Memory
8. Historical docs/comments

## Reading rule

Read [[CURRENT_STATE]] and [[CURRENT_TASK]]. Then load only the context referenced by the current task or use `builder/CURRENT_CONTEXT_PACKET.md`.

## Current phase

P0-A is still open. P0-B/C/D are deeply planned but blocked from implementation until P0-A closes and is production-verified.
