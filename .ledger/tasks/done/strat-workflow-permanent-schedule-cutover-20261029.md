# Permanent Workflow executor for the scheduled strategy batch

## Authorization and result

After the passing October 29 scheduled qualification and publication/content
inspection, the owner explicitly requested permanently setting
STRAT_EXECUTOR=fullsend. Scope is the existing batch schedule, as recommended
and accepted in chat. This supersedes the earlier one-evening override and
its already completed rollback.

At **2026-10-30 00:34:23 UTC / October 29, 8:34 PM New York**, GitLab readback
confirmed **STRAT_EXECUTOR=fullsend** on schedule **4222905** in
redhat/rhel-ai/agentic-ci/strat-pipeline. The API performed one schedule-variable
POST, followed by independent GET/configuration readback and invariant checks.
The setting is persistent; no automatic reset is configured or intended.

- Schedule remains active on refs/heads/main, owned by jtanner1.
- Cron remains `0 */6 * * *`, America/New_York: midnight, 6 AM, noon and 6 PM.
- Next occurrence: **October 30, midnight New York / 04:00 UTC**.
- Batch cap remains ten; source remains upstream fullsend-ai/strat-creator main.
- Project executor override remains absent and the CI default remains legacy.
  This change selects Workflow only for this schedule; other/manual pipelines
  retain their existing selection rules and defaults.
- stable-1.x remains the legacy fallback. No source branch, credentials,
  schedule ownership, timing or unrelated settings were changed.

No pipeline was manually launched, no Jira data was mutated, and no host
timer/service was configured. Subsequent runs will be created by GitLab's
existing schedule.

## Evidence and limits

Before/intent/response/after and verification receipts, controller and archiver:
`var/run-data/20261029-strat-workflow-permanent-cutover/`.
Controller: `/tmp/set-strat-workflow-permanent-20261029.py`.
Source script compile check and ledger diff checks pass. Remote confirmation,
not an additional paid batch, validates this settings change.

[Live qualification](strat-evening-workflow-qualification-20261029.md) records
four acquired/completed RFEs, publication and downstream dashboard success,
plus content-review findings. No live input-drift deferral occurred during
that run; its fault cases remain supported by local tests. Permanent cutover
does not change the numeric-only approval policy or claim unanimous strategy
review approval, immutable agent execution or a measured production failure
rate. The generated coexistence wording issue remains separately tracked.

## Rollback if subsequently authorized

Restore legacy by deleting only schedule 4222905's STRAT_EXECUTOR variable,
then GET/configuration-readback verifies inherited legacy. This is a documented
fallback, not an instruction to undo this permanent cutover tonight.
