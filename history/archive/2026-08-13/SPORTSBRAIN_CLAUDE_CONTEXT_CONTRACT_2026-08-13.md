# SportsBrain — Claude Context Contract

**Version:** 2026-08-13  
**Purpose:** Minimize Builder context cost while preserving CEO-grade precision.

---

# 1. Context-loading rule

Claude does not need the full SportsBrain conversation.

For a scoped task, load context in this order:
1. this Context Contract;
2. exact invariant IDs from `SPORTSBRAIN_INVARIANT_REGISTRY_2026-08-13.md`;
3. only relevant sections of `SPORTSBRAIN_SYSTEM_MAP_2026-08-13.md`;
4. task-specific source files, direct callers and tests;
5. current main/PR metadata.

Do not recursively rediscover the entire repo unless local evidence reveals an ambiguity.

---

# 2. Permanent governance

- ChatGPT/CEO is read-only.
- Claude/Builder is the project mutator.
- Do not merge without later explicit approval.
- No force push.
- No destructive reset.
- No history rewrite except a dedicated, explicitly approved migration.
- Preserve the original dirty worktree.
- Production PWA must remain usable.
- Failed required gate never goes to production.
- Every source-changing release needs rollback awareness.

---

# 3. Canonical vocabulary

**Source Release SHA** — latest accepted source-changing commit with relevant green CI.

**Runtime/Data HEAD** — newest repo commit, often bot data. Not automatically a release.

**Canonical Value Signal** — registered production signal with stable identity, current market-correct odds, current EV, freshness and valid lifecycle state.

**Manual Bet** — explicit user-selected non-model-approved bet. Never a fallback label for invalid Value.

**Authoritative Risk State** — backend-derived bankroll + active-bet state. Client hints are never authority.

**Durable ACK** — queue item removed only after canonical side effect is durably persisted.

**RETRY** — temporary infrastructure/authority failure; preserve intent.

**REJECT** — permanent validation/business rejection.

---

# 4. Hard CEO invariants

These cannot be tuned away:
- final stake <=5% authoritative current bankroll;
- max 3 active bets;
- no auto-betting;
- no Value→Manual silent downgrade;
- no client-authoritative bankroll/open-bet count;
- no stale scan odds as current executable price;
- no wrong-market odds;
- no Tennis LIVE from elapsed time;
- no live/terminal Tennis prematch Value;
- no queue ACK before durable financial mutation;
- no false `ok` for failed execution;
- no public personal betting/financial state;
- no autonomous AI source write/commit/push;
- no production rollout bypass without evidence gate.

If a task conflicts with one, stop and report.

---

# 5. Task-loading protocol

For `Close MON-001, MON-002`:
1. search only those IDs in registry;
2. read monitoring/release sections of System Map;
3. inspect canonical owner, writer, reader/aggregator, runtime wrapper and tests;
4. form local dependency map;
5. edit after understanding local boundary.

Do not analyze unrelated models, PWA screens or old roadmaps.

---

# 6. Evidence hierarchy

Strongest to weakest:
1. current production source + deployed/runtime evidence;
2. deterministic real-boundary test;
3. exact-head CI;
4. current published data;
5. real-browser behavior;
6. Builder report;
7. comments/docstrings;
8. historical roadmap.

Higher-ranked evidence wins when sources conflict.

---

# 7. Scope contract

Every Builder task must state:
- Required invariant IDs;
- Allowed primary files;
- Adjacent files that may be inspected;
- Forbidden workstreams;
- Acceptance tests;
- failure semantics.

No “while here” cleanup during P0 unless necessary for the invariant.

---

# 8. Test contract

A test must exercise the actual claimed boundary.

Weak:
- Python mirror of JS security code;
- mock says push succeeded without containment logic;
- Playwright passes without clicking submit;
- status test derives both input and expected output from same fake value.

Strong:
- actual Worker/shared JS contract;
- deterministic remote-containment decision;
- Playwright asserts enabled CTA, clicks and captures request;
- aggregator gets contradictory exit/status and must reject false green.

---

# 9. Failure semantics

| Class | Meaning | Queue/action behavior |
|---|---|---|
| PERMANENT_REJECT | cannot be valid as submitted | ACK after auditable reject |
| RETRYABLE | temporary authority/infrastructure failure | KEEP |
| DEGRADED | safe reduced informational quality | continue + expose |
| UNSAFE | hard invariant violated / safety unavailable | block |
| UNKNOWN | authoritative truth unavailable | P0 money action fails closed / retries |

Never convert RETRYABLE to REJECT for convenience.

---

# 10. Reporting contract

Builder final report:

```text
Status
Invariant IDs / scope
Branch
Base/source SHA
Head SHA
Runtime/data main SHA if relevant
Changed files
Canonical owner after change
Failure semantics
Tests + exact counts
CI exact SHA
Published/runtime verification
Known residual risks
Decision needed
CEO recommendation
```

Never claim:
- production verified from local tests;
- public PWA verified from source inspection;
- durable from local file existence;
- current odds from scan-time price.

---

# 11. Model routing

Use **Sonnet + High Effort** for precise scoped implementation/tests.

Use **Opus + Medium Effort** where multiple architectures are legitimate and the main task is choosing the canonical contract.

Do not spend Opus on lint/test repair.

---

# 12. Current sequence

```text
P0-A final closure
→ P0-B Monitoring Truth
→ P0-C Privacy/Persistence
→ P0-D Governance/Data Integrity
→ Model Integrity
→ Wave3D Production Trust
```

Audit/design may happen ahead of sequence. Implementation must not assume unclosed upstream contracts.

---

# 13. Current P0-A note

At this contract version:
- PR #10 is open;
- reviewed head is `f2f7831fdaead6667b6eb53c0021a7bc0377eebf`;
- exact-head CI was green;
- CEO blockers remain:
  - remote durability proof;
  - ACCEPT/REJECT/RETRY;
  - cancellation durability;
  - mandatory actual Playwright submit.

CI green does not close P0-A.

---

# 14. Context budget heuristic

Most scoped fixes should require:
- invariant definitions: <1k tokens;
- relevant System Map slice: ~1–2k;
- task instruction: ~1–2k;
- source inspection: affected cluster only.

Avoid repeatedly loading:
- full 159-invariant registry;
- full System Map;
- whole historical chat;
- unrelated project/user context.

The CEO retains the global model; Builder receives the bounded contract.

---

# 15. Builder pre-edit self-check

Before editing, Builder must answer:
1. Which invariant am I closing?
2. Who owns truth?
3. Which boundary violates it?
4. What is REJECT vs RETRY?
5. Which test fails on current bug?
6. What production monitor should detect recurrence?
7. What is out of scope?
8. What rollback exists?

If unclear, inspect the local dependency cluster first.

---

# 16. Final rule

> **Do not optimize for a green suite. Optimize for the invariant being true in production, with tests proving the real boundary.**
