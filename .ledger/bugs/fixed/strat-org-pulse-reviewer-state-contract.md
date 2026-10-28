# Bug: Strategy reviewer states disagree with Org Pulse validation

## Summary

PR 85 source `8b2f1e0` can publish reviewer states `pending` and architecture
`skipped`. `build_features()` passes them unchanged. Checked-out Org Pulse
`718ffa2`, `modules/ai-impact/server/features/validation.js`, accepts only
approve/revise/reject for every reviewer. Null is also invalid.

## Reproduction

Pass an actual `build_features()` payload into `validateFeature()`. An
approve control passes; each pending variant and architecture skipped fail.
This is a direct local contract probe, not a production HTTP test.

## Expected repair

Do not export provisional pending assessments as completed reviews. Define
an honest contract for final architecture skips without inventing approval
or changing the numeric gate. Add producer/consumer contract coverage. Do
not apply the reviewer's null mapping suggestion; the consumer rejects null.

Impact: per-feature ingest rejection and missing telemetry; the uploader logs
warnings and exits zero intentionally. Production deployment is unqualified.

## Local repair: 2026-10-20

Producer excludes provisional pending reviews with a warning and preserves
final architecture skips. The consumer permits skipped only for architecture;
all completed-review fields retain the numeric verdict and specialist dissent.
Matching fixtures, actual producer-to-validator checks and real local HTTP
validation/forwarding pass. Consumer full suite: 6,382 passed, eleven skipped;
lint passes. Source full suite: 1,136 passed, six optional skips; lint passes.

Consumer fix is isolated on `fix/strategy-reviewer-state-contract` in
`checkouts.tmp/rhai-org-pulse-review-contract`, from upstream main 3a564740.
Published strategy source `080700e` and companion Org Pulse `84f08dca`; GitLab
consumer `6f996e2` pins the source. Neither feature is merged/deployed. Older
production consumers still require that update before accepting architecture
skipped.
[Review and evidence](../../notes/strat-creator-pr85-fullsend-review-20261020.md).
