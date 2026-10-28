# One real Workflow batch after the placeholder fix

Owner requested triggering a batch instead of waiting for cron. Authorized
one API-created upstream-main pipeline, Opus 4.6/high, batch limit ten, one
validation iteration, live Jira/publication. Fullsend selection is pipeline
scoped; schedule stays on legacy. No synthetic fixtures or label resets.

The previous failed run and Jira work are preserved. A new host-prepared run
will perform normal discovery and import eligible existing strategies. It
does not reuse the stale failed run's source baseline or native replay ID.
Actual selected count depends on current real eligibility, not the cap of ten.

Preflight confirms no active pipeline and no project/schedule executor override.
Merged main fix b75e838 was verified against tested 0b69019. The launcher
captures the prior candidates' pre-run states but does not force their keys.
Unused selector variables are omitted, avoiding the empty-variable API rules
issue encountered in the first smoke.

Controller: /tmp/launch-strat-placeholder-batch-retest.py.
Staging/archive dirname: 20261028-real-gitlab-workflow-batch-retest.

## Submitted pipeline

Pipeline creation completed before the turn interruption. Reconciled existing
receipt and GET state instead of resubmitting: **2996960969**, created
2026-10-28T00:47:43Z on consumer main 812cfc7, source API. Recorded upstream
strat-creator main b75e838. Both checks passed (input check 16.9s, Python 32.3s).
Only model job is **17523658071 / workflow-batch-jql**, initially manual.
One play was submitted after a fresh legacy-schedule readback.

## Running

Play succeeded once; job 17523658071 started at **00:50:29Z**. Live status at
00:53:51Z confirms running, not waiting/manual, with no recorded failure.
Both model-free checks passed. Schedule before-play readback still has no
override and project default legacy; no cron setting changed.

Read-only observer /tmp/observe-strat-placeholder-batch-retest.py is active in
exec session **70850**. It validates this API pipeline's unique retest marker,
captures normal discovered/acquired keys and actual agent model when logged,
then archives terminal native/Jira/data/downstream evidence. Initial archive
verified 33 files with zero configured-secret findings. Existing before-known
snapshots preserve the prior candidates and linked STRATs before this run.

Still bootstrap at the first observation; actual model/ticket acquisition and
business result are pending. No duplicate creation/play, Jira reset, automatic
model retry or schedule re-enable. Launcher source retained in staging and
will be included in the observer's next archive refresh.

## Live status and external input edit, 01:25Z

Actual startup trace confirms merged source b75e838 and Opus 4.6 / Claude Code
2.1.296. Seven candidates discovered; six acquired, with four refine and two
create resume points. RHAIRFE-1535 remains excluded after its strategy gate.
Selected mappings: 3078->2959, 3681->3075, 3766->3077, 3785->3072,
3787->3076, 3792->3078 (RFE->STRAT).

At 01:25Z Jira shows auto-refined labels on all six strategies and current-run
updates. No new final review comments/attachments or verdict labels are yet
visible; existing attachments on 2959/3072 predate this run and must not count
as current delivery. Job still running at 01:28Z, about 38m total / 28m agent.
Heartbeat does not establish the exact inner phase or absence of a stall.

Read-only first-observed/current RFE field comparison found a description edit
on RHAIRFE-3785, and no protected field differences on the other five. Jira
changelog attributes a description change to an individual Atlassian account
at **01:20:31Z** (9:20 PM New York), after the prepared inputs. This attribution
does not prove manual human interaction; automation can use an individual's
credentials. The earlier unqualified human-edit wording was too strong.
The description drift is established independently of the actor, separate from
the repaired empty-placeholder false positive. It may legitimately trip the
freshness guard on its next check; no new error has appeared in the console
yet. Do not undo the external edit, rewrite the baseline, cancel or resubmit
automatically. Run left active for its normal completion handling/cleanup.

Saved live-progress.json, per-ticket jira-progress snapshots and 3785 changelog
to staging for archive. These observations do not claim batch success.

## Terminal result and qualification

Failed at 01:37:41Z after **47m12s**, about 36m20s of agent runtime. Native
progress verifies all six strategies refined and pushed by 01:15:58Z, passing
the previously broken placeholder checkpoint. Accepted review progress is
empty. At 01:20:31Z, RHAIRFE-3785's actual requirements changed. Changelog
94274070 attributes this to Ana Biazetti's account; manual human interaction
is unverified. The edit followed both the release gate and rubric-pass label.

The first review rejection at 01:21:04Z was for unchanged RHAISTRAT-2959:
freshness verification checks every acquired RFE. All six review completions
and result finalization were blocked by 3785. Three StructuredOutput hook
rejections followed because no completion checkpoint could be written. No
independent malformed-schema error was found. The agent attempted placeholder
receipt identifiers, which the hook rejected. No accepted completion resulted.

This exposes [batch failure isolation](../../bugs/open/strat-batch-freshness-failure-isolation.md),
separate from the fixed empty-template comparison. The job continued about
16 minutes after its first definitive freshness rejection. No new source
change or paid retry was performed as part of diagnosis.

All six lock-release logs and terminal Jira labels confirm cleanup. Partial
Jira writes remain, including the two newly created strategies and six refined
descriptions. Host publication was skipped; no data-repository run directory
exists at the captured revision, and the dashboard bridge was skipped. The
schedule has no executor override and remains on legacy.

Reported native usage: **26,547,917 tokens including cache; estimated $34.11**.
Separately reported reasoning is not added again. Not an invoice.

Read-only collection retained the 194-file native ZIP, job logs, OTel/debug/
transcripts, Jira snapshots/comments/attachments, 3785 changelog and data/
schedule receipts. Provider API dumps, syscall traces and separate MLflow
capture were not configured on this upstream runner. Offline verification
passed. Archive refresh verified **118 files plus manifest**, zero configured
credential matches, at var/run-data/20261028-real-gitlab-workflow-batch-retest/.
One transient observer GET timeout recovered; no model retry occurred.

## Acceptance

- [x] One pipeline created; checks pass before one manual batch-job play.
- [x] Actual source/model and acquired keys verified.
- [x] Terminal result, Jira/locks, publication and dashboard verified: failed.
- [x] Native evidence and first-observed/before/after receipts archived.
- [x] Schedule confirmed unchanged; no automatic model retry or re-enable.
