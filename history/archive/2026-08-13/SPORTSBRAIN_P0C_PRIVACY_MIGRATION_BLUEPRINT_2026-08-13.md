# SportsBrain — P0-C Privacy & Persistence Migration Blueprint

**Date:** 2026-08-13  
**Status:** Pre-implementation architecture. No repository changes.  
**Dependencies:** P0-A closed; P0-B Monitoring Truth deployed before destructive/cutover phases.  
**Primary invariants:** SEC-001, SEC-002, SEC-003, SEC-004, SEC-005, SEC-006, SEC-008, SEC-009, SEC-010, DATA-013, OPS-001.

---

# 1. Problem statement

SportsBrain currently mixes three fundamentally different data classes:

1. **Public sports/product data**
   - fixtures
   - model outputs
   - signals
   - odds
   - live scores
   - public health/build metadata.

2. **Private per-user betting data**
   - bankroll
   - open bets
   - settled bets
   - P&L
   - stake history
   - betting journal/history.

3. **Operational secrets/private backend state**
   - API/master tokens
   - user tokens
   - push subscriptions
   - private datastore credentials.

The current architecture replicates class 2 into public Git/Pages artifacts and exposes the default user's private state through an unauthenticated signals path.

P0-C must separate these classes without breaking the PWA.

---

# 2. Confirmed exposure surfaces

The migration must address all of these, not only one CSV.

## Public repository
Tracked personal/financial artifacts include:
- `results/ledger_philip.csv`
- `results/ledger_philip.db`
- historical ledger backups
- betting journal/report artifacts that may contain personal betting history.

## Public Pages payload
`docs/data/signals.json` contains:
- default/user identity
- open bets
- settled/history-derived state
- bankroll_state.

`docs/data/signals_philip.json` is an explicitly user-named public artifact.

## Worker public path
Unauthenticated `GET /signals.json` resolves to the default user and can fall back to default-user state.

## PWA
The browser fetches the Cloudflare signals URL without Authorization and falls back to public static `data/signals.json`.

Therefore privacy is currently a **publication architecture problem**.

---

# 3. Target data architecture

```text
                        ┌───────────────────────────┐
External/model data ───>│ Public Product Snapshot  │
                        │ fixtures/signals/odds     │
                        └─────────────┬─────────────┘
                                      │
                       public GET     │
                                      v
                               PWA public UI

Private user ledger ───> Private User State API
                         bankroll/open/settled
                                │
                       auth GET │
                                v
                           PWA private UI

Pending/cancel intent ─> Authenticated Worker API ─> durable private ledger
```

The public product must be useful without private login state.

---

# 4. Public schema

A public snapshot may include:

```text
schema_version
generated_at
build_info
health_public
schedule
football signals
tennis signals
model evaluations intended for users
current odds
public live scores
public tournament/league metadata
```

It must not include:
- username
- default_user
- bankroll
- exposure
- open_bets
- settled_bets
- personal history
- P&L
- private stake records
- tokens
- subscription endpoints.

### Hard test
A public serialization test should recursively reject forbidden keys/patterns.

Example denylist concept:
```text
bankroll_state
open_bets
settled_bets
history (if personal)
user
default_user
pnl_closed
stake history
```

The exact schema should be explicit rather than depending only on a denylist.

---

# 5. Private schema

Authenticated `/me` state may include:

```text
schema_version
user_id
published_at
bankroll
open_bets
settled_bets
pending_sync
history
preferences
private health relevant to user's actions
```

Every private response must carry an explicit owner/user identifier so the server and client can assert routing.

Missing private state:
- returns empty/404/initial state for that authenticated user;
- never falls back to another user.

---

# 6. API boundary

Conceptual separation:

```text
GET  /public/signals
GET  /me/state
POST /me/pending_bets
GET  /me/pending_bets
POST /me/cancel_bet
```

Exact route names can differ.

## Public endpoint
- no user-specific fields;
- no default-user private fallback;
- cacheable under appropriate freshness policy.

## Private endpoint
- requires user bearer token;
- resolved user comes from token identity;
- query parameter cannot switch identity;
- master/admin routing exists only for trusted backend clients;
- never accessible through static Pages fallback.

---

# 7. Authentication invariants

1. Browser never receives backend master token.
2. User token identifies exactly one user.
3. User A cannot query or mutate user B.
4. Missing token never resolves to Philip.
5. Expired/grace token semantics are explicit and tested.
6. Private endpoint response contains asserted owner identity.
7. Static fallback never contains private state.
8. Logs avoid sensitive token/private payload leakage.

Required security matrix:

| Request | Expected |
|---|---|
| no token → public | 200 public-only |
| no token → private | 401 |
| valid A → A private | 200 A |
| A token + user=B | reject |
| expired A token | 401 or documented grace |
| master backend + user=A | allowed only on admin/backend route |
| valid A, state missing | A-empty/404, never default user |

---

# 8. Zero-downtime migration phases

## C0 — Inventory and freeze
Before changes:
- enumerate every public artifact containing private fields;
- enumerate all readers of `signals.json`;
- enumerate all writers of ledgers and per-user snapshots;
- freeze creation of new public private-data formats.

No cleanup yet.

## C1 — Add clean public product snapshot
Introduce a new public serializer/endpoint that excludes all user state.

Keep legacy path alive during compatibility window.

Acceptance:
- public snapshot supports home/sport/detail views;
- no private fields;
- stable schema version;
- browser smoke.

## C2 — Add authenticated private endpoint
Expose bankroll/open/settled state only through authenticated user route.

Acceptance:
- auth isolation matrix green;
- no default fallback;
- user owner assertion;
- PWA not yet dependent on it.

## C3 — PWA dual fetch
PWA load sequence:

```text
fetch public product snapshot
→ render public UI
→ if user token:
     fetch private /me state
     render bankroll/bets/history
  else:
     render logged-out/private-unavailable state
```

Cloud/public failure semantics are independent from private failure.

Examples:
- public works, private down → models/signals visible; betting/history disabled with clear degraded state.
- private works, public stale → no Value actions because signal truth unavailable.
- no token → informational product still works.

## C4 — Stop private static publication
After deployed dual-fetch verified:
- stop writing private fields to `docs/data/signals.json`;
- stop generating `signals_<user>.json` under public Pages;
- remove public fallback to user private state.

## C5 — Move canonical private ledger
Migrate new ledger writes to private durable store.

Run dual-read/reconciliation until parity proven.

## C6 — Remove active-tree private artifacts
Only after private store cutover:
- remove personal ledger CSV/DB from public tracked tree;
- stop committing backups/private journals;
- add ignore/allowlist controls;
- scan Pages and repo tree for private artifacts.

## C7 — Historical cleanup
Separate high-risk operation after active PRs are stabilized.

Never combine with live API migration.

---

# 9. Private ledger datastore ADR

Before C5, Builder writes an ADR comparing at least:

## Option A — Separate private Git data repository

### Pros
- low migration complexity;
- existing CSV/commit audit model reusable;
- easy manual backup.

### Cons
- Git remains transactionally awkward;
- branch/push conflicts remain;
- queue durability still tied to remote Git behavior;
- not ideal for multi-user/commercial product.

## Option B — Cloudflare D1 / transactional database

### Pros
- transaction semantics;
- natural row-level user identity;
- better queue/ledger durability;
- queryable reporting;
- cleaner product architecture.

### Cons
- schema migration;
- backup/export/restore needed;
- new operational dependency;
- more initial engineering.

## Option C — Other managed DB/object store
Allowed if ADR proves:
- per-user access control;
- durable transactions or equivalent;
- backups;
- exportability;
- observability;
- acceptable cost/complexity.

### CEO target
Prefer a transactional private database for mature architecture.

A private Git bridge is acceptable only as an explicitly temporary risk-reduction step.

---

# 10. Migration reconciliation

A data migration is not complete when files were copied.

Required reconciliation for each user:

```text
row_count old == row_count new
stable bet identity sets equal
open set equal
settled set equal
sum stake equal
sum pnl equal
bankroll recomputation equal
latest mutation timestamp equal or explained
```

Differences produce a migration report and block cutover.

No silent coercion of historical sport/league identity during privacy migration.

---

# 11. Rollback strategy

Each phase must be independently reversible.

## Public endpoint rollout
Rollback:
- PWA can temporarily fall back to legacy public product path, but never to legacy private exposure after privacy cutover.

## Private endpoint
Rollback:
- preserve old private persistence during dual-write window.

## Ledger datastore migration
Rollback requires:
- immutable pre-cutover export;
- last synchronized mutation marker;
- deterministic re-import/reconciliation;
- no queue ACK during ambiguous ownership state.

## Pages cleanup
Rollback:
- code/static public product files restorable;
- private files are **not** reintroduced as rollback.

Privacy rollback may restore service functionality, never restore a known public privacy defect.

---

# 12. History cleanup rules

Removing a file from current main is not equivalent to removing prior Git history.

History cleanup should be treated as a separate migration because it can disrupt:
- open branches/PRs;
- clones/worktrees;
- commit SHAs;
- deployment references.

Prerequisites:
1. P0-A resolved;
2. P0-C new private store proven;
3. no critical open branch depends on old history;
4. complete private backup;
5. exact patterns;
6. dry-run mirror/clone;
7. Pages/deployment test;
8. explicit user approval.

Do not perform history rewrite as part of ordinary privacy code PR.

---

# 13. Public artifact allowlist

Long-term, prefer an allowlist over trying to remember every sensitive filename.

Example public `docs/data` classes:
- public signals
- public schedule
- public live scores
- public squads if intended
- public forecast
- safe health/public provenance.

CI should fail if serialized public artifact contains private keys or a filename matching:
- `ledger_*`
- user-specific financial snapshot
- private DB
- token/subscription export.

---

# 14. Legal/privacy consistency

The product privacy page must describe actual behavior.

Architecture should be fixed first, then legal/privacy copy updated to match:
- what is stored locally;
- what is stored server-side;
- why;
- retention/deletion;
- push subscription handling;
- third-party infrastructure.

Do not “fix” architecture by changing wording alone.

Legal compliance for a public/commercial launch is a separate verified legal task.

---

# 15. P0-C acceptance gate

P0-C closes only when:

- public repo current tree contains no personal ledger/DB;
- public Pages payload contains no personal bankroll/bets/P&L/user ID;
- unauthenticated Worker cannot return private user state;
- missing user state never falls back to another user;
- private state requires user auth;
- PWA works without token for public product;
- PWA works with token for private user state;
- private durable ledger reconciles exactly;
- new writes no longer go to public repo;
- private artifact CI scan is green;
- privacy copy matches deployed architecture;
- public PWA remains continuously available.

---

# 16. Recommended implementation model

### C1/C2 architecture
**Opus + Medium Effort**

### C3 frontend migration
**Sonnet + High Effort**

### C4 datastore ADR
**Opus + Medium Effort**

### C5/C6 migration implementation
**Sonnet + High Effort**, with narrow phases and rollback after each.

Do not ask one Claude session to redesign API, migrate ledger, rewrite history and update legal copy at once.

---

# 17. CEO decision

P0-C should be treated as **data-boundary surgery**, not repository cleanup.

The correct success condition is not:

> “ledger_philip.csv is gone.”

It is:

> **Public SportsBrain and private user state have separate schemas, separate access paths, separate persistence responsibilities and independently testable trust boundaries.**
