# Run one live strategy canary from merged GitLab main

## Goal and authorization

On 2026-10-21 the user authorized one live single-ticket run for the existing
synthetic RHAIRFE-3739 after MR !15 merged. Use main, Opus 4.6/high, direct
Vertex, Jira writes and data-repository publication enabled. One validation
iteration; do not launch another model run automatically after a failure.

## Acceptance criteria

- [x] Verify merged main/source, runner, schedule and existing ticket.
- [x] Run model-free input/repository checks before making the ticket eligible.
- [x] Coordinate with scheduled work and launch only one single-ticket job.
- [x] Assess live Jira strategy/link/review, cleanup and data-repo publication outcome.
- [x] Check the downstream dashboard and available Org Pulse publication evidence.
- [x] Archive available CI/Jira/data-repository evidence under var/run-data.
- [x] Remove only the eligibility/fixture labels this run adds; leave schedule intact.

## Baseline

Merged pipeline main: 38efbce2d944f005306a1515f8ecbb3a353ecbaa. Source pin:
080700e4b1b23eea9f2ffc30a32684f806dd9472. The existing ticket is Approved,
has a passing quality label and no linked issues; release scope is unset.
Legacy schedule 4222905 remains active every six hours. It cannot be paused
with the available account; use an idle interval with the shared strat-batch
resource group and preserve the fixture's baseline labels for cleanup.

Archive: var/run-data/20261021-real-gitlab-strat-single-opus46-live/.
The archive resolves outside the workspace and is written only through
approved escalated commands. Keep credentials out of logs and ledger files.

## Launched

[Pipeline 2972360596](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/pipelines/2972360596)
uses the exact merged main SHA and explicit single/RHAIRFE-3739/live/publish
inputs. Both input checks and all 74 repository tests pass. Qualified only
the synthetic ticket with `strat-creator-3.8` and a run-specific fixture
marker, preserving its existing Approved state and quality labels.

Played [job 17351822419](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/jobs/17351822419)
once at 2026-10-21T14:12:51Z. It initially waits for the runner. No competing
main/scheduled pipeline was active, and next production schedule is 16:00Z.
The same strat-batch resource group coordinates runtime work. Post-run cleanup
removes only the two labels added here; it preserves live strategy results,
user labels and the existing production schedule.

## Active execution and controller

Main model job started at 14:12:51Z; actual Opus 4.6 / Claude Code 2.1.296
agent execution began at 14:20:40Z. Workflow tool launched at 14:20:48Z.
The main agent is polling the background workflow. Credential selection,
host preparation, sandbox bootstrap and pre-agent security checks passed.
The existing workspace-trust warning ignores settings allow entries but has
not stopped execution. No evidence of an execution failure so far.

`/tmp/strat-live-canary.py watch` is running as unified exec session `43061`.
It refreshes status/trace, waits for terminal model/downstream state, removes
only fixture labels, archives native job logs/ZIPs and Jira snapshots, and
downloads this run's canonical files from the data repository at a recorded
commit. Inspect its `watch-finished.json`, `cleanup.json`, publication evidence
and actual results before declaring the canary successful. A 100-minute
controller deadline requires manual reconciliation if exceeded; it never
cancels or retries a model job automatically. No production schedule edits.

## Completed with a failed canary: 2026-10-21

Job 17351822419 failed at 14:40:16Z after **27m25s** total; agent execution
was about **18m37s**, exited zero, one model iteration. The live strategy
RHAISTRAT-3027 is cloned/linked and refined; its review comment and attachment
are on Jira, with scores 8/8 and testability dissent. Its verdict label is
missing. The final host validator correctly fails this missing effect and
skips the post-script; data-repository publication, Org Pulse publication and
the dashboard are therefore untested/skipped, not successful.

Root cause: OpenShell blocks the attachment reconciliation download redirected
to api.media.atlassian.com. The attachment already committed; the verified
host-side download matches the retained review byte for byte. The reviewer
then explicitly substitutes --dry-run and records the local review complete,
despite a live prepared run and pending attachment intent. The main agent's
local receipt reports success; host live-readback rejects the missing label.

Recorded [media egress](../../bugs/fixed/strat-fullsend-jira-attachment-media-egress.md)
and [incorrect live-to-dry-run fallback](../../bugs/fixed/strat-live-review-dry-run-fallback-completes.md)
as separate follow-ups. No code fix, approval-label patch, or additional paid
run was attempted. Existing results-token mapping passed Fullsend startup.

Model-reported cost **$5.64756225**, not an invoice. Combined input/output/cache
operations **3,112,337** tokens; separately reported reasoning 17,484 is not
added again. Metrics requests=0 is not an actual request-count measurement.

Controller 43061 completed and archived all three jobs' traces, the native
80-file/6,138,048-byte ZIP (105 entries including directories), host failure
recovery data with actual strategy/review files, Jira snapshots/comments and
the review attachment. ZIP integrity and attachment-byte checks pass. No data
run directory was published; its absence and repository SHA are recorded.
verification.json and watch-finished.json confirm final failed state.

Host lock release, sandbox/gateway cleanup and removal of only the two RFE
fixture labels are verified. Existing quality/smoke labels and the live STRAT
remain. Production schedule is unchanged, and the RFE is again outside release
scope. CI/source pin/runtime receipts remain in the native archive; no separate
syscall capture was configured on this remote job. Root diff check passes.
