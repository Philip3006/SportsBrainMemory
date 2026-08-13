# SportsBrain — P0 Execution Blueprint

**Prepared:** 2026-08-13, Europe/Berlin  
**CEO role:** Read-only architecture / audit / prioritization  
**Runtime-data `main` HEAD at planning snapshot:** `c69f5549022d372acfd2a90f3ba8e609c5d97b21`  
**Open P0-A PR #10 reviewed HEAD:** `f2f7831fdaead6667b6eb53c0021a7bc0377eebf`  
**Exact P0-A CI run:** `31741469276` — success, but CI green is not semantic approval.  
**Companion artifacts:** `SPORTSBRAIN_SYSTEM_MAP_2026-08-13.md` and `SPORTSBRAIN_INVARIANT_REGISTRY_2026-08-13.md`.

---

# 0. Purpose

This document turns the 159-invariant registry into a sequenced execution program. It is the operating bridge between CEO-level system understanding and bounded Claude Builder tasks.

The new execution model is:

> **Invariant IDs define the requirement. Task packets define the allowed change surface. Tests prove the actual boundary. The CEO independently verifies closure.**

This is intentionally designed to reduce Claude context consumption. Claude should no longer need a full project history for every fix.

---

# 1. Global rules

## 1.1 Governance
- ChatGPT/CEO remains strictly read-only.
- Claude/Builder is the normal project mutator.
- No merge without later explicit CEO/user approval.
- No force push or destructive reset.
- Preserve the user's original dirty worktree.
- Use isolated worktrees/branches.
- Production PWA must remain continuously usable.

## 1.2 Upstream dependency
P0-B/C/D can be audited and designed now, but **P0-B implementation must not begin before P0-A closes**.

Reason:
- monitoring must describe final queue/betting semantics;
- privacy migration must migrate final ledger/private-state semantics;
- governance rules must govern the final writers;
- otherwise we encode temporary defects into downstream systems.

## 1.3 Closure standard
A P0 item closes only after applicable layers are proven:
1. code reviewed against invariant;
2. deterministic real-boundary tests;
3. exact relevant SHA CI green;
4. merged;
5. post-merge source inspected;
6. runtime/backend verified;
7. published data verified;
8. real browser/public PWA verified for user-facing work;
9. high-risk monitor exists or is explicitly queued.

## 1.4 Compatibility cannot preserve wrong semantics
Backward compatibility may preserve format, not false truth.

Never preserve:
- missing Tennis league as `wm2026`;
- malformed Value as Manual;
- infrastructure outage as permanent reject;
- missing user state as another user's state;
- non-zero exit as `ok`;
- missing market quote as unrelated H2H odds.

---

# 2. Dependency graph

```text
P0-A FINAL CLOSURE
  |
  +--> P0-B Monitoring Truth
  |      B1 Execution Truth
  |      B2 Schedule / Window Truth
  |      B3 Recovery Truth
  |      B4 Release / Publication Provenance
  |
  +--> P0-C Privacy & Persistence
  |      C1 Public / Private Data Contract
  |      C2 Authenticated Private State
  |      C3 PWA Dual-Channel Migration
  |      C4 Private Durable Ledger Persistence
  |      C5 Public Artifact / History Cleanup
  |
  +--> P0-D Governance & Data Integrity
         D1 Autonomous Source Mutation Control
         D2 Hard Policy vs Tunable Config
         D3 Tennis Rollout Evidence Gates
         D4 Historical Identity Integrity
         D5 Source Release vs Runtime-Data Architecture

Then:
Model Integrity
→ Wave 3D Production Trust Monitor
```

**Implementation order:** P0-A → P0-B → P0-C → P0-D → Model Integrity → Wave 3D.

P0-B comes before P0-C because a persistence/privacy migration without truthful operational monitoring is harder to execute safely.

---

# 3. Gate A0 — P0-A final closure

PR #10 is directionally strong and its reviewed exact-head CI is green, but P0-A remains **OPEN** because four semantic blockers survive.

## A0-1 — Remote durability must be proven

**Invariants:** QUEUE-001, QUEUE-002, QUEUE-003, QUEUE-008.

Current candidate `_durable_push()` treats “nothing staged” as proof that local ledger state is already durable on canonical remote. That is not logically sufficient.

Counterexample:
1. previous run appends and commits locally;
2. remote push fails;
3. process exits;
4. retry sees ledger row as a duplicate;
5. no new staged diff exists;
6. local HEAD still contains an unpushed ledger commit;
7. candidate returns success;
8. pending KV item may be ACKed even though canonical remote never received it.

### Required target
Before ACK, prove one of:
- this run successfully pushed the relevant mutation; or
- canonical remote is proven to contain the relevant commit/state.

Working-tree cleanliness is never durability evidence.

Possible correct mechanisms:
- fetch and prove relevant local commit is ancestor/contained in `origin/main`;
- verify exact canonical bet identity exists in remote durable ledger;
- or implement a durable outbox/persistence receipt.

### Required cases
- local unpushed commit + clean tree → no ACK;
- local commit contained in origin → ACK allowed;
- remote already contains mutation → idempotent ACK;
- push exhaustion → no ACK + non-zero;
- ACK failure after remote persistence → safe retry.

---

## A0-2 — ACCEPT / REJECT / RETRY must be explicit

**Invariants:** QUEUE-004, QUEUE-005, QUEUE-010.

Current candidate returns `row=None` for both permanent validation failures and transient authoritative-state failures. `_fetch_validate_user()` then treats every `row=None` as rejected and immediately ACKs it.

This means “authoritative bankroll unavailable” can permanently delete a legitimate user intent.

### Target state machine

```text
ACCEPT(row)
REJECT(code, reason)
RETRY(code, reason)
```

Permanent REJECT examples:
- malformed payload;
- invalid source;
- canonical signal mismatch;
- confirmed stake >5%;
- fourth active bet;
- stale/terminal/non-actionable Value signal.

RETRY examples:
- authoritative bankroll unavailable;
- authoritative active-bet state unavailable;
- temporary Worker/backend/network failure;
- durable persistence unavailable.

ACK rules:
- ACCEPT → only after durability proof;
- REJECT → ACK after auditable reason;
- RETRY → never ACK.

Required regression:
authoritative bankroll lookup failure for otherwise valid bet must leave the item pending.

---

## A0-3 — Cancellation must share durable ACK semantics

**Invariants:** QUEUE-006, QUEUE-007, QUEUE-008.

Current cancellation path can mutate local ledger and clear cancellation queue before the same remote durability proof used for placements.

### Preferred transaction
```text
fetch placement intents + cancellation intents
→ classify
→ apply accepted local mutations
→ one durable persistence boundary
→ ACK placements and cancellations after proof
```

At minimum, a cancellation queue item cannot be deleted before its ledger cancellation is durably confirmed.

Required tests:
- cancellation + durable push → ACK after push;
- cancellation + push failure → request remains;
- cancellation already durable + previous ACK failure → idempotent ACK;
- mixed placement + cancellation run cannot ACK either ahead of durability boundary.

---

## A0-4 — Playwright must actually submit

**Invariants:** REL-009, UX-008, BET-019.

The current focused submit test can pass when confirmation is disabled because the request assertions are conditional on a request having been captured.

### Required browser fixture
Provide valid:
- fresh canonical signal;
- current odds;
- current EV;
- valid risk state;
- bankroll state;
- active-bet count;
- any required publication freshness.

Then assert:
1. confirm is enabled;
2. click happens;
3. `/pending_bets` intercepted exactly once;
4. payload source is `value`;
5. canonical signal_id is sent;
6. odds equal canonical current_odds;
7. stake obeys 5%;
8. no JS ReferenceError/error.

If no request is captured, the test must fail.

---

## P0-A final closure gate

P0-A may close only after:
- A0-1 through A0-4 fixed;
- new exact PR head CI green;
- remote containment logic tested, not mocked away;
- real Playwright submit mandatory;
- branch safely synchronized with latest moving main;
- no Ruff baseline inflation;
- CEO semantic re-audit passes;
- Builder merges only after approval;
- post-merge source release SHA identified;
- post-merge CI green;
- deployed Worker/public PWA verified;
- queue durability proven in production-like path.

---

# 4. P0-B — Monitoring Truth

## Objective
Monitoring must answer:

> What actually ran, did it succeed, was it expected to run now, and can recovery really execute?

Do not build full Wave 3D betting semantics yet.

## B1 — Execution Truth

**Close:** MON-001, MON-011, OPS-006.

Current health writer lets caller choose `status` independently from `exit_code`. Public health has already contained `ok` with exit code 1.

### Target snapshot fields
```text
execution_status = success | failure | skipped | running | unknown
service_status   = ok | degraded | error | stale | inactive | unknown
exit_code
execution_plane  = github_actions | launchd | worker | manual
trigger_type
run_id
source_release_sha
runtime_data_sha
started_at
finished_at / duration
fallback_used
error
```

Hard rules:
- completed non-zero exit can never be service `ok`;
- unknown execution outcome can never be `ok`;
- successful fallback can be `degraded`;
- malformed health input is visible, not silently ignored.

Likely files:
- `src/monitoring/health_writer.py`
- `src/monitoring/aggregate_health.py`
- workflow/launchd wrappers
- new `tests/monitoring/test_health_truth.py`

Recommended Builder: **Sonnet + High Effort**.

---

## B2 — Schedule / Window Truth

**Close:** MON-002, MON-012.

Current hardcoded cadence has already drifted:
- health table says Tennis Scan 4x/day;
- active workflow schedules 8x/day.

Some jobs are:
- cron sets;
- fixed interval;
- windowed interval;
- event-driven with fallback;
- manual.

A universal `age > interval + grace` rule is invalid.

### Target machine-readable expectation
Conceptually:

```text
JobExpectation:
  job
  execution_planes
  trigger_type
  cron_set / interval
  active_window rule
  fallback schedule
  grace
```

Outside an active window:
- status should be `inactive/not_expected`;
- not `stale`.

For event-driven jobs:
- absence of an event must not imply failure;
- fallback schedule health is evaluated separately.

Preferred architecture:
one job-expectation registry plus deterministic parity tests against active workflows.

Required tests:
- exact active Tennis cron set;
- off-window BL2 live not stale;
- event-driven consumer not false-stale;
- fallback lateness detectable;
- `.disabled` workflow ignored.

Architecture pass: **Opus + Medium**. Implementation: **Sonnet + High**.

---

## B3 — Recovery Truth

Current Cloud Healer and Worker healer map several jobs to workflow filenames that are not active on main because only `.disabled` variants exist.

### Target
Recovery registry explicitly knows:
- target exists;
- target active;
- supported trigger;
- cooldown;
- idempotency/safety;
- execution plane.

Unavailable recovery target:
- emit `RECOVERY_UNAVAILABLE`;
- never pretend retry happened.

Tests:
- every configured recovery target resolves;
- disabled workflows never dispatched;
- unsupported job visibly unhealable;
- active workflow not double-triggered;
- deterministic actions allowlisted.

Recommended: **Sonnet + High**.

---

## B4 — Release / Publication Provenance

**Close:** REL-004, REL-006 partial, REL-007, MON-008.

Runtime bots move main frequently. Current public build SHA can therefore be runtime-data HEAD rather than validated source release.

### Target payload
```json
{
  "build_info": {
    "source_release_sha": "...",
    "source_ci_run_id": "...",
    "runtime_data_sha": "...",
    "worker_release_sha": "...",
    "generated_at": "...",
    "schema_version": "..."
  }
}
```

Definitions:
- source_release_sha = latest accepted source-changing release;
- runtime_data_sha = commit containing current snapshot data;
- worker_release_sha = actual deployed Worker code provenance.

Tests:
- data-only commit changes runtime SHA, not source release;
- green source release updates source SHA;
- red source commit never becomes release;
- public payload carries both.

Architecture: **Opus + Medium**.

---

# 5. P0-C — Privacy & Persistence

## Objective
Stop public exposure of personal betting/financial state without PWA downtime.

The issue is architectural, not one CSV. Current public/static or repo state includes personal ledgers/DB and public signal snapshots that carry bankroll/open bets.

## C1 — Public / Private contract

**Close:** SEC-001, SEC-002, SEC-008, DATA-013.

Public may contain:
- fixtures;
- canonical signals intended for display;
- public model outputs;
- current market odds;
- public live scores;
- safe system health;
- build provenance.

Public must not contain:
- user/default-user identity;
- bankroll;
- open/settled bets;
- P&L;
- stake history;
- tokens;
- subscriptions.

Private authenticated state contains those user-specific fields.

Required hard test: public payload denylist.

---

## C2 — Authenticated private state

**Close:** SEC-003, SEC-004, SEC-005, SEC-006, SEC-010.

Conceptual endpoints:
```text
GET /public/signals
GET /me/state            user Bearer token
POST /me/pending_bets
POST /me/cancel
```

Critical rules:
- unauthenticated request never receives Philip/private state;
- missing per-user snapshot never falls back to default private state;
- master token never enters browser;
- private response binds explicit owner identity;
- user A cannot select/read B.

Security tests:
- no auth → 401 private;
- A → A only;
- A + user=B → reject;
- missing A state → no default fallback;
- master routing backend-only.

Architecture: **Opus + Medium**.

---

## C3 — PWA dual-channel migration

Zero-downtime sequence:
1. add new public endpoint, keep legacy alive;
2. add authenticated private endpoint;
3. PWA loads public sports data first;
4. with user token, separately load private state;
5. without token, product remains useful but private betting/history UI is unavailable/clearly logged out;
6. verify deployed new path;
7. stop embedding private state in static legacy JSON;
8. remove private static artifacts after compatibility proof.

Do not combine repo-visibility change, Worker migration, ledger migration and history rewrite in one cutover.

Recommended: **Sonnet + High**.

---

## C4 — Private durable ledger persistence

Public Git source repo is not a suitable canonical private ledger.

Two candidate architectures:

### Option A — separate private data repo
Pros:
- lower migration effort;
- Git history/audit familiar.

Cons:
- Git transaction/concurrency complexity remains;
- still not ideal product datastore.

### Option B — Cloudflare D1 / database
Pros:
- transactional;
- natural user isolation;
- cleaner mature architecture.

Cons:
- larger migration;
- backup/DR and reconciliation need design.

CEO target preference: database-backed private ledger. A staged private-repo bridge is acceptable only if clearly temporary.

Builder must create a migration ADR before implementation.

Migration acceptance:
- dual-read/reconciliation window;
- row parity;
- rollback;
- new writes durable privately;
- public repo stops receiving personal rows.

---

## C5 — Public cleanup and history

Only after private store works:
- stop generating/tracking ledgers/DBs/private snapshots/backups in public tree;
- add public artifact allowlist / ignore rules;
- verify Pages payload has no private fields.

History rewrite is a separate high-blast-radius operation. Before it:
- active PRs resolved;
- private backup exists;
- all worktrees/clones accounted for;
- Pages deployment validated;
- exact file patterns enumerated;
- rollback clone;
- explicit user approval.

No casual history rewrite during P0-A.

Privacy/legal text should be updated only after architecture matches reality and any legal claims needed for launch are separately verified.

---

# 6. P0-D — Governance & Data Integrity

## D1 — Autonomous source mutation control

**Close:** GOV-002, GOV-003.

Current AI healer can interpret Claude output, edit `scripts/`, run pytest, commit and push.

Target:
AI healer may:
- diagnose;
- classify;
- recommend patch;
- notify.

AI healer may not:
- write tracked source;
- commit source;
- push source.

Deterministic operational retries may remain only through explicit safe allowlist.

Recommended: **Sonnet + High**.

---

## D2 — Hard policy vs tunable config

**Close:** GOV-005 and protect betting/risk invariants.

Hard policy:
- max 3 active bets;
- max 5% bankroll stake;
- canonical MAX_EV safety bound;
- no autobet;
- no stale/live/terminal Value;
- no client financial authority.

Tunable strategy:
- min edge;
- blend weights;
- provider preference;
- display count;
- optional features.

No user/CLI flag may disable a hard invariant.

---

## D3 — Tennis rollout evidence gates

**Close:** GOV-006, MODEL-008 dependencies.

Current main documents broad LIVE categories under user override with backtest gates disabled.

Target:
every live category/surface points to machine-readable approval evidence:
- gate version;
- sample n;
- ROI;
- Brier/calibration;
- CLV when available;
- approval timestamp;
- approved mode.

No approval → shadow by default.

`--all-live` may only exist as clearly non-production debug/test behavior if retained at all.

Architecture: **Opus + Medium**.

---

## D4 — Historical identity integrity

**Close/investigate:** DATA-002, DATA-003, DATA-004, GOV-008, TEN-012, MEAS-004.

Rules:
- new rows get explicit sport/league/provenance;
- old rows are classified from evidence, not guessed;
- correction manifest records old identity, evidence, new identity, confidence, reason, tool/version;
- UNKNOWN remains UNKNOWN;
- unresolved rows excluded from sport-specific production metrics.

No destructive historical “cleanup” based only on market-name heuristics.

---

## D5 — Source release vs runtime-data architecture

Near-term:
- explicit source release SHA;
- runtime-data SHA;
- bot path allowlists;
- source-path mutation guard;
- runtime commit-rate visibility.

Longer-term:
evaluate moving high-frequency runtime data off source main:
- data branch;
- object/KV store;
- database.

Do not hide this problem by treating every bot commit as a release.

---

# 7. Cross-workstream acceptance matrix

| Risk | P0-A | P0-B | P0-C | P0-D | Wave3D |
|---|---|---|---|---|---|
| Oversized stake | enforce | execution truth | private state | hard policy | semantic monitor |
| Queue data loss | enforce | consumer failure truth | private persistence | mutation governance | durable monitor |
| False health green | — | **fix** | migration safety | recovery governance | trust aggregate |
| Public ledger | — | observe | **fix** | artifact policy | privacy check |
| Wrong Tennis market quote | remain known blocker | telemetry | — | taxonomy | **monitor** |
| All-live override | — | report | — | **fix** | rollout monitor |
| Train/live feature drift | — | telemetry support | — | promotion governance | model trust |
| Runtime main churn | durability interaction | provenance | persistence separation | architecture | release truth |

---

# 8. Builder packet standard

Each Claude task should contain only:
1. mission;
2. invariant IDs;
3. exact relevant System Map section;
4. primary allowed files;
5. forbidden scope;
6. failure semantics;
7. acceptance tests;
8. Git safety;
9. report schema.

Example:

```text
Mission: Close MON-001 and MON-011.

Read:
- Invariant Registry: MON-001, MON-011
- System Map: Monitoring + CI/Release sections

Primary files:
- src/monitoring/health_writer.py
- src/monitoring/aggregate_health.py
- tests/monitoring/*

Do not touch betting semantics, privacy migration, models or PWA.

Acceptance:
...
```

This is the token-saving mechanism: the CEO retains global architecture; Builder gets a bounded contract slice.

---

# 9. Model routing

| Work | Model |
|---|---|
| P0-A final four blockers | **Sonnet + High** |
| B1 execution truth | Sonnet + High |
| B2 schedule architecture | **Opus + Medium**, then Sonnet |
| B3 recovery registry | Sonnet + High |
| B4 release provenance | Opus + Medium |
| C1/C2 privacy boundary | **Opus + Medium** |
| C3 PWA migration | Sonnet + High |
| C4 persistence ADR | Opus + Medium |
| C5 cleanup | Sonnet + High |
| D1 healer governance | Sonnet + High |
| D2/D3 policy architecture | Opus + Medium |
| D4 audit tooling | Sonnet + High |
| D5 runtime/source architecture | Opus + Medium |
| Model feature parity | Opus + Medium |
| Wave3D | Opus + Medium |

Use Opus when choosing the contract is hard. Use Sonnet when contract is already precise.

---

# 10. Builder stop conditions

Stop and report rather than improvise if:
- required change weakens a P0 invariant;
- two sources both claim authority;
- migration risks PWA outage;
- private-state migration risks data loss;
- remote durability cannot be proven;
- historical identity lacks evidence;
- runtime materially differs from repo assumption;
- scope expands into another P0 workstream.

Stop means no merge, no semantic fallback, and explicit evidence report.

---

# 11. Immediate next action

**Do not start P0-B.**

The next Builder action remains:
close A0-1, A0-2, A0-3 and A0-4 on PR #10.

After that:
1. CEO re-audits exact head.
2. If approved, Builder merges.
3. CEO verifies post-merge source, CI, runtime, published data, PWA.
4. Then B1 starts.

---

# 12. Ready-to-copy Claude prompt — P0-A FINAL Closure

**Recommended: Sonnet + High Effort**

```text
SportsBrain — P0-A FINAL Closure Pass on PR #10

ROLE
You are the Builder. ChatGPT/CEO is read-only and will independently audit your work.
DO NOT MERGE unless the CEO/user later explicitly approves it.

CONTEXT
Continue existing PR #10. Do not restart.
The last CEO-reviewed head was f2f7831fdaead6667b6eb53c0021a7bc0377eebf, but fetch current main/PR state first because runtime-data bots move main frequently.

Read the canonical CEO artifacts if available:
- SPORTSBRAIN_SYSTEM_MAP_2026-08-13.md
- SPORTSBRAIN_INVARIANT_REGISTRY_2026-08-13.md

Close ONLY:
QUEUE-001, QUEUE-002, QUEUE-003, QUEUE-004, QUEUE-005,
QUEUE-006, QUEUE-007, QUEUE-008, REL-009, UX-008.

There are four remaining blockers.

A — REMOTE DURABILITY MUST BE PROVEN
Current _durable_push() treats “nothing staged” as proof that the ledger matches canonical remote.
That is insufficient.

Counterexample:
previous run appended + committed locally → push failed → retry sees duplicate → no new staged diff →
local HEAD still has unpushed ledger commit → current code can return success and ACK.

Fix the actual durability invariant.
Before ACK of accepted bet, prove either:
1. this run successfully pushed the relevant mutation, OR
2. origin/main is proven to contain the relevant local commit / exact canonical mutation.

Working-tree cleanliness is NOT durability.

Required tests:
- local ledger commit not contained in origin/main + nothing staged => NO ACK;
- local commit contained in origin/main => ACK allowed;
- remote already contains exact mutation => idempotent ACK;
- push fails all attempts => accepted KV remains;
- ACK fails after remote durability => retry remains idempotent.

B — EXPLICIT ACCEPT / REJECT / RETRY
Current validation collapses transient authoritative-state failure into row=None and then rejected_ids.

Introduce explicit decision semantics:
ACCEPT / REJECT / RETRY.

Permanent REJECT examples:
malformed payload, invalid source, canonical signal mismatch, confirmed >5% stake,
4th active bet, stale/terminal/non-actionable Value signal.

RETRY examples:
authoritative bankroll unavailable, authoritative active-bet state unavailable,
transient Worker/backend/network failure, durable persistence unavailable.

ACK:
ACCEPT => only after durable persistence.
REJECT => after auditable reject reason.
RETRY => NEVER ACK.

Required regression:
authoritative bankroll lookup fails for otherwise valid pending bet =>
item stays pending; not rejected; not deleted.

C — CANCELLATION MUST OBEY SAME DURABLE ACK INVARIANT
Current cancellation may mutate local ledger and delete cancel_requests before canonical remote durability proof.

Preferred:
fetch/classify placement + cancellation intents
→ apply accepted local mutations
→ one durable persistence boundary
→ ACK placements/cancellations after proof.

At minimum cancel ACK must be gated by durable persistence.

Required tests:
- cancel + push success => ACK after push;
- cancel + push failure => request remains;
- already-durable cancel + previous ACK failure => idempotent retry;
- mixed placement + cancellation cannot ACK before durable boundary.

D — PLAYWRIGHT MUST ACTUALLY SUBMIT
The focused browser submit test must fail if it cannot submit.

Provide a valid fixture with all actionability/risk state.
Then assert:
- confirm is enabled;
- click occurs;
- /pending_bets captured exactly once;
- source=value;
- signal_id equals canonical signal;
- odds equal current_odds;
- stake obeys 5%;
- no ReferenceError/JS error.

Remove conditional logic where a disabled confirm or missing request can still pass.

SCOPE
Do not start P0-B, P0-C, P0-D, model work or Wave3D.

GIT SAFETY
- preserve original dirty worktree;
- isolated clean worktree;
- no force push;
- no destructive reset;
- no history rewrite;
- safely sync latest main;
- DO NOT MERGE.

QUALITY
Run focused tests first, then:
- full relevant Python suite;
- actual Playwright frontend suite;
- Node Worker contract tests;
- Ruff regression;
- exact new PR-head CI.

Do not weaken tests or inflate Ruff baseline.

REPORT
Status
Branch + exact head SHA
Current main/runtime-data SHA
Changed files
Blocker A evidence
Blocker B evidence
Blocker C evidence
Blocker D evidence
Focused tests
Full tests
Exact PR-head CI
Remaining risks
Merge recommendation

STOP
Do not merge.
Do not start P0-B.
```

---

# 13. CEO principle

P0 is not about closing many tickets. It is about removing optimistic assumptions from SportsBrain's money, identity, privacy, execution and recovery boundaries.

A statement becomes “done” only when it is provably true where production actually depends on it.
