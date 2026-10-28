# Reuse the data-repository token for Fullsend's Analyst role

## Goal

Configure the real GitLab pipeline trial to supply its existing
`RESULTS_PUSH_TOKEN` as `FULLSEND_GITLAB_ANALYST_TOKEN`, as requested by the
user, without creating another token or changing the shared strategy code.

## Acceptance criteria

- [x] Fullsend CI explicitly maps the existing credential before setup.
- [x] Missing or whitespace-only values fail before bootstrap.
- [x] Documentation covers dry-run requirements and actual token permissions.
- [x] Offline regression tests pass without credentials or model calls.

## Scope

Consumer branch `feat/fullsend-strategy-workflow` in
`checkouts.tmp/jtanner1/strat-pipeline`, for upstream MR !15. No live GitLab
secret changes, production run, model inference or publication is requested.
Token API scope and access to the pipeline project remain unverified; the
user accepts revisiting this if production requires those operations.

## Completed: 2026-10-20

Published signed-off consumer commit `d27a314` to the existing fork branch for
[MR !15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15).
The first Fullsend `before_script` block disables shell tracing and explicitly
exports the existing results token under the Analyst variable name. It rejects
missing, empty and whitespace-only values before pip/bootstrap/gateway work.
This applies to single/batch jobs and their input check, including dry runs.
The README no longer claims that the results credential stays host-only.

All 74 pipeline tests pass in 14.49 seconds, including five new model-free
shell checks: exact token inheritance with publication on/off, no token in
trace output, and early rejection for three absent/blank forms. Root and
component `git diff --check` pass. The strat-creator source and its pinned
revision remain unchanged. No production/model run, token provisioning or
secret-variable change was performed; token API permissions remain untested.
