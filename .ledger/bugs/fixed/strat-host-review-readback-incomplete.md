# Host validation omits final live review content

On strat-creator 73c454b, `.fullsend/shared/validate_result.py:check_jira`
checks clone membership and expected labels, without calling the existing
read-only `publish_review.verify_publication`. A review summary or attachment
can disappear or change after `record-review`, or the opposite numeric verdict
label can be added, without this final check detecting it. The workflow's
earlier check is not a later host readback.

Review comment: 4354198477. Repair: invoke the trusted checkout's shared
publication verifier for each live strategy, retaining clone/provenance checks
and dry-run behavior. Test both approve and revise outcomes after recording,
with read-only emulator access and preserved progress. This is unrelated to
the accepted Org Pulse TLS exception.

[Implementation task](../../tasks/done/strat-pr85-three-review-fixes.md).

## Resolution

Trusted host validation now invokes the shared read-only publication verifier
for each live strategy. Ten regressions fail before repair and pass afterward;
HTTP observation verifies read-only access and progress remains unchanged.
The full suite passes 1,261 tests with six optional skips. Lint/types/diff pass.
Published as signed-off 0707b5b; exact PR #85 head verified and component clean.
No live Jira or model run.
[Evidence and limits](../../notes/strat-pr85-three-review-fixes-20261022.md).
