# Post-merge real GitLab single-ticket Workflow smoke

Owner authorized one smoke after GitLab !18 and strat-creator #85 merged.

## Scope

- One upstream `strat-pipeline` pipeline on `main`, one manual
  `workflow-single-rfe` job, Claude Opus 4.6/high, one iteration.
- Pipeline variables select `STRAT_EXECUTOR=fullsend`, live Jira writes and
  data publication. Project and schedule defaults remain legacy.
- Use an owned synthetic RFE. Check existing fixtures before deciding whether
  a fresh fixture is necessary. Preserve existing results and human gates.
- Run model-free CI checks before playing the model job. Persist creation and
  play intents; reconcile uncertain responses rather than retrying launches.
- Verify source/context receipts, Jira result and attachment, owner release,
  data publication and downstream delivery. Archive all available evidence in
  `var/run-data/20261027-real-gitlab-postmerge-single-opus46/`.
- No automatic second paid attempt or production cutover.

## Progress

- Merged consumer main b00078e and source main b295fe9 verified. Ten source
  interfaces match tested PR head 364e1ca; merged consumer CI matches 200b04b.
- Live preflight confirms matching runner online, no active earlier pipeline,
  no project/schedule executor override. Next scheduled legacy run is 22:00Z.
- Existing RHAIRFE-3739 and -3748 have rubric-pass STRATs. Created distinct
  synthetic RHAIRFE-3788: copy current workbench container image digest.
  Initially only neutral smoke labels; no release/quality eligibility yet.
- First setup pipeline 2996300758 included extra blocking manual jobs when
  unused selectors were supplied as empty API variables. Canceled before any
  model job started; retained cancellation and submission receipts. Corrected
  the submission by omitting unused selector variables (no CI/source edit).
- Corrected upstream main pipeline 2996306877 includes only the intended
  model job. Both model-free checks passed. Qualified only RHAIRFE-3788 with
  temporary `strat-creator-3.8` and `tech-reviewed` labels, then submitted one
  play for job 17518703899. No other model job played.
- Controller and staging evidence: `/tmp/strat-postmerge-smoke.py` and
  `/tmp/20261027-real-gitlab-postmerge-single-opus46/`.
- First archive copied and verified (32 staged files, configured-secret scan
  zero). Final native artifacts/publication readback pending job completion.
- Job reached the agent at 20:34:39Z: confirmed Opus 4.6 / Claude Code 2.1.296;
  it launched the Workflow in the background. Architecture source receipt is
  current remote HEAD 2f3ab40. A live symbolic-ref read confirms HEAD is main;
  `rhoai-3.6-ea.2` is a selected content directory, not a Git ref pin.
- A bounded read-only monitor is being started to collect native evidence,
  remove only fixture-added eligibility labels after terminal status, check
  downstream state and refresh the archive. It never creates/plays/retries a
  model job. Independent result verification remains required afterward.
- Monitor confirmed running (exec session 62805). At 20:53:51Z, read-only Jira
  progress confirms linked RHAISTRAT-3074 was created at 20:35:26Z, carries
  auto-refined and rubric-pass labels, and has one review comment (20:52:59Z)
  plus RHAISTRAT-3074-review.md attachment. RFE still holds this run's lock.
  CI only streams outer-agent heartbeats during inner Workflow activity;
  Jira gives actual phase evidence. Overall completion/publication/cleanup
  still unverified. Saved progress snapshots under staging progress-jira/.

## Acceptance

- [x] One authorized model job completes, with its outcome stated accurately.
- [x] Native artifacts, CI traces, Jira snapshots and publication readback saved.
- [x] Fixture-only temporary labels removed; processing claims released.
- [x] Project/schedule executor settings verified unchanged.
- [x] Archive integrity and configured-credential scans checked; outcome recorded.

## Final result

Core smoke passed. Pipeline 2996306877 succeeded, with model job 17518703899
taking **28m 37s** (20:26:41Z to 20:55:18Z). The agent ran about 19 minutes;
the rest includes bootstrap, final checks and publication. Merged upstream
source b295fe9 ran Opus 4.6/high, one iteration, no model retry. Consumer's
148 tests and input validation passed. No source change was needed.

RHAIRFE-3788 produced RHAISTRAT-3074. Create/refine/push/review completed;
business completion receipt and final validator passed. Review scored **7/8**,
approve. Testability specialist's **revise** is preserved independently, as
required by numeric-only policy. Host run and owned lock release exited zero.

Independent verifier confirmed exact Jira review attachment bytes and comment
ADF, all 14 sealed publication hashes, and the run in both aggregate summaries.
Dashboard pipeline 2996400047 passed (44 seconds); its 451-entry native ZIP
contains the new strategy in index, current, per-run and aggregate output.
Temporary eligibility labels removed; no owned/processing RFE lock remains.
Project and six-hour main schedule have no executor override and are unchanged.
Scheduled execution still selects legacy; this was not a cutover.

Org Pulse CI export reported 1 created, 0 updated, 1,040 unchanged, with 18
aggregate entry validation warnings. Five printed examples are older STRATs;
the remaining thirteen identities are truncated. A per-feature GET from this
host could not resolve the internal service hostname. Record this limitation;
do not call the upload counts an independently verified ingestion result.
Follow-up: [aggregate review-schema warnings](../../bugs/open/org-pulse-aggregate-review-schema-warnings.md).

Native accounting reports **3,899,064 tokens including cache**, with 17,134
reasoning tokens separately reported (not added again), and **$6.130943**.
This is model-reported cost, not an invoice reconciliation.

All available evidence is in
`var/run-data/20261027-real-gitlab-postmerge-single-opus46/`: native Workflow
ZIP (38 files), downstream ZIP, CI traces, Jira snapshots/download, publication
bytes/seal/summaries, source/context receipts, cleanup/settings readback,
controller, verifier, README and verification.json. No separate raw API,
syscall or MLflow capture was configured on the remote runner; recorded in
capture-availability.json. Final archive checksum and configured-secret scan
passed. Monitor ended normally with no collection/cleanup errors.

## Reconstruction of the quiet console interval

Native ZIP inspection confirms actual OTel JSON: **7 spans** for run, sandbox
creation, primary agent, three Bash calls and the Workflow launch. Workflow
launch spans about 0.3 seconds, not the full background execution. There are
no exported inner-agent spans in this trace.

However, **15 timestamped Claude transcripts (721 records)** and **19 journal
entries** reconstruct the inner activity. Nine journal helper agent IDs join
to transcripts; five nested skill/reviewer agents and the primary transcript
complete the set. Extracted **157 distinct tool calls and 157 tool results**,
with timestamps, commands/paths, call IDs and source transcript record UUIDs.
No model run or remote write was needed.

Observed UTC intervals: create 20:34:53-20:36:44, refine
20:36:44-20:41:49, push 20:41:56-20:42:07, scorer
20:42:15-20:44:53, review parent 20:44:53-20:53:18. Specialist
transcripts are sequential: feasibility 20:45:46-20:47:32, testability
20:47:33-20:49:43, scope 20:49:43-20:50:37, architecture
20:50:37-20:52:46. Result helper 20:53:19-20:53:27.

These are first/last transcript activity bounds, not exact independently
instrumented execution spans. Parent/child durations overlap and must not be
added together. No raw provider or syscall trace exists. The data is sufficient
for post-run phase/tool reconstruction, but the console did not stream these
inner events live. Derived timeline and tool-event JSON/CSV are archived under
`reconstruction/`, alongside the offline reconstruction script.

## Readiness assessment after the owner asked about schedule enablement

Read-only check at 2026-10-27T21:29:01Z confirms strat-creator main is still
tested b295fe9. Consumer main advanced to 812cfc7 only for a CODEOWNERS handle
correction; comparison against the smoke's b00078e contains no executable or
CI change. Project and active schedule 4222905 still have no executor override;
default remains legacy/stable-1.x. No setting was changed or run submitted.

Recommendation: enable `STRAT_EXECUTOR=fullsend` on the existing schedule,
keep the project default legacy and stable-1.x fallback, then inspect the first
scheduled batch's selection, results, cleanup and delivery. Prior ten-ticket
fresh/mixed tests qualify the Workflow on the Markov path; this single-ticket
smoke qualifies merged-source integration on the real Fullsend runner. The
first real scheduled batch remains an additional qualification point, not a
scenario already proven by this single. Aggregate Org Pulse warnings remain
a separate follow-up. This assessment is not authorization to change settings.

Readiness comparison receipt is readiness-check.json in the run archive;
read-only settings snapshot /tmp/strat-pipeline-merge-20261027T212223Z.json.
