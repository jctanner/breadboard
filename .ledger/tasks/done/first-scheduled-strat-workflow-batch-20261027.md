# Qualify the first real scheduled Workflow batch

Schedule 4222905 was switched to fullsend at 2026-10-27T21:44:15Z after owner
authorization. Owner is jtanner1; next due 22:00Z / 6:00 PM New York. Cadence
is every six hours and batch size ten. No manual trigger is required.

Find the first pipeline created by this schedule after enablement, rather than
assuming the newest main pipeline is the relevant one. Use the schedule's
pipeline-list API and verify source schedule and actual variables. Confirm
workflow-batch-jql, Opus 4.6/high, source/context receipts and acquired keys.

Check ticket selection/gates, per-ticket fresh/resume outcomes, reviews and
numeric decisions, final business validation, owned lock release, sealed data
publication and dashboard delivery. Preserve specialist dissent. Org Pulse
aggregate schema warnings are already tracked separately; report actual
delivery evidence and any readback limits.

Archive available CI traces/artifacts, native OTel/transcripts/debug/sandbox
logs, Jira before/after or first-observed/after snapshots, published bytes and
downstream artifacts under a dedicated var/run-data directory. State which
captures were not configured and which initial snapshots were unavailable.
Do not reuse the single-smoke controller's hardcoded fixture cleanup; these
are real RFEs. Do not reset Jira, seed fixtures or retry model jobs.

If a blocking runtime issue occurs, report it and assess returning the schedule
override to legacy before a later tick. No automatic cancellation, rollback or
second paid run is pre-authorized by this tracking task.

## Active run

Actual first scheduled pipeline is **2996590097**, created at 22:05:51Z,
source schedule, associated with schedule 4222905. This is a 5m51s dispatch
delay, consistent with earlier 5-7 minute historical dispatches.

Both checks passed. workflow-batch-jql job **17520981396** started at
22:07:39Z. Current consumer is 812cfc7 (CODEOWNERS-only change after smoke);
startup trace fetched tested strat-creator b295fe9, and architecture current
main 2f3ab40 / selected rhoai-3.6-ea.2 content. At 22:12:33Z bootstrap is still
running; no acquisition or actual agent-model line observed yet.

Read-only observer: /tmp/observe-first-scheduled-strat-batch.py. Staging and
archive dirname: 20261027-first-real-scheduled-workflow-batch under /tmp and
var/run-data respectively. It captures discovered RFEs' first-observed Jira
states (not claimed as pristine before snapshots), terminal native/CI/Jira/data
and downstream artifacts. It cannot mutate remote state. No second paid run
or source/settings change was performed. Result remains pending.

Observer started in exec session 39246. First archive copy verified 13 files,
configured-secret scan zero. At 22:13:22Z still bootstrap; no discovered ticket
keys or actual agent-model line yet. Observer polls GETs every 45 seconds,
captures first-observed Jira on discovery and terminal/downstream evidence,
and never launches or retries models. Its deadline is 6.5 hours plus bounded
downstream collection; independent result verification remains necessary.

## Discovery and actual agent start

At 22:15:55Z discovery printed four RFEs: 1535, 3078, 3681, 3787. Actual lock
lines and prepared resume points contain **three**, not four: RHAIRFE-3078
refine (existing RHAISTRAT-2959), RHAIRFE-3681 create, RHAIRFE-3787 create.
First-observed Jira confirms only those three carry this run's processing and
owner labels. RHAIRFE-1535 remains unlocked; linked RHAISTRAT-2405 already has
rubric-pass. Source resume gate accounts for this skip; final run receipt
will confirm the recorded reason. No gate/label was altered by observation.

At 22:16:24Z agent log confirms claude-opus-4-6 / Claude Code 2.1.296; it
launched the Workflow at 22:16:31Z. Initial artifact archive now includes the
four RFE first-observed snapshots plus two preexisting STRAT snapshots.

## Failed result and reproduced cause

Job failed after **30m16s** (22:07:39Z-22:37:55Z); pipeline failed, model
Opus 4.6, one iteration, no paid retry. A freshness mismatch on RHAISTRAT-3075
blocked completion and the failed-result writer. No agent-result.json was
written, final validation rejected it, and host publication/dashboard were
skipped. This is a real partial Workflow failure, not an outside checker-only
false negative. Fullsend's agent process exited zero, but business validation
and the CI job correctly failed.

Offline baseline/live comparison proves only staff changed: the normal empty
SME placeholder uses `---` rather than the template's em dash. Literal template
detection treats that as nonempty human input. Jira's only description edit is
the run's own bot push, confirmed by transcript call at 22:24:50Z and changelog
at 22:24:53Z. Existing text normalization equates the two placeholders, while a
real added SME instruction remains distinct. No human edit caused this failure.
[Bug and fix boundary](../../bugs/fixed/strat-freshness-empty-sme-placeholder-format.md).

RHAISTRAT-3075 and -3076 were created and remain linked. The 3075 refined
description reached Jira; existing 2959 stayed unchanged. Native progress has
create done but zero accepted refine/review entries and no completed push.
All three owned RFE locks were released, confirmed by trace and terminal Jira
snapshots. All real Jira artifacts were preserved; no fixture cleanup applies.

Read-only collector finished at 22:38:36Z with no collection errors. Native
ZIP includes recovery progress/artifacts, transcripts/debug, OTel, sandbox logs
and exit/source/context receipts. No published per-run data directory exists
(404 saved); dashboard was not triggered. Additional Jira changelogs and
offline failure-analysis.json retained. Final archive copy and checksum readback
verified 65 files, configured-secret scan zero; native ZIP integrity passed.

Native metrics: 10,437,221 tokens including cache, 26,838 reasoning tokens
separately reported, $10.56013975 reported cost (not invoice reconciliation).
The schedule still used fullsend at initial diagnosis time. Owner then approved
restoring legacy. At 22:56:10Z the schedule override was removed and GET confirms
legacy inheritance. Next due 2026-10-28T04:00Z / midnight New York. Owner remains
jtanner1; cadence, batch size and other settings unchanged. Rollback archive
verified seven files with zero configured-secret findings. No source change,
model replay or Jira mutation was performed by this investigation.
[Rollback receipt](restore-strat-schedule-legacy-20261027.md).

Qualification is complete with a **failed** result; Workflow is not enabled
for subsequent scheduled runs. The source defect remains open, with an offline
reproducer and a control preserving real SME text. A repair and any future
paid integration run are separate follow-up work.
