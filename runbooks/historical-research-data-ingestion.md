---
id: RUNBOOK-HISTORICAL-RESEARCH-DATA-INGESTION
type: runbook
tier: warm
status: active
last_updated: 2026-09-30T12:46:53+02:00
freshness_class: release-bound
canonical: true
---
# Historical Research-Data Ingestion

**TRIGGER:** A research dataset is missing, stale, or proposed for a new
experiment.

**CHECK:** Canonical source, license/provenance, temporal boundaries, PIT
availability, schema, digest, and clean output path.

**ACTION:** Use the existing canonical loader/source; write only governed
research state and record the digest.

**ABORT CONDITION:** Fixture synthesis, source substitution, look-ahead,
credential exposure, or production artifact mutation.

**ROLLBACK:** Remove only the uncommitted research output in the isolated
workspace; preserve prior datasets and evidence.

**EVIDENCE TO SAVE:** Source URL/commit, loader, row/column checks, digest,
temporal-integrity result, and experiment linkage.

## Related

- [[domains/DATA_AND_PROVIDERS]]
- [[domains/MODEL_RESEARCH]]
- [[domains/NATIONS_LEAGUE]]
- [[datasets/DAT-TENNIS-MEAS]]
- [[decisions/records/DEC-0029]]
