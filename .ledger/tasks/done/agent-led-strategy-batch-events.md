# A4: Native strategy batch and Fullsend event dispatch

Depends on [A3 single CI](../done/agent-led-strategy-single-ci.md); use its tested release.

## Acceptance criteria

- [ ] Extend `.gitlab-ci.yml` on the existing strat-pipeline project's
  `feat/fullsend-agent-led-poc` branch; add batch-discover CI calling native
  strat-batch with JQL gates,
  size/offset, candidate bounds and resource_group strat-batch.
- [ ] Seed two fresh distinguishable RFEs. One agent run processes the acquired
  subset in native order, excludes processed work, and creates two linked
  strategies, refinements, truthful reviews and output mappings.
- [ ] Verify actual 4.6 model metadata, validated phases/artifacts, lock release,
  results/summary, Org Pulse and refreshed dashboard, redaction and runtime cleanup.
- [ ] (Withdrawn 2026-10-07; see Scope amendment.) Determine the selected release's supported native event interface and
  existing producer/schema. Configure supported native triggers; prove matching,
  input mapping and
  actual dispatch of single versus batch events through the selected existing
  path. Missing/ambiguous input must not launch unintended writes. Direct CLI
  invocation alone is insufficient evidence of event dispatch.
- [ ] Exercise no-work, partial locks and interrupted-phase recovery using
  bounded fixtures; resume/reconcile without duplicating completed effects.
- [ ] Run required checks and `git diff --check`, commit/push/publish changes,
  and record pins, pipeline/job IDs and comparison with the script-led POC.
  Leave no test job or unattended recurring schedule active.

## Breakpoints

| # | What you get | How to check | Question |
| --- | --- | --- | --- |
| B4.1 | Batch CI wired to a GitLab pipeline schedule (`resource_group: strat-batch`); schedule-started no-work run; schedule removed afterwards | Pipeline with source `schedule`; trace | Is the schedule wiring right before a model run? |
| B4.2 | One schedule-started strat-batch run over two fresh RFEs on Opus 4.6: two linked STRATs, validated, published, Org Pulse, dashboard, cleanup | Jira, results commit, dashboard, artifacts | Is the output right? |
| B4.3 | Partial-lock and interrupted-phase recovery with bounded fixtures; comparison with the script-led POC; commits, pushes, no active test jobs or schedules | Ledger evidence | Close the POC? |

## Verdict log

| Breakpoint | Verdict | Date | Notes |
| --- | --- | --- | --- |
| B4.1–B4.3 | Close; carry open items forward | 2026-10-08 | User: put the open items in new milestones (A5 publication, A6 recovery in CI, A7 runner pods) |

## Scope amendment (2026-10-07)

Event-trigger dispatch and polling are out of scope; the user ruled polling
out. The acceptance item on native event triggers is withdrawn: the
reference pipelines start batch from a GitLab schedule and run the named
agent directly.

For the record, research into 0.43.0: CEL `trigger:` is a harness field,
matched only by `fullsend dispatch` (GitHub event or JSON input) and the
hidden `fullsend poll --input-driver jira-poll`. Neither launches agents.
The GitLab poller routes by hardcoded `/fs-<agent>` names. jira-poll would
need emulator changelog, project-role and user-group APIs, which return 404.

## B4.1 handoff (2026-10-07)

- **CI:** `strat-batch` now runs on `$CI_PIPELINE_SOURCE == "schedule" &&
  $RFE_KEY == ""` (scheduled, as in strat-pipeline and rfe-autofixer) or
  `STRATEGY_MODE == strat-batch` (manual or API). It uses
  `resource_group: strat-batch`, shared with strat-pipeline's native batch
  job. strat-single is unchanged.
- **publish.py `--schedule-once`:** creates a schedule whose cron names one
  minute about 3 minutes ahead (UTC; it would next recur a year later),
  waits for the emulator worker to start it, then deletes the schedule.
- **Branch head:** `c128241`; protected branches unchanged.
- **Pipeline 2082 / job 4043:** schedule 1, cron `12 0 8 10 *`, source
  `schedule`; the schedule was deleted afterwards (0 remain).
  - The job ran strat-batch at fork `a2b888a`.
  - Discovery found nothing, so the pre-script exited 78: no sandbox, no
    model, no locks.
  - The skipped result is `gitlab-job-4043`. `command_exit=0`,
    `cleanup_exit=0`.

## B4.2 attempt 1: pipeline 2083 / job 4044, stopped mid-batch (2026-10-08)

- **Seeds:** RHAIRFE-13 (workbench culling exemptions) and RHAIRFE-14
  (TrustyAI drift alerts). Overlap was 0.13, the same as the RHAIRFE-11/12
  baseline.
- **Run:** the schedule fired (`source: schedule`); the bound matched and
  the host locked both RFEs.
- **Progress:** create, refine and push completed for both; RHAISTRAT-13
  was reviewed (approve 8/8).
- **Stop:** the parent then ended its turn after the review skill's
  "advise the user" report (`stop_reason: end_turn`). There was no result,
  so nothing was published, and both locks were released.
- **Bug and fix:**
  [bug](../../bugs/open/agent-led-batch-ends-turn-after-skill-report.md).
  The user chose option 3: fork `9350c89`, resume on a validation retry.

## B4.2 attempt 2: pipeline 2084 / job 4045, success (2026-10-08)

- **Seeds:** RHAIRFE-15 (Feast scheduled materialization) and RHAIRFE-16
  (Kueue admission visibility). Overlap 0.13; at most 0.16 against any
  existing RFE.
- **Bounds:** full discovery returned 14, 15 and 16. The schedule used
  offset 1, size 2 and expected keys `RHAIRFE-15 RHAIRFE-16`, which keeps
  RHAIRFE-14 for the recovery test.
- **Start:** one-shot schedule, cron `16 2 8 10 *`, `source: schedule`;
  deleted afterwards (0 remain). Fork `9350c89`, branch head `6e3ab46`.
- **Agent:** completed in iteration 1 of 2 (2611.7 s); no retry was needed.
  - Progress: create, refine_15, refine_16, refine, push, review_15,
    review_16, review, in order.
  - All 13 transcripts are `claude-opus-4-6` (532 turns).
- **Result:** RHAISTRAT-15 is revise 5/8 (needs_attention); RHAISTRAT-16 is
  approve 6/8.
- **Validation:** matches the run record, artifacts, progress and Jira.
- **Jira:** each STRAT is Cloners-linked to its own RFE, with labels
  matching its verdict (needs-attention or rubric-pass), the review
  attached and a comment posted.
- **No cross-contamination:** RHAISTRAT-15's description has 117 Feast or
  materialization terms and 0 Kueue terms; RHAISTRAT-16 has 0 Feast and 97
  Kueue terms.
- **Results:** in `strat-pipeline-data`, run commit `e0d5976` (run
  `20261008-030443`, 2 tasks, 2 reviews) and summary commit `b4cf112`.
  Both summaries list the run as current, `pipeline-settings`, not a dry
  run, with the right rows and scores.
- **Org Pulse:** the push reported 0 created and 2 updated, but the GETs
  returned 404 (stale keys). After the documented `releases:jira-sync`
  (202), both read back with the right sourceRfe, run ID, verdict and
  title.
- **Locks and cleanup:** both locks released; `command_exit=0`,
  `cleanup_exit=0`.
- **Credentials:** 0 hits in 37 files.
- **Dashboard:** fresh build, pipeline 2085 / pages job 4046, succeeded.
  `public/runs/20261008-030443.json` exists, and `summary.json` and
  `index.html` contain the run and its STRATs.
- **Not yet proven:** the in-run retry, since the stop did not recur.

## B4.3: recovery across runs, pipeline 2086 / job 4047 (2026-10-08)

- **Baseline:** RHAISTRAT-14 from pipeline 2083 was cloned, refined and
  pushed but not reviewed, with no verdict label; description sha
  `61bbe172c341`, updated 00:52:08.
- **Discovery:** full discovery returned only RHAIRFE-14; 15 and 16 were
  now processed.
- **Start:** one-shot schedule, cron `9 3 8 10 *`, size 1, expected keys
  `RHAIRFE-14`, `source: schedule`; 0 schedules remain.
- **Agent:** host locked RHAIRFE-14; finished in iteration 1 of 2
  (1418.8 s).
- **Create imported the existing clone (Path A):** the skill found
  RHAISTRAT-14 without pipeline completion labels.
- **No duplicate clone:** RHAIRFE-14 still has exactly one clone,
  RHAISTRAT-14.
- **Completed effects not repeated:** RHAISTRAT-13 untouched (updated
  01:06:24, the time of its 2083 review).
- **Repeated effect, as predicted:** refine and push ran again, so
  RHAISTRAT-14's description changed (sha `041a278b1957`). The skills gate
  only on verdict labels, so an unreviewed STRAT is refined again.
- **Review:** approve 8/8; one review attachment and one comment, because
  there was no earlier review.
- **Validation:** matches the run record, artifacts, progress and Jira.
- **Results:** run `20261008-033707`, results commit `5b60e30`, summary
  commit `f16b24f`; the summary row is correct.
- **Org Pulse:** after `releases:jira-sync`, it reads back run
  `20261008-033707`, approve.
- **Models and cleanup:** 315 turns, all `claude-opus-4-6`; lock released;
  `cleanup_exit=0`.
- **Credentials:** 0 hits in 31 files.

Other boundaries:
- **No-work:** B4.1, pipeline 2082.
- **Partial and blocked locks:** emulator-backed tests
  (`TestPrepareBatch`, `TestPrepareSingle`). Doing this in CI would need a
  temporary Jira label write.
- **In-run validation retry:** implemented and unit-tested, but not yet
  observed in CI because the stop did not recur
  ([bug](../../bugs/open/agent-led-batch-ends-turn-after-skill-report.md)
  stays open).

## Comparison with the script-led POC

| Aspect | Script-led (feat/fullsend-strategy-poc) | Agent-led (this POC) |
| --- | --- | --- |
| Fullsend | Feature binary built per pipeline (custom entrypoint patch) | Released 0.43.0, checksum-verified, unpatched |
| Orchestration | `strategy-entrypoint.sh` runs one `fullsend-claude` per phase | One native Claude agent per run; the prompt drives the phases through the existing skills |
| Discovery and locks | Entrypoint script | Host pre-script (`prepare_run.py`); agent receives keys only |
| Vertex auth | `--from-gcloud-adc` provider shim | Upstream provider and profile; ADC file mounted; no shim |
| Sandbox egress | Jira, GitLab, Org Pulse and GitHub (context fetch) | Jira only; context and publication on the host |
| Completion check | Phase exit codes | Host validator: run record, artifacts, progress, scores and Jira readback |
| Publication | Inside the sandbox entrypoint | Host post-script, only after validation |
| Failure handling | Script `trap` cleanup | CI `release-locks.sh` always; one validation retry with resume |
| Batch trigger | GitLab schedule or manual | GitLab one-shot schedule (same resource group) or manual |
| Observed single run | ~21–22 min (e.g. 2071) | ~19 min of agent time (2078) |
| Observed 2-RFE batch | 2053: two approve 8/8 | 2084: 43.5 min of agent time; revise 5/8 and approve 6/8 |
| Defects found here | n/a | Validator required unanimous prose reviewers (fixed); headless `end_turn` mid-batch (fixed by retry and resume, unproven); unset host variables rejected (fixed in CI) |

Both POCs need the same emulator recoveries: the Org Pulse stale-key sync,
and a manual dashboard rebuild because of the eager-bridge bug.

## Status

Done, 2026-10-08. Closed with the open items carried forward to
[A5](../pending/agent-led-strategy-publication-recovery.md),
[A6](../pending/agent-led-strategy-recovery-ci.md) and
[A7](../pending/gitlab-runner-job-pod-cleanup.md). Batch-selected and
reprocess-strat remain outside this POC.
