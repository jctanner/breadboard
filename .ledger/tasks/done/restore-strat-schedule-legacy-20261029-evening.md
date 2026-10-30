# Restore legacy after the October 29 evening Workflow batch

Completed at **2026-10-30 00:02:31 UTC / October 29, 8:02 PM New York**.
Scheduled pipeline 3006130966 and Workflow job 17591617217 both succeeded;
the downstream dashboard pipeline 3006261958 also succeeded. Removed only
the schedule-level STRAT_EXECUTOR variable. Independent readback confirms
no schedule/project executor override, inherited **legacy**, and unchanged
owner, main ref, cron, timezone, source configuration and batch cap ten.
Next occurrence remains midnight New York (2026-10-30 04:00 UTC).

The first preflight stopped before any write because GitLab returned an
additional `raw` metadata field on the variable. A fresh GET confirmed the
same single fullsend override; the corrected metadata-tolerant guard then
allowed one DELETE. No ambiguous write was retried. No pipeline was launched,
no Jira data was changed, and no host automation was added.

Rollback receipts: `var/run-data/20261029-strat-workflow-evening-rollback/`.
Controller: `/tmp/restore-strat-evening-legacy-20261029.py`.

## Original authorized procedure

Owner authorized temporarily setting schedule 4222905 to fullsend now and
explicitly agreed to undo it later tonight after the job completes. No host
automation or automatic rollback is configured.

At 2026-10-29 17:58:54 UTC, the GitLab API confirmed exactly one schedule
variable: `STRAT_EXECUTOR=fullsend`. Project executor override remains absent;
CI default remains legacy. Next occurrence is **October 29, 6 PM EDT**
(22:00 UTC), main, cron `0 */6 * * *`, America/New_York, batch size ten.
Owner jtanner1 and all unrelated schedule/configuration fields are unchanged.

After that run completes:

1. Identify the pipeline created by schedule 4222905 for the 22:00 UTC slot;
   collect its status/results and preserve evidence as usual.
2. GET the schedule and confirm the temporary executor is still fullsend.
3. Delete only `/pipeline_schedules/4222905/variables/STRAT_EXECUTOR` on
   redhat/rhel-ai/agentic-ci/strat-pipeline, using .env.gitlab locally.
4. Independently GET the schedule/configuration and verify there is no executor
   override, effective default is legacy, and owner/cron/ref/other variables
   are unchanged. Retain rollback receipts; do not retry uncertain writes
   without readback.

Do not leave this override into the **midnight New York recurrence**
(2026-10-30 04:00 UTC). If the evening job is still running close to midnight,
verify its pipeline already captured fullsend and restore the schedule before
the next occurrence; do not cancel or change the running job.

Controller used for enablement: /tmp/enable-strat-workflow-evening.py.
Before/intent/response/after, verification and rollback plan:
`var/run-data/20261029-strat-workflow-evening-override/` (seven files plus
verified hash manifest, zero configured credential findings).

No pipeline was manually started by the enablement. Do not add machine timers,
services, Markov schedules or other host automation; owner explicitly rejected
that direction and chose a later explicit GitLab rollback.
