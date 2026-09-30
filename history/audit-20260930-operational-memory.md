---
id: AUD-20260930-OPERATIONAL-MEMORY
type: historical-audit
tier: warm
status: complete
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: historical
canonical: true
source_paths:
  - /Users/philiprassillier/SportsBrain-Memory
  - /Users/philiprassillier/Downloads/SportsBrain-Memory
  - /Users/philiprassillier/sportsbrain
---
# Operational Memory Audit and Migration — 2026-09-30

## Before-state audit

### Location

The authoritative system is the versioned private repository
`/Users/philiprassillier/SportsBrain-Memory`, remote
`Philip3006/SportsBrainMemory`, branch `feat/memory-v2-live-obsidian`. The
Obsidian UI mirror is `/Users/philiprassillier/Downloads/SportsBrain-Memory`;
its tracked content hashes matched the authoritative clone for the inspected
reference files. The mirror contains `.obsidian/`; the canonical Git clone
intentionally does not. No competing vault was created.

### Concrete gaps

- Current views were still anchored to source main
  `6493f14093aa08e457e610c2961da1e77b80bc76` and a 2026-09-13 audit, while
  fresh `origin/main` was `cdcfa2d57266cd3089d2910e6aa9d1a623a8300b`.
- The home/current-state layer did not surface the merged Nations League,
  Worker observability, or current PostHog PR boundary in one place.
- The existing V1/V2 validator checked structured schema but had no dedicated
  human-navigation check for wikilinks, orphan notes, duplicate IDs, or
  stale current references.
- Decisions, evidence, runbooks, and templates existed in fragments but had
  no single operational navigation contract.
- The existing memory modeled Builders 1–3; the newer dispatch policy also
  names Builder 4/5 lanes without a source-backed role registry.
- The requested recent NL negative-result markers were not present in current
  main or fetched branch trees; they could not safely be promoted from prior
  memory claims.

The pre-change canonical schema validator was green, but a direct test run in
the protected canonical directory could not rewrite generated views. The
isolated clone was used for the complete post-change test run.

## After-state architecture

- [[architecture/OPERATIONAL_KNOWLEDGE_BASE]] is the single two-minute
  navigation contract.
- [[_meta/SOURCE_HIERARCHY]] defines precedence and required epistemic labels.
- [[state/records/STATE-20260930-001]] owns current operational state; the
  2026-08 baseline is explicitly superseded, not deleted.
- Domain notes now cover product, operations, Top-5, Nations League, data and
  providers, model/research, governance, and builder ownership.
- [[findings/NEGATIVE_EVIDENCE]] prevents rejected or unsupported work from
  being rebuilt as if it were current.
- [[evidence/PR_EVIDENCE_INDEX]] distinguishes merged main, open PR, exact
  head, and production evidence.
- [[runbooks/INDEX]] provides twelve bounded operational runbooks.
- [[templates/INDEX]] provides eight reusable governed-note templates.
- `tools/validate_operational_memory.py` checks current navigation and
  governance quality without modifying files.

## Reconciliation results

- Fresh source main: `cdcfa2d57266cd3089d2910e6aa9d1a623a8300b`.
- Latest meaningful merged source/configuration change: Workers Logs PR #210,
  `c6a7b7ed0c0824276650f241ec41ca53a27e63b7`.
- PostHog PR #221 remains branch-only at
  `b67fde78e82ce169f9b23f109818ffca0ce0db20`; controlled test ingestion was
  observed previously, but real production traffic is not claimed.
- Nations League shadow/public work is documented as non-actionable; no
  activation or betting authority was inferred.

## Validation report

- Existing Memory validator: `Errors: 0`, `Warnings: 0`.
- Operational validator: `271` Markdown files, `178` IDs, `0` errors,
  `0` warnings, `0` orphans.
- Memory acceptance: all gates passed, including render idempotence,
  strict validator, provenance separation, lifecycle consistency, and scale
  check.
- Unit suite: `60` tests passed.
- `git diff --check`: passed.
- No production/runtime/model behavior, Worker/KV data, secrets, provider
  authority, ledger, scheduler, or deployment was modified.

## Maintenance workflow

1. Fetch current source and record the exact main SHA.
2. Separate meaningful source release from runtime/data HEAD.
3. Verify PR/CI/production evidence before changing current state.
4. Update one canonical owner, preserve history, and mark supersession.
5. Render projections and bounded builder packets.
6. Run `python tools/validate_memory.py`,
   `python tools/validate_operational_memory.py`, the test suite, and
   `python tools/memory.py acceptance`.
7. Review the Memory-only diff and open one narrow PR.
8. Sync the Obsidian mirror only through the existing safe user-level sync.
