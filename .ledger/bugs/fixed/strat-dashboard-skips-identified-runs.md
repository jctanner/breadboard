# Bug: Dashboard ignores identified Workflow publication directories

## Summary

PR 85 source `8b2f1e0` publishes stable `RHAISTRAT/run-<run_id>` directories
with `strat-publication-v1` manifests. The summary extractor supports that
contract; `scripts/generate-dashboard.py:605` still accepts only timestamp
directories. The GitLab dashboard calls this generator.

## Reproduction

Pass real `organize_identified_run()` output to `scan_all_runs()`: empty list.
Copy identical content to `20261020-150000`: the dashboard includes it.

## Expected repair

Share run discovery between extractor/dashboard, retain validation of the
manifest and recorded time, and sort chronologically across both layouts.
Keep stable identities and the protection against an old reconciliation
rolling `current` back over a newer run.

Impact: missing dashboard history despite successful processing/publication.

## Local repair: 2026-10-20

Dashboard and extractor now share `discover_runs()`, preserving both layouts,
manifest identity checks, current-pointer semantics and chronological ordering.
Explicit time offsets normalize to UTC. Actual publisher-to-reader, mixed
history/max-run/dry-run and invalid-metadata tests pass. Full source suite:
1,136 passed, six optional skips; lint passes. Published as source `080700e`,
pinned by GitLab consumer `6f996e2`. External dashboard deployment/merge remains
separate from publication of the feature branch.
[Review and evidence](../../notes/strat-creator-pr85-fullsend-review-20261020.md).
