---
type: architecture
status: active
last_updated: 2026-09-15T00:00:00+02:00
freshness_class: stable
---
# Memory V2 Source Observer and CEO Control Plane

The Source Observer is a manually controllable, read-only observer for
`Philip3006/sportsbrain` and `Philip3006/SportsBrainMemory`. It reads GitHub
through authenticated `gh api` GET requests and records main SHAs, merged/open/
closed pull requests, PR head and merge SHAs, merge times, and available
workflow state.

## Truth boundaries

- Canonical history remains append-only under `events/records/`.
- Observed source changes become `SOURCE_CANDIDATE_EVENT` records under the
  Obsidian vault `_live/SOURCE_CANDIDATES.json` only.
- Candidate records are non-canonical, require explicit CEO promotion, and are
  never inserted into `events/records/` by the observer.
- Builder handoffs are stored as non-canonical operational evidence under
  `_live/BUILDER_HANDOFFS.json` and require an explicit `BUILDER: 1`, `BUILDER:
  2`, or `BUILDER: 3` header.
- Runtime observer output is separate from the existing canonical sync and
  does not change the 90-second LaunchAgent contract.

## Deterministic identity and failure behavior

Candidate identity is the SHA-256 digest of repository, PR number, head SHA,
and merge SHA. Repeated observations update last-seen metadata without adding
duplicates. A moving main creates a visible source-drift record. GitHub
outages, malformed responses, or stale state preserve last-known observations,
mark observer health degraded, and never replace canonical truth with empty
data.

## CEO Control Plane

`_live/CEO_CONTROL_PLANE.md` projects source state, PR #59 detection, pending
candidates, Builder 1/2/3 state, external blockers, source conflicts, frozen
Research SHA, SEALED 2425/2526 state, NO-BET/no-live state, both repository
main SHAs, and separate canonical/observer freshness. It is generated runtime
state and is not canonical history.

Manual commands:

```text
python3 tools/memory.py observe --vault /path/to/vault
python3 tools/memory.py ingest-handoff handoff.txt --vault /path/to/vault
python3 tools/memory.py validate-candidates /path/to/vault/_live/SOURCE_OBSERVER.json
```

Persistent scheduling is intentionally out of scope until separately approved.
