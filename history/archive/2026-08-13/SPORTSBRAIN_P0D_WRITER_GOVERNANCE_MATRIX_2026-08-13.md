# SportsBrain — P0-D Writer & Governance Matrix

**Date:** 2026-08-13  
**Status:** Pre-implementation architecture; no repository mutation.  
**Primary invariants:** GOV-002, GOV-003, GOV-005, GOV-006, GOV-007, GOV-008, OPS-003, OPS-007, REL-004.

---

# 1. Core problem

SportsBrain does not have one writer.

It has a distributed writer ecosystem:
- Claude/Builder;
- local launchd scripts;
- GitHub Actions workflows;
- Worker-triggered GitHub runs;
- consumer ledger persistence;
- model retrain jobs;
- runtime data bots;
- autonomous AI healer.

Some writers are correctly restricted to runtime-data paths. Others use direct Git commands. One AI path can mutate source.

Therefore P0-D needs a **writer governance model**, not only branch hygiene.

---

# 2. Writer classes

| Writer class | Intended authority | Current risk | Target policy |
|---|---|---|---|
| Claude/Builder | source code, reviewed architecture changes | normal trusted source writer | keep as primary source mutator |
| Human/user | approvals/manual operational action | can trigger debug/override paths | hard safety still cannot be bypassed |
| Local runtime bots | runtime data/cache/health | can race with GHA; main churn | strict path allowlist + provenance |
| GitHub runtime workflows | data, ledger, models, health | many direct push implementations | one governed bot-persistence primitive |
| Consumer | financial ledger mutation | durability/P0-A transaction risk | transactional durable mutation owner |
| Model retrainers | model artifacts + data | model promotion may be implicit | promotion gate + artifact provenance |
| Worker | KV state + workflow dispatch | recovery/action routing | explicit action allowlist |
| Cloud Healer | retry existing workflows | stale/nonexistent mappings | verified recovery registry |
| AI Healer | diagnosis + currently source edits/commit/push | violates Builder-only source governance | diagnosis only; no source mutation |

---

# 3. Existing good control: `_git_safe_push.sh`

The helper already contains important safety concepts:

- process-level lock;
- fetch/rebase/push retries;
- explicit bot-permitted path function;
- fail-closed behavior for source conflicts;
- staged-file safety assertion;
- specialized signals merge;
- source conflict requires human review.

Observed permitted bot path families include:
- `docs/data/*`
- `data/cache/*`
- odds history
- health
- ledgers
- scan results
- selected model artifacts.

This is a useful foundation.

---

# 4. Governance gap: safety primitive is not universal

Many GitHub workflows do **not** call the shared bot safety primitive.

Instead they directly run patterns such as:

```text
git add ...
git commit ...
git fetch origin main
git rebase --strategy-option=theirs origin/main
git push origin main
```

Examples observed in:
- Tennis Closing Odds
- Bundesliga2 Scan
- Bundesliga2 Settlement
- Bundesliga2 Live Push
- Bundesliga2 Retrain
- Bundesliga2 Closing Odds
- Tennis LGBM Retrain
- Consume Pending Bets.

Thus:
- bot path allowlist is not universally enforced;
- conflict policy differs by workflow;
- retry behavior differs;
- durability assumptions differ;
- source-release provenance becomes harder to reason about.

### P0-D rule
All automated Git writers should use one governed persistence primitive or a small number of formally equivalent primitives with tests.

---

# 5. Writer authority model

Recommended conceptual policy:

## SOURCE_WRITER
Allowed:
- tracked source/config/tests/workflows/docs source.

Actors:
- Claude/Builder under explicit scoped task;
- human reviewed process.

Not allowed:
- autonomous AI healer;
- runtime bots;
- data refresh jobs.

## RUNTIME_DATA_WRITER
Allowed:
- explicitly allowlisted runtime/cache/public data paths;
- no source.

Actors:
- local jobs;
- GitHub data workflows.

Required:
- bot path assertion before commit;
- atomic persistence where possible;
- source release SHA retained separately;
- runtime_data SHA reported.

## FINANCIAL_WRITER
Allowed:
- canonical private ledger mutations.

Actor:
- transaction coordinator/consumer/settlement service.

Required:
- durable ACK rules;
- per-user identity;
- transactional/reconciliation semantics;
- never incidental generic bot merge.

## MODEL_ARTIFACT_WRITER
Allowed:
- model binary/calibrator/metadata.

Actor:
- retrain/promotion pipeline.

Required:
- candidate vs production-approved distinction;
- gate result;
- training data/version metadata;
- source release provenance.

## RECOVERY_ACTOR
Allowed:
- deterministic allowlisted retries.

Not allowed:
- source mutation unless converted into Builder-reviewed task.

---

# 6. AI healer governance

Current AI healer can:
1. read health/log;
2. ask Anthropic/Claude for diagnosis;
3. accept a `FIX` block;
4. edit `scripts/...`;
5. run tests;
6. `git add`;
7. `git commit`;
8. push.

The fact that tests pass is not sufficient source governance.

### Target AI healer capabilities

Allowed:
- diagnosis;
- classification;
- log analysis;
- proposed diff/text recommendation;
- notification;
- deterministic operational retry through explicit action map.

Forbidden:
- write tracked source;
- `git add` source;
- `git commit` source;
- `git push` source;
- silently apply LLM-generated patch.

### Desired output
A fixable code issue should become:

```text
SOURCE_FIX_PROPOSED
job: ...
file: ...
diagnosis: ...
suggested_patch: ...
evidence: ...
```

Then Builder handles implementation.

---

# 7. Hard policy vs tunable strategy

Current config mixes:
- safety policy;
- model/strategy thresholds;
- rollout mode;
- user overrides.

That creates a governance risk.

## Hard policy layer
Examples:
- max active bets = 3;
- max final stake = 5% authoritative bankroll;
- canonical MAX_EV bound;
- no autobet;
- no client-authoritative risk state;
- no terminal/live prematch Value;
- no stale current price;
- no queue ACK before durable mutation.

These are not normal tuning knobs.

## Strategy layer
Examples:
- min edge;
- category-specific thresholds;
- model blend weights;
- provider preference;
- display priority;
- experiment/shadow selection.

### Required architecture
Hard policy should have:
- dedicated module or clearly immutable policy structure;
- no production CLI/user override;
- tests that enumerate all override surfaces.

---

# 8. Tennis rollout governance

Current production config explicitly documents a broad user override with backtest gates disabled for most Tennis categories.

Additionally, Tennis Scan exposes an `all_live` manual dispatch input.

That is unacceptable as long-term rollout governance because “live” is a model/product approval state, not merely a runtime preference.

### Target rollout registry

Each live category/surface should have:

```text
category
surface
mode = live | shadow | disabled
approval_id
gate_version
model_version
sample_n
calibration evidence
CLV evidence where applicable
approved_at
expires/review_at
```

Default:
- no valid approval → shadow.

A manual production dispatch must not bypass hard approval.

If `--all-live` remains:
- test/dev only;
- production scheduled workflow cannot use it;
- code asserts non-production environment.

---

# 9. Model writer governance

Retrain workflows currently write model artifacts directly to main.

This is operationally convenient but semantically conflates:
- “a model was retrained”
with
- “a model is approved for production”.

### Target
Retrain produces candidate artifact + metadata.

Promotion occurs only if:
- evaluation gate passes;
- model/schema compatibility passes;
- required evidence exists.

Production predictor loads only approved artifact.

SportsBrain already has parts of this pattern (e.g. gate metadata); P0-D should make it universal.

---

# 10. Backfill / migration governance

SportsBrain has several historical backfill scripts.

A backfill must be treated as a data migration.

Every migration should produce a manifest:

```text
migration_id
tool/source SHA
started_at
completed_at
target data
rows examined
rows changed
rows unresolved
evidence rule
before checksum
after checksum
rollback/export
```

Historical semantic changes require provenance.

Forbidden:
- silently assigning league based on convenience default;
- converting UNKNOWN to a confident identity without evidence;
- modifying historical model provenance while generating a report.

---

# 11. Runtime-data main churn

Frequent data commits on `main` are an architectural fact.

Problems:
- PR base moves continuously;
- mergeability becomes noisy;
- public build SHA looks like a release SHA;
- source CI provenance obscured;
- automation races increase.

### Near-term controls
- publish `source_release_sha`;
- publish `runtime_data_sha`;
- bot path allowlists;
- one persistence primitive;
- source-changing commits always CI-gated;
- runtime commit actor/path telemetry.

### Long-term options
Evaluate:
1. dedicated runtime-data branch;
2. object/KV storage;
3. transactional DB;
4. release artifact channel.

Do not migrate solely to make Git history prettier. Move runtime data only if reliability/privacy/operability improves.

---

# 12. Bot path governance

A canonical automated writer policy should be testable.

Conceptual allowlist:

```text
Runtime public data:
  docs/data/<approved public artifact>
Runtime caches:
  data/cache/<approved>
Health:
  results/health/<approved>
Private financial data:
  NOT public source repo after P0-C
Model artifacts:
  models/<approved candidate/production path>
```

A CI/static test should fail if a bot-capable workflow stages source paths outside its declared class.

---

# 13. Workflow permission governance

Each GitHub workflow should use minimum necessary permissions.

Classes:
- read-only analytics → `contents: read`;
- runtime data writer → scoped `contents: write`;
- recovery dispatcher → `actions: write` only if required;
- private-state writer → eventually private datastore credentials, not public repo write.

Audit should flag:
- write permission without write action;
- source write possible from runtime workflow;
- master/private secret exposed to unneeded jobs.

This belongs partly to P0-C security and partly to P0-D governance.

---

# 14. Recovery governance

Separate two concepts:

## Recovery
Retry known operation safely.

Examples:
- re-run settlement;
- re-fetch provider data;
- re-consume pending queue;
- refresh publication.

## Repair
Change source/config to alter system behavior.

Recovery may be automated if allowlisted and idempotent.

Repair must enter Builder/review flow.

The current AI healer blurs the two.

P0-D should make the boundary explicit in code and naming.

---

# 15. Required tests

## Source writer policy
- AI healer contains no tracked-source write path.
- AI healer contains no source commit/push path.
- runtime bot helper refuses source file.
- every automated Git-writing workflow declares writer class.

## Hard policy
- no production override can set max active >3;
- no production override can disable 5%;
- no production override can bypass canonical signal actionability.

## Tennis rollout
- no approval artifact → shadow;
- approved category → live;
- expired/failed approval → shadow;
- scheduled production cannot invoke all-live bypass.

## Backfill
- migration manifest emitted;
- unresolved identity remains unknown;
- repeated migration idempotent or explicitly guarded.

## Provenance
- runtime data commit does not change source release marker;
- model candidate is not production without gate.

---

# 16. Implementation packets

## D1 — AI healer mutation removal
Primary:
- `scripts/auto_heal_ai.py`
- healer tests.

Model:
**Sonnet + High**.

## D2 — Writer registry / bot primitive
Primary:
- `_git_safe_push.sh` or successor;
- GitHub workflow writer wrappers;
- writer policy tests.

Architecture:
**Opus + Medium**, implementation Sonnet.

## D3 — Hard policy split
Primary:
- config/policy modules;
- CLI override surfaces;
- tests.

Architecture:
**Opus + Medium**.

## D4 — Tennis rollout registry
Primary:
- Tennis config/mode logic;
- scan workflow dispatch;
- approval artifacts/tests.

Architecture:
**Opus + Medium**.

## D5 — Data migration manifest + historical identity
Primary:
- backfill scripts;
- ledger identity tooling;
- report population filters.

Implementation:
**Sonnet + High**.

## D6 — Runtime data architecture ADR
Architecture only first.
**Opus + Medium**.

---

# 17. P0-D closure criteria

P0-D is materially closed when:
- only controlled Builder path can mutate source;
- AI healer is diagnosis/recovery-only;
- automated Git writers obey tested path policy;
- hard betting safety cannot be bypassed by user/CLI config;
- Tennis live rollout requires evidence approval;
- migrations/backfills are auditable;
- source release and runtime data provenance are separate;
- model retraining does not imply model promotion;
- runtime-data churn has an explicit long-term architecture decision.

---

# 18. CEO decision

SportsBrain should not try to eliminate automation.

It should make automation **legible and bounded**.

The mature architecture is:

> **many automated operators, but each with one declared authority, one allowed mutation class, one failure policy and one audit trail.**

That preserves the speed SportsBrain has gained without allowing bots or AI to silently redefine production truth.
