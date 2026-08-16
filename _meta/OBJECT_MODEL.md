# SportsBrainMemory V1 Object Model — M1 Foundation

M1 installs the typed object engine without migrating canonical V0 truth.

First-class V1 objects: `finding`, `decision`, `incident`, `task`, `workstream`,
`component`, `job`, `provider`, `model`, `dataset`, `test`, `evidence`, `verification`.

Canonical frontmatter is deliberately restricted to top-level scalars and scalar
lists. Nested mappings are forbidden. Existing stable IDs are preserved. M1 is
shadow-only; M2 performs canonical migration after production reconciliation.
