# Reject ambiguous optional context during import recovery

## Scope

The owner approved fixing reproduced review 4359883142 on clean fbbbc6e.
Check missing staged optional inputs before publishing or marking completion.
Preserve task/review bytes and stop for reconciliation where file ownership is
unknown. Keep legitimate reviews created after a completed import. Qualify
completion records so pre-fix records cannot silently bypass the new check.
No model/live-service run, push or architectural redesign is included.

## Acceptance

- [x] Regression covers each optional path and leaves artifacts untouched on refusal.
- [x] Managed SIGKILL/remote-removal reproduction now stops without a completion receipt.
- [x] Explicit fixture reconciliation allows a later normal import to finish.
- [x] Later local review work survives completed-import reuse.
- [x] Pre-fix completion metadata cannot bypass the new optional-input check.
- [x] The create Skill's exact empty-comments placeholder remains compatible and recorded.
- [x] Required full suite, lint, descriptors and whitespace checks pass.
- [x] Evidence archived; reproduced bug and work index updated.

[Confirmed reproduction](../../notes/strat-stale-optional-reproduction-20261023.md).
[Repair and validation](../../notes/strat-import-optional-context-fix-20261023.md).
All 65 focused checks pass. Final full suite: 1,282 pass/six optional skips,
434.68s. Lint, descriptors and whitespace checks pass. Seventeen-file archive
`var/run-data/20261023-strat-import-optional-context-fix/` passes credential
scanning (zero findings) and hash readback. The intermediate suite and discovered
empty-comments compatibility failure are retained as well.
The owner subsequently authorized commit and push. All three tested files were
published as signed-off `95a5c8febb0b7deb7cda663e5390d8b3a1feabcd` to
the existing fork branch `feat/s1-workflow-hardening`. Every staged byte matches
the tested archive; the full staged credential scan has zero findings. GitHub
API confirms this exact PR #85 head, and the component worktree is clean.
No model/live service action, review reply, deployment or merge. Remote CI and
review results for this new head were not assessed in the publication task.
