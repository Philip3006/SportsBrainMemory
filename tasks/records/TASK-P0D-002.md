---
id: TASK-P0D-002
type: task
title: Financial Writer Governance — Private Ledger Datastore
status: completed
canonical: true
tier: warm
workstream: P0-D
created_at: 2026-08-16T13:04:00+02:00
updated_at: 2026-09-13T23:04:08+02:00
freshness_class: release-bound
budget_class: standard
findings:
  - FND-20260814-011
  - FND-20260814-017
invariants:
  - GOV-005
  - GOV-007
  - QUEUE-001
  - QUEUE-002
  - QUEUE-003
  - SEC-001
depends_on:
  - TASK-P0D-001
source_paths:
  - scripts/consume_pending_bets.py
  - src/betting/
  - src/config.py
  - tests/betting/
  - tests/scripts/test_consume_pending_bets.py
  - tests/monitoring/test_financial_writer_governance.py
  - .github/workflows/consume_pending_bets.yml
  - .github/workflows/tennis_settle.yml
  - .github/workflows/tennis_closing_odds.yml
  - .github/workflows/bundesliga2_settle.yml
  - .github/workflows/ci_gates.yml
---
# TASK-P0D-002 — Financial Writer Governance — Private Ledger Datastore

Historical task completed in the source repository during the backfill window;
current financial mutation remains outside Memory V2 scope. See the canonical
P0-D and runtime/provider events for later governance hardening.

## Mission

Keep financial ledger mutation on its own durable transaction boundary; do not
collapse P0-A ACK semantics into generic bot persistence. Migrate private
financial data out of the public repository to satisfy SEC-001.

## CEO-Approved Architecture (2026-08-18)

**Authoritative private ledger datastore:** `Philip3006/sportsbrain-ledger` (private GitHub repo)

**Key decisions:**
- CSV is authoritative ledger; SQLite is derived private mirror
- `SPORTSBRAIN_LEDGER_DIR` env var is the explicit ledger root — fail-closed if unset
- `betting_journal.md` is private financial state; lives in private repo
- All four financial workflows checkout private repo via `LEDGER_PRIVATE_PAT` secret
- No fallback to public `results/ledger_*.csv` — failure is fatal, not silent
- Full public history cleanup required after migration (separate CEO authorization)
- PR #19 superseded by v2 implementation

**Private repo layout (flat, at root):**
```
sportsbrain-ledger/
├── ledger_philip.csv          ← authoritative per-user ledger
├── ledger_philip.db           ← SQLite mirror
├── bankroll_snapshot_philip.json
└── betting_journal.md
```

## Primary files / boundaries

- `src/config.py` — `SPORTSBRAIN_LEDGER_DIR`, `_resolve_ledger_dir()`, `ledger_path_for()`, `bankroll_snapshot_path_for()`, `betting_journal_path()`
- `scripts/consume_pending_bets.py` — `_LEDGER_ROOT`, `_durable_push()` uses private repo cwd
- `.github/workflows/consume_pending_bets.yml` — private ledger checkout
- `.github/workflows/tennis_settle.yml` — private ledger checkout, fatal ledger commit step
- `.github/workflows/tennis_closing_odds.yml` — same
- `.github/workflows/bundesliga2_settle.yml` — same
- `.github/workflows/ci_gates.yml` — HARD GATE 9 runs all four financial suites
- `tests/monitoring/test_financial_writer_governance.py` — 29 tests (12 new P0D-002 + 17 ported)
- `tests/conftest.py` — sets `SPORTSBRAIN_LEDGER_DIR` to tmp dir if unset

## Forbidden scope

- public serializer work
- AI healer
- model artifact promotion
- D1/KV/R2 migration (not in P0D-002 scope)

## Transaction / ACK contract (unchanged from P0-A)

```
validate → write local private ledger → stage in PRIVATE repo
→ commit PRIVATE repo → push PRIVATE repo successfully
→ ONLY THEN ACK/delete accepted pending bet from Worker KV
```

On any private ledger git failure: NO ACK. Transient failure → RETRY.

## Financial workflow classification

- **AUTHORITATIVE FINANCIAL TRANSACTION**: tennis_settle, tennis_closing_odds, bundesliga2_settle
  → own private ledger checkout + fatal commit step + own 5× retry loop
- **SECONDARY RUNTIME PUBLICATION**: consume_pending_bets workflow health step
  → Python `_durable_push()` owns private ledger durability; workflow commit = health only

## STOP conditions

- proposed shared primitive weakens P0-A durability
- canonical private ledger destination unresolved ← **RESOLVED 2026-08-18 by CEO arch decision**

## Public history cleanup

REQUIRED. Full history rewrite via `git-filter-repo --sensitive-data-removal`.
Must NOT happen during P0D-002 code cutover. Requires separate CEO authorization
after production migration is verified.

## Builder report contract

Return only: status; exact branch/head; changed files; invariant/finding
evidence; exact test counts; CI evidence; production verification state;
rollback note; remaining risks. Do not merge or broaden scope.
