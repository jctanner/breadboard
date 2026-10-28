# Downstream dashboard cannot authenticate to the data repository

## Evidence

Smoke pipeline 2974269929 triggers dashboard pipeline 2974334519 on main
3970ae4f. Its pages job 17366831288 fails at 2026-10-22 00:18:30Z after
about 13 seconds. The strat-creator clone succeeds; the subsequent data-repo
clone using DATA_REPO_TOKEN receives HTTP Basic Access denied. No dashboard
generation or Pages publication occurs.

The trace establishes rejected Git authentication, but does not distinguish
a missing, expired, invalid or insufficiently scoped token. The upstream
strategy job used its own RESULTS_PUSH_TOKEN and successfully published.
Do not assume these credentials or their scopes are identical.

## Impact and follow-up

The trigger bridge and parent pipeline report success without waiting for
the downstream result. Parent green is not complete end-to-end success.
Inspect dashboard credential presence/scope without revealing values; repair
the consumer credential/configuration and rerun only the downstream build
once authorized. No new model inference is necessary. No credential changes
or dashboard retry were performed during this status check.

Evidence: var/run-data/20261021-real-gitlab-fresh-single-opus46-postreview/
dashboard/job-17366831288-pages/trace.log.

## Diagnosed and fixed on a tested branch: 2026-10-22

An isolated CI diagnostic confirms DATA_REPO_TOKEN is present but Git rejects
it; it is not the known-working pipeline results credential. Both that results
credential and the dashboard's native CI_JOB_TOKEN can read the repository.
The precise expiry/revocation/scope defect in the static token remains unknown,
but the replacement design no longer uses it.

Ready [MR !7](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-dashboard/-/merge_requests/7)
uses CI_JOB_TOKEN via a process-scoped Git header, regenerates served summaries
and makes source branch/API smoke selection explicit. Exact source 6a9085d
passes pipeline 2976991608/job 17385905560 without a secret override. HTML,
run JSON and summary JSON contain RHAISTRAT-3038 and its original review.
Required MR approval is pending (API not_approved); main is unchanged. Keep
this bug open until that fix lands. No need to replace a static secret or
grant variable-admin access for the new approach.

[Recovery evidence](../../tasks/blocked/strat-downstream-publication-recovery.md)
is archived separately from the original failed smoke.

## Historical failure predates PR #85

Read-only GitLab/GitHub audit on 2026-10-22 establishes a pre-existing
credential failure, not an authentication regression from the Workflow PR.
The oldest of the 100 main pipelines fetched is 2891274781, 2026-09-28
22:33:48Z. Its [Pages job 16793120645](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-dashboard/-/jobs/16793120645)
fails with HTTP Basic Access denied and Authentication failed on the
strat-pipeline-data clone. September 29 job 16797493191 and October 15
10:29Z job 17197881186 show the same failure.

GitHub API dates PR #85 to 2026-10-15 12:37:40Z; GitLab pipeline MR !15 was
created October 20 13:05Z and merged October 21. The September failure precedes
both changes. No successful build appears in the fetched 100 main pipelines.
Only representative traces were inspected; do not assert every failure had
the same cause or that September 28 was the first occurrence. Archive:
var/run-data/20261022-strat-dashboard-auth-history/.

The identified-run/JSON-reader changes in MR !7 are a separate compatibility
requirement for the new publication format. They do not explain the old
authentication failure, which prevents dashboard generation altogether.
