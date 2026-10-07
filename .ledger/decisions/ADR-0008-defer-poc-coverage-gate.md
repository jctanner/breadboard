# ADR-0008: Defer coverage thresholds while completing the POC

## Status

Accepted by user direction on 2026-10-05.

## Decision

Accept M3 for POC progression and defer coverage-threshold work so the hooks
switch, strategy harness, integration, and single-runner outcome can proceed.
Continue relevant functional tests and regression checks; this defers the
coverage percentage gate, not testing or correction of known behavior bugs.

The measured full-feature coverage remains approximately 72.73% at
`8f628aec6`, below the repository's 75% floor. Do not report that gate as
passed. Restore the repository's coverage requirements before preparing the
upstream PR, measured across the full proposed change from its actual base.

## Follow-up

Track deferred work in [the coverage task](../tasks/pending/fullsend-entrypoint-patch-coverage.md).
This supersedes the coverage gate for POC milestones only; the other
requirements in ADR-0007 remain in effect.
