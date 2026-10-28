# Bug: Fresh-ticket Fullsend dry runs query synthetic strategies in Jira

## Summary

PR 85 source `8b2f1e0` prepares dry runs with live freshness. New local tasks
use `STRAT-*` and `jira_key=null`, but freshness recording reads their human
fields from Jira unconditionally. `record-create` fails with HTTP 404 before
saving progress. Push recording and verification have equivalent readbacks.

## Reproduction

Prepare a single eligible fresh RFE with `STRAT_DRY_RUN=1`, create its local
`STRAT-7001` task as instructed, then run `strat_pipeline_state.py record-create`.
Isolated Jira returns `Issue Does Not Exist: STRAT-7001`.

## Expected repair

Handle local-only strategy identity explicitly throughout recording and
verification. Retain live RFE freshness and real strategy/SME checks. Test the
host-prepared fresh-ticket dry-run lifecycle through completion, not only
selection and absence of locks.

Impact: blocked the default real-GitLab dry-run smoke.

## Local repair: 2026-10-20

`strategy_jira_key()` distinguishes actual Jira identities from local-only dry
tasks, checks identity/path consistency, and retains live RFE and existing
strategy/SME verification. Fresh host preparation through completion and trusted
validation passes; RFE edits still block reuse, real strategy SME changes still
block dry runs, and invalid identities cannot take the exception. Full source
suite: 1,136 passed, six optional skips; lint passes. Published as source
`080700e`; GitLab consumer `6f996e2` pins it. Actual bootstrap and native locks
pass; real-runner smoke qualification remains outstanding.
[Review and evidence](../../notes/strat-creator-pr85-fullsend-review-20261020.md).
