# Enable Workflow for the real strat-pipeline schedule

Owner authorized setting the proposed schedule override after the successful
post-merge single-ticket smoke and readiness review.

## Scope

- Existing upstream GitLab schedule 4222905, main, every six hours in
  America/New_York: set only `STRAT_EXECUTOR=fullsend`.
- Initially preserve owner, active state, cron, ref, batch size ten, upstream main source,
  Opus 4.6 model configuration and project default legacy/stable-1.x fallback.
- Persist before/intent/response/after receipts and verify readback.
- Do not manually trigger a pipeline or retry an uncertain mutation.
- First actual scheduled batch still needs result qualification and archiving.

## Acceptance

- [x] Schedule override read back as fullsend.
- [x] Unrelated settings verified unchanged; no manual pipeline launched.
- [x] Receipts archived and ledger updated with the next scheduled run.

Controller: /tmp/enable-strat-workflow-schedule.py.
Staging receipts: /tmp/20261027-strat-workflow-schedule-enablement/.

## Ownership prerequisite

Initial variable POST returned HTTP 403; GET confirmed no change. Schedule
belongs to @eignatow; authenticated @jtanner1 is project Maintainer (40).
GitLab requires schedule ownership to edit and runs schedules with owner
permissions. Explicitly asked about this identity change rather than silently
altering ownership. Owner approved: **Take ownership as jtanner1 and enable
Workflow**. Scope now includes that transfer; preserve all other settings and
retain the rejected request receipts. No manually triggered run.

## Completed

At 2026-10-27T21:44:15Z the API confirms owner jtanner1 and one schedule
variable: STRAT_EXECUTOR=fullsend. Active state, cron 0 */6 * * *, timezone
America/New_York, refs/heads/main, batch size 10, source main and project
default legacy/stable-1.x are unchanged. Next run due 22:00Z / 6:00 PM New York.
No pipeline was manually submitted or played.

One failed variable POST was followed by the explicitly approved ownership
transfer, then a successful variable POST and independent GET readback. No
uncertain request was blindly retried. Ownership is now jtanner1, so scheduled
pipelines use that account's permissions. API prerequisites are documented at
https://docs.gitlab.com/ci/pipelines/schedules/#edit-a-pipeline-schedule.

Receipts, controller and checksum manifest:
`var/run-data/20261027-strat-workflow-schedule-enablement/`.
Configured GitLab credential scan and copied-file hash verification passed.
No repository executable change, commit, push or extra model run was needed.

Executor rollback: remove schedule-level STRAT_EXECUTOR to restore the legacy
default on future runs. This does not cancel an in-flight run or undo the
separately approved ownership change.

Follow-up: [first scheduled batch failed](first-scheduled-strat-workflow-batch-20261027.md).
Owner subsequently approved restoring legacy; executor override removed and
read back at 22:56:10Z. See [rollback](restore-strat-schedule-legacy-20261027.md).
