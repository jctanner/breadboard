# Optional import context must be reconciled before completion

## Scope and choice

The owner requested a fix for reproduced review 4359883142. Started from clean
`fbbbc6eb10e67472d15bad0a80b850873bce8d95` on feat/s1-workflow-hardening.
Existing partial files have no reliable ownership evidence: they may be old
imported context or local reviewer work. The repair preserves them and stops
for explicit reconciliation. No automatic deletion or quarantine is performed.
No hooks, agents or live-service actions are added.

## Implementation

After all remote inputs are staged, `prepare_import` checks the allowed optional
paths omitted from staging: RFE comments, the prior review summary and the full
prior review. Unmatched local input causes a reconciliation error
before publishing any staged files, replacing a task or writing completion.
The error identifies the affected scoped paths; existing artifacts are intact.

Completion records now use `strat-import-v2`, which attests that this check ran.
Old v1 records are retained and refused instead of permitting the former unsafe
fast path. A completed v2 import still reuses its original inventory without
overwriting a later local review or refinement. This is an import/recovery
quality check, not a tamper-resistant sandbox boundary.

The create Skill explicitly writes an empty-comments placeholder before Path A
when the RFE has no comments. When the completed remote read also found none,
the importer recognizes exactly that two-line placeholder, stages its original
bytes and includes it in completion inventory. Added local text does not qualify
for this exception. This keeps the normal no-comment flow and prior bytes intact.

## Verification

Seven new cases: all three optional paths with pre-existing refined task bytes,
the real managed SIGKILL/remote-attachment-removal case, later local review
preservation, refusal of a pre-fix completion record and the documented empty
comment placeholder. Before repair: five failures/one control pass. After repair,
all 65 selected optional/import/freshness checks pass in 64.86 seconds. In the
managed case, the retry refuses
completion while preserving evidence; explicit fixture reconciliation then
permits normal import, record-create and live freshness verification to pass.

The first guard version passed the original 1,281-test suite, but source inspection
found the create Skill's empty-comment convention. An added compatibility test
failed that intermediate guard before the exact placeholder was supported. That
failure and intermediate suite log are retained; the final source gets a fresh
full-suite run. No model-calling test is involved.

The final required `env -u STRAT_WORKFLOW_SMOKE make test` passes **1,282 tests
with six optional skips**, 434.68 seconds. Ruff, type descriptors and whitespace
checks pass. Three component files changed: importer, new regression module and
Fullsend README. They were subsequently committed and pushed as recorded below.
No model call, live Jira/export mutation or remote reply during verification.

Tested source, complete patch, regression XML/logs, final and intermediate suite
logs, the empty-placeholder compatibility failure and managed recovery diagnostics
are retained at `var/run-data/20261023-strat-import-optional-context-fix/`,
with credential scanning and a SHA256 manifest. Earlier archives remain sealed.

## Publication

At the owner's explicit request, committed with signoff and pushed
`95a5c8febb0b7deb7cda663e5390d8b3a1feabcd`
(Reject unreconciled optional context during import recovery) to
`jctanner-fullsend-ai/strat-creator:feat/s1-workflow-hardening`.
All three staged files match the tested archive; the complete staged credential
scan has zero findings. GitHub API readback confirms the exact PR #85 head,
and the component worktree is clean. The original seventeen-file precommit
archive retains its original base/state metadata unchanged.
No paid smoke, live Jira/export action, remote reply, deployment or merge.
Remote CI/review results for this new head have not been assessed here.

## Limits

An ambiguous leftover intentionally ends the automatic import. Operators must
preserve and reconcile it before retrying. Existing source/freshness rules still
apply; an old prepared run cannot bypass changed-source checks by editing its
receipt. The marker is editable workspace data, not malicious-agent containment.
No model consumption or real GitLab smoke was exercised for this repair.
