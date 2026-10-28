# Repair empty-SME-template freshness detection

First real scheduled Workflow batch 2996590097 failed on a literal template
comparison. Own push changed U+2014 in the empty SME template to three ASCII
hyphens, so staff() classified it as real SME input. Exact live baseline and
Jira change-history evidence is archived. Schedule was restored to legacy
with owner approval; do not re-enable or rerun paid jobs implicitly.

Read the strat-creator checkout's local instructions before changing it. PR85
is merged, so prepare a separate repair branch from current upstream main.
Keep the fix narrow: canonicalize recognized empty template variants, preserve
actual SME input and real freshness drift, and test the archived failure case
without inference. Check that failure reporting preserves stale-run evidence
without falsely asserting successful completion; track any distinct change
separately. Follow source-required offline checks before any later push.

Bug: [placeholder formatting](../../bugs/fixed/strat-freshness-empty-sme-placeholder-format.md).
Reproducer and source records:
var/run-data/20261027-first-real-scheduled-workflow-batch/.

## Authorized implementation and PR

Owner requested a bugfix branch in the fork and a PR. Read component CLAUDE.md;
checkout was clean. Fetched fullsend/main b295fe9 and created
`fix/empty-sme-placeholder-freshness` in the jctanner-fullsend-ai fork checkout.
Keep implementation limited to recognizing the known empty placeholder and
regressions protecting genuine SME changes. Full required `make test` will run
with the paid smoke explicitly disabled before a signed-off commit and push.
Then open a focused upstream-main PR. No schedule re-enable or paid retest.

## Regression and implementation

Ten focused cases: before repair, five failed/five controls passed. Includes
the real publisher against an isolated Jira emulator, not just string matching.
`staff()` now strips already-ignored HTML comments before recognizing the known
empty template, with U+2014 and ASCII triple-hyphen spelling treated as equal
only for that placeholder. It returns genuine SME content unchanged. Added
text, an emoji-only addition and meaningful punctuation differences remain
visible to freshness checks; no broad normalize_for_compare is used.

After repair, complete freshness suite: **86 passed**. Focused lint passed.
Only scripts/strat_freshness.py and tests/test_strat_freshness.py changed.
Repository-wide make test and make lint completed, paid smoke disabled.
No code change to failure-reporting recovery or any other pipeline behavior.

## Published fix and PR

Required `env -u STRAT_WORKFLOW_SMOKE make test`: **1,444 passed, six skipped**
in 571.59 seconds. Five optional Fullsend-trigger checks and the explicit
model-calling smoke are skipped. Full make lint and descriptor validation pass.
The saved batch's three staff projections match under the repaired parser;
existing genuine SME input remains nonempty. No historical receipt or baseline
was rewritten and no successful rerun is claimed.

Only two files changed: four additions/two removals in strat_freshness.py and
62 test lines (ten cases). Signed-off **0b69019d46879e5587046ee6aadd543b3b8d8703**
pushed to origin/fix/empty-sme-placeholder-freshness. Component checkout clean.
Candidate and staged credential scans: zero configured-secret findings.

Opened **https://github.com/fullsend-ai/strat-creator/pull/92** against upstream
main. GitHub readback confirms exact tested head, two expected files and
mergeable. DCO, remote lint and Unicode check passed; Python 3.11/3.12 tests
and automated review still running at the recorded check. No merge, schedule
re-enable, live model test or Jira mutation performed.

Validation/publication archive:
var/run-data/20261027-strat-sme-placeholder-bugfix/.
At publication the source bug remained open pending upstream merge and any
separately authorized live qualification; merge verification is below.

## Review check, 2026-10-28T00:11Z

Owner requested status only. Fetched all review, inline and regular comments
with pagination, including pending comments visible to the token: five regular
comments, one submitted review, zero inline comments; no human review yet.
Qodo reports zero bugs, rule violations or requirement gaps. Fullsend risk
assessment is low (1/5); its sole finding is protected-path governance: scripts/
changed without a linked tracking issue, requesting that issue and human
maintainer approval. Review 5675888281 is CHANGES_REQUESTED; no code defect
identified. Finding comment 6456282653. No issue/comment/review resolution or
source change was made in this read-only status check.

All check-run pages were fetched (default first page omits older required
checks after dispatch reruns). Latest DCO, lint, hidden-Unicode, Python 3.11
and Python 3.12 checks all pass; no pending/failing checks remain. GitHub
reports mergeable true / state clean. Do not turn the bot's process finding
into an asserted CI failure or an unverified hard merge restriction.

Review export and paginated CI receipt added to the bugfix archive. PR remains
open/unmerged and scheduled execution stays legacy.

## Merge verified, 2026-10-28T00:40Z

PR92 merged at 00:38:47Z as **b75e8384454f606a2e8b187bf09cbd0dd2ce14e9**.
Current upstream main points there. Both changed Git blobs exactly match
tested 0b69019. Moved the source defect to bugs/fixed; no live rerun is claimed.

Schedule 4222905 still has no executor override and inherits legacy. Owner
jtanner1, batch ten, main ref and six-hour New York cron unchanged. Next due
2026-10-28T04:00Z / midnight New York. No automatic re-enable or run submission
inferred from merge notification. No source checkout changed by the check.

Merge and current-schedule readback receipts appended to the bugfix archive:
merge-verification.json and postmerge-schedule.json. Any next Workflow test
must be freshly host-prepared on merged main; stale failed-run baselines stay
intact. A paid run or schedule switch requires separate owner authorization.
