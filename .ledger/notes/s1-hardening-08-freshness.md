# S1 hardening 8: freshness before recovering saved work

Completed 2026-10-14 on local `eval/s1-hardening` at
`0e7e752702727076818001d3a29208532b40dbab`. Historical benchmark sources and
outcomes are preserved. No Fullsend entrypoint or deployed service was changed.

## Contract

The host records **strat-freshness-v1** before agent work. Saved completion alone
cannot authorize reuse. `scripts/strat_freshness.py` checks inputs against that
baseline and binds saved phase progress to it.

| Input | Identity checked |
| --- | --- |
| Pipeline | Logical contents of scripts, Skills, agent instructions, workflows, config, hooks and project instructions |
| Host | Instruction manifest from the pinned host clone, checked independently during host validation |
| Architecture | Pinned context contents and inventory, including added, changed or deleted overlays |
| Request | Run identity, selection, mode, dry-run policy, resume points and other declared parameters; bookkeeping timestamps excluded |
| Live RFE | Jira upstream, description, summary, priority, status, versions, components, parent, gate labels and paginated comments |
| Strategy/work | Assigned identity, title/priority, strategy text, staff input, cached RFE files and refinement/push/review provenance |
| Publication | Live description and latest strategy-attachment identity compared with the recorded push |

File modification time alone does not invalidate work. Internal Skill script
aliases and vendored copies are compared by logical contents. Our processing/
owner labels and status/counter/diff bookkeeping can advance. The empty default
SME template is normalized to empty input; recorded title cleanup can explain
our own summary update without accepting arbitrary external title changes.

**Same run:** changed or unverifiable inputs stop reuse and writes. Progress,
artifacts and mutation intent are retained. Helpers do not refresh the baseline,
erase the ledger or regenerate/repost under the old identity. Checks cover
state/reuse/completion, review composition/publication, mutation boundaries and
loaded Skill/Workflow launch hooks. The trusted host compares the downloaded
baseline with its run record and checks downloaded files as data.

**Later job:** review-only continuation requires matching prior refinement/push
provenance, source/context, live RFE inputs, staff context and publication
read-back. The imported strategy must match that push. Changed or legacy
progress selects refinement again. A new job gets its own baseline and parameters;
the previous owner must release its claims before a different host state directory
can reuse the checkout. Same-run lost host receipts still stop preparation.

**Native replay:** S1 launches a fresh Workflow by name and uses application
progress. Its loaded hook refuses `resumeFromRunId` while S1 is active, preventing
native cached returns from bypassing these checks. Native journal restoration
remains unsupported.

Standalone/manual Skills and minimal older authored unit fixtures retain their
existing behavior outside the S1 harness. Current S1 preparation and host
admission require the baseline; actual S1/vendor markers reject legacy prepared
input. This does not retroactively modify older pinned benchmark releases.

## Checks and spend

Final **make test: 990 passed, seven skipped, 262.47 seconds**. Ruff, repository
diff checks and the staged credential-pattern scan pass. The component is clean
and pushed to the authorized local branch.

Local tests cover changed helper/Skill/rubric/workflow files, overlay inventory,
cached RFE and strategy artifacts, parameters, missing baselines, live RFE
description/comments/gates and staff input. Rejection preserves progress and
uncertain intent and prevents the tested external comments. Unchanged inputs
retain refinement marks. Verified live pushes qualify for later-job reuse;
changed source/context/RFEs/publication and legacy progress do not. The actual
host path starts a later job at review, then refuses a subsequent RFE edit.
Repeated preparation checks source changes before vendoring can hide them.

Native controls use Claude Code **2.1.296**, SHA-256
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`:

| Control | Verified outcome | Authored API pairs |
| --- | --- | ---: |
| Unchanged completion | Receipt/state/journal agree; wrong final hash rejected; reporting recovery preserves work | 6 |
| Source added after preparation | Real hook refuses launch before any Workflow worker starts | 2 |
| Replay of a real completed run | Real hook refuses replay; only the original completed Workflow remains | 7 |

All three independently verify again from the finalized archive. The completed
state matches the receipt's actual hash; source refusal reaches the receiving
tool result; the refused replay references the actual saved run ID.

**Provider calls: 0. Inference tokens/spend: 0.** Responses and usage counters
are authored loopback fixtures, not GLM inference. No GLM, Haiku or Opus trial
was needed. No deployed reset or live model/MLflow job was created.

## Earlier failures retained

The first focused suite passed 64 tests and exposed a malformed-progress case;
an explicit JSON-object check restores normal host failure reporting. The first
full suite passed 988 tests with two failures: later-job admission was too broad
when an earlier run's input remained with a new host state directory, and the
bundled review helper needed synchronization. The final revision admits a
different run after verifying ownership is released, retains refusal for
same-run lost receipts/active claims, and synchronizes the bundle. Trusted host
imports stay separate from the sandbox CLI import path.

Three replay fixtures did not reach the hook: invalid run-ID syntax, missing a
named/script selector, and a nonexistent journal. They remain failed fixtures,
not enforcement passes. The corrected control completes a real run first, then
requests its replay by name and actual ID. Tool/journal validation precedes the
hook. Each native case/revision was executed once; no paid scenario was rerun.

## Private evidence

Finalized and independently checksum-verified:

`var/run-data/strat-workflow-hardening/08-freshness/controls/20261014T190730664867Z/`

**17,723 files, 182,139,499 bytes**. The capture includes all **21 authored API
pairs** across passing/failed fixtures, native config/state/journals, hook and
transcript output, focused/full-suite logs, local fixture state, an earlier
source patch and exact published source archive. Its 220 symlinks are retained
as target metadata without following them. Strace was not enabled for these
controls; there was no live job or new deployed-system capture.

Manifest SHA-256:
`4d302b472bbf7d011856c96fad20fbe43b0d9a6cda2589e52cf01f054b657b9e`.

## Limits

Checks observe inputs at boundaries, not in an atomic transaction with human
Jira edits. Cross-host lease/fencing remains the #7 follow-up. Architecture
identity describes the pinned snapshot used for work, not continuous fetching
of a newer remote branch. Declared parameters/repository instructions are
tracked; every external runtime setting or dependency is not attested.

Content accuracy, full batches, Fullsend/OpenShell deployment, other Claude
releases and throughput with the extra hashing/Jira reads remain unqualified.
Numeric scores remain the sole approval gate. Item 9 was subsequently
[rejected as not a bug](../tasks/done/s1-hardening-09-limits.md) on 2026-10-14;
no repair remains pending in the original list.

[Plan](../plans/strat-workflow-s1-hardening.md).
