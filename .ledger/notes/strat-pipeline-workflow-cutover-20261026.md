# Strategy pipeline Workflow cutover

## Scope

On 2026-10-26 the owner requested a new strat-pipeline branch replacing all
legacy pipeline execution with the strat-creator Claude Workflow. The owner
confirmed preservation of all four job types, including necessary source-side
interfaces. This authorizes local implementation, not execution or publication.

| Repository | Branch | Base |
| --- | --- | --- |
| jtanner1/strat-pipeline | feat/fullsend-workflow-cutover | 9bbac1e |
| jctanner-fullsend-ai/strat-creator | feat/fullsend-ci-cutover | 95a5c8f |

The S1 hardening branch remains unchanged. Following the owner's correction,
the consumer targets `https://github.com/fullsend-ai/strat-creator.git` on `main`
and registers single, batch and resume harnesses from that same upstream branch.
The Workflow and companion four-job support must merge upstream before the
pipeline cutover is enabled; it no longer follows a personal fork/feature branch.

## Behavior

- `batch-jql`: scheduled default-JQL discovery or manual web/API invocation.
- `batch-config`: source-local config file, baseline filter, size/offset, owned claims.
- `single-rfe`: one explicit RFE with ordinary gates.
- `reprocess-strat`: import the selected pipeline-created STRAT and prior review
  on the host, record create, then perform new refinement/review in the Workflow.

Reprocessing differs from ordinary resume. Only its exact prepared request can
reassess rubric-pass. The helper verifies the acquired RFE/owner, pipeline
provenance and unique open clone. Needs-attention, human sign-off, active/completed
states and ambiguity refuse. No label is deleted to force the work through.
Ordinary resume continues to skip approved strategies. Repeated host preparation
preserves imported artifacts and already recorded progress.

The four original job names remain. Duplicate trial jobs and the legacy
create/refine/review shell orchestration are removed from CI; old utilities
remain available for maintenance. Batch jobs retain the shared queue and
single/reprocess jobs retain immediate execution. Schedule cadence stays six
hours. Direct Vertex, Opus 4.6/high effort, concurrency ten, one iteration,
current architecture context and the existing cleanup/publication checks remain.

Regular consumer jobs explicitly default to live Jira writes/publication.
The reusable launcher retains dry/no-publication defaults for direct use.
For a consumer dry run, both flags must be overridden. Push/MR pipelines run
tests only; web/API model jobs require manual start. Dashboard triggering
requires successful live publication. Invalid selectors fail before model work.

## Validation

- Consumer full suite: 63 pass, 14.05 seconds.
- Source initial CI/input/host selection: 77 pass, 25.46 seconds.
- Source current wrapper/input checks: 85 pass, 13.92 seconds, including forwarding
  all four operations and preserving cleanup/failure results.
- Source full suite: 1,343 pass, six optional skips, 464.49 seconds.
- Ruff, type-descriptor validation, shell syntax and diff checks pass.
- Actual consumer registrations verified against a local committed source
  snapshot: all three harnesses materialize with commit/hash-bound runtime URLs,
  required companions and the new helper. Consumer config remains unchanged.
- GitLab upstream CI lint accepts the actual YAML: valid, no errors/warnings.
  The API call performed configuration validation only.
- Thirty-file archive at `var/run-data/20261026-strat-pipeline-workflow-cutover/`:
  changed source, complete patches including new/deleted files, full-suite logs,
  lint/package receipts and metadata. Hash readback passes; credential findings zero.

Model-calling smoke tests were explicitly disabled. No live Jira change, model
request, real CI run, deployment, remote source publication, or merge occurred.
An initial sandbox-only emulator attempt failed to create a loopback socket;
the authorized local integration run outside the sandbox passed.

## Next validation

Merge the Workflow and required four-job support into fullsend-ai/strat-creator
main. Review the consumer change and run an explicitly authorized real
GitLab/Fullsend smoke on the final revisions before deploying the cutover.
No claim of live qualification is made for the
new config/reprocess interfaces.

## Publication

The owner subsequently authorized commit and push and will create the PR/MR.
Published with signoffs, source first:

- strat-creator `feat/fullsend-ci-cutover`:
  `284389cdd36938714c1819bbf1c68aa4ead7ec98`,
  Support all strategy CI job types in Fullsend (15 files).
- strat-pipeline `feat/fullsend-workflow-cutover`:
  `48f4eebc639ba3862bfa385b6fa7ce55ad20e6ba`,
  Run all strategy jobs through the Fullsend Workflow (six files).

Validated both stages against the exact archived source and deletion inventory.
All blobs match the credential-scanned snapshot. SSH pushes and remote SHA
readback succeeded; both component worktrees are clean. Source branch
feat/s1-workflow-hardening and PR #85 were not updated by this publication.
The sealed archive remains unchanged, including its historical pre-publication
flags. Remote CI outcomes were not assessed in this publication task.

The paid model smoke remains a separate authorized step. No PR/MR, schedule
change, deployment, or merge was performed.

## Post-merge source reference correction

The owner clarified that the consumer prepares for the upstream strat-creator
merge. Updated the bootstrap URL, branch, all three registrations, resource
allowlist, documentation and existing regression assertions to fullsend-ai/main.
Removed the personal-fork allowlist entry. Full consumer suite: 63 pass;
GitLab CI lint: valid, no errors/warnings. Actual consumer registrations also
package against a local main-named source snapshot without model calls.

Committed and pushed signed-off `c51451357c6b833be4d55b0918a2b509f6d8a548`
on the existing consumer branch; authenticated remote readback matches and the
worktree is clean. Four files; credential-pattern checks found nothing. GitLab
push output identifies the owner's MR !18:
https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/18.
The agent did not create or edit the MR. Companion source commit 284389c is
unchanged. No new model run, schedule change, deployment or merge.

## Source integration into PR #85

The owner subsequently chose to include commit 284389c's CI support in #85
instead of a separate follow-up PR. It is now cherry-picked as b8d67c3 on
feat/s1-workflow-hardening, alongside new review repairs and upstream main.
The original companion branch is unchanged. See the
[current PR review assessment](strat-pr85-review-and-merge-20261026.md) for
combined validation and publication status. The consumer continues to target
fullsend-ai/strat-creator main after that merge.
