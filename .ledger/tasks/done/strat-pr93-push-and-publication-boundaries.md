# PR93 push recovery and publication validation

Owner authorized fixing all four new reports on e9bcdc3 and local Claude
review. Model preference remains claude-opus-5-5. Component checkout clean at
start, branch feat/isolate-stale-batch-tickets.

- Reproduce a gate during push recording; retain unaffected push snapshots
  only after independently verified batch deferrals. Shared/unrelated and
  unverifiable failures remain fatal; numeric approval policy stays unchanged.
- Reject malformed STRAT mapping keys, including deferred pairs, before Jira
  requests; verify returned issue identity before using change evidence.
- Limit published ticket artifacts to verified completed inventory and check
  embedded identities, retaining legitimate report/provenance/summary outputs.
- Retry both changelog GETs with the existing read-only helper. Exhausted or
  malformed history remains fail-closed; no new mutation retries.
- Reproduce with offline/local Jira fault tests, fix, run focused checks/lint,
  obtain read-only Opus 5.5 review, then full make test on final source.
- Retain credential-scanned test/review/source receipts under var/run-data.
  No paid Workflow batch, live Jira write, schedule change, deployment, merge,
  public PR comments or automatic commit/push.

Reports: review 5692606833; discussion_r4408488381, discussion_r4408488385,
discussion_r4408488388. GET snapshot:
/tmp/strat-pr93-review-refresh-20261029T040426Z/.

Reproduction and repair:

- Initial 20 cases: 18 failures/two controls passed. The first artifact cases
  rejected only because an existing receipt checksum was broken, so those were
  corrected to regenerate the agent-written receipt before host validation.
- Isolated e9bcdc3 worktree at /tmp/strat-pr93-e9b-reproduction: expanded
  32-case baseline had 26 failures/six controls pass, including host acceptance
  of renamed task/review/original copies with coherent regenerated receipts.
- Added specific optional-original metadata/review-comment checks and corrected
  SME fixtures to edit the existing section instead of appending a second one.
  Five selected cases all fail on isolated e9bcdc3, as expected. Native raw Jira
  descriptions/comments retain their existing unstructured format.
- Main checkout: **64 focused checks pass**, 113.82 seconds (35 new plus existing
  history checks). Lint/descriptor schema passed. Wrong-RFE/unproven typed
  errors, shared source and local artifact changes remain fatal with unchanged
  saved progress. New first/later race cases complete unaffected review and
  pass strict host validation.

Implementation records only successful push snapshots, independently reconciles
typed claims and late inputs before saving, and removes verified deferrals
from coverage. Exact ASCII mapping validation includes excluded pairs; Jira's
returned identity must match the requested evidence key. Canonical publication
paths come from completed inventory; existing structured/provenance checks are
retained, optional original identity claims checked, derived comments verified.
Both history GETs use the bounded read retry helper. Push-phase SME mismatch
is typed for the same independent reconciliation, with artifact parsing outside
that conversion and unrelated/local-only edits still fatal.

Read-only Opus 5.5 review running under
/tmp/20261029-strat-pr93-push-publication/claude-review/; full make test running
on the same unchanged source with paid Workflow smoke disabled. No commit/push.

First Opus 5.5/high review completed in 416 seconds ($2.3320286 CLI list-price
estimate), source unchanged, confirming the four reported issues resolved.
It found a new raw-original YAML parsing regression and an optional unpinned
STRAT-original slot, plus two weak test assertions. Interrupted the active full
suite (exit two, log retained) for these concrete corrections.

Four corrected reproduction controls all failed before repair: native raw Jira
Markdown with horizontal rules in RFE original/comments/STRAT original, plus a
raw STRAT original added after composition. The fixture now accepts explicit
source_text so preparation cannot overwrite the RFE test content. Catch only
yaml.YAMLError while parsing optional original metadata; structured artifact
parsing remains strict. Bind a present STRAT original into review input
provenance in both artifacts and local modes. An absent slot keeps the prior
snapshot shape; adding/removing/changing a file invalidates composition.

Assertions now name the actual guard. Follow-up focused run: 114 pass/one
fixture failure; the preexisting optional-original metadata test now hits the
stronger provenance check before its intended metadata guard. Production
corrections passed their four controls. Opus 5.5 final verification running;
adjust that negative fixture after review and run the full final suite.

Second Opus verification ($1.2612354, 193.43 seconds) confirmed YAML and snapshot
logic correct, but caught the bundled Fullsend hook copy still using the old
snapshot and confirmed the known fixture-order problem. Synced the bundled
review_composition.py byte-for-byte with scripts/. Reprepared the negative
STRAT-original case with its mismatched metadata already present, so it reaches
the intended metadata identity guard. No broad design change. Four new cases
bring this task's additions to **39**.

Final focused set: **154 passed**, 114.91 seconds, including scope/hook parity
and all composition/history/new cases. Final narrow Opus verification of the
two mechanical fixes is running. Full make test restarted on this final source;
prior interrupted log retained separately. No live Workflow or source commit.

Final narrow Opus review completed ($0.4253556, 54.72 seconds), confirming both
mechanical corrections close its remaining points, with no material defects.
Total three completed review calls: $4.0186196 CLI list-price estimate.

Final lint caught one blank separator in the new import group (ruff I001).
Removed that blank line and lint/schema passed. Interrupted/restarted the full
suite again because freshness fingerprints include source whitespace. Both
interrupted logs are retained separately; neither counts as a passing suite.
This single formatting-only delta is recorded against the final reviewed
source. No other code/test changes followed the final review. Current full
suite then completed on the lint-clean source.

Completed locally: **1,605 passed, six skipped**, 1,184.46 seconds (19m44s),
`env -u STRAT_WORKFLOW_SMOKE make test`, exit zero. Lint and descriptor schema
checks pass. Component and ledger diff checks pass. No implementation or test
changes followed this final passing suite.

Archive: `var/run-data/20261029-strat-pr93-push-publication/`, **108 files plus
hash manifest**, every copied hash verified. Includes all three Opus reviews,
initial/corrected reproductions, isolated e9bcdc3 source/test evidence,
interrupted runs, final passing logs, complete source/diffs and exact post-review
formatting delta. All **34 pending PR source files** and retained evidence
scanned against configured credentials/private-key material, zero findings.
Separate raw API/syscall/Kubernetes/MLflow captures were not generated for this
local task; CLI streams and local test logs are retained.

Nine tracked files modified plus one new 39-case test file, uncommitted on
feat/isolate-stale-batch-tickets at e9bcdc3. No commit/push, public review
comment, merge, paid Workflow batch, live Jira write, deployment or schedule
change. Aggregate bug remains open pending delivery/merge/live qualification.

Owner then authorized commit/push. Reverified all source and archived receipt
hashes against the passing 1,605-test/six-skip snapshot, scanned all 34 PR files
and the ten-file staged patch with zero configured credential findings.
Signed-off **6334546f1a733b3962166c91322cf84d48c80b68** (`fix: isolate push drift
and constrain artifact publication`) pushed normally to
origin/feat/isolate-stale-batch-tickets. GitHub GET readback at 2026-10-29
16:09:43 UTC confirms PR93 main base/exact head, 34 expected files, mergeable
state and clean local checkout. Committed contents match the tested archive
byte-for-byte. DCO/lint/Unicode passed; Python 3.11/3.12 tests and automated
review were running. Publication receipts at
`var/run-data/20261029-strat-pr93-push-publication-delivery/`: **16 files plus
manifest**, every copied hash verified, zero credential findings. No merge,
public review comment, live smoke, Jira write, deployment or schedule change.

GET-only review refresh at 2026-10-29 16:37 UTC: Fullsend review 5701162342
marks all four findings resolved and reports no new code issues. All CI passed;
only the unchanged protected-path approval requirement remains. No new inline
comments; Qodo reports zero bugs. Snapshot:
`/tmp/strat-pr93-review-refresh-20261029T163713Z/`. No further code or remote
changes performed during this status check.

Owner then pointed out GitHub's unresolved-conversation indicator. A separate
GraphQL query found nine unresolved bot threads despite resolved finding
summaries. Verified the old fixes/title-advice disposition and unchanged
bot-only comments, resolved those conversations, and confirmed zero unresolved
threads at 16:47 UTC. Eight previously resolved threads remained untouched;
no review/comment posted, review dismissal or merge. Latest bot review was
already dismissed before this action. Merge remains BLOCKED, with org-level
approval rules present and precise remaining unmet rule unconfirmed. Thread
and rule receipts archived at
`var/run-data/20261029-strat-pr93-thread-resolution/`: 21 files plus verified
hash manifest, zero credential findings. Source remains unchanged and clean.

Owner merged PR93 at 2026-10-29 17:09:11 UTC. GET-only confirmation verifies
the reviewed 6334546 head was merged as e8f3e5b7722eb3c4f689b3da900bbfba2f4dd837,
which is upstream main. Merge receipts archived at
`var/run-data/20261029-strat-pr93-merge/`: five files plus manifest, copied
hashes verified, zero configured credentials. Next recommended step is one
supervised live batch on main; no run or schedule change was triggered.
