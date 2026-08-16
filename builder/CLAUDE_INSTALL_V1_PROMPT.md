# Claude Prompt — Install SportsBrainMemory V1

Use Claude Sonnet with high effort.

```text
You are the Builder for TASK-MEM-V1-ACCEPT. Work ONLY in the SportsBrainMemory repository. Do not modify SportsBrain.

A fully built and acceptance-tested SportsBrainMemory V1 package is provided. Your job is installation/verification, not redesign.

1. Confirm the current SportsBrainMemory branch/HEAD and working-tree status. Expected canonical baseline is 67444780f8ed0a1340a935934638a7cbd3dfe83b. If HEAD differs materially or there are user changes that would be overwritten, STOP and report.
2. Create a recoverable local backup or isolated worktree/branch before applying anything. No destructive reset and no force push.
3. Apply the V1 package exactly, preserving package paths and generated/canonical distinctions.
4. Run the package acceptance gate exactly as documented: compileall, full unit/acceptance tests, strict validator, generated-view rebuild+drift check, context previews, scale test, and package fingerprint check.
5. Inspect the diff for accidental secrets, deletion of historical knowledge, or SportsBrain product files.
6. Report: status; branch/head; changed files; exact test counts; validator errors/warnings; fingerprint; rollback location; unresolved risks.
7. STOP. Do not merge or start P0-B.
```
