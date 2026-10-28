# Bug: Repeated strategy pull appends instead of replacing the local document

## Evidence

The real SME campaign's post-CI `/strategy-pull RHAISTRAT-16` returns success
on strat-creator 6ed858b / Claude 2.1.296, but produces two Business Need,
Strategy and SME sections in the existing local file. The first set is the
pre-CI local revision and the second is the newly pulled CI revision.

Jira itself has one document; pipeline 2102 and its four-role review passed.
The independent post-pull inspection catches the local duplication before
sign-off. Raw stage evidence is retained in
`/tmp/strat-sme-flow-20261019/local-stages/pull-after-ci` and the final campaign
archive will preserve it. Do not rewrite that historical result as passing.

## Cause and impact

`pull_strategy.py` calls `write_frontmatter`, which intentionally preserves
the existing body, then appends the newly fetched body. Pulling into an
existing human workspace therefore retains stale content and adds another
copy. Later refinement or sign-off can select the old first Strategy section
and republish stale content. Fresh CI workspaces do not exercise this case.

## Required fix

Replace the pulled strategy file with one validated latest document. Preserve
the previous file if building the replacement fails. Add model-free regression
coverage for repeated pulls and a changed upstream strategy. Do not alter the
general frontmatter helper's body-preserving contract.

## Local repair and verification

The feature checkout now builds a fresh validated sibling file and replaces
the destination only when writing succeeds. Three new emulator cases fail
before the patch and pass after it; all 26 pull tests pass. Required
`make test-unit` passes 1,092 tests, with five conditional Fullsend dispatch
checks skipped because that CLI was not on the test process PATH.

The repaired Python helper refreshes the actual existing SME workspace against
live Jira without inference: one latest document, full SME section unchanged,
all Jira unchanged. Subsequent real sign-off publishes exactly that latest
generated body and SME section, verified with canonical ADF read-back.

Published with the guide updates as signed-off commit
`1bcb8f4bab6d03619cd8da672c0b7a103e3bdb1f` on
`origin/feat/s1-workflow-hardening`, verified by remote read-back. Required
pre-push `make test` passes 1,092 tests with six conditional skips (the five
dispatch checks plus the opt-in paid Workflow smoke). The checkout is clean.
Paid CI 2102 used 6ed858b, before this repair, and was not rerun. The original
failed post-CI human pull remains a failed historical result.
