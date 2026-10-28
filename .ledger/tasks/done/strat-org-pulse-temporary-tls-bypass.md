# Temporarily disable Org Pulse certificate verification

## Authorization

After discussing the trust failure and the legacy exporter's behavior, the
user explicitly chose to disable verification for now. Apply that exception
only to the host Org Pulse exporter, document it, test without inference and
publish to the existing strat-creator feature branch/PR #85. No paid run,
production cutover, dashboard credential change or live export replay.

## Acceptance

- [x] Restore the legacy uploader's unverified SSL context for Org Pulse.
- [x] Document the temporary exception and retain the CA follow-up.
- [x] Verify an actual HTTPS upload to a local untrusted certificate endpoint.
- [x] Pass required full repository tests, lint, diff and secret checks.
- [x] Commit/push the scoped change and record the source revision.

## Baseline

Source feat/s1-workflow-hardening at b3c10ec, clean. The prior real smoke
passed strategy/Jira/data publication but all 42 Org Pulse export batches
failed certificate-chain verification. The user's decision overrides the
earlier ledger recommendation against a temporary bypass. Permanent CA trust
remains a separate follow-up; existing failed-run evidence stays unchanged.

## Validation so far

Local real HTTPS regression: 1 failed/7 passed before implementation, failing
with the same certificate verification error. After implementation: 8 passed.
The fixture confirms normal Python verification rejects its self-signed cert
and the exporter successfully sends the expected authenticated bulk payload.
Lint/types and component diff check pass. Full make test running; no model
smoke enabled, no upstream publication or Jira mutation.

## Completed

Signed-off **85e830713e21fbea74518e87e6d62df0355c7234** pushed to
feat/s1-workflow-hardening; GitHub API verifies PR #85's head. Three source
files: exporter, its real local HTTPS regression and README. The exception
uses a request-local SSL context; no global Python trust override is installed.

Full make test: **1,190 passed, six skipped**, 347.11s. Focused: eight passed.
Lint/types, staged and root diff checks pass. All three staged files scanned
against configured credentials: zero findings. The checkout is clean after
publication. Future branch-following GitLab jobs pick up this source without
a consumer change. Existing smoke/archive remains the original failed-ingestion
record; no claim of actual Org Pulse ingestion yet.

Evidence is retained separately at
var/run-data/20261021-org-pulse-temporary-tls-bypass/ with test logs and source
patch. Permanent CA trust remains an open follow-up. No model call, live export
retry, Jira mutation, dashboard credential change or production cutover.
