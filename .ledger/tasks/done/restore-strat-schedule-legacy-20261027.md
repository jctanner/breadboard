# Restore legacy after the first scheduled Workflow batch failed

Owner explicitly selected Restore legacy for scheduled runs after the actual
batch failed on the reproduced placeholder freshness defect.

At 2026-10-27T22:56:10Z, deleted only the STRAT_EXECUTOR schedule variable on
4222905. Independent GET confirms no override and effective default **legacy**.
Owner remains jtanner1; main ref, active state, six-hour New York cron, batch
ten, source configuration and project variables are unchanged. Next due
2026-10-28T04:00Z, midnight America/New_York.

No model job was launched or retried. No real Jira field, strategy, label or
failed-run artifact was changed. All three prior locks had already been
released by the failed job. This executor rollback does not reverse the
separately approved ownership transfer.

Receipts: var/run-data/20261027-strat-workflow-schedule-rollback/.
Before/intent/response/after and verification.json plus audit controller and
README: seven files verified against copied SHA-256 manifest, zero configured
credential findings. Source fix and a paid retest are separate.
