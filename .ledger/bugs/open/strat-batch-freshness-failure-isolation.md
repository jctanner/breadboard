# One changed RFE blocks the entire Workflow batch

## Evidence

Real GitLab pipeline 2996960969 / job 17523658071, upstream strat-creator
b75e838, Opus 4.6, one iteration. Six RFEs acquired. All six strategies were
refined and pushed by 2026-10-28T01:15:58Z. RHAIRFE-3785's description changed
at 01:20:31Z; Jira attributes changelog 94274070 to Ana Biazetti's account.
Account attribution does not establish manual human activity.

scripts/strat_freshness.py::verify checks all baseline RFEs. At 01:21:04Z,
review composition for RHAISTRAT-2959 was rejected because RHAIRFE-3785 changed,
although 2959 belongs to unchanged RHAIRFE-3078. All six review completions
were blocked; accepted review progress remained empty. Result finalization
also failed the freshness check. The completion hook then rejected three
StructuredOutput calls because no completion checkpoint existed. This was a
cascade from input drift, not evidence of a separate malformed-schema defect.
The job ended at 01:37:41Z, about 16 minutes after the first rejection.

## Impact

A valid stale-input refusal for one ticket prevents five unchanged tickets
from completing. Partial Jira work is retained, but the batch has no normal
failed-result receipt, host publication is skipped, and remaining agent work
continues after a definitive rejection. All six locks were released correctly.

## Follow-up

Owner policy and implementation decision pending. Consider isolating changed
tickets from unchanged work and/or stopping remaining work promptly, with an
explicit failure receipt that cannot authorize stale publication. Preserve
freshness protection: do not silently refresh a baseline, ignore real edits,
or approve the changed ticket using its old inputs. No source patch or paid
rerun authorized as part of this diagnosis.

Evidence: var/run-data/20261028-real-gitlab-workflow-batch-retest/verification.json
and the native ZIP, Workflow journal, transcripts, Jira snapshots/changelog.

Related: [live batch qualification](../../tasks/done/strat-placeholder-repair-live-batch-20261028.md).

## Authorized repair

Owner subsequently requested a new feature branch and PR. Implementation and
verification are tracked in [batch freshness isolation](../../tasks/done/strat-batch-freshness-isolation.md),
on feat/isolate-stale-batch-tickets from main b75e838. Per-ticket deferral,
independent host verification, filtered publication, diagnostic failure receipts
and successful-partial recovery snapshots are implemented. Full local suite:
1,463 passed/six skipped; lint/type/diff and credential checks pass. Signed-off
6ad16b5 is proposed in [PR #93](https://github.com/fullsend-ai/strat-creator/pull/93),
which is open and mergeable. Repair remains pending merge and live qualification.
No paid rerun or schedule switch was performed.

PR93 review follow-up is pushed as signed-off 13a4f71. Boundary races and
creation/skip accounting are reproduced/fixed; reverted inputs need host-pinned
external history proof, with unprovable cases still refused. Forty follow-up
tests; full 1,503 passed/six skips and Python 3.11/3.12 CI green. Source remains
pending merge/live qualification. [Repair details](../../tasks/done/strat-pr93-review-followup.md).

## Automated review refresh, 2026-10-28 15:42 UTC

Read-only refresh confirms PR93 is open at 13a4f71. Fullsend's latest review
5684626830 requests changes and has two runtime concerns requiring reproduction:

- [High: agent-writable STRAT baselines](https://github.com/fullsend-ai/strat-creator/pull/93#discussion_r4402069815).
  Changing progress targets' human snapshots (or pushed publication snapshots)
  could manufacture a mismatch against unchanged Jira. Computed deferrals then
  avoid history proof and could exclude all work from host completion checks.
- [Medium: late human-gate labels](https://github.com/fullsend-ai/strat-creator/pull/93#discussion_r4402069824).
  Sign-off/needs-attention between push and label write raises plain ValueError
  in check_owner/check_human_gates before verify_progress can raise StaleTicket.
  The existing handler may still abort later unaffected pushes in that case.

Source inspection supports investigating both paths, but no reproducer has been
run yet. Neither was identified in the independent local Claude review. This
refresh does not establish an observed exploit or a new live-run failure.
Qodo reports zero bugs and six earlier findings resolved; Python 3.11/3.12,
lint, Unicode and DCO pass. Existing protected-path approval reminder remains
a separate process concern. No source edit or public comment performed.
All paginated review/comment JSON plus current checks/head are retained at
/tmp/strat-pr93-review-refresh-20261028T154244Z/ (GET requests only).

## Local repair and independent verification follow-up

Owner authorized fixing both concerns and an independent Claude check, then
specified claude-opus-5-5. Both automated findings reproduced. The first fix
requires independent host proof for STRAT exclusions and preserves ownership
checks before typed gate handling. Opus verified those paths, but found old
gated-clone evidence injection, pipeline-authored SME history and late review
recovery gates. All five additional emulator cases reproduced and are repaired
locally. Host clone gate/status/inventory anchors, managed SME preservation and
verified recovery deferrals close the concrete cases. Full first-source check
passed 1,521/six skips; final-source full check and Opus verification are pending.
No commit/push, merge, live Workflow smoke or schedule change yet.
[Repair task](../../tasks/done/strat-pr93-host-proof-and-human-gate.md).

Final local repair includes the independently reproduced SME equivalence and
encoded-payload cases: managed normal/stub publication compares the exact ADF
against actual live SME content before any mutation. Full final suite **1,536
passed/six skipped**; 33 added cases, lint/type/schema/diff checks pass. Final
Opus 5.5 verification confirms the remaining correction with no concrete defects.
Source remains uncommitted at parent 13a4f71; this bug stays open pending delivery,
merge and live qualification. Evidence archive:
var/run-data/20261028-strat-pr93-host-proof/ (96 files plus verified manifest;
31 source files and evidence credential scan zero). No live smoke or schedule
change. Actor attribution, journal/CAS assumptions and separately tracked
parser/layout issues remain explicit limitations.

Owner-authorized publication complete: signed-off **17a684f** pushed to existing
PR93; exact upstream head and clean component checkout verified. All committed
source matches the tested archive, credentials scan zero. DCO passed, other
GitHub CI/review checks started. Bug remains open pending merge/live qualification;
no schedule switch. [Delivery](../../tasks/done/strat-pr93-host-proof-publication.md).

## Review refresh at 2026-10-29 01:01 UTC

GET-only refresh confirms open PR93 at 17a684f. Fullsend review 5690011195
(2026-10-28 21:36 UTC) marks the prior fail-open and late-push findings resolved,
and requests changes for two new medium batch-isolation cases:

- [Gate before first create record](https://github.com/fullsend-ai/strat-creator/pull/93#discussion_r4406334441):
  freshness.targets is empty, so load_state cannot classify a newly gated STRAT.
  record raises HumanGateChanged before save_progress, losing unaffected create
  coverage; workflow reconciliation repeats the failure.
- [Typed drift converted to CLI exit](https://github.com/fullsend-ai/strat-creator/pull/93#discussion_r4406334447):
  cmd_record_review catches StaleTicket/ValueError during review/publication
  verification and die() converts it to SystemExit. prepare-reviews cannot
  reconcile that typed error and stops before processing unchanged tickets.

Code inspection supports investigating both; no reproduction, implementation,
paid review or live mutation performed as part of this status check. Python
3.11/3.12, lint, Unicode, DCO and review workflow all pass; Qodo reports zero
bugs and the six earlier items resolved. Existing protected-path human-approval
reminder remains separate. Complete paginated comments, reviews, checks/head
and delta: /tmp/strat-pr93-review-refresh-20261029T010115Z/.

## Local recorder-boundary repair, 2026-10-29

Both newly reported cases reproduced at 17a684f. Creation now stages candidate
mappings and records each ticket independently, requiring the actual unique
owned RFE and host-pinned change proof before deferring an unbound STRAT.
Review recording preserves typed freshness errors for batch reconciliation.
Unproven drift, wrong ownership/source, shared changes and unrelated verifier
failures remain fatal. Numeric scores remain the sole approval policy.

Read-only Opus 5.5 review found two adjacent cases, also reproduced and repaired:
structured SME drift before first creation recording and an external attention
gate at publication readback. Final Opus verification found no remaining
material defects within the documented evidence/containment limits. Thirty
new tests pass; full final suite **1,566 passed/six skipped**, lint/schema clean.
Archive `var/run-data/20261029-strat-pr93-recorder-boundaries/` verified 89 files
plus manifest, zero configured credentials across source and evidence.
Source is local/uncommitted;
this bug remains open pending delivery, merge and live qualification. No live
Workflow smoke, Jira mutation, schedule change or deployment was performed.

Owner-authorized delivery: signed-off e9bcdc3 pushed to the same feature
branch and verified as PR93's exact head. All 32 PR source files match the
tested/reviewed archive; checkout clean. DCO/lint/Unicode passed, other tests
and review running at 2026-10-29 03:24:55 UTC. Publication receipts retained in
`var/run-data/20261029-strat-pr93-recorder-publication/` (16 files plus manifest,
hashes verified, zero configured credential findings). Bug remains open until
merge and live qualification; no schedule change or paid Workflow smoke.

## Review refresh at 2026-10-29 04:04 UTC

GET-only snapshot confirms PR93 remains open at e9bcdc3. Python 3.11/3.12,
lint, Unicode, DCO and automated-review workflow checks passed. Fullsend's
03:46 UTC review marks both previous recorder findings resolved and requests
changes for four new reports:

- Medium, [push-recording boundary](https://github.com/fullsend-ai/strat-creator/pull/93#pullrequestreview-5692606833):
  a gate during `_mark`'s push snapshot loop can raise before save_progress,
  discarding unaffected push records. Initial code inspection confirms there
  is no per-ticket typed-error handler at this boundary; not reproduced yet.
- Low, [ticket-key validation](https://github.com/fullsend-ai/strat-creator/pull/93#discussion_r4408488381):
  prefix-only validation allows a deliberately crafted query-bearing STRAT
  mapping to alias a real Jira ticket and alter host-evidence lookup identity.
- Low, [artifact allowlisting](https://github.com/fullsend-ai/strat-creator/pull/93#discussion_r4408488385):
  a deliberately renamed copy of a deferred artifact may escape filename-only
  exclusion because its embedded identity/completed inventory is not checked.
- Low, [history retries](https://github.com/fullsend-ai/strat-creator/pull/93#discussion_r4408488388):
  both changelog reads use api_call rather than the existing read retry helper;
  a transient failure disables deferral proof and fails closed.

The middle two are defense-in-depth reports involving deliberately edited
agent artifacts. The protected-path human-approval reminder is unchanged;
Qodo reports zero bugs and six earlier findings resolved. No reproduction,
code edit, paid review, public comment or live mutation performed for this
status check. Complete paginated comment/review snapshot and delta:
`/tmp/strat-pr93-review-refresh-20261029T040426Z/`.

## Four-report local repair, 2026-10-29

Owner authorized fixing all four and local Claude review. All reproduced on
isolated e9bcdc3 (including regenerated unsigned receipts for the artifact
attack). Push recording now preserves successful snapshots, independently
proves typed ticket changes, catches late changes on earlier recorded tickets,
and excludes deferred coverage. Shared/unrelated and unproven errors remain
fatal. Evidence mappings require exact ASCII keys, even for deferred pairs,
and returned Jira identity must match. Both history GETs use read retries.

Publication now allowlists canonical completed-ticket outputs. Existing
task/review/provenance identities stay checked; optional original metadata
claims and derived review comments are validated. Claude caught raw Jira text
being parsed as mandatory YAML and an unbound optional STRAT-original slot;
reproduced and repaired both. Raw Markdown parse failures mean no optional
metadata, while a present STRAT original is content-bound into review inputs.
Synced the bundled hook's snapshot implementation byte-for-byte and verified
normal composition/scope behavior.

Thirty-nine new cases; **154 focused checks passed**, lint/schema clean. Three
Opus 5.5 read-only reviews complete ($4.0186196 CLI estimate), final corrections
have no material defects. One blank import separator was then removed for
ruff; that exact formatting delta is recorded separately. Full suite passed:
**1,605 passed/six skipped**, 19m44s; lint/schema clean. Archive under
`var/run-data/20261029-strat-pr93-push-publication/` verified 108 files plus
manifest; 34-file source/evidence credential scan zero. No commit/push, live
smoke, Jira write, merge or schedule change. This remains open pending
delivery/merge/live qualification.

Owner-authorized delivery: signed-off **6334546** pushed and verified as PR93's
exact head at 2026-10-29 16:09:43 UTC. All 34 committed PR files match the
passing 1,605-test/six-skip archive; checkout clean. DCO/lint/Unicode passed;
Python CI and automated review running. Delivery archive
`var/run-data/20261029-strat-pr93-push-publication-delivery/` verified 16 files
plus manifest, zero configured credential findings. Remains open pending merge
and live qualification; no paid Workflow batch or schedule change.

## Review refresh at 2026-10-29 16:37 UTC

GET-only refresh confirms open PR93 at 6334546. Latest Fullsend review
5701162342 (16:20:10 UTC) reports **no new code findings** and marks all four
previous reports resolved: push recording, exact evidence identities,
completed-inventory publication and history retries. No new inline comments.
Qodo reports zero bugs and six earlier findings resolved. Python 3.11/3.12,
lint, Unicode, DCO and automated-review workflow checks all passed.

The remaining CHANGES_REQUESTED item is the unchanged protected-path
governance requirement: link authorizing work or obtain explicit approval
from an authorized maintainer. No further implementation request in this
review. [Review summary](https://github.com/fullsend-ai/strat-creator/pull/93#issuecomment-6468962783).
Snapshot/delta: `/tmp/strat-pr93-review-refresh-20261029T163713Z/`.
No code change, paid review/run or remote mutation for this status check.

## GitHub conversation flags reconciled, 2026-10-29

Owner reported GitHub still showed an unresolved comment. The preceding
refresh checked review summaries, not GitHub's independent review-thread
resolution flags. GraphQL at 16:43 UTC found nine unresolved bot threads,
including already fixed older runtime/error-message issues, the informational
fix/feat title suggestion, and three of the latest fixed low findings. Checked
the source for the two older CLI error-handling items as well; both are fixed.
All selected threads had unchanged bot-only comments and viewerCanResolve.

Resolved those nine addressed conversations; 16:47 UTC readback confirms
**zero unresolved threads**, same 6334546 head, eight previously resolved
threads untouched. No comment/review was posted, no review was dismissed, and
no merge occurred. The latest Fullsend review was already DISMISSED when this
investigation began; its earlier governance reminder should not be described
as an active changes-requested review now.

GitHub still reported merge state BLOCKED. Read-only 16:53 UTC rule inspection
shows organization-level pull-request rules requiring thread resolution,
code-owner review, and extra approval for unattributed changes (ordinary
required approval count zero). No CODEOWNERS file is present in this checkout;
the precise remaining unmet rule was not established. Commit-status API has
no legacy status contexts; its empty-list pending result is not an observed
failed check. Traditional branch-protection API returns 404, while organization
rulesets do apply. Do not claim the PR is unblocked or approved.

Before/after thread states, nine mutation receipts and branch-rule readback:
`var/run-data/20261029-strat-pr93-thread-resolution/`, **21 files plus manifest**,
hashes verified and zero configured credential findings. Future status checks
should inspect both review finding summaries and reviewThreads.isResolved.

## Merged; live qualification pending

Owner merged PR93 at 2026-10-29 17:09:11 UTC. GET confirmation at 17:10 UTC
verifies merged head 6334546 and upstream main/merge commit
**e8f3e5b7722eb3c4f689b3da900bbfba2f4dd837**; main contains the merge. Previous
BLOCKED status is historical and no longer an outstanding merge issue.
Receipt: `var/run-data/20261029-strat-pr93-merge/`, five files plus verified
hash manifest, zero configured credential findings.

Implementation/review delivery is complete. This bug remains open only for
live qualification: recommend one supervised manual Workflow batch on merged
main before switching the schedule back. No paid batch, live Jira mutation,
schedule change or local branch switch was performed in response to the merge
notification. Local checkout remains clean on the feature branch at 6334546.

## Evening qualification scheduled through the existing GitLab schedule

Owner asked to wait until evening, then authorized setting only the existing
schedule to fullsend now and explicitly undoing it after tonight's job.
At 2026-10-29 17:58:54 UTC, readback confirms schedule 4222905 has
STRAT_EXECUTOR=fullsend, next due **6 PM America/New_York / 22:00 UTC**.
Project default remains legacy; owner/ref/cron/batch size/source configuration
and other variables are unchanged. No run was manually launched.

Owner rejected host-level automation; only read-only service-availability
checks had occurred, no timers/services were created. There is no automatic
reset. [Explicit rollback task](../../tasks/done/restore-strat-schedule-legacy-20261029-evening.md)
tracks removing the schedule override after completion and before midnight.
Enablement receipts: `var/run-data/20261029-strat-workflow-evening-override/`,
seven files plus hash manifest, hashes verified, zero credential findings.
Live qualification remains pending the scheduled run.

## Scheduled run succeeded; post-run business checks passed

At 2026-10-30 00:01 UTC, GitLab confirms scheduled pipeline 3006130966
succeeded at 22:54:56 UTC October 29. Workflow job 17591617217 succeeded in
48m04s, using claude-opus-4-6; downstream dashboard pipeline 3006261958 also
succeeded. Five RFEs discovered; four acquired (three refine, one create).
Native completion reports four reviewed strategies, all approved by the numeric
gate, zero errors/deferrals and zero Workflow/release exit statuses. Post-run
checks confirm exact published pair inventory, live Jira clone links and
rubric-pass labels, review comments and downstream publication. No live
input-drift deferral occurred: normal/resume-path qualification passed, but
the specific race remains covered by local fault tests rather than this run.
[Qualification details](../../tasks/done/strat-evening-workflow-qualification-20261029.md).

The temporary schedule override was removed at 00:02:31 UTC; readback verifies
inherited legacy and all unrelated settings unchanged, before the midnight
recurrence. No extra run, Jira mutation or host automation was performed.

Evidence: `var/run-data/20261029-real-gitlab-evening-workflow-batch/`, with native
ZIP, published artifacts, Jira snapshots, dashboard logs and independent
`verification.json`; rollback receipts verified ten files plus manifest,
configured credential scan zero. Source receipt identifies upstream main
987a2005, Fullsend 0.47.1, Opus 4.6/high, concurrency ten, one iteration.

## Owner-authorized permanent scheduled cutover

After inspecting the passing scheduled run and its published content, the
owner authorized permanent Workflow execution on the existing batch schedule.
Readback at **2026-10-30 00:34:23 UTC** confirms STRAT_EXECUTOR=fullsend on
4222905; six-hour New York cadence, source main, owner and cap ten unchanged.
The earlier temporary override/rollback is historical. Project/manual defaults
remain legacy and no automatic rollback applies. This rollout decision accepts
the stated evidence limits; it does not mean a live drift race occurred.
[Cutover receipt](../../tasks/done/strat-workflow-permanent-schedule-cutover-20261029.md).
