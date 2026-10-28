# Fresh single-ticket real GitLab smoke after PR #85 fixes

## Authorization and scope

The user authorized proceeding without waiting days for Stoyan's additional
security review. Run one fresh synthetic RFE with Opus 4.6/high through the
real GitLab runner, Podman, OpenShell and Fullsend. Enable live Jira/data-repo
publication. No automatic model retry, schedule change or production cutover.
Existing RHAIRFE-3739/RHAISTRAT-3027 remain untouched.

## Acceptance

- [x] Verify main, published source, runner and a clear legacy schedule window.
- [x] Create a distinct synthetic RFE outside scheduled discovery scope.
- [x] Pass model-free CI checks, then temporarily qualify and launch once.
- [x] Verify actual Jira review bytes/verdict, data publication and downstream results.
- [x] Verify owned cleanup and remove only temporary fixture qualifications.
- [x] Archive available traces, native outputs, Jira and publication evidence.

## Baseline

GitLab main fe9ca62; source branch feat/s1-workflow-hardening at b3c10ec.
Legacy schedule 4222905 remains active every six hours. Initial read-back:
no running/pending pipelines; shared runner online; next schedule 2026-10-22
04:00Z. This is opt-in integration testing, not a security approval or cutover.

## Pipeline and controller

Created distinct [RHAIRFE-3748](https://redhat.atlassian.net/browse/RHAIRFE-3748)
with the credential-free CSV inventory request. It is New, with no links,
versions, release/quality labels or processing owners. The configured gates
permit New; temporary `tech-reviewed` is a synthetic-fixture qualification,
not a claim that a human quality review occurred.

[Pipeline 2974269929](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/pipelines/2974269929)
on merged main fe9ca62; fullsend-single-rfe job 17366396650. Explicit inputs:
single, RHAIRFE-3748, dry-run=0, publish=1. Source PR head b3c10ec verified.
Input validation has passed; repository tests remain running at 23:50:54Z.
A manual start preflight stopped before any qualification/play because tests
were still running. No model attempt was made by that call.

Controller `/tmp/strat-fresh-smoke.py run`, exec session 83805, waits for both
checks before qualifying this one fixture and playing the job once. It then
monitors terminal model/downstream state, removes only the added release,
quality and run-specific fixture labels, verifies the unchanged schedule,
and archives traces/native ZIPs/Jira/data-repo and downstream metadata.
Persistent intent files prevent uncertain creation/play retries. It never
cancels or repeats a paid model job. Review actual results and archive checks
before calling the smoke successful. Archive root:
var/run-data/20261021-real-gitlab-fresh-single-opus46-postreview/.

## Launched once

Both checks passed by 23:51:05Z. The controller added only `strat-creator-3.8`,
`tech-reviewed` and `strat-live-fresh-csv-20261021` to the RFE, then played
job 17366396650 once at 23:51:10Z. Read-back confirms running at 23:51:12Z.
No production schedule edits or legacy executor change. Completion, live
publication, archive integrity and downstream ingestion are still pending.

## Completed: core passes, downstream delivery incomplete

Job 17366396650 succeeded at 2026-10-22 00:18:11Z after **27m00s**.
Actual agent execution starts 23:59:13Z, with output saved 00:16:49Z, about
17m36s. Source receipt confirms b3c10ec, Opus 4.6/high, concurrency ten,
one validation/model iteration. Both preliminary checks and strict final
business validation pass. No additional inference or retry was launched.

RHAIRFE-3748 links uniquely to RHAISTRAT-3038. Numeric 8/8 approves and the
feasibility reviewer's revise remains in both the review and aggregate data.
One Jira summary comment and one attachment; attachment bytes match the
published review, including the Jira-to-media redirect path. Correct final
rubric-pass label present. No processing/owner labels remain on either ticket.

Data project 81219071 at 5205dca publishes
RHAISTRAT/run-gitlab-job-17366396650/. Fourteen sealed content hashes verify;
fifteen files including the seal are downloaded. Both aggregate summaries
contain this exact run-directory identity and strategy. Temporary RFE labels
are removed, baseline labels preserved, legacy schedule unchanged. Source
and architecture receipts, transcripts/debug/telemetry, runtime logs, Jira
snapshots and all published business files retained. No separate syscall/raw
API capture was configured on the remote runner.

The green parent pipeline is not complete downstream success:

- [Org Pulse CA trust](../../bugs/open/strat-fullsend-org-pulse-ca-trust.md):
  all 42 aggregate export batches (1,031 features) fail TLS chain verification;
  zero ingested. Export remains non-blocking.
- [Dashboard data-repo authentication](../../bugs/open/strat-dashboard-data-repo-auth-smoke.md):
  downstream pipeline 2974334519/pages job 17366831288 fails HTTP Basic
  authentication while cloning the data repository, before generation.
  The trigger bridge does not propagate this failure to the parent.

Native metrics report **3,024,433 combined input/output/cache tokens** and
**$5.25737975**, an estimate rather than an invoice. Reasoning 14,578 is
reported separately and not added again. Metrics requests=0 is not a measured
request count. Archive verification: **62 files plus manifest**, ZIP integrity,
publication hashes, review bytes and configured-credential scan pass (zero
findings). Final verification.json records the qualified outcome. The first
offline summary assertion expected bare run ID; corrected to the documented
run-prefixed directory identity, then all checks pass. No pipeline code fix
was needed for that verification-script mismatch.

Controller 83805 completed normally; no running controller remains. Stoyan's
additional review is still outstanding. No production cutover, credential
change, downstream retry or additional model run was performed.
