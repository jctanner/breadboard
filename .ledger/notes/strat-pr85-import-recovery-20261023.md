# Prepared strategy import recovery

## Scope and baseline

The owner approved fixing comments 4355503644 and 4355503650 from automated
review 5623201873 on PR #85. Clean starting commit:
`0707b5baf546b2e0712cb4f9861a8f7705b4815f`, feat/s1-workflow-hardening.
No paid model, live Jira/export action, review reply or deployment is involved.
Org Pulse's accepted certificate exception remains outside this repair.

## Missing full strategy attachment

Prepared `pull_strategy` calls now reject a description with the overflow notice
when its exact named strategy attachment is absent. The error occurs before
artifact writes. Both direct prepared pulls and the import CLI path are covered,
with and without an existing task. An unrelated prior-review attachment does
not stand in for the missing full strategy. Standalone human pull behavior is
preserved.

## Incomplete context import

`import_strategy.py` stages the task, source snapshots, RFE comments, prior review
summary and prior review attachment. Nothing is published until every download
that Jira advertises has completed. Context files are replaced atomically; a new
task is published last. An existing task with matching identity keeps its bytes,
including refinement already performed.

The importer writes `tmp/strat-imports/<KEY>.json` only after publication. The
record identifies the contract, prepared run, strategy, source RFE and downloaded
artifact inventory. Task existence alone no longer proves completion. Without
the record, retry rebuilds supporting inputs, including partial older snapshots
or reviews, while retaining the task body. A per-strategy local lock serializes
duplicate imports without serializing different tickets' network reads.

A valid completion record permits reuse without refreshing later refinement or
review files. Missing recorded files or a different run identity stops the
import. An incomplete import already bound to a composition/review also stops,
so recovery cannot silently replace context consumed by a review. This does not
introduce hooks or another agent call.

## Verification

Before repair: 13 failures and one idempotence control passing. After repair:
**90 passing** import/pull/freshness checks, 75.01 seconds. Cases include failure
at each late download, actual SIGKILL during a context read, interruption after
publishing the task but before completion, repair of partial legacy context,
preservation of refined text and completed-import idempotence. Existing real
inline/oversized Jira round-trip and freshness checks pass.

Full required `env -u STRAT_WORKFLOW_SMOKE make test`: **1,275 passed,
six optional skips**, 417.30 seconds. Ruff, type descriptors and whitespace
checks pass. Four component files changed: importer, pull helper, new regression
module and Fullsend README. They were subsequently committed and pushed as
recorded below. No model call or live-service mutation during verification.

Source, complete patch, before/after XML/logs, the full suite log and actual
process-death/recovered-import diagnostics are retained under
`var/run-data/20261023-strat-pr85-import-recovery-fixes/`, with a credential
scan and SHA256 manifest. Earlier sealed archives remain unchanged.

## Publication

At the owner's explicit request, committed with signoff and pushed
`fbbbc6eb10e67472d15bad0a80b850873bce8d95`
(Stage complete strategy imports and verify retry completion) to
`jctanner-fullsend-ai/strat-creator:feat/s1-workflow-hardening`.
All four staged files exactly match the tested archive, and the complete staged
credential scan has zero findings. GitHub API readback confirms the exact new
PR #85 head, and the component worktree is clean. The original sixteen-file
precommit archive remains sealed with its original base/state metadata.
No paid smoke, live Jira/export action, review reply, deployment or merge.
Remote CI and review results for the new head were not assessed here.

## Limits

Publication uses atomic replacement per file, not a single atomic replacement
of all directories. An interruption may leave complete context files alongside
no completion record; the next import re-fetches supporting data. SIGKILL tests
exercise process restart, not host power loss. Completion records are editable
workspace state and do not contain a malicious agent. Existing prepared-input
freshness and final business verification remain authoritative for later work.
