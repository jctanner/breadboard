# Testing the strat-creator Claude Workflow in Breadboard

Created 2026-10-09. Source: `eval-plan-workflow-vs-bash.md` in
`2026_10_09_strat_creator_workflow_debate/`.

Reader's report: [Claude Workflows and scripted pipelines](../notes/claude-workflows-vs-scripted-pipelines.md).
It summarizes the execution layers, evidence limits, proposed testing budgets,
and production recommendation. Proposed study levels do not authorize new runs.

Production coverage update, 2026-10-12: the user confirms a ten-RFE batch limit,
roughly three RFEs on average, and a six-hour schedule. The
[narrative report](../notes/claude-workflows-vs-scripted-pipelines-human.md)
now proposes ten-RFE batches for level 3 and full-size level 4 trials. Existing
three-RFE measurements remain baselines. The production batch limit is not being
reduced; ten-RFE cases have not run. Their budgets are provisional projections.
They cover pipeline work only. Proposed level 5,
[independent strategy-content evaluation](../notes/strat-workflow-content-eval-harness-assessment.md),
adds a separate judge-model budget and can reuse frozen outputs from earlier
levels without waiting for the level 4 reliability campaign. The framework
inspection is complete; an artifact adapter and paid judging remain unrun.

2026-10-12 hardening: [fresh reproduction and reusable delivery checks](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-benchmark-hardening.md)
are complete and privately archived. The installed binary is still 2.1.296;
no newer-version conclusion is implied. Full normalized selected assessments
match 2/12 versus 12/12 expected returns. [R1 matched-concurrency design](strat-workflow-matched-concurrency-retest.md)
is pre-registered but has not launched. Delivery is measured separately from
scope, final incorporation and technical accuracy; no baseline implementation changed.

## What we are trying to learn

strat-creator turns approved RFEs into strategy documents in three steps:
create, refine and review. Production runs those steps from a bash script.
gsun's PR #83 runs the same steps from a Claude Code **Workflow**: a small
JavaScript file that Claude runs. It starts one helper agent per step and
passes the results between them.

The question underneath is about **orchestration**: is it better to let
**bash orchestrate** a series of `claude` and script calls (an
"entrypoint", PR #80), or to use **Claude's native Workflow feature** (PR
#83)? "Better" means correct, reliable, cheap and fast. fullsend is where
the debate started, but it isn't what we're testing; we test the two
orchestration styles.

The first question is narrow: **does the Workflow version run the steps
correctly and keep its records straight?** We test it in two tiers:

1. **Smoke tests.** One RFE, start to finish. A smoke test is a single run
   of either the Claude Workflow (PR #83) or the bash entrypoint (PR #80) on
   one RFE. Does it start, run every step and finish here in Breadboard?
2. **Full tests.** Does it still behave with bigger batches where the RFEs
   are in different states: new, half-finished, blocked or already done?

The same setup also runs **A/B comparisons**: two configurations, such as
opus-4-6 and haiku-5-5, on identical scenarios. See "A/B comparisons".

The bash version (PR #80) is in the smoke tier from the start, because the
same script mode runs both. A full comparison with it and with the
single-agent version (PR #81) comes later as A/B variants; see "Later".

## Does the proposed approach make sense?

Yes. Each choice and what it gives us:

| Choice | Why it works here |
| --- | --- |
| Model Relay credentials | Dashboard jobs already go through the relay, which records every model call and its token use per job. That gives cost numbers we would otherwise have to rebuild for the Workflow. |
| haiku-5-5 to wire things up | Cheap enough to rerun a lot while plumbing is broken. Its results say nothing about quality, which is fine at this stage. |
| opus-4-6 for the real runs | The model production uses, so the cost and behaviour numbers are comparable with production's (~$8 per RFE). |
| PR #83's Workflow | Pinned to the PR's commit `6b78355` in a local copy of strat-creator in the GitHub emulator, so every run uses exactly the same code and we can patch it for the evals. |
| Jira emulator seeded per test | Each test starts from a known state, and we can read Jira afterwards to check what the run actually did. |
| An MLflow experiment per test | Repeats of one test land together and different tests stay apart. |
| The dashboard job API | Every run gets strace, API request dumps, OTel traces to Observatory and an MLflow trace without extra work. |

Five adjustments:

1. **The job runner needs a script mode.** Today a dashboard job always ends
   in one `claude -p` call. Both designs are really scripts that call Claude
   several times:
   - PR #83 runs a prepare step, the Workflow, then a checker;
   - PR #80's entrypoint runs create, refine and review as separate `claude`
     calls.

   So the job API gets a **script entrypoint**: the job does all of its
   usual setup (relay credentials, MLflow tracing, OTel, strace, API dumps),
   then runs a script instead of `claude -p`. Every `claude` the script
   starts inherits that setup. See "Script entrypoint jobs".
2. **Tests run one at a time.** There is one Jira emulator, and seeding a
   test wipes it, so two tests at once would trample each other. A small
   driver script runs a list of tests in order.
3. **We assume the upstream account keeps up.** The Workflow runs up to
   about 16 helper agents at once. The relay itself has no request limit,
   but the Anthropic account behind it does: the first relay job got two
   "too many requests" (429) replies from Anthropic when three calls arrived
   together, and still finished. We go ahead assuming the account copes and
   watch for 429s in the relay's request log. **If they get in the way, the
   fix is to add a real Vertex upstream to Model Relay** and point the eval
   project at it. The jobs and their credentials stay the same; only the
   relay's upstream changes.
4. **Smoke and tier 2 baseline tests use the real skills.** The
   2026-10-11 decision to keep S1 and S2 as-is supersedes the original
   proposal to use stubs for most of tier 2. PR #83's stand-in skills can
   still help debug an isolated problem, but replacing skills is not part
   of the baseline comparison. See the tier 2 baseline policy below.
5. **Our own checks decide pass or fail, not just the exit code.** A run can
   "succeed" and still post something wrong to Jira. That's how the known
   rfe-autofixer incident happened. After every run, a script reads the run's
   files and Jira and checks the list in "What counts as a pass".

## What we build first

**Pinned values so far** (2026-10-10):

| Item | Value |
| --- | --- |
| strat-creator source | Local copy in the GitHub emulator: `https://github.local/opendatahub-io/strat-creator` (see "strat-creator lives in the GitHub emulator") |
| PR #83 (Claude Workflow) | `opendatahub-io/strat-creator` branch `pr-83` in the GitHub emulator, commit `6b78355ebc450ff4737fd10ba4857c26086ceac0` |
| PR #80 (bash entrypoint) | branch `pr-80`, commit `78ab3f1e97b09d02229bd03dd045a7eed97b0c33` |
| PR #80 eval branch | `eval/pr-80` at `c6fc33138320f0c88cf927e2c95eb4f18f9eb3dd`: PR #80 plus two eval patches, `STRAT_MODEL` and `STRAT_ARCHITECTURE_CONTEXT_PATH`. Both change behaviour only when their variable is set. |
| PR #80 results repository | `https://github.local/admin/strat-workflow-eval-results.git`, a throwaway repository in the GitHub emulator; PR #80 requires one |
| PR #81 (single agent, for later) | branch `pr-81`, commit `9350c89bcf1fd09acc0a3d1ef44ec6a59e47efe3` |
| Architecture snapshot | `/app/.context/snapshots/architecture-context/7d61f097a9220aeb1280837b66b532177ec558b6` (`rhoai-3.6-ea.2` and `overlays/`, 1,845 files, 88 MB) |
| Smoke scenario | `data/scenarios/smoke-one-rfe.yaml`: one eligible RFE, template `kserve-canary-rollback` |
| Eligibility at PR #83 | labels `strat-creator-3.6`, `rfe-creator-autofix-rubric-pass` and `rfe-creator-feasibility-pass`, checked against the commit's own discovery query |


| # | Piece | What it is |
| --- | --- | --- |
| 1 | Pinned PR code (done 2026-10-10) | A local copy of strat-creator in the GitHub emulator holding each PR's commit unchanged, plus eval branches that carry our patches on top. Jobs clone it at an exact commit. Details under "strat-creator lives in the GitHub emulator". |
| 2 | Architecture snapshot (done 2026-10-10) | One fixed copy of the architecture-context documents on the shared `/app/.context` volume, so every run reads the same reference material and nothing is fetched from the internet mid-test. |
| 3 | Jira seeding (done 2026-10-10) | A script in `var/benchmarks/strat-workflow/scripts/` that resets the Jira emulator and creates the RFEs (and existing strategies, labels and comments) for one named scenario from `data/scenarios/`. It reuses `var/demos/fullsend-entrypoint-poc/jira-seed/prepare.py` and `var/demos/fullsend-agent-led-poc/seed_rfe.py`. |
| 4 | Script entrypoint in the job API (built 2026-10-10; [task](../tasks/current/strat-workflow-eval-script-mode.md)) | `/api/jobs/submit` accepts a script to run in place of `claude -p`, after the usual setup. Plus two arm scripts in `var/benchmarks/strat-workflow/scripts/`: one runs PR #83's Workflow, one runs PR #80's bash entrypoint. Details below. |
| 5 | MLflow experiment name per job (built 2026-10-10) | An explicit `mlflow_experiment` field on the job API. Today the name is built automatically from the skill and model. |
| 6 | Checks | A script that reads the run's result, progress file, artifacts and Jira, and writes `eval-result.json` with each check's pass or fail and the reason. |
| 7 | Test driver (Markov) | A Markov workflow that takes a list of tests (scenario, repeats) and one or more variants (named sets of model, skills and commit; see "A/B comparisons"). For each test, variant and repeat it seeds Jira, submits the job through the dashboard API, waits for the job, reads its `eval-result.json`, and adds the outcome to one summary table with the variants side by side. Details below. |
| 8 | markovd setup | Register Breadboard's GitHub repository as a markovd project, and patch markovd so git imports keep the helper scripts and record their commit. Details under "The Markov test driver". |

### strat-creator lives in the GitHub emulator

We test **local copies** of strat-creator, kept in the GitHub emulator
(`github.local/opendatahub-io/strat-creator`), so we can **patch the code under test when an eval needs
it**: making a PR runnable outside fullsend, adding instrumentation, or
fixing a defect that blocks a test. Patches must never be invisible, so:

- **Unchanged PR commits stay as they are.** Each PR's head is pushed
  unmodified (for example `pr-83` at `6b78355`), so there's always a
  baseline that matches the PR exactly.
- **Patches go on eval branches on top,** one commit per patch, each with a
  message saying why it exists and which test needs it. For example,
  `eval/pr-83` is `pr-83` plus our commits.
- **Every run records the exact commit it used.** `STRAT_CREATOR_REF` in
  the job and `strat_creator_ref` in the run summary and seed report. A
  result from a patched commit can always be traced to its patches with
  `git log pr-83..<commit>`.
- **Comparisons state their patches.** When designs are compared (A/B or
  #80 vs #83), each variant lists the patches its commit carries. Patches
  that change behaviour, not just make the code run here, are called out in
  the results.

`pr-83`, `pr-80` and `pr-81` are already there unchanged (piece 1), and
`run-workflow.sh` and `seed_scenario.py` already clone from it.

### Running each design as it is

Each arm runs **as its own design defines it**, and the harness adds
nothing in between:
- **Workflow arm (PR #83):** its prepare step (`pre-strategy.sh`), then the
  Workflow started directly as its slash command, **once**:
  `claude -p --plugin-dir .fullsend/plugins/strat-pipeline "/strat-pipeline:strat-pipeline"`,
  with the settings the design declares (model, `effort: high`). Then its
  checker and post step.
  - Claude Code has no `--workflow` flag (checked against 2.1.296, the
    latest release, and the Workflows docs). A workflow starts through the
    Workflow tool or as a slash command, and plugin workflows are
    `/<plugin>:<name>`.
  - No agent prompt around it. fullsend's `strat-single` agent only told
    Claude to call the Workflow, wait, and write a failure result.
  - **No retry.** S1's first run passed only through fullsend-style
    validation-loop feedback. PR #80's entrypoint has no retry, so neither
    arm gets one. A retry variant can be tested separately.
  - The prepare step stays separate because PR #83 keeps it outside the
    Workflow by design; PR #80's entrypoint does the same work itself.
- **Bash arm (PR #80):** `.fullsend/scripts/strategy-entrypoint.sh
  RHAIRFE-N`, called directly by script mode from the strat-creator clone
  (no wrapper script), unchanged, including its own `claude` calls and its
  own output handling. It's the first thing executed after the
  environment setup. What it expects from its environment:
  - the `fullsend-claude` helper, installed in the pipeline-agent image;
  - results-repository settings, from job settings;
  - a non-opus model for haiku runs, as a recorded patch on `eval/pr-80`,
    because `strategy-model.sh` hard-codes `claude-opus-4-6`.
  Our checks run as a separate step afterwards.
- **No processing of Claude's output in the harness.** Raw output is
  `tee`d, unprocessed, to files (`stream.jsonl`, stderr) and to the job log,
  so the log shows the run live. Our checks read the files after the run.
- **Instrumentation is environment-level only, and identical for both
  arms:** relay routing, model pinning, MLflow hooks, OTel export, API
  dumps and strace. It observes the run and is never in the output path.

### Script entrypoint jobs

**What the dashboard job does in script mode:**
1. **The usual setup,** shared with prompt and skill jobs:
   - CA certificates;
   - Vertex settings pointed at Model Relay;
   - MLflow tracing hooks in `~/.claude/settings.json`, with the requested
     experiment name;
   - OTel export to Observatory;
   - API-body dumps.
2. **Model settings for whatever the script starts:** `ANTHROPIC_MODEL`,
   `CLAUDE_CODE_SUBAGENT_MODEL` and the `ANTHROPIC_DEFAULT_*_MODEL` aliases,
   all from the variant. Any `claude` the script starts, and any helper
   agent that starts, uses the variant's model unless the script overrides
   it.
3. **Run the script under strace** when strace is on. `strace -f` follows
   every process the script starts, including each `claude`.
4. **The script's exit status becomes the job's,** as for prompt jobs since
   the exit-status fix.

**How code gets into the job pod.** Two kinds of code end up there, by
different routes:

1. **PR code (strat-creator), cloned inside the job at a pinned commit.**
   - Each PR's commit lives in the local strat-creator copy in the GitHub
     emulator (piece 1), unchanged or with eval patches on top.
   - The arm script clones that repository at the exact commit.
   - PR #83's Workflow is a file inside that clone,
     `.fullsend/plugins/strat-pipeline/workflows/strat-pipeline.js`, loaded
     with `claude --plugin-dir .fullsend/plugins/strat-pipeline`. Its
     prepare and check scripts are in `.fullsend/shared/`.
   - PR #80's entrypoint is `.fullsend/scripts/strategy-entrypoint.sh` in its
     clone.
   - Job pods can already clone from `github.local`: FQN skill jobs do it,
     with the internal CA trusted in the pod.
2. **Our scripts (the Workflow arm script, seeding, reset and checks), from
   one of two sources.** The job API names the source:
   - **From the image,** a path under `/app/var/benchmarks/`. The
     pipeline-agent image already copies Breadboard's `var/`. Quick for
     wiring work, but every change needs `make host-rebuild-agent`, and the
     image is built from the working tree, so a result can't be tied to a
     commit.
   - **From a Breadboard clone** at a given commit (repo, commit, path). The
     Markov workflow passes in the Breadboard commit markovd imported the
     benchmark from (markovd now records it). Then the Markov workflow, the
     scenarios, the arm scripts and the checks all come from one recorded
     commit. No image rebuild is needed when a script changes, only a push.

   Use the image while wiring things up. **Any run whose results count**
   (smoke repeats, tier 2, A/B) uses the pinned Breadboard clone.

The API takes no arbitrary command lines: a script comes from the image's
`/app/var/benchmarks/` or from a pinned clone of an allowed repository.
Prompt jobs can already run anything through Claude, so this is about
keeping runs reproducible and readable, not new security.

**The Markov workflow doesn't run in the job pod.** markovd mounts it in a
separate Markov runner pod, which only seeds Jira, submits jobs through the
dashboard and collects their results. Every model call happens in the job
pods.

A request might look like this (the shape is to be settled when we build
it):

```json
{
  "script": {
    "repo": "https://github.com/jctanner/breadboard",
    "ref": "<breadboard commit>",
    "path": "var/benchmarks/strat-workflow/scripts/run-workflow.sh",
    "args": ["RHAIRFE-1"]
  },
  "args": {
    "model": "claude-haiku-5-5",
    "mlflow_experiment": "strat-workflow-eval/smoke/S1",
    "extra_env": {"STRAT_CREATOR_REF": "6b78355..."},
    "strace": true
  }
}
```

**What each arm's job runs:**

| Arm | Script mode runs | What happens |
| --- | --- | --- |
| PR #83, Claude Workflow | `var/benchmarks/strat-workflow/scripts/run-workflow.sh RHAIRFE-N`, from a pinned Breadboard commit | Clone strat-creator at the pinned commit. Run `pre-strategy.sh` (picks and locks the RFE; exit 78 means nothing to do). Run `claude -p --plugin-dir .fullsend/plugins/strat-pipeline "/strat-pipeline:strat-pipeline"` once, with raw output to files. Run PR #83's checker (`validate-output.sh`), and its post step when the run validated. Release the locks, always. |
| PR #80, bash entrypoint | `.fullsend/scripts/strategy-entrypoint.sh RHAIRFE-N`, from the strat-creator clone at PR #80's commit (or `eval/pr-80`) | The entrypoint itself, unchanged; no wrapper. Our checks run afterwards as a separate step. |

**How the bash arm gets what PR #80 expects from its environment** (built
2026-10-10):

| PR #80 expects | Provided by |
| --- | --- |
| `fullsend-claude` on the PATH | `scripts/job-bin/fullsend-claude` in the pipeline-agent image. It's a stand-in for fullsend's generated helper (fullsend PR #8202, `ClaudeEntrypointHelper`): `claude --print --verbose --output-format stream-json --dangerously-skip-permissions --model <model> --effort high "$@"`. The model comes from the job. fullsend's security hooks and integrity guard aren't reproduced; they belong to fullsend's sandbox. |
| `FULLSEND_OUTPUT_DIR` | `run_script.sh` defaults it to `$JOB_ARTIFACT_DIR/output` |
| `CLAUDE_CONFIG_DIR` (`prepare-claude-settings.py` requires it) | job setting: `/home/pipelineagent/.claude` |
| `RESULTS_REPO_URL`, `RESULTS_GIT_USER`, `RESULTS_PUSH_TOKEN` | job settings: the throwaway results repository, pushed with the emulator's development admin token. The token appears in the job's settings and environment dump; it's the emulator's default, already in a committed manifest. |
| A non-opus model for haiku runs (`strategy-model.sh` pins `claude-opus-4-6` and unsets `ANTHROPIC_MODEL`) | eval patch: `STRAT_MODEL`, set by the job |
| The pinned architecture snapshot (the entrypoint always fetched the newest from github.com) | eval patch: `STRAT_ARCHITECTURE_CONTEXT_PATH`, set by the job |
| Its own OTel collector and `stream-claude.py` | left as they are. PR #80 points OTel at its local collector, so Observatory doesn't receive its OTel. |

**Publishing results, the same for both arms:** PR #80 publishes to the
results repository on every run. `run-workflow.sh` now passes
`RESULTS_REPO_URL` through to PR #83's post step too (it used to unset it),
so both arms publish when the job sets the same three results settings. S1's
runs so far published nothing.

Each job's settings come from the job API: test ID, RFE key, variant
(model), MLflow experiment name, dry run or real Jira writes, and any
pinned commits.

### The Markov test driver

The tests are sequenced by a Markov workflow. Markov handles the order,
repeats, saved progress and review pauses; the dashboard still builds every
job pod.

**Layout:** the benchmark is a Markov **directory workflow** (Markov's
`docs/reference/workflow-file.md`, "Directory Workflow Layout"), so each part
sits in its own small file. Markov merges the files into one workflow when
it loads them; `markov validate var/benchmarks/strat-workflow` checks the
result.

```text
var/benchmarks/strat-workflow/
  README.md                what the benchmark is and how to run it
  meta.yaml                entrypoint (main), namespace, forks (1)
  vars.yaml                run settings: tier, only_tests, variants,
                           repeats, Breadboard commit, wipe and review
                           switches, job timeout, service URLs
  vars/
    tiers.yaml             test lists per tier (smoke: S1–S4, 3 repeats)
    arms.yaml              each design's pinned commit and settings
    models.yaml            variant names to models
  rules.yaml               the review_stop gate rule
  step_types/
    dashboard.yaml         dashboard_api (dashboard API call) and job_wait
                           (k8s_job_wait on a dashboard job)
    bench.yaml             bench_script: a runner-side script with the
                           dashboard and Jira settings
  workflows/
    main.yaml              settings, active-job check, wipe, rounds,
                           summarize, review gate
    round.yaml             the tier's tests (for_each_when: only_tests)
    test-variants.yaml     one test under each variant
    run-test.yaml          one run: seed, submit, wait, check
    wipe.yaml              clear artifacts, MLflow and Observatory
  scripts/
    run-workflow.sh        job side: the PR #83 arm
    seed_scenario.py       job side: reset Jira, create a scenario's issues
    check_run.py           runner side: the checks and usage -> eval-result
    summarize.py           runner side: eval-results -> summary tables
    benchlib.py            runner side: dashboard, Jira and file API helpers
    reset_environment.py, selfcheck.sh, snapshot-architecture-context.sh
                           host side
  data/
    scenarios/             one seed definition per scenario
    rfe-templates/         RFE texts the scenarios use
```

Notes on the layout:
- `meta.yaml`, `vars.yaml` and `rules.yaml` are required, plus either
  `step_types.yaml` or a `step_types/` folder. Workflow file names are only
  for reading; Markov finds workflows by their `name:` field.
- `markov validate` accepts the extra `data/` and `README.md` (checked on a
  copy of Markov's own example).

**How markovd gets the benchmark: git project sync.** markovd tracks
Breadboard's GitHub repository as a project:
- **Project:** markovd already has one for Breadboard: project 1,
  `ai-first-pipeline`, at `https://github.com/jctanner/ai-first-pipeline`,
  which GitHub redirects to `jctanner/breadboard`. It already imports
  Breadboard's demo workflows (`var/demos/end-to-end` and others). Reuse it,
  ideally with its URL updated to `https://github.com/jctanner/breadboard`.
  The repository is public, so markovd needs no credentials.
- **Sync** clones or pulls the repository. **Import** copies a chosen
  workflow into markovd's database. markovd recognises any folder with a
  `meta.yaml` as a directory workflow and names it after its path, so this
  one appears as `var/benchmarks/strat-workflow`.
- **Changing the benchmark** means committing and pushing to `main`, then
  sync and re-import. Experimental changes can go on a branch with its own
  project entry.
- markovd keeps its clone inside the container without a volume. That's
  fine: after a restart it clones again, and imported workflows are already
  in its database.

**markovd changes needed:**
1. **Done 2026-10-09: keep non-YAML files on import.** For a directory workflow
   read from git, markovd keeps only `.yaml` and `.yml` files
   (`ReadWorkflowDefinition` in `internal/projects/git.go`), so
   `scripts/*.py` and `README.md` would never reach the runner. Uploading the
   same folder through the CLI keeps every file. Patch the git path to match:
   keep every file except hidden ones.
2. **Done 2026-10-09: record the commit.** markovd now stores the commit an
   import or re-sync came from (`workflows.source_commit`). Each run keeps a
   copy from when it started (`runs.workflow_source_commit`), so every
   benchmark result can be traced back to the exact workflow, scenarios and
   scripts that produced it. Both show in the markovd UI.
3. **If large RFE bodies need it: lift the run-time size cap.** markovd packs
   all of a run's files into one Kubernetes ConfigMap
   (`internal/runner/k8s.go`), and ConfigMaps max out around 1 MiB. RFE size
   is something the benchmark should vary (scenario F11), so it can't simply
   stay small. Fix: give the runner pod an init container that downloads the
   run's files from markovd, which already stores them, into a scratch
   volume. That removes the cap instead of moving it.

The nginx upload limit in front of markovd (1 MiB by default, since
`deploy/k8s/15-markovd.yaml` doesn't set `client_max_body_size`) only
applies to uploads through the UI or CLI. Git sync doesn't go through it,
so it can stay as it is unless we start uploading benchmarks by hand.

**Resetting between tests.** Every test starts from a clean environment.
`scripts/reset_environment.py` does it through the dashboard's admin API,
from outside the job pods:
1. refuse to start while any pipeline job is pending or running;
2. clear the **artifacts volume** (`/app/artifacts`: job logs, strace, API
   dumps, script artifacts) with a cleanup job. The context volume is left
   alone, because it holds the pinned architecture snapshot;
3. **hard-delete all MLflow** experiments, runs and traces;
4. clear **Observatory's** claims, verdicts and explanations. Observatory has
   no API to clear OTel traces; those stay, tagged by job;
5. **reset Jira and seed** the scenario: a script job runs
   `seed_scenario.py` from a pinned Breadboard commit.

It prints one JSON summary and exits 0 only if every step worked and the
seed check passed. The Markov workflow runs the same steps as its own
dashboard API calls.

**What one test run does in Markov** (`workflows/run-test.yaml`, rebuilt
2026-10-10 on Markov's own steps):
1. `describe_run`: one `run` record (ID, test, arm, variant, model, commits,
   MLflow experiment), kept with the result.
2. Reset Jira and seed the scenario: a `dashboard_api` step submits
   `seed_scenario.py` as a script job, and `job_wait` (`k8s_job_wait`) watches
   it. The job's `seed.json` is read through the dashboard's file API, and an
   `assert` checks it.
3. Submit the design's job with a `dashboard_api` step. Each arm has its own
   step with the full request in the YAML, chosen by `when`.
4. Wait with `job_wait` and `ignore_errors`: a failed job is recorded as a
   failed test, and the tier goes on. A job still running at the timeout is
   stopped before the next run resets Jira.
5. `check_run.py` checks Jira and the job and sums usage from the API dumps.
   Its output is the run's eval-result, stored in the Markov run (the runner
   can't write to the artifacts volume).

**Resetting, as built:** the artifacts volume, MLflow and Observatory are
cleared **once, before the first run** (`wipe_at_start`). Only Jira is reset
before every run. Wiping everything per run would delete the earlier
repeats' strace, API dumps and MLflow traces, and an MLflow experiment could
then never hold more than one run.

**Loops** are nested Markov `for_each` steps, all with concurrency 1,
because every run resets the one shared Jira emulator:
- rounds: `repeats | seq`;
- tests: `for_each_when` applies `only_tests`;
- variants: `variants | csv | default:test.variants`.

Rounds come outermost, so arms and variants alternate (S1, S2, … then
again).

**Resume:** Markov saves progress after each step, and a resumed run skips
the runs already finished. The CLI can resume (`markov resume`); markovd
can't resume a run yet.

**Review stops** are a Markov gate (`review_stop` rule) at the end. It's off
by default (`review_stop: false`) because markovd can't resume a paused run.
With the CLI, resume with `--var reviewed=true`.

**Don't use Markov's own `agent_job` step for model runs.** It creates pods
directly. The existing benchmark's version mounts `gcp-credentials` and goes
straight to Google, with no relay, strace or API dumps. Every model run goes
through `dashboard_api`, so relay routing and tracing stay in one place: the
dashboard's job builder. This is the same submit-and-wait pattern the
end-to-end demo uses (markov task `k8s-job-wait-step-type`).

### How this differs from production fullsend

These runs test the Workflow's logic, not the fullsend platform. In
fullsend, the prepare and check steps run on the CI host and the Workflow
runs inside an OpenShell sandbox with network rules. Here all three run in
one job pod. Running the winning design on real fullsend is a separate,
later check: "Layer B" in the original plan.

## What counts as a pass

Every check is a script, not a model's judgement, and the same list applies
to every test:

1. **Finished.** The run's result file exists and says completed, or skipped
   when skipping is expected. The job exited as expected: 0 normally, 78 for
   "nothing to do".
2. **Right steps, right order.** Each RFE went through exactly the steps its
   starting state calls for. New RFEs get create, refine, push and review. A
   strategy that was already refined gets only review. A blocked RFE gets
   nothing.
3. **Records agree.** The result file, the progress file, the files written
   and what Jira now shows all tell the same story.
4. **Nothing posted twice.** Each Jira change (strategy text, review comment,
   labels) happened once per strategy, including after a retry.
5. **Nothing half-done posted.** No review is posted for a strategy whose
   refine or push did not complete.
6. **Locks released.** No RFE is left carrying a lock label after the run.
7. **Resume works.** Running again on a half-finished state does only the
   missing steps.

We also record, without pass or fail: model calls and tokens from the relay,
wall time, and how many "too many requests" replies the run hit.

## Tier 1: smoke tests

Goal: one RFE, start to finish, through each design, with every piece of
wiring working: relay, MLflow, OTel, strace, API dumps and our checks.
Each smoke test seeds Jira with **one eligible RFE** and runs the real
skills.

| Test | Design | Model | Runs | What it shows |
| --- | --- | --- | --- | --- |
| S1 | Claude Workflow (PR #83, `claude -p "/strat-pipeline:strat-pipeline"`) | haiku-5-5 | until it passes, then 3 | The script mode, the Workflow launch and all the wiring work; checks 1–6 pass on one RFE. |
| S2 | bash entrypoint (PR #80, `strategy-entrypoint.sh`) | haiku-5-5 | until it passes, then 3 | The same for the bash design, including the `fullsend-claude` stand-in and the model override. |
| S3 | Claude Workflow | opus-4-6 | 3 | The real thing on the production model. Cost per RFE compared with production's ~$8. |
| S4 | bash entrypoint | opus-4-6 | 3 | The same for bash. S3 and S4 together are the first like-for-like cost and time comparison. |

**If S1 won't start,** PR #83's own stand-in-skill test (its pre-written
input, no Jira, dry run) is a cheaper way to debug just the Workflow
launch. It's a debugging aid, not one of the smoke tests.

**Smoke tier passes** when S1–S4 pass every check on every repeat. We also
note how many 429s the account returned. If they get in the way, switching
the relay to a Vertex upstream comes before tier 2.

## Tier 2: full tests (larger, mixed batches)

**Mandatory evidence archival (user requirement, 2026-10-11):** each run,
including failed runs, must have a verified final local archive under
`var/run-data` before the next Jira reset or artifact/MLflow/Observatory
wipe. Preserve strace, exact API dumps and index, full MLflow traces/span
payloads, logs, Jira issues/comments/links/attachments, seeds, native state,
outputs, eval/summary, Markov identity/steps, Kubernetes state/events, and
related relay/Observatory evidence. Provisional captures do not count.
Generated archives stay out of git. Archival completeness is distinct from
strategy correctness. The implementation and coverage are recorded below.

Goal: show the Workflow keeps its records straight across batch sizes and
the states RFEs are really in. Run it on haiku first to get the scenarios
and checks right, then on opus for the results that count.

**Tier 2 requirements agreed 2026-10-11:**

- **Distinct RFEs within each batch.** Items must differ substantially in
  problem, requested capability and acceptance criteria, so agents have no
  reason to treat them as duplicates. Changing keys or titles on copies of
  the same RFE is insufficient. Review the seed content for this before
  running either design; both designs receive the same distinct items.
- **Smoke runs use haiku**, including helper conversations. Opus is for
  the subsequent evaluation passes.
- **One smoke run per scenario per design**, not three repeats. For the
  S1/S2 comparison this means one run of S1 and one of S2 on each scenario.
  The completed tier 1 evidence remains as recorded. Repeat counts for
  subsequent opus passes are a separate decision.

**Execution policy agreed 2026-10-11: one S1 test, then stop and analyze.**

1. Run **one selected batch scenario on S1 only**, once, with real skills
   on haiku for the smoke pass. Do not automatically run the remaining
   scenarios, another variant, additional repeats or S2.
2. Stop and inspect that run: per-item steps and Jira writes, concurrency,
   failures and reviewer output, token use/cost, and primary/helper context
   growth. Preserve its raw evidence with `wipe_at_start=false`.
3. Run the matching S2 test **later, after the user explicitly authorizes
   it**, once, using the same seed content, starting state, model and
   architecture snapshot. Record any intervening harness change that
   affects comparability instead of silently replacing the S1 result.
4. Decide on the next scenario or larger batch only after reviewing the
   completed results. The scenario catalog and proposed opus repeats below
   describe possible coverage, not a queued sweep or blanket run approval.

**Selected first case:** F1 with three new, substantially different RFEs.
This exercises actual batch concurrency with simple starting states before
adding resume or fault injection. The user authorized local implementation
on 2026-10-11; implementation evidence is recorded below. No live run has
been launched by this update.

**Baseline policy agreed 2026-10-11: keep S1 and S2 as-is.**

- Use the existing pinned eval commits (`1bd7f17` S1, `0287b83` S2),
  including their already-recorded evaluation patches. Add no new changes
  to either implementation or its skills for tier 2 unless absolutely
  necessary to restore critical functionality that blocks the evaluation.
- Use **real skills for both the haiku smoke and opus baseline passes**.
  Substituting stub skills would be a separate diagnostic variant, not an
  as-is comparison; this supersedes the original stub-based T2a/T2b design.
- Extend the benchmark harness to seed distinct RFEs and starting states,
  inject external Jira failures, capture evidence and check outcomes. Run
  each design through its own reference entrypoint without replacing its
  orchestration, output handling, retries or resume behavior.
- Measure existing defects, including S1's reviewer-output loss. Stronger
  checks expose a defect; they do not require fixing it before testing.
  Distinguish design failures from failures of the benchmark itself.
- If a critical repair becomes necessary, first document why the baseline
  cannot be evaluated, preserve its evidence, and record the patch and
  exact new commit. Results from the repaired variant must be identified
  separately from the original baseline.

**Scenarios** (each one is a Jira seed plus, where needed, a leftover
progress file from a "previous run"):

| ID | Starting state |
| --- | --- |
| F1 | All new RFEs |
| F2 | Strategy exists, still needs refining |
| F3 | Strategy refined and pushed, still needs review |
| F4 | RFE has a "needs attention" label (should be left alone) |
| F5 | RFEs that should be skipped: wrong status, no release label, quality label, or already passed |
| F6 | Previous run stopped after create (resume should pick up at refine) |
| F7 | Previous run stopped after push (resume should do only review) |
| F8 | Nothing eligible at all (expect a clean "nothing to do", not a failure; this is 58% of production's bash failures) |
| F9 | Jira rejects a write partway through (needs the emulator to inject errors; see open questions) |
| F10 | Dry run of a mixed batch (no Jira writes at all) |
| F11 | Very large RFE bodies: long problem statements, many acceptance criteria and attached detail, as seen on the largest production RFEs |

**Batch sizes:**
- each scenario alone with 1–3 RFEs;
- two mixed batches of 3 drawn from F1–F7;
- two mixed batches of 10 drawn from F1–F7, with some RFEs at F11 size.
  Ten is the size where small per-step failure rates start to add up: a
  batch of 10 makes about 34 agent calls, 24 of which must not fail.

**Runs:** smoke repeats are agreed; each scenario/design is launched
separately under the execution policy above. Opus repeats below remain
proposed for review after the smoke results.

| Pass | Skills | Model | Repeats | Purpose |
| --- | --- | --- | --- | --- |
| T2a | real | haiku | 1 | Get the scenarios, seeds and checks right, once per scenario per design |
| T2b | real | opus | 3 proposed | Main baseline evidence across scenarios and batches |
| T2c | real | opus | 3 proposed | Optional additional confirmation on F1, F3, F6 and one batch of 3, if T2b leaves a question open |

**A design passes tier 2** when its main evaluation runs satisfy the
applicable checks on every repeat. A failed check is a result to explain,
not an instruction to patch the implementation until it passes. Any
failure gets a written explanation from that run's files: transcript,
strace, API dumps and progress file. T2c is needed only if additional
confirmation is authorized after reviewing T2b.

## A/B comparisons

The same setup also compares two configurations side by side, for example
opus-4-6 against haiku-5-5. This is built in from the start, not added
later.

**A variant is a named set of job settings.** For example:

| Variant | Main session model | Helper agent model | Skills | strat-creator commit |
| --- | --- | --- | --- | --- |
| `opus` | claude-opus-4-6 | claude-opus-4-6 | real | `6b78355` |
| `haiku` | claude-haiku-5-5 | claude-haiku-5-5 | real | `6b78355` |
| `opus-main-haiku-helpers` | claude-opus-4-6 | claude-haiku-5-5 | real | `6b78355` |

The main session and the helper agents can use different models: the
Workflow's helpers take theirs from `CLAUDE_CODE_SUBAGENT_MODEL`. Other
settings can be variants too: stub or real skills, effort level, or a
different strat-creator commit or PR.

**How an A/B run works:**
- A comparison is a list of tests plus two (or more) variants.
- Every test runs once per variant per repeat, from the **same Jira seed and
  the same starting files**.
- The driver alternates them (A, B, A, B), so the account's rate limits,
  emulator state or time of day don't favour one side.
- Each MLflow experiment (one per test) holds both variants' runs, tagged
  `variant=<name>`, so they show side by side.
- The driver's summary puts the variants in adjacent columns.

**What each kind of comparison can answer:**

| Comparison | Answered by | Ready when |
| --- | --- | --- |
| **Reliability:** does the smaller model still run the Workflow correctly? | The checks in "What counts as a pass", on stub or real skills | Now. This is a real question for the Workflow design: every step depends on a helper agent running a command and handing back its output exactly. A weaker model may garble that, and the checks would catch it. |
| **Cost and time** | Relay token totals and wall time per run | Now |
| **Strategy quality:** are haiku's strategies as good? | Scoring each finished strategy against strat-creator's rubric (feasibility, testability, scope, architecture, out of 8) **with one fixed judge model for both variants** | Needs a scoring step. The pipeline's own review step can't be used, because in the haiku variant haiku grades its own work. |

**The scoring step for quality comparisons:** after the run, a separate job
runs strat-creator's scorer (`strat-scorer` with the rubric in
`scripts/assess-strat/agent_prompt.md`) on every strategy the run produced.
It always uses the same judge model, opus-4-6, whatever variant made the
strategy. Scores go into the run's `eval-result.json` and MLflow.

**How many runs a quality comparison needs:** the debate plan measured that
rubric scores move by about 0.7 points out of 8 when the same strategy is
simply re-scored. Comparing two variants with 3 repeats per RFE:
- a small difference (a quarter of a point) needs about 40–45 RFEs;
- a large difference (a full point) shows up with only a handful.

Start with 10 RFEs. If the models are clearly apart, stop there; if they're
close, extend towards 45. Comparing three variants at once needs more
(about 56), because there are more pairs to compare.

**A first A/B to run,** after tier 1:
- **Reliability:** T2b's scenarios with the real skills, `opus` vs `haiku`.
  A separate stub-based diagnostic variant could isolate handoffs, but is
  outside the as-is baseline comparison.
- **Quality and cost:** 10 real RFEs × 3 repeats, `opus` vs `haiku`, scored
  by the fixed opus judge. About $300–400 for the opus side, a small
  fraction of that for haiku, plus about $2–4 per strategy for judging.

## Where results go

- **MLflow**, one experiment per test, named
  `strat-workflow-eval/<tier>/<test-id>`. Each run is tagged with variant,
  model, scenario, batch size, skills (stub or real), pass or fail, and the
  relay token totals. Judge scores are added when a scoring step runs.
- **The job's artifacts:** strace, API dumps and `eval-result.json` under
  `/app/artifacts/`.
- **Observatory:** OTel traces, as for every job.
- **Model Relay telemetry:** model calls and tokens per run, filtered by time
  or job.
- **A summary table per tier**, written by the test driver, added to this
  plan's ledger task as the evidence.

## Rough cost and time

These are the original estimates. The tier 2 rows below assumed stub
passes and a separate real-skill confirmation pass; they are superseded
by the 2026-10-11 as-is baseline policy. Re-estimate tier 2 after selecting
the real-skill scenario set and opus repeats. Account-budget 429s can abort
the runs, not merely lengthen them. Report whether the campaign completes
within the available five-hour account allowance; see the account-budget
finding below.

| Part | Runs | Model cost (list price) | Time (one at a time) |
| --- | --- | --- | --- |
| Tier 1 on haiku (S1, S2) | ~6–10 | a few dollars | ~2–3 hours |
| Tier 1 on opus (S3, S4) | 6 | ~$50–60 | ~2–3 hours |
| Tier 2 T2a, haiku | ~14 | a few dollars | ~3 hours |
| Tier 2 T2b, stub on opus | ~42 | ~$150–250 | ~8–10 hours |
| Tier 2 T2c, real on opus | ~12 | ~$300–400 | ~6–10 hours |

The PR measured its stub run at $3.39 for 2 strategies. Production pays
about $8 per RFE with real skills on opus.

## Stops for review

**Current tier 2 policy:** stop after each individual run. In particular,
review the first S1 batch result before authorizing the matching S2 run;
do not wait for a whole tier or A/B pair before analysis. The historical
tier-level gates below do not override this requirement.

Stops 2–5 are gates in the Markov workflow: the run pauses at
`markovd.local` and resumes when you approve. Stop 1 comes before the
driver exists.

1. **After pieces 1–5 and S1 on haiku.** You submit S1 from the dashboard (or
   the driver does) and check that it shows in MLflow, the relay, and the
   strace and API dumps. We confirm the shape before building the checks.
2. **After tier 1.** Smoke summary table, rate-limit findings and real-skill
   cost. Decide whether to go on to tier 2 as planned or scale it down.
3. **After T2a on haiku.** Scenarios and checks behave as intended. Decide
   whether to spend on the opus passes.
4. **After T2b and T2c.** Final tables and an explanation of every failure.
5. **After the first A/B (opus vs haiku).** Reliability, cost and judged
   quality side by side. Decide whether to extend the quality comparison
   towards ~45 RFEs.

## Open questions

1. **Rate limits (decided 2026-10-09).** Assume the personal account copes.
   If 429s get in the way, patch Model Relay to use a real Vertex upstream.
2. **Jira error injection (F9).** Can the Jira emulator be told to fail a
   write? If not, F9 waits or needs a small emulator change.
3. **MLflow coverage.** Does MLflow's Claude tracing record the Workflow's
   helper agents, or only the main session? S1 answers this. If only the
   main session, the API dumps and relay telemetry cover the rest.
4. **RFE sizes.** How large are the largest production RFEs? Sample
   `strat-pipeline-data` to size F11 realistically. That also tells us
   whether the two 1 MiB caps above will be hit.
5. **Markov details to confirm while building.** Where markovd runs its
   shell steps, and whether they can reach the Jira emulator's admin
   endpoint (for seeding) and the artifacts volume (for reading
   `eval-result.json`). How a paused gate appears in the markovd UI, as
   opposed to the CLI's `--var` resume.
6. **Dry run or real writes.** Tiers use real writes to the emulator unless
   the scenario is a dry run. Checks 4–6 need real writes.

## Later

- **The other two designs as variants.** The same job type can run PR
  #81's single-agent version: same launch shape, different agent prompt. PR
  #80's bash version needs a different launch step. Each then becomes
  another A/B variant over the same scenarios and checks, which is the
  comparison the original plan asks for (its A1 stage).
- **A full quality study.** The original plan's A2/A3 scores about 71 cases
  across designs. The scoring step from "A/B comparisons" is the piece it
  needs; the rest is more cases and repeats.
- **Running on fullsend.** Running the chosen design on real fullsend and
  OpenShell (Layer B) is also outside this plan.

## Observations

Dated notes from building and running the benchmark, newest last. Facts
only; interpretation goes in the tier summaries.

### 2026-10-09 — Model Relay and dashboard jobs

- The first relay-routed job failed before any model call. Google's auth
  library looked up the project for the `external_account` credential
  through Cloud Resource Manager, which rejected the relay's token (strace:
  connections to 8082 and Google, none to relay 8080). Setting
  `GOOGLE_CLOUD_PROJECT` on job pods fixed it.
- The fixed job's five upstream calls all went through the relay. Two of
  the three calls sent in the same millisecond got **429 from Anthropic**
  (Anthropic request IDs recorded); the job still completed. The relay
  itself has no concurrency limit.
- `run_skill.sh` never exited with the agent's status, so failed jobs showed
  Complete. Fixed; prompt jobs also stopped printing skill-only messages.
- Rebuilding `pipeline-agent` moved Claude Code from 2.1.238 to 2.1.296,
  because the OpenCode build stage missed the cache and the Claude Code
  install is unpinned.

### 2026-10-10 — Building pieces 1–5

- Script mode: the selfcheck job passed 14/14 from the image and from a
  Breadboard clone at a pinned commit; a missing script fails the job.
- markovd: git import dropped non-YAML files from directory workflows, and
  imports didn't record their commit. Both were patched (markovd `71cd673`).
  markovd is served at `markovd.local`; `markov.local` (listed in
  `CLAUDE.md`) returns 404.
- The dashboard admin page's "Clear via Job" polled a route that doesn't
  exist (`/api/jobs/<name>/status`); fixed.
- Observatory's clear removes only claims, verdicts and explanations. There
  is no API to clear OTel traces.
- First full reset: artifacts cleared, MLflow emptied (1 experiment, 46
  traces), Observatory already empty, Jira reset with RHAIRFE-1 as the only
  RFE PR #83 discovers. The agent-led POC's Jira data is gone (approved).

### 2026-10-10 — S1, first run (PR #83 Workflow, haiku-5-5, RHAIRFE-1)

Job `script-run-workflow-rhairfe-1-claude-haiku-5-1010-014546-c44d83`, from
Breadboard `be4791d`. Real skills, real Jira writes, strace on, MLflow
experiment `strat-workflow-eval/smoke/S1/haiku`.

- **Prepare worked.** `pre-strategy.sh` loaded the pinned snapshot
  (`rhoai-3.6-ea.2`), locked RHAIRFE-1 with resume point `create`, and wrote
  the run input.
- **Launch matched PR #83's own smoke test.** The session ran on
  `claude-haiku-5-5`; its first tool call was
  `Workflow {"name": "strat-pipeline:strat-pipeline"}`.
- **strace covered the whole script:** the first traced process was
  `bash run-workflow.sh RHAIRFE-1`, with 531 per-process files a few
  minutes in (55 `claude.exe` execs, ~60 `git`, 20 `python3`).
- **Attempt 1 failed PR #83's checker.** Create made **RHAISTRAT-1** in
  Jira. Then the **refine helper agent returned no result** in the shape
  the Workflow requires, so push and review never ran. Checker output:
  - `refine: RHAISTRAT-1 returned no result; review: RHAISTRAT-1 not recorded; push: RHAISTRAT-1 not recorded`;
  - `RHAIRFE-1 has neither a reviewed strategy nor a skip reason`.

  This is the risk the plan names for the Workflow design: each step
  depends on a helper agent handing back structured output.
- **Attempt 2** (the validation-loop retry, with the checker's feedback
  appended) re-ran the Workflow, which resumes from the recorded progress.
  The agent then waited for it in a Bash `sleep 10` loop. It first read the
  previous attempt's stale `agent-result.json`, noticed that its freshness
  check was wrong, and switched to waiting on the resumed run's own output.
- **Relay:** 101 model calls in the first ~8 minutes, all HTTP 200; no 429s.
- **The job log goes quiet while the Workflow runs.** `claude`'s output shows
  only the main session's turns. The helper agents' work doesn't appear,
  and the main session sat in a Bash `sleep 10` loop, which prints nothing
  until it returns. The work kept going: at 01:59 the progress file had
  refine (01:49:26) and push (01:49:49) recorded with review in progress,
  the relay had 141 calls (latest 01:59:44), and attempt 2's stream had
  been written seconds earlier. An `agent-result.json` appeared in
  iteration 2 at about 01:51, before any review; to be explained from the
  final summary.
- **Why the job log went quiet: `scripts/stream-claude.py` drops the
  Workflow's events.** `claude` emitted them all to the stream: 140
  `system:task_progress` (each Workflow step with tokens, tool uses and
  time), `task_started`/`task_notification` for the Workflow, the four
  review sub-agents and the agent's own background waits, and
  `tool_progress` heartbeats. The parser prints only `init`, `api_retry`,
  `compact_boundary` and hook events, so none of it reached the job log. It
  should print these as one line each.
- **Review ran as four sub-agents.** The stream shows
  `/strategy-feasibility-review`, `/strategy-testability-review`,
  `/strategy-scope-review` and `/strategy-architecture-review` each started
  and completed as `local_agent` tasks during the Workflow's Review step.

### 2026-10-10 — Decision: run each design as it is

The comparison is bash orchestration (an entrypoint script making `claude`
and script calls) against Claude's native Workflow feature, not fullsend
itself. Each arm runs as its design defines it. The harness no longer
pipes Claude's output through Breadboard's `stream-claude.py`; S1's first
run did, which only affected the job log. Raw output goes to files. See
"Running each design as it is".

### 2026-10-10 — Decision: each arm starts at its own entry, once

- **PR #80:** script mode calls `.fullsend/scripts/strategy-entrypoint.sh`
  directly.
- **PR #83:** its `pre-strategy.sh`, then
  `claude -p --plugin-dir .fullsend/plugins/strat-pipeline "/strat-pipeline:strat-pipeline"`.
  Claude Code has no `--workflow` flag; the slash command is the direct way
  in.
- Neither arm is retried. S1's first run used fullsend's `strat-single`
  agent prompt and its validation-loop retry, so it isn't a pristine
  result for PR #83.

### 2026-10-10 — Decision: patchable local copies of strat-creator

The code under test comes from the local strat-creator copy in the GitHub
emulator, so we can patch it for the evals. Unchanged PR commits stay as
baselines, patches go on eval branches one commit each, and every run
records the commit it used. See "strat-creator lives in the GitHub
emulator". S1's first run used `pr-83` unchanged.
- **Outcome: passed on attempt 2, in 20 minutes; job Complete, exit 0.**
  Attempt 2's resumed Workflow ran the missing steps (refine, push, score,
  review), PR #83's checker reported `PASS: result matches the run record,
  progress, artifacts and scores`, `post-strategy.sh` reported
  `action=completed mode=single dry_run=False`, and `release-locks.sh`
  released RHAIRFE-1.
- **Result:** 1 of 1 strategies reviewed; RHAISTRAT-1 got recommendation
  **revise** (4/8) and `needs_attention: true`. Phases create, refine, push
  and review all completed; no errors.
- **Jira after the run, no duplicate writes:**
  - exactly one RHAISTRAT issue, RHAISTRAT-1, linked to RHAIRFE-1 as Cloners;
  - its description is the refined strategy (17,471 characters);
  - **one** review comment, "[Strat Creator] Strategy Review — REVISE
    (Score: 4/8)", at 02:05:25;
  - labels `strat-creator-auto-created`, `strat-creator-auto-refined` and
    `strat-creator-needs-attention`;
  - no `strat-creator-processing` lock on RHAIRFE-1. The retry didn't
    re-create, re-push or re-review anything.
- **Relay: 173 calls, all HTTP 200, no 429s.**
  - Tokens: 117,425 input, 243,149 output, 5,941,658 cache read and
    1,016,598 cache write.
  - 171 calls were `claude-haiku-5-5`. **Two weren't:** 1-token probes
    (`max_tokens: 1`) to `claude-sonnet-4-5@20250929` and `claude-opus-5-5`
    at session start (01:46:04), which bypass the model pinning. They're
    negligible in cost, but A/B accounting must exclude them.
- **MLflow:** experiment `strat-workflow-eval/smoke/S1/haiku` holds **3
  traces**, all `claude_code_conversation`; the longest ran 962 s. The
  Workflow's helper agents don't appear as traces of their own. Per-step
  detail is in the stream's `task_progress` events and the API dumps.
- **Saved artifacts:** 1,894 strace files and 335 API-body dumps.
  `publish/results` holds the strategy, review, originals, report and
  `pipeline-data.json`; both iterations' streams and validation output are
  kept too.
- **Not checked yet:** whether Observatory received the run's OTel.

### 2026-10-10 — S1, first pristine run (direct slash command, no retry)

Job `script-run-workflow-rhairfe-1-claude-haiku-5-1010-023258-0da910`,
Breadboard `1899e87`, haiku-5-5, after a full reset. **Failed after 10
minutes: the Workflow was killed before it finished.**

- `claude -p "/strat-pipeline:strat-pipeline"` started the Workflow and the
  session **ended its turn after 10 s** ("I'll wait for the completion
  notification"; 2 turns).
- `claude -p` then waited for the background Workflow **only up to 10
  minutes**. stderr: `Background tasks still running 10m after the last turn
  (workflow …); stopping them. Set CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS=0 to
  wait indefinitely.`
- By then the Workflow had completed create (02:33:51), **refine (02:36:53,
  which worked this time)**, push (02:36:58), score, and three of four
  reviewers. It was killed during the architecture review (`task_updated:
  killed`). There was no `agent-result.json`, so PR #83's checker failed it;
  `claude` itself exited 0. The locks were released.
- **Why the earlier run didn't hit this:** fullsend's `strat-single` prompt
  told the agent not to end its turn while the Workflow ran, and the agent
  kept polling. A direct launch relies on the CLI's background wait, which
  has a 10-minute ceiling by default. PR #83's note that "`-p` waits for the
  workflow" holds only within that ceiling.
- **Needed for headless Workflow runs:** a longer background-wait ceiling.
  Decision: `run-workflow.sh` sets `CLAUDE_CODE_PRINT_BG_WAIT_CEILING_MS` to
  **30 minutes** (overridable per job with `STRAT_BG_WAIT_CEILING_MS`), not
  unlimited. A strategy run takes 10–20 minutes. This is a CLI setting;
  PR #83 is unchanged.
- **Noise:** the dashboard sets `ANTHROPIC_LOG` to a directory path for API
  dumps. Claude Code expects a log level there and warns on stderr. The API
  dumps come from `OTEL_LOG_RAW_API_BODIES` and are unaffected.

### 2026-10-10 — Model Relay telemetry is lossy under load

During the S1 runs the relay's `/health` reported `dropped_records: 3901`
against 449 stored records. Its telemetry queue (1,024 entries, one SQLite
commit per write) discards writes when full. Inference is unaffected, but
relay call and token totals so far are **lower bounds**, including the 173
calls recorded for S1's first run. Recorded as a bug:
[model-relay-telemetry-drops-under-load](../bugs/open/model-relay-telemetry-drops-under-load.md).
Until it's fixed, take per-run cost from the API dumps or Claude's `result`
events.

### 2026-10-10 — S1 passes, pristine (direct slash command, no retry, 30-minute wait ceiling)

Job `script-run-workflow-rhairfe-1-claude-haiku-5-1010-024656-0d35f7`,
Breadboard `5e57401`, haiku-5-5, after a full reset. **Passed on its single
attempt in 12 minutes; exit 0.**

- **Launch:** `claude -p --plugin-dir .fullsend/plugins/strat-pipeline "/strat-pipeline:strat-pipeline"`.
  The session ran 2 turns (13 s), and `-p` waited for the background
  Workflow within the 30-minute ceiling.
- **Workflow steps** (cumulative tokens / tool uses / elapsed):
  - read input;
  - create: 14k / 2 / 4 s;
  - refine: 43k / 13 / 27 s;
  - push: 58k / 16 / 235 s;
  - score: 72k / 19 / 240 s;
  - review: 129k / 32 / 299 s;
  - result: 164k / 51 / 685 s.

  Refine worked first time; it was the step that failed on the very first
  run.
- **Result:** `completed`, 1 of 1 strategies reviewed. RHAISTRAT-1 got
  **revise** (4/8, needs attention), the same verdict as the first run.
  PR #83's checker: `PASS: result matches the run record, progress,
  artifacts and scores`. The post step completed, and the locks were
  released.
- **Jira:**
  - exactly one RHAISTRAT issue;
  - one review comment ("REVISE (Score: 4/8)");
  - labels auto-created, auto-refined and needs-attention;
  - no lock left on RHAIRFE-1.
- **Cost and usage from Claude's own `result` event** (`modelUsage`, which
  includes the Workflow's agents; list prices):
  - **$0.31**;
  - all `claude-haiku-5-5`;
  - 147,499 output tokens, of which 93,146 were thinking;
  - 3,666,550 cache read and 596,700 cache write.
  - API time was 674 s.
  - 213 API-body dumps.
  - Unlike the relay, this source isn't lossy.
- **Live output:** the job log showed the raw stream throughout (`tee`).

### 2026-10-10 — S2 passes, pristine (PR #80 entrypoint, haiku-5-5)

Job `script-strategy-entrypoint-rhairfe-1-claude-1010-030700-7c3093`:
strat-creator `eval/pr-80` (`c6fc331`), Breadboard `f17059b`, after a full
reset. **Passed in 14 minutes; exit 0.**

- **Launch:** script mode ran `.fullsend/scripts/strategy-entrypoint.sh
  RHAIRFE-1` directly. The entrypoint did everything itself:
  - cloned the results repository;
  - loaded the pinned snapshot (the `STRAT_ARCHITECTURE_CONTEXT_PATH`
    patch worked: "Architecture context copied from local path");
  - locked RHAIRFE-1;
  - ran create, refine, push and review as separate `fullsend-claude`
    calls;
  - published the results ("Pushed to remote") and released the lock.

  Review used the Agent tool (`[strat-scorer]` and the reviewer
  sub-agents), which is available here because nothing runs inside a
  Workflow.
- **Result:** RHAISTRAT-1 got **revise, 4/8**, the same verdict as S1. All
  four reviewer verdicts were revise; the central concern was that the
  strategy assumes Knative revisions where the architecture context points
  elsewhere.
- **Jira:**
  - one RHAISTRAT issue (description 19,481 characters);
  - **one** review comment ("REVISE (Score: 4/8)");
  - labels auto-created, auto-refined and needs-attention;
  - no lock left on RHAIRFE-1.
- **Results repository:** `admin/strat-workflow-eval-results` moved to
  `50b89e9`.
- **Usage, from the job's API dumps:**
  - 88 model calls, **all `claude-haiku-5-5`** (the `STRAT_MODEL` patch
    worked);
  - 173,203 output tokens;
  - 4,155,436 cache read and 577,651 cache write.
  - PR #80's `run-claude.sh` renders the stream through its own parser and
    keeps no raw stream, so there's no `modelUsage` figure from Claude for
    this arm.
- **PR #80's own OTel summary was empty:** "No OTEL data collected (log
  file not found)". Its local collector didn't produce `claude-otel.jsonl`.
  The cause isn't investigated yet; it may interact with the job's own OTel
  environment.

**First like-for-like comparison** (one run each, haiku-5-5, RHAIRFE-1, the
same snapshot and the same reset):

| | S1: Claude Workflow (PR #83) | S2: bash entrypoint (PR #80) |
| --- | --- | --- |
| Outcome | passed, single attempt | passed |
| Wall time | 12 min | 14 min |
| Verdict | revise 4/8 | revise 4/8 |
| Jira writes | 1 STRAT, 1 review comment | 1 STRAT, 1 review comment |
| Output tokens | 147,499 (93,146 thinking) | 173,203 |
| Cache read / write | 3.67M / 0.60M | 4.16M / 0.58M |
| Usage source | Claude `modelUsage` ($0.31 list) | API dumps (88 calls) |

These are single runs. The repeats (3 each) are what count.

### 2026-10-10 — The Markov driver for the smoke tier

`var/benchmarks/strat-workflow/` is now a Markov directory workflow (layout
under "The Markov test driver"). `markov validate` passes.

- **Tested without model spend:** the Markov CLI (built from markov
  `c312a4b`) ran the workflow locally against a stand-in dashboard. The
  stand-in turned submits and clears into no-ops that returned the real S2
  seed and run jobs, and proxied everything else to the live dashboard.
  - The run went: plan, wipe, then 4 runs (S1, S2, S1, S2), checks,
    summary, pause at the gate, and resume with `reviewed=yes`.
  - On S2's real job, the checks reproduce the figures recorded by hand:
    88 calls, 173k output, 4.16M cache read and 578k cache write. All 7
    checks pass.
- **What the build changed from the design:**
  - Waiting is a dashboard poll, not `k8s_job_wait`. The latter fails the
    step on a failed job, and Markov has no "ignore errors", so one failed
    test would stop the tier.
  - The wipe (artifacts, MLflow, Observatory) runs once per Markov run; Jira
    is reset before every run, so repeats keep their evidence.
  - eval-results live in the Markov run (each `check` step's output), not
    in `eval-result.json` files: the runner can't write to the artifacts
    volume.
  - The review gate is off by default: markovd can't resume a paused run.
- **Markov quirks found:**
  - Steps have no `description` field. The arch-context demo's workflows
    use one, so they don't validate with current Markov.
  - `--var` overrides arrive typed (`repeats=2` is an integer), and
    `script_exec` args must be strings. Workflow args use `--name={{ var }}`
    for that reason.
  - A template must pipe JSON through `| safe`, or it comes out HTML-escaped.
- **markovd `d923fe5`:** starting a run now passes the workflow's import
  commit as `workflow_source_commit`. The benchmark uses it as the Breadboard
  commit its jobs clone from.
- **Imported into markovd:** project 1 synced; the workflow is
  `var-benchmarks-strat-workflow` at Breadboard `921cce9`, with all 30
  files. No run has been started from markovd yet.

### 2026-10-10 — The driver rebuilt on Markov's own steps

The first driver passed most of its control flow to Python scripts
(planning, submitting, waiting). The cause was gaps in Markov. Markov
`5783094` and `34fead7` fill them:

- **`ignore_errors`:** a failed `k8s_job_wait` no longer stops the tier.
- **`for_each_when`:** filters the loop items one at a time.
- **Step `description`:** for long-form notes.
- **Native exact expressions:** in params and `set_fact`, including
  `tiers[tier]` and filter results.
- **`for_each` over expressions:** for example `repeats | seq`.
- **`csv` and `seq` filters.**
- **The loop item inside sub-workflows.**
- **No HTML escaping.**
- **`script_exec` accepts numbers and booleans** as arguments.
- **A `vars/` directory** for data files.

The benchmark now has nested `for_each` workflows, `dashboard_api` submits,
`job_wait` and an `assert` on the seed report. Scripts are left only for
the checks and the summary.

- **Tested under the CLI** against a stand-in dashboard. It handed back real
  completed jobs, and `k8s_job_wait` watched them in the cluster.
  - The full flow ran; `only_tests` skipped S3 and S4.
  - The submitted requests carried their `extra_env` maps intact.
  - In a second run the stand-in gave the S1 submit a real failed job. S1
    was recorded as failed (`finished`), and the run went on to S2 and
    completed.
- **The Markov job image** was rebuilt with `34fead7`.
- **markovd's own Markov was stale:**
  - **The problem:** markovd validates every import and upload with a
    bundled `markov` binary. Its Dockerfile copies that binary from
    `checkouts/markovd/bin/markov`, an untracked build from 2026-07-09, so
    rebuilding markovd never updated it.
  - **The fix:** `deploy/scripts/05c-build-markovd.sh` now builds that
    binary from `checkouts/markov` first, so markovd validates with the same
    Markov the job image runs. markovd was rebuilt and redeployed with it.
  - **Checked in the pod:** the binary matches the fresh build, and its
    schema lists `description`, `for_each_when` and `ignore_errors`.
    Validation now rejects `for_each_when` without `for_each`.
  - **Re-imported:** project 1 synced and the benchmark re-imported at
    `769edde`, with 30 files.

### 2026-10-10 — Markov and markovd gaps closed; checked without model calls

**Markov:**
- **`a2f189e`:**
  - `failed_when`;
  - the `flatten` and `pluck` filters;
  - `script_exec` `stdin`, which avoids the 128 KB per-argument limit;
  - chained subscripts, via a vendored pongo2 with a one-line fix;
  - docs.
- **`d52aee8`:** `for_each` no longer starts the next item after one
  failed. With concurrency 1 it used to.
- **`3520707`:** `resume` takes `run`'s execution flags.
- **`88190a4`:** numbers stay ints after a resume.

**markovd:**
- **`0c668dd`:**
  - a `markovd-data` volume holds the run files, the Markov state and the
    project clones, with no ConfigMap cap;
  - `POST /runs/{id}/resume`;
  - paused and resumed run states;
  - a Resume dialog and step descriptions in the UI.
- **`78cf57b`:** resume Jobs pass `--namespace`.
- **`3186ce0`:** steps that run again drop their old error.

**Checked with `var/demos/markov-feature-check`** (Breadboard `45eec72`), run
through markovd with no model calls. It went from failure to resume to the
gate to completion. That covered:
- the `workflow_source_commit` var (gap 4);
- fan-out results kept across a resume (gap 11);
- resume itself (gap 1);
- run files on the volume (gap 2);
- importing after a restart with no new sync (gap 3).

**strat-workflow now uses the new features:**
- `breadboard_ref | default:workflow_source_commit`;
- `tiers[tier].tests` directly;
- `job_name` through `default`;
- a summary that reads its results from stdin, collected with
  `pluck`/`flatten`.

CLAUDE.md and the README now say `markovd.local`.

### 2026-10-10 — Templated sub-workflow names and write_file

**Markov:**
- **`d9b2b8e`:**
  - `workflow:` can be a template, resolved when the step runs (per item
    under `for_each`);
  - a `write_file` step type;
  - a built-in `markov_run_id` var.
- **`7723016`:** `write_file` honours the setgid, setuid and sticky bits in
  its modes.

A resume refuses a sub-run whose templated name now resolves to a different
workflow than it ran. Step state is kept per workflow, so continuing would
mix the two.

**markovd:**
- **`0b3ebc7`:** the diagram shows templated calls without expanding them.
- **Runner pods** now mount `pipeline-artifacts` at `/app/artifacts` by
  default (`MARKOVD_JOB_VOLUMES` in `deploy/k8s/15-markovd.yaml`).

**strat-workflow** (Breadboard `506a7c2`):
- `run-test` calls `submit-{{ test.arm }}`, so each arm's job request is
  its own small workflow.
- Each eval-result is saved as
  `/app/artifacts/scripts/<job>/eval-result.json`, next to the job's
  artifacts.
- The summary and every eval-result are saved under
  `/app/artifacts/benchmarks/strat-workflow/<markov run id>/`.
- eval-results now carry `markov_run_id`.

**Checked:**
- **Locally against the stand-in dashboard:** both arms' submit workflows
  ran, and the files were written with modes 0664 and setgid 2775.
- **Through markovd** (`markov-feature-check`):
  - the templated call ran;
  - `write_file` saved `result.json` to the artifacts volume as root, with
    group `dashboarduser`;
  - the dashboard's user (uid 1000) read the file and deleted the
    directory, so the dashboard's artifacts wipe can still clear what Markov
    writes.

### 2026-10-10 — Definition graph layout reworked in markovd

The strat-workflow graph in markovd (`/workflows/var-benchmarks-strat-workflow`)
had three problems:
- call and return lines overlapped in each gap between columns;
- the return to `summarize` crossed four columns and the `wipe` group;
- fit-to-view zoomed out to 21%.

markovd `897d7d6` and `4c1ddd4` (ADR-0006 in markovd's ledger):
- **Returns stay in the adjacent gap.** A call that ends its workflow
  returns into the calling step.
- **Each call and return edge has its own lane** in its gap: the server
  assigns them and orders them to minimise crossings.
- **Calls and returns meet a card at separate points,** 25px and 47px from
  its top.
- **A child's first step lines up with its caller** where there's room.
- **Steps are spaced 36px apart** instead of 60px.

**Result on the deployed page:**
- fit-to-view is now 33% instead of 21%;
- round → test-variants → run-test now sits in one row;
- no edges overlap;
- one crossing is left between the `wipe` return and the `rounds` call,
  which no lane order can avoid.

The feature-check graph's call and return are both straight lines.

### 2026-10-10 — The submit step's targets shown and checked

`submit` calls `submit-{{ test.arm }}`. markovd's graph showed it without
targets, because the name is resolved at run time.

- **Markov `2caa232`:** `workflow_names` lists the workflows a templated
  name may resolve to. Each must exist when the definition loads, and a run
  that resolves to another name fails.
- **markovd `d61e80a`:** a templated call is drawn with its possible
  targets as alternative groups (fainter edges, "one possible target"). The
  targets come from `workflow_names`, or from workflow names that fit the
  template.
- **strat-workflow (`03dec23`):** `submit` has
  `workflow_names: [submit-workflow, submit-bash]`. An arm in `vars/arms.yaml`
  with no workflow now fails at the step, with a message naming the
  expected set.

Checked on the deployed page: both submit workflows are drawn next to
`run-test`, and the step's details list them from `workflow_names`.

### 2026-10-10 — First smoke runs through markovd

**`markov-run-731ce624`** stopped at the preflight check. The dashboard's job
list includes markovd's own runner Job, which the check counted as active.
Fixed in `c404cf6`: only jobs with a phase count.

**`markov-run-d91e2f5b`** (Breadboard `c404cf6`, S1 and S2 on haiku) was
cancelled to pick up live logging. Before that, it produced one real result.

**S1, round 1 failed** (job `script-run-workflow-all-claude-haiku-5-5-1010-153054-5d8230`,
6 minutes):
- **Steps:** create, refine, push and score ran. The haiku scorer helper
  scored REVISE 4/8 but refused to write its result file, claiming the
  session forbids writing report `.md` files. Nothing says so.
- **Knock-on:** without that file, the review helper wrote no review, and
  `record-review` exited 1 ("review file not found").
- **Design gap in PR #83:** the Workflow doesn't check `record-review`'s
  exit code. It took the helper's structured "revise" as the verdict, then
  `assemble()` reported "review: RHAISTRAT-1 not recorded", with
  `action: failed`.
- **Outcome:** PR #83's checker failed the run (`validate_rc 1`), and the
  locks were released. Jira was left with a pushed strategy but no review
  comment, which our checks would score as "steps_done" failing. The driver
  was cancelled before its checks step, so this result is recorded here
  only.

This is the reliability question the plan asks of the Workflow design: a
helper agent on a smaller model doesn't follow its instructions, and the
Workflow doesn't catch the failed step itself.

**Gap found:** cancelling a Markov run removes its runner but not the
dashboard jobs it submitted. The S2 job submitted at 15:37 kept running and
had to be stopped by hand. The next run's preflight check refused to start
until it was, as intended.

**Live logs:** Markov `ea133d5` makes `k8s_job_wait` emit `job_created`.
Checked on **`markov-run-9d30a751`**: while `wait_for_run` is still
running, markovd has the job name and streams the dashboard job's log.
That run is the smoke run of record (S1 and S2, three rounds).

**markovd stopped receiving the run's events** (15:50 to 16:22):
- **Cause:** restarting markovd to deploy the cancel fix gave it a new
  random callback token. `MARKOVD_CALLBACK_TOKEN` and `MARKOVD_JWT_SECRET`
  weren't in `pipeline-secrets`. `markov-run-9d30a751`'s runner kept sending
  the old token, and markovd rejected every event with 401 (Markov doesn't
  retry them). The page froze at S1's `wait_for_run`, while the run itself
  finished S1 at 16:13 and moved on to S2.
- **Fix:**
  - both values are now in `pipeline-secrets`, the callback token set to
    the one the runner sends;
  - `06-create-secrets.sh` keeps them stable: the cluster's value, else
    `.env`, else a new random one (`8357df0`).
- **Check:** after S2 round 1 finished at 16:28, the runner's events had no
  401s and markovd's page followed round 2. Events from 15:50 to 16:22 are
  missing from markovd's view only; Markov's state and the run's results
  have them.
- **Still open:** Markov drops a rejected callback rather than retrying or
  buffering it, so a markovd outage still loses events.

### 2026-10-10 — Smoke tier on haiku: results (markov-run-9d30a751)

Driven through markovd from Breadboard `c404cf6`, with three rounds of S1
then S2, from 15:47 to 17:27 UTC. The summary and eval-results are in
`/app/artifacts/benchmarks/strat-workflow/markov-run-9d30a751/`.

| Run | Pass | Verdict | Minutes | Calls | Output | Cache read | Cache write |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 r1 (Workflow) | yes | revise 4/8 | 25.5 | 181 | 315k | 8.40M | 1.31M |
| S2 r1 (bash) | yes | revise 4/8 | 15.3 | 90 | 188k | 3.83M | 652k |
| S1 r2 | yes | revise 4/8 | 17.9 | 126 | 201k | 5.52M | 842k |
| S2 r2 | **no** | – | – | 41 | 52k | 1.91M | 169k |
| S1 r3 | yes | revise 4/8 | 20.0 | 152 | 251k | 6.29M | 948k |
| S2 r3 | yes | revise 4/8 | 13.6 | 88 | 161k | 3.98M | 609k |

- **S1 (Workflow):** 3/3 passed, median 20.0 minutes. Per run it averaged
  256k output, 6.74M cache read and 1.03M cache write.
- **S2 (bash):** 2/3 passed, median 14.4 minutes over its two passes.
  Its passes averaged about 175k output, 3.9M cache read and 0.63M cache
  write.
- **No 429s.** Every call was `claude-haiku-5-5`.
- **The other S1 failure today** (cancelled run `d91e2f5b`, scorer refusing
  to write its file) is recorded above; it isn't in this table.

**Why S2 round 2 failed:** a strat-creator bug, triggered by the pinned
snapshot.
- **What happened:** the review step's agent ran the review skill's
  `fetch-architecture-context.sh` with no argument. Finding
  `.context/architecture-context` present, it ran
  `git -C .context/architecture-context sparse-checkout set architecture/rhoai-3.6-ea.2 overlays`.
- **Why it hit the checkout:** that directory was filled by the script's
  own local-copy mode (`fetch-architecture-context.sh <path>`, used for
  `STRAT_ARCHITECTURE_CONTEXT_PATH`), so it has no `.git`. Git used the
  enclosing repository, the strat-creator checkout, and sparse-checked it
  down to two paths.
- **Evidence:** strace shows the exec at 16:51:45. After it, `scripts/`,
  `config/`, `.fullsend/` and `.claude/skills/` were gone, while
  `git status` showed nothing deleted.
- **Outcome:** the review, the CI post step and the lock release
  (`scripts/lock_issues.py`) all failed. RHAIRFE-1 kept its lock until the
  next round's Jira reset.
- **A second problem in the same path:** without an argument the script
  also fetches the *latest* architecture context from GitHub, so a pinned
  snapshot isn't pinned for a review that re-runs it.
- **PR #83 has the same exposure:** its `pre-strategy.sh` supports
  `STRAT_ARCHITECTURE_CONTEXT_PATH` natively through the same copy mode,
  and its review skill re-runs the script without an argument. It didn't
  trigger in S1's runs.
- **Not specific to this eval:** production hits it whenever
  `STRAT_ARCHITECTURE_CONTEXT_PATH` is set and a review re-runs the script.

### 2026-10-10 — Why the Workflow arm used more tokens (API dumps, smoke tier)

The job's API dumps were grouped into conversations (main session, each
Workflow helper, each bash-step `claude`, each reviewer). Requests and
responses have unrelated IDs, so each response was matched through the next
request that carries it. The script is
`var/benchmarks/strat-workflow/scripts/conv_breakdown.py`, run inside the
dashboard pod with job names as arguments. All five passing runs were
compared by role.

**Per run, cache read (M), S1 Workflow ×3 vs S2 bash ×2:**

| Role | S1 | S2 |
| --- | --- | --- |
| refine (the skill's work) | 1.32 / 1.67 / 1.27 | 0.98 / 0.99 |
| scorer | 0.81 / 0.32 / 0.33 | 0.18 / 0.32 |
| orchestrating the review | 0.46 / 0.38 / 0.43 | 1.25 / 0.84 |
| reviewer: architecture | **2.98 / 1.69 / 1.63** | 0.28 / 0.80 |
| reviewer: feasibility | **1.88 / 0.78 / 1.67** | 0.57 / 0.52 |
| reviewers: testability + scope | 0.49 / 0.31 / 0.37 | 0.22 / 0.27 |
| Workflow plumbing (state, record, push, check, orchestrator) | 0.19 / 0.15 / 0.35 | – |

**What the dumps show:**
- **Most of the gap is the architecture and feasibility reviewers.** In S1
  they run more turns (architecture: 15–42 calls against 6–11), and every
  turn re-reads its growing context.
- **Refine is also consistently dearer** in S1.
- **Orchestrating the review is cheaper** in S1: the Workflow does that
  coordination instead of an agent.
- **Plumbing is small:** 0.15–0.35M per run.

**What's the same in both designs:** the reviewers' system prompt (identical
once paths are normalised), their task prompt (the same skill), the model,
adaptive thinking, `effort: high`, and nearly the same tool list (S1 has
`StructuredOutput` where S2 has `Agent`; neither has `Glob`). Tool calls
per turn are about the same too: S1 2.0, S2 2.3. So the extra turns aren't
a batching or configuration difference.

**Friction seen in S1's reviewers:**
- **Missing `Glob`:** the skill tells them to use `Glob`, which isn't in
  either session. S1 tried it 6 times in one architecture review; S2 didn't.
- **Different working directory:** the Workflow's agents start outside the
  strat-creator checkout, so relative `Read`s failed ("your current working
  directory is …"), and the agents explored with `ls`/`cat` first.
- **Small share:** these errors are 9 of 115 tool calls in that review, so
  they explain only part of the extra turns.

**Still open:**
- Why S1's refine and reviewers take more turns beyond that friction. It
  may be how the Workflow phrases each helper's task around the skill
  (record commands, structured return), or just run-to-run variation; three
  and two runs are too few to separate the two.
- strace (time per process) and MLflow (main sessions only) haven't been
  analysed yet.

### 2026-10-10 — Where the wall time goes (strace and API dumps, smoke tier)

**Scripts**, both in `var/benchmarks/strat-workflow/scripts/` and run inside
the dashboard pod with job names as arguments:
- **`strace_timing.py`:** builds each job's process tree from
  `strace -ff` and splits every `claude` process's wall time into "model
  call in flight" (from API dump timestamps), "tools running" (its child
  processes) and neither.
- **`concurrency.py`:** counts model calls in flight over time (+1 per
  request dump, −1 per response dump; the two can't be paired).

**One run of each, split:**

| | Claude wall | Model in flight | Tools running | Neither |
| --- | --- | --- | --- | --- |
| S1, its one `claude` | 17.6m | 17.0m | 37s | 8s |
| S2 create / refine / review | 1.0m / 2.7m / 10.8m | 46s / 2.5m / 10.5m | 13s / 11s / 25s | 3s / 1s / 4s |

**Across the five passing runs:**
- **Model calls run one at a time:** average concurrency 1.00 in every
  run of both designs, peak 2 for an instant.
- **Not a relay limit:** PR #83's Workflow parallelises across strategies
  (`parallel()` for refine, `pipeline()` for score then review), but within
  one strategy every step is sequential. The four reviewers run inside the
  review skill one after another, in both designs. With one RFE there's
  nothing to run in parallel.
- **About 8 seconds per call in both:** S1 7.5–8.1s, S2 8.2–9.1s. Wall
  time is roughly calls × 8s. S1 makes 126–181 calls against S2's 88–90,
  which explains its extra 3–10 minutes.
- **Tools and setup barely register:**
  - tool processes total under a minute per run;
  - S2's `run-claude.sh` sleeps 7s after each step (21s);
  - MLflow's stop hook takes about 7s per `claude` session (S2 has three
    sessions, S1 one);
  - S2 also runs its own OTel collector for the whole job.

**Conclusion so far:** on one RFE the Workflow design is slower and dearer
for the same reason: its helpers and reviewers take more model turns (see
"Why the Workflow arm used more tokens"). Its parallelism only helps with
several RFEs, which tier 2's batches will test. They will also show
whether Model Relay or the account serialises concurrent calls.

### 2026-10-10 — What each run read (strace opens against model requests, smoke tier)

**Script:** `var/benchmarks/strat-workflow/scripts/file_reads.py`, run
inside the dashboard pod as `python3 - [--compact] <job>...`. For every
successful read-only `openat` in a job's strace, it records the file and
who opened it:
- **"claude":** Claude Code's in-process Read/Grep/Glob tools;
- **otherwise the command**, such as `cat`, `grep` or `python3 <script>`.

Paths are normalised to `<repo>/…`. Directories, `.git` and system and
library files are dropped. Next to the opens it counts what the model asked
for in the API dumps: Read calls plus Bash commands naming the file.

| Run | Model calls | File requests by the model | Opens by Claude Code | Architecture docs opens / requests | Artifacts opens / requests |
| --- | --- | --- | --- | --- | --- |
| S1 r1 | 181 | 209 | 3476 | 743 / 86 | 465 / 95 |
| S1 r2 | 126 | 123 | 3099 | 483 / 35 | 319 / 65 |
| S1 r3 | 152 | 139 | 2778 | 403 / 27 | 380 / 84 |
| S2 r1 | 90 | 123 | 2568 | 312 / 43 | 260 / 67 |
| S2 r3 | 88 | 82 | 2985 | 257 / 14 | 248 / 55 |

**What it shows:**
- **S1's model asks for more files:** about 157 requests per run against
  about 103. Mostly architecture docs and the run's own artifacts.
- **The strategy file is re-read heavily in both designs:** 25 requests
  in one run of each, because every agent (create, refine, scorer, review
  and four reviewers) reads it afresh.
- **Raw opens are dominated by two things that don't depend on the
  model:**
  - Grep sweeps of the architecture context, about 1,800–2,000 files once
    each, hidden `.discovery` and `.analyzer` folders included, in both
    designs;
  - Claude Code's own housekeeping: `.claude/settings.json` 43–55 opens
    and the `.claude` folder about 130 per run.

  So opens per request (16–36) isn't a useful measure.
- **strace can't separate S1's agents.** They all run inside one `claude`
  process, so attributing reads to an agent needs the API dumps
  (`conv_breakdown.py`). In S2 each step is its own process.

**Correction:** an earlier note in this log, based on one run of each
design, said both asked for about the same files (123). Across all five
runs S1 asks for about 50% more.

### 2026-10-10 — Architecture docs re-requested, per agent (API dumps, smoke tier)

**Script:** `var/benchmarks/strat-workflow/scripts/arch_requests.py`, run
inside the dashboard pod with job names. It rebuilds each agent's
conversation and collects its architecture-context requests:
- Read calls;
- Bash commands naming context files (bare names resolved against the
  folder the command `cd`s into);
- Grep and Glob calls over the context.

**Requests per run, by agent:**

| Agent | S1 (Workflow) | S2 (bash) |
| --- | --- | --- |
| refine | ~36 | ~36 |
| architecture reviewer | **~95** | ~40 |
| feasibility reviewer | **~68** | ~21 |
| scorer | ~10 | ~12 |
| testability + scope | ~5 | ~3 |

**Most re-requested within a single agent (S1, max in one agent):**
- architecture reviewer: `kserve.md` 22, `odh-model-controller.md` 16,
  `odh-observability.md` 10;
- feasibility reviewer: `odh-observability.md` 15, `kserve.md` 13,
  overlay `0014-model-runtimes-team-architecture.md` 13.

S2's highest is 8 (`kserve.md`, architecture reviewer).

**How the requests were made** (all runs): mostly separate `grep` calls
against the same few docs, one term per tool call.

| Agent | S1 (3 runs) | S2 (2 runs) |
| --- | --- | --- |
| architecture reviewer | 147 grep, 124 Read | 30 grep, 48 Read |
| feasibility reviewer | 145 grep, 26 sed/head, 22 cat, 12 Read | 28 grep, 8 cat, 4 sed/head, 2 Read |

**The same docs fetched independently by several agents in one run**
happens in both designs:
- S1: `kserve.md` by 3–5 agents, `odh-model-controller.md` by 4,
  `odh-observability.md` by 3–5, `PLATFORM.md` by 3, in every run;
- S2: `LATEST_VERSION` by 4, overlay 0023 by 3–4, `PLATFORM.md` and
  `odh-observability.md` by 3.

Every agent starts cold and rediscovers the same platform facts.

**Reading:** the extra cost of S1 found earlier is concentrated in two
reviewers searching the same few architecture docs term by term. Refine
behaves the same in both designs. The cause isn't settled:
- the reviewers' prompts, model and settings are identical in both
  designs (see the token analysis above);
- S1's agents start outside the checkout and keep reaching for tools
  they don't have;
- three and two runs leave room for run-to-run variation.

**A possible change for strat-creator, not for this eval:** give
reviewers a shared digest of the relevant architecture facts, built once
per strategy, rather than each agent searching the docs from scratch.

### 2026-10-10 — The architecture-context fix, applied to both designs

**What changed:** one commit, identical on both designs, in the github.local
strat-creator copy (author `strat-workflow-eval`). It changes
`scripts/fetch-architecture-context.sh`, the one file behind the
entrypoint, `pre-strategy.sh` and the review skill (which reaches it
through `.claude/skills/strategy-common/scripts`).
- **`eval/pr-80`:** `c6fc331` → **`0287b83`**.
- **`eval/pr-83`** (new): PR #83 `6b78355` plus the fix → **`1bd7f17`**.
  Until now S1 ran PR #83 unchanged.

**What the fix does:**
- `STRAT_ARCHITECTURE_CONTEXT_PATH`, when set, is used on every call,
  including the review skill's call with no argument.
- The update path only runs git in a directory that is a clone of its
  own; a copied snapshot is replaced with a fresh clone.

**Tested** in a throwaway repo:
- **The old script:** run with no argument after a copy, it deleted
  `config/` and set `core.sparseCheckout` on the enclosing repo.
- **The patched script (both branches):** re-copied the pinned snapshot
  when the variable was set, cloned properly when it wasn't, and left the
  enclosing repo intact.

`vars/arms.yaml` now pins both designs to the new commits. The haiku smoke
tier is re-run on them before the opus tier, so the comparison stays like
for like.

### 2026-10-10 — Re-run: why the first S1 run took 21+ minutes

S1 round 1 of `markov-run-41e56ed5` did a normal amount of work: 125 calls,
4.53M cache read and 191k output. Generation speed was normal too, about
210–220 tokens/s while generating. The extra time:
- **Two relay timeouts:** two calls failed at exactly 120 seconds in Model
  Relay and were retried, about 4 minutes lost. Relay's upstream timeout
  defaults to 120s (`SHIM_UPSTREAM_TIMEOUT_SECONDS`, not set in our
  deployment). Recorded as a bug
  (`.ledger/bugs/fixed/model-relay-120s-upstream-timeout.md`).
- **A few heavy thinking turns:** one took 97s for 23k output tokens (17k
  thinking), and others 30–50s.

**Before the opus tier:** raise the relay timeout (opus turns run longer),
and check every run for 120s failures. The first smoke run's times may
include such stalls too; its relay records weren't checked.

**Evidence loss:** each Markov run's `wipe_at_start` clears the artifacts
volume, so this re-run deleted the first smoke run's API dumps, strace and
summary files. The analyses of that run are recorded in this log, and its
eval-results are still in markovd's run state, but its raw data is gone.
**Before the next run:** set `wipe_at_start: false` and keep earlier runs'
artifacts, or archive them first.

### 2026-10-10 — Smoke re-run on the architecture-context fix (markov-run-41e56ed5)

Driven through markovd, 18:04–19:50 UTC, with both designs on the fixed
commits (`eval/pr-83` `1bd7f17`, `eval/pr-80` `0287b83`), haiku-5-5. The
summary is in `/app/artifacts/benchmarks/strat-workflow/markov-run-41e56ed5/`.

| Run | Pass | Verdict | Minutes | Calls | Output | Cache read | Cache write |
| --- | --- | --- | --- | --- | --- | --- | --- |
| S1 r1 (Workflow) | yes | revise 4/8 | 22.8 | 138 | 197k | 4.86M | 745k |
| S2 r1 (bash) | yes | revise 4/8 | 13.1 | 97 | 152k | 4.42M | 550k |
| S1 r2 | yes | revise 4/8 | 25.4 | 159 | 320k | 6.94M | 1.26M |
| S2 r2 | yes | revise 4/8 | 13.5 | 92 | 158k | 4.45M | 651k |
| S1 r3 | yes | revise 4/8 | 17.1 | 123 | 215k | 4.82M | 777k |
| S2 r3 | yes | revise 4/8 | 13.3 | 73 | 159k | 3.43M | 611k |

**6/6 passed.** Every run gave the same verdict, revise 4/8. There were no 429s.

**The fix worked** (strace of all six jobs):
- In five of six runs the review skill ran `fetch-architecture-context.sh`
  without an argument, and the script fell back to the pinned snapshot
  (`/app/.context/snapshots/architecture-context/7d61f09…`).
- No job ran `git sparse-checkout` or cloned the architecture context from
  GitHub. The only `git clone` was S2's results repository.
- So the S2 r2 failure mode of the first run is gone, and every run reviewed
  against the same snapshot.

**Against the first smoke run (`9d30a751`):**

| | S1 before → after | S2 before → after |
| --- | --- | --- |
| Passed | 3/3 → 3/3 | 2/3 → 3/3 |
| Median minutes | 20.0 → 22.8 | 14.4 → 13.3 |
| Mean calls | 153 → 140 | 89 → 87 |
| Mean output | 256k → 244k | ~175k → 156k |
| Mean cache read | 6.74M → 5.54M | ~3.9M → 4.10M |

The gap is the same within the noise of three runs. S1 makes about 1.6×
the calls of S2 and takes 1.3–1.9× as long.

**Relay timeouts:** two calls failed at exactly 120 s, both in S1 r1
(18:14 and 18:22). strace shows them: S1 r1's `claude` spent 3.9 minutes
with neither a model call nor a tool running, against 4–10 s in the other
runs. Without them S1 r1 would have taken about 19 minutes. One more call
took 104 s (S1 r2), close to the limit. Relay telemetry also had five
records stuck at `in_progress`: their final record was dropped
(see the telemetry drop bug).

**Timing** (`strace_timing.py`, `concurrency.py`): unchanged. Model calls
run one at a time (average concurrency 1.00–1.08, peak 2), at 7–10 s per
call. Tools take under a minute per run.

**Where S1's extra calls go** (`conv_breakdown.py`, mean per run, S1 vs S2):

| Agent | S1 | S2 | Difference |
| --- | --- | --- | --- |
| Workflow orchestration (main, state read, record-refine, push, check) | ~17 | – | +17 |
| feasibility reviewer | 27.0 | 9.7 | +17 |
| architecture reviewer | 18.7 | 11.3 | +7 |
| testability + scope reviewers | 17.7 | 11.0 | +7 |
| refine | 22.0 | 19.0 | +3 |
| scorer | 10.7 | 8.7 | +2 |
| create | 11.3 | 10.3 | +1 |
| review wrapper | 16.0 | 17.3 | −1 |

- About a third of the gap is structural: the Workflow's own sessions that
  read and record pipeline state, which the bash design does in shell.
- Most of the rest is the reviewers again. The feasibility reviewer is the
  largest: 31–42 Bash calls in S1 against 8–11 in S2.
- One outlier: S1 r2's architecture reviewer made 114 Read calls, reached
  193k context and wrote 508k cache. That alone explains most of r2's
  25 minutes.

**Architecture-doc requests** (`arch_requests.py`, per run): architecture
reviewer 88 in S1 vs 42 in S2, feasibility 72 vs 26, refine 45 vs 32.
- This is the same pattern as before the fix, so the architecture-context
  bug didn't cause it.
- The same docs top the list: `kserve.md`, `odh-model-controller.md`,
  `odh-observability.md` and overlay 0014.
- Every run in both designs had 3–6 agents fetching the same docs
  independently.
- How the requests were made:
  - S1's feasibility reviewer: 154 `grep` calls over three runs, against
    52 in S2;
  - S1's architecture reviewer: 173 Reads, against 45.

**Open question:** why the same reviewer prompts search two to three times
more in the Workflow arm. Candidates:
- the reviewers run as Workflow agents rather than as the review skill's
  subagents;
- they start in a different working directory;
- they get a different tool set.

Comparing the first few turns of one reviewer in each design would show
which.

### 2026-10-10 — Every tool call, from the API dumps; S1 loses reviewer output

**MLflow can't count tool calls.** Each trace covers only a `claude`
process's top-level conversation, not its sub-agents.
- S1: two traces per run, with 4–5 tool calls in total (the `Workflow`
  call plus a few Bash), out of 193–292.
- S2: one trace per step (round 1 is missing one), 22–33 tool calls, out of
  117–126. The reviewers are missing because they run as forked skills.

**Script:** `var/benchmarks/strat-workflow/scripts/tool_calls.py`, run
inside the dashboard pod; `--jsonl` gives one record per call. It records
each call's agent, turn, time, tool, input, error flag and result head:
- the `tool_use` blocks come from the assistant turns that later requests
  carry;
- `tool_result` comes from the next user turn;
- a conversation's last response, which nothing carries, answers the
  latest open request.

Attributing that last response to whoever asked most recently, as
`conv_breakdown.py` and `arch_requests.py` do, misplaced final calls when
another agent started in between. Their per-agent numbers above are close,
but not exact, for that reason.

**Tool calls per run:**
- S1: 208, 292, 193;
- S2: 118, 123, 126;
- errors: 6–10 per S1 run, 3–5 per S2 run, mostly `Glob` "not available"
  in both, and `ls` on paths that don't exist.

**Finding: S1's reviewers return no review, and get re-run.**
- S1 runs the review skill inside a Workflow agent whose result has a
  schema. Every request in that agent and its forked skills offers
  `StructuredOutput`. Every S1 reviewer request lists 10 tools,
  `StructuredOutput` among them.
- A reviewer that finishes by calling `StructuredOutput` (with only
  `{key, recommendation, needs_attention}`) instead of writing its review as
  text returns nothing but "Skill execution completed" to the review agent.
- **Counts:**
  - S1: 15 empty reviewer results in 3 runs, matching 15 reviewer
    `StructuredOutput` calls exactly (feasibility 7, testability 3, scope 3,
    architecture 2);
  - S2: none of either.
- **The review agent re-launches the empty reviewers:** 22 reviewer
  launches in S1 against the 12 needed (10 reruns). S2 launched exactly 12.
  - Feasibility never returned text in any S1 run;
  - in round 1, testability and scope didn't either.
- **Then the review agent writes the missing sections itself.** In S1 r2
  and r3 it appended `## Feasibility Review` to the review file with
  `cat >>`. In r1 it used an Edit. The posted review then contains reviewer
  sections that no reviewer returned, and the eval's checks (one comment,
  verdict matches label) can't see that.
- **This explains much of S1's extra cost:** the reruns, and the repeated
  architecture-doc reads within one "agent". Identical reruns share a
  conversation key, so S1 r2's "114 Reads" architecture reviewer was three
  launches, re-reading the same docs (`kserve.md`, `PLATFORM.md` and
  others 3×).
  - Identical repeated calls per run: S1's architecture reviewer 22,
    feasibility 3, and the review agent's skill relaunches 3.
  - S2: none.

**Consequences:**
- **A PR #83 defect, independent of model.** Forked skills inside a schema
  Workflow agent inherit `StructuredOutput`.
- **Possible fixes on the strat-creator side:**
  - run the review skill's reviewers with no schema;
  - have reviewers write to files that the review step reads;
  - or tell reviewers not to use `StructuredOutput`.
- **For the eval:** add a check that every reviewer section in the posted
  review came from a reviewer's own output (or a file it wrote), and count
  reviewer reruns.

## Smoke on opus 4.6 (markov-run-f2f3b733, S2 r3 re-run as markov-run-5884ad2a)

Both designs on `claude-opus-4-6`, 3 rounds, at the same commit as the
haiku re-run (`4648532`), `wipe_at_start=false`, so the haiku evidence was
kept. The relay had the telemetry fix and `SHIM_UPSTREAM_TIMEOUT_SECONDS=600`
deployed first.

**S2 round 3 was re-run.** The first attempt
(`…opus-4-1011-020151-d0246c`) hit the Claude account's usage limit after
about 610 opus calls: two 429s, "This request would exceed your account's
rate limit", at 02:11:36. Claude Code doesn't retry that error, so the job
failed after 10 minutes. It was re-run alone after the limit reset
(`…opus-4-1011-042540-5f963f`), same commit and seed, and replaces the
failed attempt below. `markov-run-f2f3b733`'s own `summary.md` still lists
it as failed.

**Results:** 6/6 passed.

| | Haiku S1 | Haiku S2 | Opus S1 | Opus S2 |
| --- | --- | --- | --- | --- |
| Minutes, r1/r2/r3 | 22.8 / 25.4 / 17.1 | 13.1 / 13.5 / 13.3 | 24.6 / 27.5 / 28.8 | 24.0 / 33.8 / 37.6 |
| Same, less 120 s cuts (approx.) | 18.8 / 25.4 / 17.1 | same | 24.6 / 25.5 / 24.8 | 24.0 / 25.8 / 25.6 |
| Model calls | 138 / 159 / 123 | 97 / 92 / 73 | 108 / 105 / 105 | 86 / 88 / 99 |
| Tool calls | 208 / 292 / 193 | 118 / 123 / 126 | 179 / 191 / 177 | 144 / 165 / 167 |
| Output tokens | 197k / 320k / 215k | 152k / 158k / 159k | 61k / 65k / 62k | 60k / 64k / 62k |
| Verdict | revise 4/8 ×3 | revise 4/8 ×3 | approve 6, 6, 7 | revise 5, approve 7, approve 6 |
| Empty reviewer results | 15 of 22 launches | 0 | 12 of 12 | 0 |
| Reviewer reruns | 10 | 0 | 0 | 0 |

**Timing:**
- **Concurrency is still 1.0** in every job, opus and haiku.
- **Opus calls are about twice as slow.** The median is 6–8 s against 3 s on
  haiku, and up to 120 s for long writes. Opus writes 3–5× fewer output
  tokens.
- **Subtracting 120 s per cut gives approximately 25 minutes for both
  designs on opus.** This is a heuristic adjustment, not a measured
  fixed-relay runtime or evidence of timing equivalence. Haiku's S1
  overhead included reviewer reruns; opus does none.

**The relay still cut streams at 120 s.**
- The 600 s setting only reaches the environment-configured upstream.
- Managed accounts are hard-coded to 120 s. See
  `.ledger/bugs/fixed/model-relay-120s-upstream-timeout.md`. The earlier
  `59d6f06` fix missed this constructor; the complete repair was deployed
  later on 2026-10-11 and verified in `markov-run-c5ba3904`.
- 13 calls were cut after 2 minutes and retried:
  - S1: 0, 1, 2 per round;
  - S2: 0, 4, 6 per round.
- **The cuts hit whichever agent writes about 5k output tokens in one
  turn:** the scorer, the reviewers, or refine. Both designs have those
  agents. This small sample does not establish whether S2's larger share
  reflects chance or differences in timeout exposure. S2 r3's architecture
  reviewer was cut four times on the same request.
- The haiku re-run's two cuts (S1 r1) had the same cause.

**S1 reviewers on opus: every one ends on `StructuredOutput`.**
- All 12 reviewer launches (4 per run) called `StructuredOutput` with
  `{key, recommendation, needs_attention}` and returned no text. S1's
  forked refine skill did the same in all 3 runs. Refine writes its result
  to the strategy file, so that one is harmless.
- **Haiku did this 15 times in 22 launches; opus every time.** Opus follows
  the inherited tool's "MUST call this tool exactly once" more consistently,
  as expected.
- **Opus never reruns the empty reviewers.** After the four empty results,
  the S1 review agent:
  - reads 3–4 architecture docs itself (`kserve.md`,
    `odh-model-controller.md`, `odh-observability.md`, and `PLATFORM.md` in
    r3);
  - then writes all four reviewer sections, plus agreements and
    disagreements, in one Edit (1.5 min).
- **So every posted S1 opus review is the review agent's work, not the
  reviewers'.** Section sizes are similar to S2's (2–5k characters each),
  so nothing in the output shows it.
- **Reviewer conclusions are lost.** In S1 r2 the feasibility and
  testability reviewers concluded `revise, needs_attention: true` in their
  `StructuredOutput`. The posted review says approve, with no mention of
  their concerns.
- **The verdict is unaffected:** it comes from the scorer
  (`apply_scores.py`), which runs before the reviewers in both designs.
- **S2** reviewers returned their reviews as text in all three runs.

**Verdicts:** opus scored 5–7/8 where haiku scored 4/8 in all six runs. The
scorer and the strategy writer both changed model, so this doesn't say
which got better. Cross-scoring (the haiku scorer on opus strategies, and
the other way round) would separate them.

**Analysis fixes made for this run:**
- `tool_calls.py` strips `<system-reminder>` blocks before checking for an
  empty skill result. Before, it missed empty results that had a reminder
  appended. The haiku counts didn't change.
- `concurrency.py` and `strace_timing.py` count only requests that
  `index.jsonl` pairs with a response. A cut stream leaves a request with no
  response, which made the counter stay above zero, showing false 2–3×
  concurrency and "model 0 s, neither 27 min".
- `strace_timing.py` handles jobs that cross midnight UTC. strace times
  have no date, so S1 r1 had a negative wall time.
- `index.jsonl` in each API dump directory pairs every request file with
  its response file. `conv_breakdown.py` and `arch_requests.py` could use it
  in place of their time-order heuristics.

**Opus S1 vs S2: tool calls, file reads, tokens (mean per run)**

| | S1 (Workflow) | S2 (bash) |
| --- | --- | --- |
| Model calls | 106 | 91 |
| Tool calls | 182 | 159 |
| Output tokens | 62.7k | 62.3k |
| Cache read | 3.63M | 4.02M |
| Cache write | 569k | 588k |
| Architecture docs the model asked for | 37 | 38 |
| Strategy/review artifacts asked for | 31 | 32 |

- **Tokens are a wash.** S1's extra calls are its orchestration: about
  18 calls of workflow plumbing, which `conv_breakdown.py` lumps in with
  S1's forked refine at 36 calls and 1.45M cache read. That roughly
  balances S2's three separate `claude` processes, each re-reading its own
  context: S2's refine alone is 1.34M cache read.
- **The S1 reviewers' tokens buy nothing.** They spend 25 calls, 23k output
  and 0.76M cache read per run, and none of it reaches the posted review.
  The review agent then spends 10 more calls rewriting the reviews: 37
  calls against S2's 27, including 11 architecture-doc reads.
- **File opens are noise.** Totals range from 1.4k to 9.4k per job. The
  architecture-context Grep sweeps dominate them: about 1,844 opens per
  sweep, 0–4 sweeps per run, set by how the scorer searches, not by
  design. The files the model asked for are the same in both designs.

**Opus S1 vs S2: statistics (n = 3 per design, S2 r3 = the re-run)**

| Metric | S1 mean ± sd (range) | S2 mean ± sd (range) | S2 − S1 | Cohen's d | Welch p | 95% CI of the difference | Mann–Whitney p |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Wall minutes | 27.0 ± 2.2 (24.6–28.8) | 31.8 ± 7.0 (24.0–37.6) | +4.8 | 0.93 | 0.36 | −10.9 … +20.6 | 0.70 |
| Wall minutes, less 120 s cuts | 25.0 ± 0.5 (24.6–25.5) | 25.1 ± 1.0 (24.0–25.8) | +0.2 | 0.22 | 0.81 | −1.9 … +2.2 | 0.70 |
| Model calls | 106.0 ± 1.7 (105–108) | 91.0 ± 7.0 (86–99) | −15.0 | −2.94 | 0.058 | −31.2 … +1.2 | 0.10 |
| Tool calls | 182.3 ± 7.6 (177–191) | 158.7 ± 12.7 (144–167) | −23.7 | −2.26 | 0.064 | −49.7 … +2.4 | 0.10 |
| Tool errors | 6.0 ± 2.6 (3–8) | 6.0 ± 2.6 (3–8) | 0 | 0 | 1.00 | −6 … +6 | 1.00 |
| Output tokens (k) | 62.8 ± 2.1 | 61.8 ± 1.9 | −0.9 | −0.46 | 0.60 | −5.5 … +3.7 | 1.00 |
| Cache read (M tokens) | 3.63 ± 0.20 | 4.02 ± 0.36 | +0.39 | 1.36 | 0.19 | −0.34 … +1.11 | 0.20 |
| Cache write (k tokens) | 570 ± 55 | 589 ± 41 | +18 | 0.38 | 0.67 | −95 … +132 | 1.00 |
| Score out of 8 | 6.3 ± 0.6 (6, 6, 7) | 6.0 ± 1.0 (5, 7, 6) | −0.3 | −0.41 | 0.65 | −2.4 … +1.7 | 1.00 |
| Median call latency (s) | 6.7 ± 0.7 | 7.9 ± 0.4 | +1.3 | 2.42 | 0.057 | −0.1 … +2.6 | 0.10 |
| 120 s stream cuts | 1.0 ± 1.0 (0–2) | 3.3 ± 3.1 (0–6) | +2.3 | 1.03 | 0.32 | −4.5 … +9.1 | 0.50 |
| Architecture docs the model asked for | 37.3 ± 7.0 | 38.0 ± 6.2 | +0.7 | 0.10 | 0.91 | −14.5 … +15.8 | 1.00 |
| Reviewer outputs lost, of 4 | 4.0 ± 0 | 0.0 ± 0 | −4 | ∞ | – | – | 0.10 |

- **The tests:** Welch's t-test and its CI (scipy); the exact two-sided
  Mann–Whitney test, by enumeration. With n = 3 the Mann–Whitney p can't
  go below 0.10, so these flag differences worth watching, never confirm
  them.
- **The one clear result is the lost reviewer output.** Per launch it is
  12/12 against 0/12, Fisher exact p ≈ 7 × 10⁻⁷. It is a mechanism, not
  noise.
- **Model and tool calls lean towards S1 doing more** (p ≈ 0.06): its
  Workflow plumbing and the review agent's rewrite. That costs no time
  or tokens.
- **The latency lean is probably time of day:** S2's slowest run is the
  solo re-run at 04:25.
- **Raw wall time is confounded by unequal relay timeout exposure.** The
  approximate subtraction does not establish that the relay accounts for
  the entire difference.
- **Tokens, file reads, errors and scores** show no difference.
- **For conclusive timing and token comparisons,** run 4 or more per
  design (or more scenarios). 4 is the smallest n at which the
  Mann–Whitney test can reach p < 0.05 (minimum 0.029; 0.008 at n = 5).

## Reviewer output contract: same in both designs; S1 breaks it

Read from the pinned strat-creator commits (`1bd7f17` S1, `0287b83` S2).
All five review skills are identical in both. The only differences are
PR #83's `--scores-from` mode in `strategy-review` and the
architecture-context fetch script.

**The intended contract: reviewers return prose as text, and the
orchestrator writes the file.**
- **Each reviewer skill** (`strategy-{feasibility,testability,scope,architecture}-review`)
  is `context: fork` with `allowed-tools: Read, Grep, Glob`: read-only, no
  Write, Bash or `StructuredOutput`. Its `## Output` section is a markdown
  block (`### STRAT-NNN: <title>`, one bold field per dimension,
  `**Recommendation**: …`). Nothing asks it to write a file or return JSON.
- **`strategy-review`:**
  - Step 6 invokes the four reviewers with the Skill tool.
  - Step 7, "Write Prose to Review Files", fills
    `artifacts/strat-reviews/{id}-review.md` with "the prose from all four
    reviewers", plus Agreements and Disagreements.
  - It then sets `reviewers.*` from each reviewer's own verdict.
  - The orchestrator is the only writer, and it works only from what each
    fork returns.
- **PR #83's own smoke fixtures** (`tests/fixtures/workflow-smoke/skills/strategy-*-review/SKILL.md`)
  also return text: "Reply with exactly these two lines…".
  `tests/test_strat_pipeline_workflow.py` checks only that the review file
  exists, not its content. The stubs also say "Do not use any tool". So
  PR #83's tests can't catch the defect.

**Where S1 departs.**
- **The schema:** `workflows/strat-pipeline.js` runs the review step as
  `agent(…, { schema: VERDICT })`, with
  `VERDICT = {key, recommendation, needs_attention}`. That is the review
  step's own answer, the output of `record-review`.
- **The leak:** Claude Code also offers the matching `StructuredOutput` tool
  inside the forked reviewer skills, with "You MUST call this tool exactly
  once at the end".
- **The tool lists in the API dumps:**
  - S1 reviewer requests (haiku and opus): Bash, Edit, ListAgents, Read,
    ReportFindings, Skill, **StructuredOutput**, ToolSearch, Write.
  - S2: the same set with **Agent** in place of `StructuredOutput`.
- **The effect:** a reviewer that obeys ends its fork with JSON in place of
  its Output block, and Step 7 has no prose to write. Haiku obeyed in 15 of
  22 launches and opus in 12 of 12. Haiku then reran the reviewers, and
  opus wrote the reviews itself.
- **This is a leak from the Workflow into a skill with its own output
  contract,** not intended behaviour in either design.

**Skill settings that neither design honours:**
- **`allowed-tools` doesn't restrict.** Reviewers were offered Bash, Write
  and Edit, and used `ls` freely in both designs. In Claude Code it
  pre-approves the listed tools; it doesn't remove the others.
- **The reviewer skills' `model: opus` is ignored.** In the haiku runs,
  every reviewer request in both designs went to `claude-haiku-5-5`. So the
  haiku tier never had the opus reviewers the skills ask for. This affects
  haiku-versus-opus comparisons, not S1 versus S2.

**Fixes, for PR #83:**
1. **Drop the schema from the review step** (keep it elsewhere). Parse
   `record-review`'s JSON from the agent's plain-text reply.
2. **Or tell reviewers explicitly** not to call `StructuredOutput` and to end
   with their Output block as text. This is fragile: it relies on the model
   obeying it over the tool's "MUST".
3. **Or have reviewers write their blocks to files** that Step 7 reads. This
   changes the skill contract for both designs.

Whichever fix is chosen, PR #83's smoke test should assert that the posted
review contains each stub reviewer's line (`feasibility review of KEY`, and
so on).

## Did the haiku runs predict the opus outcomes?

Haiku was used to set the benchmark up. It was a good shakedown, but a poor
proxy for the S1-versus-S2 comparison: its large S1 overhead turned out to
be haiku-specific.

| Question | Haiku (markov-run-41e56ed5) | Opus (markov-run-f2f3b733 + 5884ad2a) | Predicted? |
| --- | --- | --- | --- |
| Both designs complete and pass the checks | 6/6 | 6/6 | Yes |
| S1 loses reviewer output | 15 of 22 reviewer launches empty | 12 of 12 | Yes: found the defect, but understated how severe it is |
| What S1 does about it | Reruns the reviewers (10 reruns) | Review agent writes the reviews itself; no reruns | No |
| Wall time, S1 vs S2 (mean) | 21.8 vs 13.3 min (S1 1.6× slower) | ~25 vs ~25 min less the relay cuts | No: the gap was haiku's reruns |
| Model calls, S1 vs S2 | 140 vs 87 (+60%) | 106 vs 91 (+16%) | Direction right, size wrong |
| Tool calls, S1 vs S2 | 231 vs 122 (1.9×) | 182 vs 159 (1.15×) | Direction right, size wrong |
| Output tokens, S1 vs S2 | 244k vs 156k | 63k vs 62k | No |
| Score / verdict | revise 4/8 in all 6 runs | 5–7/8 | No: zero variance, nothing to compare |
| Concurrency | 1.0 | 1.0 | Yes |
| Relay 120 s cuts | 2 cuts; bug filed predicting opus would exceed 120 s | 13 cuts | The risk, yes. But haiku rarely writes long enough to show the 600 s fix didn't reach managed accounts |
| Account usage limit | No sign of it | 429s after ~610 opus calls | No |

**What haiku was good for:**
- **Validating the harness:** seeding, submission, the checks, evidence
  capture (API dumps, strace, MLflow), and the analysis scripts.
- **Finding problems cheaply,** at 13–25 minutes a run:
  - the architecture-context fetch bug;
  - the relay telemetry drops and the console that never moved past the
    oldest requests;
  - the 120 s timeout;
  - the reviewer `StructuredOutput` defect.

  All of them carried over to opus.
- **Showing which way the effects go:** S1 makes more calls and loses
  reviewer output. Both held on opus.

**Where haiku misled:**
- **What a model does after a failure is model-specific.** The defect is
  the same, but the cost differs. Haiku's numbers said "S1 is 60% slower";
  the real problem is that S1's posted reviews aren't the reviewers'. Opus
  hides that better, which is worse.
- **No quality signal.** Every haiku run scored 4/8, which separates
  neither designs nor runs. The reviewer skills' `model: opus` was ignored,
  so the haiku runs didn't use the reviewers the skills intend.
- **Opus-only infrastructure limits:** long single turns that hit the 120 s
  cut, and the account usage limit.

**For future tiers:**
- Use haiku to shake out the harness and find mechanisms. Don't use it to
  measure time, cost or quality differences between designs.
- When haiku surfaces a defect, check how each model behaves *after* the
  failure, not only whether it happens.
- Run one short round on the target model early. It would have caught the
  timeout and usage-limit problems before a full tier, for about one
  round of calls.

## How much confidence do 3 runs buy? Control flow vs handoffs

**Cost of the opus A/B test** (3 runs per design, failed attempt excluded):
- Job time 2 h 56 min (S1 80.9 min, S2 95.3 min); about 26 min of it was
  relay 120 s cuts.
- Tokens: 591 calls, 3.48M cache write, 22.94M cache read, 374k output.
- **$42.54 at Opus 4.6 list prices** (platform.claude.com pricing:
  $5/M input, $6.25/M 5-minute cache write, $0.50/M cache read, $25/M
  output):
  - S1 $20.84, S2 $21.70, about $7 per run;
  - all cache writes were 5-minute, and all calls ran `inference_geo:
    global` on the standard tier, so no multipliers apply.
- The haiku A/B test would have cost $2.77 at Haiku 5.5 rates.

**Statistical power at n = 3 per design.** A two-sample test with 80% power
at p < 0.05 detects only differences of about 3 sd. S2 is not
deterministic: every step is an agent, and S2 varied more than S1 (wall
time sd 7.0 vs 2.2 min, model calls sd 7.0 vs 1.7).

| Question | Detectable with 3 per design | Runs per design needed |
| --- | --- | --- |
| S1 loses reviewer output | Settled: 12/12 vs 0/12 (P = 0.0002 even if the true rate were 50%) | 3 |
| Cost per run (sd $0.43) | Only a gap of $1.33 or more (~19%) | ~8 for 10%; ~25 for 5% |
| Wall time, relay fixed (sd 0.8 min) | Only a gap of 2.4 min or more | 3 for 2.5 min; ~8 for 1.25 min |
| Wall time, with cuts (sd 5.2 min) | Only a gap of 16 min or more | ~18 for 5 min; ~69 for 2.5 min |
| Model calls (sd 5.1) | Only a gap of 16 or more | ~6 for 10; ~18 for 5 |
| Quality score (sd 0.8 of 8) | Only a gap of 2.5 points or more | ~12 for 1 point; ~43 for 0.5 |
| Reliability | 3/3 passes bounds the pass rate at ≥ 37% | 10/10 → ≥ 74%, 30/30 → ≥ 90%, 60/60 → ≥ 95% |

- Fixing the relay cuts does more for timing than extra runs: at the same
  2.5-minute sensitivity it takes the runs needed from ~69 per design to 3.
- The single scenario (one RFE) limits generalisation more than the
  repeat count does. For cost and quality, use 4–5 RFEs × 2 designs × 2
  repeats, analysed as pairs.

**S1's control flow is deterministic too; its handoffs are not.**
- **The control flow:** `workflows/strat-pipeline.js` is plain JavaScript
  (branches, loops, `parallel`/`pipeline`, failure handling).
- **The handoffs:** every value it branches on is first read and
  transcribed by a model. S2 runs the same scripts directly and reads
  their output and exit codes.

| Handoff | S2 (bash) | S1 (Workflow) |
| --- | --- | --- |
| Read the run's input state | Runs `strat_pipeline_state.py read` | An agent is told to "run … `read` once and return the JSON it prints, field for field" (`schema: READ`, `effort: low`) |
| Record create, refine, review | Script exit code and files | An agent runs `record-create` / `mark refine` / `record-review` and relays the output through `StructuredOutput` |
| Push to Jira | Runs `push_refined_strategies.py` | An agent runs it once, checks the exit code, returns `{"recorded": "none"}` on failure |
| Final result | Script | An agent runs `result --failed …` and `fullsend-check-output`, then reports the exit status |

- **The extra surface:** both designs share the probabilistic work
  (create, refine, scorer, reviewers). S1 adds about 7 model-mediated
  handoffs per RFE for what is script execution in S2: the ~18 plumbing
  calls per run.
- **The reviewer defect comes from this mechanism.** The review handoff's
  `StructuredOutput` tool leaked into the forked reviewers.
- **What zero failures rules out:** S1's reliability is the product of its
  handoff success rates. Zero failures in n handoffs bounds the
  per-handoff failure rate at about 3/n (95%):

| Evidence | Per-handoff failure, upper bound | Per run (7 handoffs), upper bound |
| --- | --- | --- |
| 3 opus S1 runs (21 handoffs, none failed) | 13% | 63% |
| All 12 S1 runs, haiku and opus (84 handoffs) | 3.5% | 22% |
| 100 clean runs (700 handoffs) | 0.4% | 3% |

  A batch of 10 RFEs has ~33 handoffs per run, so the risk compounds.

**Measure reliability with the right instrument, not more A/B runs:**
1. **Test the handoffs on their own.** The read, push and result steps are
   `effort: low` agents running one script. Hundreds of isolated trials per
   model, at cents each, give transcription and schema failure rates
   directly. So does record-review with the full review step, where the
   defect was.
2. **Fault-inject `strat-pipeline.js` with stubs,** as PR #83's smoke test
   does: script failures, wrong keys, empty results. Assert the posted
   review's content, not just that the file exists. That tests S1's
   orchestration as deterministically as S2's bash.
3. **Keep full A/B runs for end-to-end cost, time and quality:** 8 or more
   per design, or a paired set across several RFEs.

**A design question for PR #83:** if Workflow scripts can run a command
directly, the read, push and result steps need no agent. That would remove
most of S1's extra probabilistic surface. Whether the Workflow API offers
this hasn't been checked.

## 2026-10-11 — Context growth: S1's primary session stays around 30k tokens

Reconstructed from existing evidence; no new benchmark runs. The primary
Claude session is the one that invokes `Workflow`. The JavaScript Workflow
coordinates its helper agents without a model conversation of its own.
Each helper and forked skill has a separate model conversation.

**Measurement:** each request's input context is
`input_tokens + cache_read_input_tokens + cache_creation_input_tokens`
from its response's usage. This includes system instructions, tool
definitions, message history and cached input. It is a per-request size,
not the sum of token usage across requests or the model's window capacity.
See [Anthropic's token accounting](https://platform.claude.com/docs/en/build-with-claude/prompt-caching#tracking-cache-performance).
The final completion is reported separately because there is no subsequent
request measuring the retained conversation after that completion.

**Attribution:** `index.jsonl` pairs each request with its actual response;
response IDs were validated. All conversations within each job share a
session ID, so that ID alone cannot separate agents. The analyzer groups
by system/task prompt and shared tool-use history, splitting identical
reviewer prompts when a new fork starts with a fresh history. The primary
is identified by its explicit Workflow invocation instructions. Requests
without indexed responses are counted separately, without inventing token
sizes. There are 738 indexed pairs across the six S1 smoke runs; the two
unindexed requests belong to a refine fork and a scope reviewer. None
belongs to a primary session.

### Opus: three S1 smoke runs

| Round (job suffix) | Primary calls | First input | Last/peak input | Net growth | First-to-last request span | Net tokens/minute |
| --- | --- | --- | --- | --- | --- | --- |
| 1 (`1010-234154-2647bf`) | 5 | 24,100 | 29,903 | 5,803 | 23.96 min | 242 |
| 2 (`1011-003101-159e0e`) | 6 | 24,103 | 30,311 | 6,208 | 26.93 min | 231 |
| 3 (`1011-013249-74e51a`) | 5 | 24,103 | 30,066 | 5,963 | 28.19 min | 212 |

The final replies add 241, 192 and 202 output tokens respectively. Last
input plus final output is therefore 30,144 / 30,503 / 30,268 tokens.
No primary input drops or compaction markers were found, and the three
job streams have **zero `compact_boundary` events**.

**Growth happens in bursts, not continuously with the pipeline's work:**

| Primary request | What has arrived | Input, round 1 | Input, round 2 | Input, round 3 |
| --- | --- | --- | --- | --- |
| 1 | Initial instructions and tool definitions | 24,100 | 24,103 | 24,103 |
| 2 | Workflow launch acknowledgement | 24,758 | 24,774 | 24,766 |
| 3 | Workflow completion notification | 25,621 | 25,589 | 25,586 |
| 4 | Read of Workflow task output and initial result-file check | 29,612 | 29,604 | 29,630 |
| 5 | Artifact/progress checks | 29,903 | 29,869 | 30,066 |
| 6 | Further progress-file check, round 2 only | — | 30,311 | — |

- Request 2 to request 3 spans **23.71 / 26.64 / 27.93 minutes** with
  no primary-agent model calls. The helpers do the pipeline work there.
- The completion notification is about 2,200 characters and carries
  `{"action":"completed","check_exit":0,"failed":[]}` plus diagnostics
  and paths. The primary does not receive the helpers' full conversations.
- All three primary sessions then read the Workflow's task output file
  (`tasks/<workflow-task-id>.output`). The Read result is about 9,970
  characters of Workflow state/logs. This transition adds **3,991 / 4,015 /
  4,044 tokens**, including the preceding assistant output and other tool
  results; that is roughly two-thirds of total net context growth.
- Net growth per request transition averages **1,451 / 1,242 / 1,491
  tokens**. The elapsed-time rates above mostly measure waiting, so they
  should not be extrapolated as a steady accumulation rate.

### The other windows are independent and much larger

Peak input tokens for opus S1:

| Conversation | Round 1 | Round 2 | Round 3 |
| --- | --- | --- | --- |
| Primary | 29,903 | 30,311 | 30,066 |
| Refine helper | 13,769 | 13,737 | 13,779 |
| Forked refine skill | 103,874 | 110,542 | 106,377 |
| Review helper | 81,173 | 47,357 | 57,958 |
| Feasibility reviewer | 107,810 | 74,672 | 77,228 |
| Architecture reviewer | 105,770 | 108,436 | 50,484 |
| Scorer | 44,472 | 80,179 | 54,978 |

This is evidence that S1's delegation keeps the **primary** context small
for single-RFE jobs. It does not reduce the helpers' own context pressure,
and it does not establish batch scaling. A larger batch can grow the
Workflow's result/state file if the primary reads it; tier 2 should measure
that file and these windows separately.

**Haiku reference only:** the three primary sessions start at 21,147
tokens and finish at 27,495 / 29,537 / 28,415 (6 / 7 / 6 calls). No input
drops or primary compaction markers appear. A haiku architecture reviewer
reaches 192,798 input tokens, while that run's primary stays below 30k.

**Reproduction:** `scripts/context_growth.py` in the benchmark runs inside
the dashboard pod like the other analysis scripts; `--json` emits each
conversation's per-request timestamps, input sizes, growth and exact dump
filenames. Its synthetic validation checks exact pairing despite shuffled
index order, cache-inclusive sizing, independent windows with a shared
session ID, repeated forks, missing responses and response-ID rejection.
All six real S1 jobs were analyzed. A chart and primary-request CSV were
generated at `/tmp/strat-primary-context.{png,svg,csv}` in this session;
these scratch files can be regenerated from the durable API dumps.

### Process boundary: no separate JavaScript exec at Workflow launch

Checked every strace file in all three opus S1 jobs. Each job has one
successful execution of `/usr/local/bin/claude`, with no execution of
`node`, `nodejs`, `bun`, `deno`, `qjs`, `quickjs`, `jsc` or `d8`, and no
`execveat` calls. The additional `claude.exe` executions are bundled
search utilities (`argv[0]` is `rg`, `ugrep` or `bfs`), not helper-agent
sessions or Workflow JavaScript workers.

Concrete sequence for round 1 (`1010-234154-2647bf`), UTC:

- **23:42:09.447234:** PID 148 successfully execs `/usr/local/bin/claude`.
  This is that PID's only successful exec in the complete trace.
- **23:42:09.539873 / .540892:** thread 148 creates thread 152, which
  creates thread 153. Both `clone3` calls use `CLONE_THREAD|CLONE_VM`;
  these are threads sharing the Claude process, not separate processes.
- **23:42:09.994151:** thread 148 opens the plugin's
  `workflows/strat-pipeline.js`.
- **23:42:15.164125:** thread 153 creates the run-specific copy under
  `workflows/scripts/strat-pipeline-wf_4bd49684-2da.js`, immediately after
  the first model response calling `Workflow` (23:42:15.159).
- The model gets the launch acknowledgement, then makes no primary calls
  until the Workflow completes. The same launch/file-write pattern appears
  in rounds 2 and 3.

**Interpretation:** the primary model hands control to the Workflow tool;
the JavaScript is executed by Claude Code's existing runtime. The trace
does **not** show a shell-style `execve("node", ["node", "workflow.js"], …)`
handoff. Strace establishes the process boundary, but cannot identify the
particular internal evaluator, isolate or JavaScript engine. Logical
conversation separation does not imply a separate OS process per agent.

### The primary agent sees a background task, with completion pushed to it

From the primary model's perspective, invoking `Workflow` resembles
delegating to a background subagent: it receives a task ID, a status and,
later, a result. The implementation behind that interface is JavaScript
coordinating several helper conversations inside Claude Code's runtime.

The three opus S1 runs show this sequence:

1. The primary calls `Workflow({name: "strat-pipeline:strat-pipeline"})`.
2. The tool returns **"Workflow launched in background"**, with a task ID
   and transcript path. The primary ends its turn and waits.
3. The runtime sends a **completion notification**, containing the task ID,
   `status: completed`, the result and diagnostic paths.
4. The primary reads the Workflow output and checks the artifacts.

**The primary does not poll in these runs.** There are no primary model
calls between the launch acknowledgement and completion notification.
The evidence supports an asynchronous task in the existing runtime, rather
than a model repeatedly checking status or a Workflow tool call that blocks
until the whole pipeline finishes. The CLI stays alive awaiting background
work even though the primary model has ended its turn.

**There is no measured growth curve during polling, because no polling
occurred.** Input context moves from about 24.8k after launch to 25.6k on
completion: that transition adds only 815–863 tokens, including the
preceding assistant reply. The noticeable jump comes after completion,
when reading the Workflow output adds 3,991–4,044 tokens and takes the
primary to about 29.6k. Final artifact checks bring it to 29.9–30.3k.
The gap without primary model calls provides no intermediate context
measurements; it should not be presented as continuous sampled growth.

This explains the small primary context: it receives the launch response,
completion notification and any output it chooses to read. The helpers'
full conversations remain separate. These observations describe the three
opus smoke runs; they do not establish that every Workflow invocation must
use this waiting behavior.

## 2026-10-11 — Relay timeout fix deployment verified

The user rebuilt and redeployed Model Relay. Read-only checks confirm:

- Pod `model-relay-55bcd9875f-n9tmb` started at **11:55:42 UTC**, is ready
  and has zero restarts.
- The running environment has `SHIM_UPSTREAM_TIMEOUT_SECONDS=600`.
- The health endpoint's build ID,
  `2a27f2b3251e389bb7bacefff579c4eb5a781957c48cb169e92bc3658f4c7550`,
  matches the Dockerfile's source fingerprint recomputed from the clean
  checkout at **`59d6f06`**. The managed-account timeout fix is deployed.
- Private health reports zero dropped requests, dropped events and storage
  errors, but `last_persisted_at_unix_ms: 0`: there is no new runtime
  evidence since the restart.

**No further rebuild is required.** On the next authorized run, verify
successful managed-account streams beyond 120 seconds, absence of errors
at the old cutoff, and telemetry completeness under load. Successful
requests longer than 120 seconds are expected, so latency alone must not
be treated as an error. Both open relay bugs await runtime verification;
these deployment checks launched no model work.

## 2026-10-11 — First tier 2 batch harness implemented locally

The first F1 scenario is `batch-three-new-rfes`: three new eligible RFEs,
no existing STRATs. It reuses the full existing `workbench-cull-exemption`,
`dsp-retention`, and `feast-scheduled-materialization` templates. Their
problems, requested capabilities, and acceptance criteria are independent:
temporary notebook culling exemptions; object-storage retention with pinned
and registered-model exceptions; incremental feature-store scheduling and
freshness. No model generates the seed content.

**Native batch support verified at the pinned commits.** S1 `1bd7f17`
already supports `STRAT_MODE=batch` through `pre-strategy.sh` and
`prepare_run.py`; S2 `0287b83` already accepts `batch-discover`. Both honor
`BATCH_SIZE` and exact `BATCH_EXPECTED_KEYS`. The harness now supplies these
using the seed's discovery query order, since both entrypoints compare the
ordered candidates. Neither implementation nor its real skills changed.

**Separate tier:** `tier2-smoke`, with S1 and S2 entries for this scenario,
Haiku only, one repeat. Before any service calls, its guard requires exactly
`only_tests=S1` or `only_tests=S2`, one run, no Opus override, and
`wipe_at_start=false`. An invocation cannot automatically sweep both designs.
The intended first run is S1; matching S2 requires a later explicit go-ahead
after S1 analysis. Tier 1 remains `smoke`, with its existing scenario, S1–S4
entries, variants, repeats, and single-RFE checks.

**Seed and evaluation evidence:**

- Fixture validation runs before any reset/write; all-new batch fixtures
  require three eligible items with distinct summaries and descriptions.
  The seed checks the exact discovery set, including unexpected candidates
  and truncation. `seed.json` retains summaries, source description hashes,
  labels, keys, and discovery order.
- Each eligible RFE gets its own strategy/review/verdict/lock checks and
  result record. Batch completeness rejects shared strategies and dropped
  items; per-item project counts also catch orphan strategies. The summary
  displays all three verdicts.
- `reviewer_outputs_returned` joins actual reviewer Skill launches to parent
  tool results by tool-use ID, deduplicating repeated history, and requires
  returned review text for all four roles for every strategy. It counts
  empty returns and reruns. It does **not** establish verbatim preservation
  in the published comment; inspect that during post-run analysis.
- `haiku_only` checks the models observed across request and response dumps,
  including helper calls, and requires a successful response. Failed jobs
  still emit per-item evaluation results when Jira is readable.

**Local validation:** 12 Python unittest tests pass, including real Markov
orchestration over a temporary copy whose service steps are replaced by
local facts. They exercise each one-design batch selection, discovery order,
guard rejection before seeding, seed-count mismatch, missing/shared
strategies, later-item locks and review mismatches, duplicate reviews,
empty reviewer returns, failed jobs, and a wrong helper model. Tier 1's
S1/S2 selection and complete default 12-run matrix also execute in that
isolated copy. No test invokes a model or writes Jira.

The host's existing `checkouts/markov/bin/markov` is stale and rejects
pre-existing step `description` fields. Built the current checkout into
`/tmp/strat-tier2-markov` without changing component source, then validated
the actual benchmark and used that binary for the orchestration tests.
Python compile checks, `bash -n`, and `git diff --check` pass.

**Retained evidence replay:** the new return check fails historical S1 Haiku
job `script-run-workflow-all-claude-haiku-5-5-1010-180408-0d4a57`: feasibility,
testability, and scope each launch twice and return only empty completion
messages; architecture returns text once. It passes historical S2 Haiku
job `script-strategy-entrypoint-all-claude-haiku-1010-182709-92cd57`, with
four roles returning text once each. This replay only reads saved API dumps;
it leaves historical eval-results untouched and launches no model work.

**Prepared settings for the next separately authorized live run:**

```yaml
tier: tier2-smoke
only_tests: S1
variants: haiku
repeats: 1
wipe_at_start: false
```

Local implementation is complete. Commit/push, markovd sync, Jira reset and
seeding, and the first S1 model run have not occurred. The broader mixed-state,
resume, fault-injection, large-body, and ten-item scenarios remain future
work; this implementation prepares only the agreed first three-item F1 case.

## 2026-10-11 — Single tier 2 S1 Haiku pass launched

User authorization: "lets proceed ... i want to kick off the single S1
pass." Published the prepared harness and prior session findings in
Breadboard commit **`2cf4540113a38fbbed7e3366e55ce84e942ea40e`**, then synced
project 1 and imported `var-benchmarks-strat-workflow` in markovd. Verified
the imported directory workflow's exact source commit, tier 2 entries, and
selection guard. Twelve offline tests and workflow/diff checks passed
before publication. No component source/pin changed.

**Preflight:** no pending/running dashboard pipeline jobs or Markov runs;
the pinned architecture snapshot is present (1,846 files). Relay health
reports zero dropped requests/events, zero pending writes, and zero storage
errors, with no persisted requests since its rebuild (`last_persisted_at_unix_ms=0`).

Submitted **exactly one** benchmark run:

| Field | Value |
| --- | --- |
| Markov run | `markov-run-02336f23` (database ID 562) |
| Submitted | 2026-10-11 **13:47:49 UTC** / **09:47:49 EDT** |
| Tier/scenario | `tier2-smoke` / `batch-three-new-rfes` |
| Selection | S1 only, `variants=haiku`, `repeats=1` |
| Evidence preservation | `wipe_at_start=false`; the wipe step was skipped |
| S1 pin | `1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43` |
| Seed job | `script-seed-scenario-all-claude-haiku-5-5-1011-134751-1e1732` |
| S1 job | `script-run-workflow-all-claude-haiku-5-5-1011-134802-315418` |
| S1 job created | 13:48:02 UTC / 09:48:02 EDT |
| MLflow experiment | `strat-workflow-eval/tier2-smoke/S1/haiku` |

**Initial status: running, strategy creation.** The seed completed and its
check passed with no problems: exactly RHAIRFE-1 (workbench exemption),
RHAIRFE-2 (pipeline retention), and RHAIRFE-3 (feature materialization), all
eligible, discovered in that order. The S1 job received `batch-discover`,
`BATCH_SIZE=3`, and `BATCH_EXPECTED_KEYS=RHAIRFE-1 RHAIRFE-2 RHAIRFE-3`.
The Workflow's read-input helper reports native `mode=batch`, all three
acquired keys and pending-create keys. Claude's init reports Haiku; the
first 12 API requests also all use `claude-haiku-5-5`.

Evidence locations on the artifacts volume:

- Seed: `/app/artifacts/scripts/script-seed-scenario-all-claude-haiku-5-5-1011-134751-1e1732/seed.json`.
- S1 output: `/app/artifacts/scripts/script-run-workflow-all-claude-haiku-5-5-1011-134802-315418/`.
- API dumps: `/app/artifacts/apibodies/script-run-workflow-all-claude-haiku-5-5-1011-134802-315418/`.
- strace: `/app/artifacts/strace/script-run-workflow-all-claude-haiku-5-5-1011-134802-315418/`.
- Summary after completion: `/app/artifacts/benchmarks/strat-workflow/markov-run-02336f23/`.

No S2 or additional S1 repeat was submitted. Next: inspect the completed
run's per-item results, actual refine/review overlap, reviewer return and
published-comment provenance, usage/cost, primary/helper context growth,
and relay timeout/drop behavior. This launch is not a passing result;
analysis is pending. The first batch has no measured completion ETA yet.

**Startup progress check:** by the next stream inspection, create is done
and three separate strategies exist (RHAISTRAT-1/2/3). The Workflow has
started separate refine helpers for all three; each reports Haiku. Full
overlap measurements will come from the completed API/strace evidence.

## 2026-10-11 — S1 completion and mandatory host evidence archives

Markov `markov-run-02336f23` completed at **14:18:35.968 UTC**, while its
S1 job **failed validation**. The benchmark deliberately records a failed
test without failing the outer collection workflow. Saved evaluation:
`pass=false`; checks `finished`, `steps_done`, `one_review`, `records_agree`,
and `reviewer_outputs_returned` failed. Batch completeness, Haiku-only,
released locks, no half-done publication, and one strategy per RFE passed.
RHAISTRAT-1 and RHAISTRAT-3 have revise 4/8 reviews; RHAISTRAT-2 has no
returned review. Native summary records Claude exit 0, validation exit 1,
and final exit 1. Root cause, concurrency, usage, and context growth analysis
remain pending; no S2 or repeat was launched.

**New acceptance criterion:** before any subsequent reset/wipe, preserve
all available run and shared system evidence in a verified final capture
under `var/run-data`. Failed runs require the same evidence preservation.
The host collector `scripts/archive_run.py`, streamed remote exporter
`archive_remote.py`, and pre-reset guard `require_archive.py` implement
collection, integrity verification, and receipts. The README documents usage
and scope. The configured `var/run-data` symlink targets `/data/breadboard`;
archives and the symlink are ignored by git and created with private modes.

**Verified final S1 capture:**
`var/run-data/strat-workflow/markov-run-02336f23/20261011T143354300275Z/`.
Twenty sources succeeded without errors. It preserves exact job API bodies
and indexes, per-process strace, job outputs and progress, seed/evaluation
files, Markov run/steps and pinned benchmark source, architecture snapshot,
Kubernetes job/pod state and logs/events, service logs, readable Jira data,
full retained dashboard artifact/log/issue/workspace volumes, consistent
Jira/MLflow/Observatory database backups and stored files, plus paginated
relay requests and usage events. The MLflow backup contains **33 trace
records and 488 spans**; relay capture contains **318 requests**. Shared
dashboard capture also retains older artifacts still present (about 4 GB
uncompressed), so a later wipe cannot silently discard them.

Initially raw job files were packed in `jobs/<job>/files.tar.gz`. After the
user reported strace/API dumps were not visible, expanded job evidence into
directly browsable **`jobs/<job>/api-dumps/`, `strace/`, and `artifacts/`**.
S1 has **605 API dump files, 3,698 strace files, and 26 job artifacts**;
the seed has one artifact. Original tarballs remain. Future collections
automatically expose these folders; `--verify <capture> --unpack
--publish-receipts` upgrades packed-only captures, verifying first, refusing
unsafe paths/links or edited evidence, then extending checksums and
refreshing receipts. The final expanded manifest covers **4,694 files,
1,601,583,672 bytes** (about 1.60 GB, including retained compressed copies).
All sizes and SHA-256 hashes verified; the refreshed final receipt is stored
on the dashboard logs volume and points at this host capture.

**Reset enforcement:** new local guards precede both the initial workflow
wipe and every per-test seed, and direct seed/reset helpers also check them.
Missing, provisional, or unverified receipts block deletion. The cutoff
includes this first tier 2 run. Multi-test invocations require archival
checkpoints between tests; tier 1 remains available. **These guard changes
are local and still require publication/sync before they affect deployed
Markov runs**, whose current benchmark pin remains `2cf4540`. The collector
and final receipt have already been exercised live; the guard recognized
the verified S1 receipt. No reset or additional model run was performed.

**Limits:** SQLite backups are individually consistent, with the overall
capture spanning a recorded interval. Historic Jira states already reset
and expired logs/events cannot be recovered retroactively. Stored symlinks
are inventoried without following them. Full database snapshots and raw
evidence are private ignored data. Archive completeness is independent of
the strategy's pass/fail result.

Validation: **20 offline tests passed**, including committed WAL retention,
integrity/provisional rejection, safe repeatable unpacking, guard ordering,
receipt validation, and credential redaction; directory workflow validation,
Python compilation, and `git diff --check` passed.

## 2026-10-11 — Why the first tier 2 S1 batch failed

**Immediate job failure: refine return mismatch for RHAISTRAT-2.** Its
refinement completed successfully: the raw Bash tool result confirms
`status: Refined`, `refine_count: 1`, and the state command prints
`{"recorded": "RHAISTRAT-2"}`. The helper then calls StructuredOutput at
13:52:28.226 UTC with **`{"recorded": "{\"recorded\": \"RHAISTRAT-2\"}"}`**,
encoding the entire JSON result as a string in `recorded`. This passes S1's
RECORDED schema because it only requires a string. The JavaScript compares
`r.recorded === toRefine[i].strat`, rejects this value, and adds
`refine:RHAISTRAT-2` to its failed list.

**Model error versus Workflow robustness:** the malformed StructuredOutput
originates in the Haiku helper's response. This suggests a formatting or
instruction-following error: it put the command's JSON into a string instead
of returning the fields. A single run does not establish that weaker
reasoning caused the mistake or that a stronger model would reliably avoid
it. S1 also has a robustness gap: its permissive schema accepts this value,
then its exact-key check rejects it without reconciling the successfully
persisted refinement. A stronger model might avoid triggering that gap;
the interface would remain fragile. Treat the observed model mistake and
the Workflow's handling as separate findings. The reviewer prose loss
below is a separate issue and cannot be attributed to Haiku's reasoning
from this evidence.

The Workflow's in-memory `refined` set consequently differs from the saved
progress file. It computes `ready` from that set, so only RHAISTRAT-1 and
RHAISTRAT-3 enter the scorer/reviewer pipeline. The push helper separately
pushes all three refined files. Final assembly correctly reports
`action: failed`, `refine: RHAISTRAT-2 returned no result`, and
`review: RHAISTRAT-2 not recorded`. "Returned no result" is misleading:
there was a returned object, but its value did not match the target key.
The host checker exits 1, skips post-processing, and releases the locks.

Evidence in the final capture's S1 job directory:
`api-dumps/c77fdced-41d7-443f-911f-68e9fb368dab.request.json` (successful
command output), `api-dumps/2b29c154-5388-4a29-a44e-83dae2e05515.response.json`
(malformed StructuredOutput), `artifacts/workflow/stream.jsonl` line 49
(refine helper result), `artifacts/repo-tmp/strat-progress.json` (saved
completion), and `artifacts/workflow/validation.txt` (host failure).
The exact executed Workflow source is included in its task_started prompt
in stream line 5. No need to infer this cause from elapsed time or the
primary agent's own diagnosis; the raw return and selection code establish it.

**Separate benchmark failure: reviewer prose loss.** Of 16 reviewer Skill
launches, 14 parent tool results are only `Skill execution completed`.
Each reviewed strategy has three roles empty on both attempts; the fourth
role has one empty attempt followed by a returned result. Only RHAISTRAT-1
feasibility and RHAISTRAT-3 scope return prose. The final review files
explicitly acknowledge missing reviewer text, and
`reviewer_outputs_returned` fails. This reproduces the known tier 1 defect.
The underlying fork return behavior still needs implementation-level
diagnosis; the observed empty returns are confirmed. Returned feasibility
and scope prose also discuss all three strategies despite their parent
being one per-strategy review, which warrants a separate scope investigation.

**The two revise 4/8 outcomes are valid test outcomes.** They do not cause
execution failure. The missing third review causes finished/steps/review/
agreement checks to fail; missing reviewer prose independently fails its
gate. All three distinct strategies exist, so deduplication did not remove
an RFE from the batch.

**No background timeout observed.** The Workflow's completion notification
records 1,771,080 ms (about 29 min 31 s), completed status, and all step
agents done. Claude exits 0; stderr contains no background-ceiling stop
message. The run stayed within its configured 30-minute background wait.
Captured relay health reports zero dropped requests/events/records, zero
pending writes, and zero storage errors. These observations do not identify
relay loss or timeout as the cause of the missing third review.

Recorded [refine return mismatch](../bugs/open/strat-workflow-refine-return-mismatch.md)
and [reviewer output loss](../bugs/open/strat-workflow-reviewer-output-loss.md).
S1/S2 remain unchanged. No repair, resume, reset, or new model run performed.

## 2026-10-11 — Estimated runtime for one three-ticket Opus S1 batch

**Planning estimate: about 50 minutes, with a 40–60 minute range**, for one
complete three-ticket batch on Opus 4.6, assuming the observed two-helper
concurrency continues through scoring/review and no account-limit stop or
large retry overhead occurs. This is an extrapolation, not a measured Opus
batch or a statistical confidence interval. Completion does not imply
passing the reviewer-output gate, whose defect also occurred on Opus.

Historical tier 1 S1 Opus jobs took 24.6, 27.5, and 28.8 minutes; removing
the identified 120-second stream-cut overhead gives approximately 25 minutes
per ticket. Re-read their original Workflow streams from the final capture's
`system-state/dashboard-files.tar.gz`. Step-agent durations:

| Step | Opus r1 | Opus r2 | Opus r3 |
| --- | --- | --- | --- |
| Create | 1.76 min | 1.76 min | 1.79 min |
| Refine | 5.79 min | 7.17 min | 8.70 min |
| Score | 2.93 min | 3.21 min | 3.98 min |
| Review | 12.68 min | 13.94 min | 12.71 min |

The current Haiku batch establishes two simultaneous refine step agents:
RHAISTRAT-1/2 start at 13:49:05; RHAISTRAT-3 starts at 13:52:20 after the
first slot frees. With two slots, three refinements require two waves;
three scorer/reviewer chains also need more than one wave, with pipelining
allowing some overlap. Rough critical-path budget: 3–6 minutes for batch
create/setup, 12–18 for refinement, and 25–35 for pipelined score/review.
These assumptions motivate the central estimate and range; different RFEs
and reviewer behavior can move it outside that range.

The observed 29 min 31 s Haiku Workflow duration is not a full three-item
completion baseline: the malformed refine return excluded RHAISTRAT-2 from
dedicated scoring/review, while the remaining reviewers spent time on
repeated empty returns. Neither multiplying that duration by the Opus/Haiku
per-call latency ratio nor multiplying the single-ticket Opus runtime by
three models this pipeline well.

The current 30-minute background-wait ceiling is below this estimate.
Before an authorized Opus batch, use a longer runner wait budget (for
example 90 minutes, matching the existing outer timeout), without changing
the pinned S1/S2 designs. No configuration or run was changed for this
estimate; the post-completion archive is additional time outside agent
runtime.

## 2026-10-11 — Authorization and preparation for one S1 Opus batch

User authorized "okay lets do a single S1 batch run w/ claude-opus-4-6".
Prepare/publish the harness, sync/import the exact source in markovd, and
launch exactly one run: `tier=tier2-opus`, `only_tests=S1`, `variants=opus`,
`repeats=1`, `wipe_at_start=false`, `workflow_bg_wait_ceiling_ms=5400000`.
The same three distinct fixtures are used; S1 remains pinned to `1bd7f17`
and S2 to `0287b83`. The Haiku smoke selection remains restricted to Haiku;
the separate Opus tier enforces one matching-model run and retains evidence.
The Opus batch's observed-model gate checks `claude-opus-4-6` for primary
and helpers. No design fix is included, so known defects remain measurable.

The final Haiku archive was reverified before any reset; the live archival
guard recognizes its refreshed receipt. Preflight finds no active pipeline
jobs or Markov runs. Relay health has zero drops, storage errors, or pending
writes. All **23 offline tests**, Markov directory validation, Python
compilation, shell syntax, and diff checks pass, including Opus selection,
model mismatch rejection, wait-budget forwarding, and terminal-run archival
waiting. A detached host collector will wait for this run to finish, then
save the full verified archive and publish its receipt, including failure
evidence if the run fails. No S2 or additional repeat is authorized.

**Publication and launch completed:** pushed Breadboard
**`2615e72e79704874620be092af2ae5fffc76b8e9`**, synced project 1 and imported
the exact 45-file benchmark definition. New archive guards are now deployed
in the imported workflow; both passed before the seed reset. The initial
artifact wipe was skipped. Submitted exactly one POST to create the run:

| Field | Value |
| --- | --- |
| Markov run | `markov-run-7845a7f1` (database ID 565) |
| Submitted | 2026-10-11 **15:10:00.522 UTC / 11:10:00 EDT** |
| Tier/design/model | `tier2-opus` / S1 / `claude-opus-4-6` |
| Scenario/repeats | `batch-three-new-rfes` / 1 |
| Seed job | `script-seed-scenario-all-claude-haiku-5-5-1011-151003-ca726b` |
| S1 job | `script-run-workflow-all-claude-opus-4-6-1011-151014-95af64` |
| S1 job created | 15:10:14 UTC / 11:10:14 EDT |
| S1 design pin | `1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43` (unchanged) |
| Background wait | 5,400,000 ms / 90 minutes |
| MLflow experiment | `strat-workflow-eval/tier2-opus/S1/opus` |

Seed completed and discovery exactly matched RHAIRFE-1/2/3 in that order.
Verified S1 job arguments `batch-discover`, `BATCH_SIZE=3`, matching
`BATCH_EXPECTED_KEYS`, design pin and wait override. Claude init and all
first **23 indexed requests** use Opus 4.6. Creation completed; refinement
started. Planning finish window is **15:50–16:10 UTC / 11:50–12:10 EDT**,
conditional on normal progress; archive collection follows completion.

**Automatic final evidence collection:** detached host collector PID
`2315335`, launched with `archive_run.py --run markov-run-7845a7f1 --wait
8100`. Its log/state are under `var/run-data/strat-workflow/markov-run-7845a7f1/`.
Host inspection confirmed it remains active. Sandbox process inspection
initially hid the escalated host process, leading to a duplicate managed
waiter; that duplicate was stopped, leaving one collector and the model job
running. A temporary status-log gap from the second writer does not affect
raw model evidence. The collector waits for terminal jobs/run, creates a
separate timestamped final capture with browsable API/strace directories,
verifies checksums, and publishes a receipt. Check its log/manifest after
completion before claiming archival success. No additional S1 run or S2
was submitted. Next: completed-run analysis, including model handoffs,
reviewer outputs, concurrency, usage, context growth and relay behavior.

## 2026-10-11 — Provisional assessment: Claude Workflow, bash, and Markov

Architectural preference for this platform: **Markov owns the long-running
pipeline; small scripts execute deterministic operations and validate agent
outputs; agents perform strategy creation, refinement, scoring and review.**
Markov has substantial integration evidence as the benchmark driver, but
has not yet been tested as a third strategy-orchestration arm. This is a
design judgment, not a measured Markov/S1/S2 reliability or performance result.

| Approach | Best fit | Main tradeoff in this evaluation |
| --- | --- | --- |
| Bash | Small, stable pipelines and deterministic adapters | Direct exit codes/JSON avoid model-mediated bookkeeping; durable recovery, concurrent work, cancellation and operational visibility require additional implementation. Current S2 is sequential; bash itself does not require sequential execution. |
| Claude Workflow | Agent-local coordination with native agent integration | Its JS control flow is deterministic and supports parallel/pipelined work, but current S1 hands ordinary script output through agents and couples execution to CLI/session and tool-schema behavior. The malformed refine return and inherited reviewer StructuredOutput show failures at those boundaries. |
| Markov | Cross-service, long-running pipelines with recorded steps, gates and bounded fan-out | Explicit control and checkpoint state support operator visibility and recovery; there is more engine/deployment complexity, and external side effects still require idempotency and postcondition checks. |

Evidence for Markov includes exact-source imports, nested fan-out, submitted
job identity/log tracking, recorded failed tests, and the no-model feature
check exercising failure → resume → gate → completion. New archive guards
also ran successfully before the current Opus batch reset. Prior work
exposed and repaired resume behavior, bundled-binary drift, callback auth
stability and tracked-job cancellation. Current markovd cancellation evidence
documents a remaining window before a newly submitted job's identity reaches
the wait step. Current Markov callback code has bounded HTTP retries but can
still drop events after retries or on unretried statuses; avoid repeating the
old blanket claim that it has no callback retries. These are operational
limits, not proof Markov cannot coordinate the pipeline.

Checkpointing alone cannot guarantee exactly-once Jira writes: a crash
after a successful POST but before recording completion can replay the
operation. Stable identities, read-before-create/reconciliation, and explicit
result validation are needed regardless of orchestrator. Markov completion
also does not imply all business checks pass: our driver intentionally
collects a failed S1 result and completes its evidence/reporting workflow.

A third arm should expose create/refine/push/score/review as Markov steps,
with script-validated results and per-strategy identities, using the same
fixtures, skills, model and postconditions. Wrapping unchanged S1/S2 as one
Markov job measures the wrapper rather than Markov's internal orchestration.
No third arm or pipeline modification was implemented during the active
Opus run.

## 2026-10-11 — Markov development proposals

The proposed engine/language features are maintained in Markov's
[durable task orchestration plan](../../checkouts/markov/.ledger/plans/002-durable-task-orchestration.md).
This evaluation plan retains the comparison evidence; implementation
planning belongs to the Markov repository.

## 2026-10-11 — Single S1 Opus batch completed; reviewer-return gate failed

`markov-run-7845a7f1` completed **16:22:08.825 UTC / 12:22:08 EDT**.
S1 job `script-run-workflow-all-claude-opus-4-6-1011-151014-95af64`
completed **16:21:59 UTC**, after **4,305 seconds / 71.8 minutes**.
All runner stages (pre, Claude, validation, post, release) exited zero.
All three RFEs have exactly one strategy and recorded APPROVE review:
RHAISTRAT-1 **8/8**, RHAISTRAT-2 **8/8**, RHAISTRAT-3 **7/8**.
Locks were released, records agree, and all observed models match Opus 4.6.
The Haiku refinement-return mismatch did not recur.

**Benchmark result remains FAIL:** the sole failed check is
`reviewer_outputs_returned`. Eleven of twelve specialist Skill calls return
only `Skill execution completed`; the twelfth (RHAISTRAT-3 architecture)
returns `API Error: Connection lost mid-response. The response above may be
incomplete.` The current detector counts this nonempty error as returned,
so its nominal 1/12 return count is not one substantive specialist review.
Final review documents do contain substantive prose; the failing check
specifically measures the Skill tool-result handoff. Whether reviewers'
output was recovered through another path needs separate inspection.
Successful job completion and APPROVE verdicts do not establish that this
handoff worked or that the evaluation passed.

Measured agents: create **3.4 min**; refinement **5.1 / 5.9 / 5.0 min**;
scoring **3.8 / 4.0 / 2.8 min**; reviews **24.5 / 20.4 / 29.3 min**.
Review 3 starts when review 2 frees a worker at 15:51:39 UTC. Reviews
exceeded the historical single-ticket estimates and explain the overrun of
the initial 40–60-minute planning range. Captured usage: **292 calls**,
**172,332 output**, **12,346,641 cache-read**, **1,692,890 cache-write**
tokens; zero reported rate limits. These are aggregate usage counts, not
the primary agent's final context size.

**Final archive verified and receipts published** by the automatic
collector: `var/run-data/strat-workflow/markov-run-7845a7f1/20261011T162230677725Z/`.
Manifest: final=true, complete=true, zero errors, **20 sources**, **2,517
files / 1,210,005,016 bytes**. S1 browsable evidence includes **587 API
dump files** and **1,471 strace files**, plus workflow streams/results,
Jira, shared-service state, logs and relay telemetry. Capture interval:
16:22:30.678–16:26:31.790 UTC. Collector verification returned ok=true,
problems=[], receipts_published=true. No repeat or S2 was launched.

**Connection-error follow-up:** relay telemetry contains 19
`upstream_stream_error` failures at 120001–120003 ms, HTTP 200 and partial
usage; 17 message IDs match S1 API dumps. No completed stream in this
capture exceeds 120 s. The relay raises this classification when reading
its upstream response stream, indicating a failure on its model-provider
path. The deployment still specifies a 600 s timeout and the archived
build ID matches the previously verified fixed source. The remaining
120 s limit's origin is unresolved; deployment verification did not prove
the fix effective. Details/evidence are recorded in
`bugs/fixed/model-relay-120s-upstream-timeout.md`. This also qualifies the
previous timing analysis: interrupted/retried streaming is a potential
contributor to the long reviews, not simply normal model work. The single
error string surfaced to the review parent is not the total upstream
failure count. No model rerun or redeployment was performed.

**Remaining timeout identified:** live `upstream-profiles` confirms
`tanner-jc-personal` is a UI-managed OAuth account. Its separate constructor
`checkouts/model-relay/src/accounts.rs:208` still supplies a hard-coded
120 s timeout to reqwest. The earlier fix in `projects.rs` covered
configured profiles, not this constructor. The relay's HTTP client thus
ends these streams at its own 120 s deadline; it does not wait the
configured 600 s. The generic `upstream_stream_error` classification masks
timeouts during response-body reads and does not by itself prove the
provider terminated the connection. The prior claim that the deployment
fully fixed managed-account timeouts was too broad. Bug updated with
source and live-routing evidence; no component change or redeployment.

## 2026-10-11 — Remaining managed-account timeout fixed and deployed

User authorized the relay fix. The UI-managed account constructor now
uses the shared configured timeout. Stream read timeouts are classified
as `timeout_error`; non-timeout read errors remain `upstream_stream_error`.
Synthetic regression checks effective 1 s/3 s budgets against the same
1.5 s SSE response through the managed-account client and production
forwarder, including usage telemetry and a separate broken stream.
All 29 tests, format and clippy pass, including the production image's
pinned Rust toolchain checks. No paid model call or strategy rerun.

`make host-rebuild-relay` succeeded; new pod
`model-relay-f46688557-5tflw` started **16:54:20 UTC**, ready/zero restarts.
Live health build fingerprint exactly matches tested source:
`84bb7c79a09bfcb0c29dd7edd517605bfcf293994d95a9dbe4818a0fdc40b8c0`.
Pod timeout remains 600 s, and the real managed OAuth account is restored.
Private storage health is clean. The identified constructor bug is fixed;
actual provider-stream behavior beyond 120 s awaits the next authorized
run. Existing S1 evidence is preserved in its verified final archive.

## 2026-10-11 — Single S1 Opus repeat launched after the relay fix

User requested another S1 batch. Submitted exactly one unchanged three-RFE
S1 Opus pass: **`markov-run-c5ba3904`**, database ID 568, started
**17:04:21.986 UTC / 13:04:21 EDT**. Harness/import stays `2615e72e`,
S1 source stays `1bd7f17`; only_tests=S1, tier2-opus, repeats=1,
Opus 4.6 and 90-minute wait budget. No S2 or follow-on repeat.

Before launch, the previous Opus final archive passed host checksums and
the live reset guard recognized both earlier Haiku/Opus receipts. No active
pipeline jobs or Markov runs; fixed relay build `84bb7c79...dc40b8c0`,
private storage health clean. Seed
`script-seed-scenario-all-claude-haiku-5-5-1011-170425-10f2cf` completed
and exactly selected RHAIRFE-1/2/3. S1 job
`script-run-workflow-all-claude-opus-4-6-1011-170435-3f61ed` is running.
Actual K8s job batch size, expected keys, source pin, wait budget and
MLflow experiment fields match the intended settings.

Detached collector host PID **2460265**, started 17:06:25 UTC, waits for
terminal state with `--wait 8100`, then captures/verifies/publishes receipts.
Logs/state: `var/run-data/strat-workflow/markov-run-c5ba3904/`.
Verified `launch-context/` additionally retains the exact uncommitted relay
source, patch and deployment provenance (three files, 135,333 bytes), so
the run remains reproducible if the component working tree later changes.
Next: final evidence and analysis of >120 s streams, timeout classification,
retries, runtime, reviewer handoffs, usage and primary context. The unchanged
S1 reviewer-return bug can still fail the benchmark independently of the
relay fix.

## 2026-10-11 — Relay-fixed S1 repeat completed and archived

`markov-run-c5ba3904` completed 17:55:49.922 UTC; S1 job finished
**17:55:45 UTC / 13:55:45 EDT** after **51.2 min (3070 s)**.
All runner stages exit zero. Exactly three strategies, one recorded review
per RFE, all locks released and records consistent. All strategy model
calls match Opus 4.6. Verdicts: **APPROVE 7/8, APPROVE 8/8, APPROVE 6/8**.
The evaluation still **FAILS solely on reviewer_outputs_returned**.

### Relay and runtime evidence

The repaired relay records **335 complete requests and zero failures**:
283 streaming generations (all join to S1 API responses), 50 token-count
requests and two preflight generations. All captured records have the
repaired build ID. **Seven streams complete beyond 120 s**, spanning
**124.211–170.314 s**, all with complete usage and matching S1 response
IDs. This confirms the 120 s managed-account deadline is removed. It does
not exercise the full 600 s ceiling. No rate limits or storage loss/errors.

| Measure | Pre-fix Opus batch | Relay-fixed Opus batch |
| --- | --- | --- |
| Job minutes | 71.8 | 51.2 |
| Review agent minutes, strategies 1/2/3 | 24.5 / 20.4 / 29.3 | 15.2 / 19.0 / 16.3 |
| Reported calls | 292 | 283 |
| Output tokens | 172332 | 216778 |
| Cache-read tokens | 12346641 | 11038816 |
| Cache-write tokens | 1692890 | 1696541 |
| Failed relay requests in capture | 19 | 0 |
| Substantive specialist Skill returns | 0/12 (one error string counted nonempty) | 2/12 |

Observed wall time decreases **20.6 min / 28.7%**, despite higher output
token volume. This is a two-run observation with nondeterministic model
work, not a guaranteed or isolated causal performance estimate. Concurrency
remains a two-worker pipeline: review 1 starts while score 3 runs; review 2
starts when score 3 finishes; review 3 starts when review 1 finishes.
No connection-error retries are evident in the complete relay records;
the reviewer gate records one launch per strategy/role, no reruns.

### Persistent specialist return and scope defects

Ten of twelve Skill tool results are only `Skill execution completed`.
Two testability returns have substantive prose, but both assess the entire
three-strategy batch despite being launched separately for strategies 1
and 2. This is additional evidence that the handoff defect persists
independently of relay failure, and that returned prose alone does not
establish correct review scope. Scope drift is recorded separately in
`bugs/open/strat-workflow-specialist-review-scope.md`; existing return-loss
bug updated. Final reviews exist and approve all three; no S1/S2 change.

### Primary workflow agent context

Joined the six unique outer-stream assistant message IDs to relay records,
separately from all helper calls. Measured input context:

| Primary call | Input tokens | Meaning |
| --- | --- | --- |
| 1 | 24103 | Launch Workflow |
| 2 | 24762 | End turn while background workflow runs |
| 3 | 25584 | Resume after completion; attempt result-file read |
| 4 | 25827 | List output files |
| 5 | 26192 | Read pipeline progress/result |
| 6 | 26887 | Final reply |

There are **no primary model calls/polls** between completion of call 2 at
17:05:02.590 UTC and call 3 at 17:55:16.548 UTC, about 50 minutes.
Completion adds **822 tokens** relative to the pre-wait sample; subsequent
checks add **1303**. Overall measured input growth is **2784 tokens**.
Last measured input is **26.9k**, about 2.69% of the recorded 1M capacity;
the final answer adds 161 output tokens. There is no sampled growth curve
during the wait. The run's 11M cache-read usage is repeated aggregate
billing/usage, not the primary context size. Other agent input samples reach
167579 tokens, reinforcing the need to keep these conversations separate.

### Final evidence

Verified capture:
`var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z/`.
Manifest final=true, complete=true, errors=[]; **20 sources, 2715 files,
1267550579 bytes**. Browsable S1 **566 API dumps and 1710 strace files**;
workflow results, Jira state, databases/files, service logs and relay
telemetry included. Capture interval **17:56:15.928–18:00:46.133 UTC**.
Collector report ok=true, problems=[], receipts_published=true. Separate
verified launch-context snapshot preserves the uncommitted relay source
and deployment provenance. No additional S1 or S2 was launched.

## Tier 1 runtime interpretation after the complete relay repair

The single-RFE measurements remain observations of the pre-fix stack;
timeout-affected wall times are not clean baselines for the repaired stack
or for comparing workflow designs. Opus S1 rounds had 0/1/2 cuts, versus
S2's 0/4/6. Thus the raw means (27.0 versus 31.8 minutes) are confounded
by unequal timeout exposure. The zero-cut first rounds, 24.6 and 24.0
minutes, remain useful historical anchors, but do not alone establish
current-stack performance or equivalence.

Subtracting two minutes per cut is a rough diagnostic, not a replacement
measurement: interrupted work, retries and model variation prevent exact
reconstruction of the counterfactual runtime. The tier 2 batch's observed
28.7% decrease must not be used as a correction factor for tier 1.
Recorded Haiku rerun data has two cuts in S1 round 1 and none in the other
rounds; the earlier wiped smoke lacks raw evidence to certify its status.

Retain the historical results labeled pre-fix. If current-stack single-RFE
timings are required, the minimal matched check would be one Opus pass per
design with the same scenario and pins, archived relay evidence and no
timeout failures. Such a pair would be a sanity check, not a statistical
comparison. No new runs are authorized or launched by this analysis.

## Single S2 Opus batch launched on the repaired relay

User authorized one batched S2 pass on 2026-10-11, following the repaired
S1 analysis. Submitted `markov-run-6bcb3c32` at **18:19:35 UTC / 14:19 EDT**:
tier2-opus, only_tests=S2, repeats=1, same three fixtures and harness
`2615e72e`. Prior archives verify and both reset guards pass; repaired
relay build `84bb7c79…` remains ready. No S1/S2 source changes.

S2 job `script-strategy-entrypoint-all-claude-opus-4-1011-181949-e387e8`
is running on native bash entrypoint pin `0287b838`, Opus 4.6. Seed passed;
native discovery found/locked RHAIRFE-1/2/3. API dumps, strace, MLflow and
OTel enabled. One detached collector (PID 2550958) saves final system/run
evidence under `var/run-data/strat-workflow/markov-run-6bcb3c32/`; verified
launch-context preserves exact relay source/deployment provenance. Final
capture and comparison with S1 pending; no repeats or additional tests.
Task: `tasks/done/strat-workflow-tier2-s2-opus-pass.md`.

## Relay-fixed S1 batch token cost

For `markov-run-c5ba3904` (51.2 min, three RFEs), archived evaluation usage
agrees with all 283 Opus streaming generation records in the relay capture.
Totals cover the primary workflow agent and all helpers/specialists.
Count-token operations and the two small non-Opus preflight probes are
excluded from the S1 inference total.

| Category | Tokens | USD per million | List-price equivalent |
| --- | --- | --- | --- |
| Uncached input | 1880 | 5.00 | $0.0094 |
| Cache writes, 5-minute TTL | 1696541 | 6.25 | $10.6034 |
| Cache reads | 11038816 | 0.50 | $5.5194 |
| Output | 216778 | 25.00 | $5.4195 |
| Total | 12954015 | — | **$21.5516** |

Average **$7.18 per RFE**. Relay usage explicitly records zero 1-hour cache
write tokens, so the 5-minute write rate applies to all cache creation.
Rates verified 2026-10-11 against
[Anthropic pricing](https://platform.claude.com/docs/en/about-claude/pricing).
This is standard API list-price equivalent; the run used the managed
Claude OAuth account, so it is not a measured invoice or subscription-limit
charge. These were ordinary streaming calls, without the provider Batch
API discount. Cached input is repeated usage across calls, not a single
12.9M-token context or unique source volume.

### Comparison with historical single-RFE S1 Opus

The three tier 1 S1 runs have a recorded total list-price equivalent of
$20.84 (see "How much confidence do 3 runs buy?"), averaging **$6.95 per
RFE**. The repaired-relay batch is **$21.55 total / $7.18 per RFE**, about
**$0.24 or 3.4% higher per RFE**. This is approximately the same per-RFE
cost, without evidence of a substantial batching saving.

Calls decreased from 318 across the three single-RFE runs (106 per RFE)
to 283 for the batch (94.3 per RFE), about 11% fewer. Batch output averages
72.3k tokens per RFE versus approximately 62.8k historically, about 15%
more. Cache writes per RFE remain approximately 570k versus 565.5k;
cache reads approximately 3.63M versus 3.68M. Thus fewer calls do not imply
lower token cost in these observations.

Limits: tier 1 repeated the KServe canary/rollback fixture; tier 2 uses
three different capabilities. The historical runs had 0/1/2 relay cuts,
and their recorded usage is not an independently reconciled invoice for
interrupted requests. This is a comparison of recorded usage at the same
rates, not a controlled estimate of batching efficiency on the fixed stack.

## S2 batch ended on an upstream account limit

`markov-run-6bcb3c32` finishes its driver/reporting workflow at
**19:15:42.682 UTC**. S2 job
`script-strategy-entrypoint-all-claude-opus-4-1011-181949-e387e8`
**fails**, exit 1 at **19:15:33 UTC / 15:15:33 EDT**, after **3344 s /
55.7 min** from job creation. Script-only elapsed is 3334 s. The failed
job's evaluation metadata has completed=null, so duration is derived from
the job creation timestamp and explicit archived runner finish line.

The terminal error is **HTTP 429: "This request would exceed your account's
rate limit. Please try again later."** It occurs while the second strategy's
review parent is about to assemble its final review after specialist work.
Claude child exits 1 and the bash script aborts before reviewing strategy 3.
All owned RFE locks are released. This is the same type of account-limit
interruption seen in tier 1's initial S2 Opus round 3, separate from the
repaired relay deadline. No repeat or recovery run was launched.

### Persisted state and checks

All three RFEs have distinct, created/refined strategies. RHAISTRAT-1 has
published **APPROVE 7/8**. RHAISTRAT-2's scorer/specialists ran but no final
review was published; RHAISTRAT-3 has no dedicated review. Failed checks:
finished, steps_done, one_review, records_agree, reviewer_outputs_returned.
Markov completed status denotes the completed reporting harness, not a
successful S2 workload.

### Relay and token cost

Archive contains **235 relay records: 234 complete, one failed**, all from
repaired build `84bb7c79…`. Only failure is rate_limit_error, HTTP 429,
request **32d8fb77-a78d-404e-bbdb-627f2f56865d**, at
19:15:25.737–19:15:25.960 UTC (222 ms), real managed Claude OAuth profile
`tanner-jc-personal`; upstream request ID recorded. There are **no timeout
or stream errors**. All **187 completed S2 streaming generation** message
IDs match archived API responses; one further streaming request is rejected.
Seven successful streams exceed 120 s, longest **186.484 s**. Relay health
reports zero drops, storage errors and pending writes.

| Measure | Repaired S1 batch | Repaired S2 attempt |
| --- | --- | --- |
| Job duration | 51.2 min | 55.7 min, then abort |
| Created/refined strategies | 3 | 3 |
| Published final reviews | 3 | 1 |
| Completed streaming model calls | 283 | 187 |
| Uncached input | 1880 | 227 |
| Cache writes, all 5-minute | 1696541 | 1403324 |
| Cache reads | 11038816 | 8655663 |
| Output | 216778 | 168170 |
| Standard API list-price equivalent | $21.5516 | $17.3040 spent before abort |
| Relay failures | 0 | 1 account HTTP 429 |
| Benchmark result | FAIL: reviewer-return gate | FAIL: incomplete reviews/job and return gate |

At the same verified Opus rates, S2's incurred $17.30 is not a complete
batch cost and cannot establish savings against S1. This is not a clean
comparison of end-to-end timing or quality because S2 was interrupted.
Subscription billing and actual quota consumption are not inferred from
the API list-price equivalents.

### Specialist evidence and evaluation limits

Eight specialist Skill launches for strategies 1/2 return nonempty text;
**seven substantive assessments all cover all three strategies** despite
individual-target launches. Feasibility/testability/scope for target 1 and
all four roles for target 2 have explicit headings for RHAISTRAT-1/2/3.
This reproduces scope drift in S2; the finding now spans both designs.
API request evidence: `7b43b84e-238e-466e-871e-cc1a5a23b8ec.request.json`
and `09cf2531-d9ad-42e0-aed4-125b81b1b889.request.json`.

Target 1 architecture returns only a 170-character message saying it has
launched four research agents and will wait before composing the review.
The detector marks it returned=true despite no assessment in that result.
Recorded a separate gate bug for status/error false positives; this does
not establish whether later asynchronous work arrived via another path.
Target 3 roles have no launches, so the overall return gate fails anyway.
No S1/S2 or benchmark implementation change.

### Final archive

Collector completed; independent host verification passes, receipts published:
`var/run-data/strat-workflow/markov-run-6bcb3c32/20261011T191550355513Z/`.
final=true, complete=true, errors=[]; **20 sources, 2457 files,
1382240358 bytes**, including browsable S2 **376 API files and 1774 strace
files**. Capture interval **19:15:50.356–19:19:56.927 UTC**. Launch-context
provenance retained. Task moved to done for the completed authorized attempt,
archive and analysis; workload outcome remains failed. No further run.

## Account-budget completion is a benchmark metric

2026-10-11 user observation: **we could not finish the L1 Opus campaign
(three iterations per design) within the available Anthropic five-hour
usage allowance.** Record this operational outcome alongside token cost,
runtime, output quality and handoff correctness. A campaign whose active
execution fits inside five hours can still exceed that window's account
usage allowance and require a reset before completing.

Evidence: tier 1's original third S2 Opus attempt was rejected after about
610 accumulated Opus calls, with two account-limit 429s at 02:11:36 UTC.
It failed after approximately ten minutes and needed a separately authorized
rerun after the limit reset. Six successful single-RFE runs were eventually
obtained, but the original campaign did not finish uninterrupted on the
available allowance. The later tier 2 S2 attempt also aborts on an account
429 after preceding Opus work, leaving only one of three final reviews.

Limits: these are observed campaign outcomes on a shared managed OAuth
account. We did not measure a fresh, otherwise idle five-hour window's
remaining allowance at launch. Therefore the evidence does not establish
that every isolated L1 campaign necessarily exceeds a full allowance, nor
that approximately 610 calls is a fixed quota threshold. Call count and
API list-price equivalent are usage descriptors, not a measured conversion
to the subscription's allowance.

For future authorized campaigns, report:

- Whether all planned iterations finish before an account-budget rejection.
- Planned versus completed runs/RFEs and partial work at the first rejection.
- Calls, token categories and elapsed time accumulated before the first 429.
- Account allowance/reset observations at launch and rejection, when available;
  distinguish unmeasured/shared prior use from an isolated fresh window.
- Reset waiting time and repeats needed, so campaign elapsed time includes
  account-limit delays as well as active job runtime.

This metric requires no change to S1/S2. It is a constraint on practical
evaluation and production throughput under our current account allowance;
no further test, recovery run or account change is authorized by this note.

## GLM compatibility validation authorized

2026-10-11: with EnMaaS model routing deployed, user authorized exactly one
single-RFE iteration each of S1 and S2 on `rits/zai-org/glm-5-3`, using medium
effort. S1 first, archive/analyze, then S2 separately. This is compatibility
validation, not another three-ticket batch or a quality/cost A/B campaign.
Keep both implementation pins unchanged and preserve all evidence.

Harness adds isolated `glm-smoke` with one selected design/repeat and no artifact
wipe. A tiny job wiring check precedes S1 and is included in that run's archive.
Explicit helper/default alias env avoids the existing wrapper's `claude-*`-only
pinning. Jobs retain their Vertex relay credentials and built-in project;
private EnMaaS credentials stay server-side. GLM-only identity checks require the
exact hosted request ID, allowing the verified `zai-org/GLM-5.3` response spelling.
Reconcile actual routing separately from relay telemetry, including helper calls.

[Task](../tasks/done/strat-workflow-glm-single-passes.md). No run launched yet.

### GLM S1 single-RFE result

Published harness `7f4362ec65a56cbf8c58da1cda76acb775a9b055`; separate
`glm-smoke` tier preserves tier 1/2 and both design pins. Markov run
`markov-run-23df27ac`, S1 job
`script-run-workflow-all-glm-5-3-1011-224849-152aa2`, 22:48:49–23:29:15 UTC
on 2026-10-11, **2426 seconds / 40.4 minutes**. Tiny GLM job wiring check
and one-RFE seed passed first. All single-RFE smoke checks pass: one created,
refined/pushed strategy, APPROVE 6/8 review, consistent label/comment, released
locks, exact GLM request IDs and verified response spelling. No extra iteration.

180 request/response pairs; provider-reported usage: 740791 uncached input,
7258112 cache-read input, zero cache writes, 179890 output tokens. No API errors,
missing/unreadable responses or Claude helpers. Relay has 198 records including
wiring/counting, all `rits/zai-org/glm-5-3` on `enmaas-personal`, no errors.
No GLM price/invoice inferred, and the absence of a separate thinking count does
not prove absence of reasoning. Native CLI duration excludes background workflow
work; use job wall time rather than its approximately 45-second result duration.

**Known S1 defect reproduces:** all four specialist Skill results contain only
completion acknowledgements (100/100/94/101 characters). Captures contain 11
StructuredOutput calls overall. The reviewer-return detector fails when applied
manually; tier 1's smoke pass does not establish reviewer handoff correctness.
No S1/S2 changes were made. GLM transport compatibility does not repair PR #83.

**New telemetry limitation:** EnMaaS response IDs are `chatcmpl-...`, discarded by
relay `msg_`-only filtering, so exact generation-ID reconciliation gives 0/180.
Job API indexes retain original IDs; isolated time/account scope confirms routing.
[Deferred bug](../bugs/open/model-relay-enmaas-message-id-not-recorded.md).
Two MLflow traces in experiment 9 report OK; API dumps still cover subagents.

Final archive independently verified and receipts published, before S2 reset:
`var/run-data/strat-workflow/markov-run-23df27ac/20261011T232950539833Z/`.
Complete/final=true, errors=[], 21 sources, 1931 files, 1304175093 bytes;
361 browsable S1 API files, 1197 strace files. S2 is separately authorized and
will use the same exact model, scenario and repeat count after this analysis.

### GLM S2 result and compatibility comparison

After S1 archive/analysis, one separate POST at 2026-10-11 23:37:40.618 UTC
created `markov-run-428f237a`, source `7f4362e`. S2 job
`script-strategy-entrypoint-all-glm-5-3-1011-233753-27ed46` runs
23:37:53 UTC–2026-10-12 00:23:59 UTC, **2766 seconds / 46.1 minutes**, exit 0.
Same single-RFE fixture and exact hosted model, medium request effort, original
S2 pin `0287b838d2bc59a2569cf2dd971aad7ad2d76dad`. All smoke/model gates pass,
APPROVE 6/8, one created/refined/pushed strategy and released locks.

| Metric | S1 GLM | S2 GLM |
| --- | --- | --- |
| Benchmark iterations / RFEs | 1 / 1 | 1 / 1 |
| Smoke outcome | PASS | PASS |
| Published review | APPROVE 6/8 | APPROVE 6/8 |
| Job wall time | 2426 s / 40.4 min | 2766 s / 46.1 min |
| Request dumps / successful responses | 180 / 180 | 143 / 141 |
| Provider-reported uncached input | 740791 | 790961 |
| Provider-reported cache-read input | 7258112 | 7814144 |
| Provider-reported cache writes | 0 | 0 |
| Provider-reported output | 179890 | 206070 |
| Specialist assessments returned | 0/4 (acknowledgements only) | 4/4 substantive |
| StructuredOutput calls | 11 | 0 |
| Relay incomplete streams / cancellations | 0 / 0 | 1 / 1 |
| Same-model non-stream fallback responses | 0 | 1 |
| HTTP 429s | 0 | 0 |

S2's 162 relay records all use GLM on `enmaas-personal`: 142 streaming
attempts (140 complete, one failed, one cancelled), one complete non-stream
generation and 19 complete count requests. They reconcile with the job's
143 request files / 141 response files. No Claude-model requests or Anthropic
account usage. Source API response-only errors={} is not clean-stream evidence:
two attempted streams have no successful response dump.

The incomplete stream is relay `16e8d603-1e7d-44ee-8774-6e21a87a9fc7`, HTTP
200, starts 23:55:12.463, ends `incomplete_upstream_stream` after 48381 ms.
`06e2b7fa-ed2f-4eb9-bbf6-3ef0eaa7edad` starts 23:58:29.875 and becomes
cancelled after 323979 ms. Neither is an observed 600-second relay timeout.
The exact reason for cancellation and the incomplete-stream root cause remain
unresolved. The client recovers within this single attempt: streaming request
`42606e7c-77da-4ea7-84d0-3c479a3dcf9b.request.json` and non-streaming request
`929c9558-d65b-412b-a509-22bd209e965b.request.json` differ only in `stream`.
The latter succeeds at 00:04:37.094 UTC, model echoes the exact hosted ID,
stop_reason=tool_use, 3584 output tokens. All other successful response bodies
report `zai-org/GLM-5.3`. [Stream investigation](../bugs/open/enmaas-strategy-stream-incomplete.md).

S2 four Skill returns contain 12439/7859/5488/11399 chars of substantive
feasibility/testability/scope/architecture assessment. Manual return gate passes;
this does not prove verbatim preservation in the final published summary. S1
forked reviewers all selected approve in StructuredOutput; feasibility also set
needs_attention=true. Those fields, like the absent prose, were not delivered
in the acknowledgement-only Skill result; the final review helper returns
needs_attention=false. Do not infer an intentional flag override from this alone.

A S2 reviewer examines earlier archived review files under shared
`artifacts/RHAISTRAT/2026*/` and identifies one as a pre-refinement version;
its final assessment identifies the current refine_count=1 strategy. This is
prior-artifact access, not proof it used an incorrect strategy. Retained artifacts
and reused Jira keys limit the isolation of this validation. S2 is 5.7 minutes
longer in this pair despite fewer successful model calls; n=1, recovery and
review-context differences prevent a general runtime/quality comparison.
GLM billing rates, cache billing semantics, context capacity and actual reasoning
budget remain unverified; native client's assumed prices/limits are not evidence.

Final S2 capture independently verifies, receipts published:
`var/run-data/strat-workflow/markov-run-428f237a/20261012T002415035434Z/`.
Complete/final=true, errors=[], 20 sources, 1700 files, 1310235963 bytes;
285 browsable API files, 1190 strace files. Two MLflow traces in experiment 10
report OK; raw API dumps cover subagents. Relay message-ID joins are 0/141,
so routing/error reconciliation uses isolated run/account/time scope and counts.

Both authorized one-iteration GLM passes are complete. Job env pinning and
existing Vertex relay credentials work without exposing the private EnMaaS key
to jobs or changing S1/S2. GLM compatibility is established for these attempts;
S1's reviewer contract remains defective and S2's stream recovery deserves
follow-up. No extra iteration, provider redeploy or design change was performed.

### S2 tier 2 Opus repeat after account rate-limit reset

User reports the rate-limit window has passed and requests the outstanding
level 2 S2 run. One iteration authorized; no design changes or automatic paid
retry. Cluster idle, all six prior design jobs have verified final archive
receipts, managed Anthropic auth ready. Auth readiness does not measure quota.

One POST at 2026-10-12 00:50:22 UTC creates `markov-run-79d3241a`, harness
`7f4362e`, tier2-opus / S2 / opus / repeats=1 / wipe_at_start=false. Both
archive guards and distinct three-RFE seeding pass. S2 job
`script-strategy-entrypoint-all-claude-opus-4-1012-005035-b81781` starts
00:50:35 UTC on original pin `0287b838d2bc59a2569cf2dd971aad7ad2d76dad`,
batch_size=3, expected keys RHAIRFE-1/2/3. Early evidence: 42 requests all
claude-opus-4-6, 41 successful response dumps, no response error bodies.
The batch is still running; no terminal outcome inferred.

Detached archive collector PID 3021536 waits for terminal run/jobs and will
collect/verify/publish receipts under
`var/run-data/strat-workflow/markov-run-79d3241a/`. Launch context saved.
[Task](../tasks/done/strat-workflow-tier2-s2-opus-rate-limit-retry.md).
Compare the completed three-strategy review coverage, actual specialist returns,
scope drift, runtime, usage and relay failures with the earlier 429-aborted
S2 run before drawing S1/S2 conclusions. Final capture/analysis pending.

#### Completed S2 Opus batch: PASS, with reviewer scope drift

Job finished 2026-10-12 02:19:18 UTC (22:19:18 EDT on Oct 11), exit zero;
**5323 seconds / 88.7 minutes**. Markov reporting finished 02:19:25.651 UTC.
All benchmark gates pass, failed_checks=[]. Three distinct RFEs have exactly
one linked created/refined/published strategy and one final review each:
RHAISTRAT-1 APPROVE 7/8, RHAISTRAT-2 APPROVE 7/8, RHAISTRAT-3 APPROVE 6/8.
Labels/comments agree and all locks released. Third review explicitly retains
testability=revise and unresolved implementation questions alongside aggregate
approve / needs_attention=false; the aggregate verdict is not unanimous
specialist approval or proof the implementation is ready.

**12/12 substantive specialist Skill returns**, 8952–18350 characters excluding
wrappers; none are acknowledgements or progress-only messages. Every return has
separate assessment headings for RHAISTRAT-1/2/3 despite a single-strategy
launch target. The known scope-drift bug reproduces for all roles and targets.
The detector passes the handoff; intended per-target isolation remains broken.
This attempt provides a complete batch outcome, without fixing either design.

| Metric | Repaired S1 Opus | Completed S2 Opus repeat |
| --- | --- | --- |
| RFEs / iterations | 3 / 1 | 3 / 1 |
| Benchmark outcome | FAIL reviewer return gate | PASS |
| Job wall time | 3070 s / 51.2 min | 5323 s / 88.7 min |
| Successful captured generation calls | 283 | 248 |
| Substantive specialist results | 2/12 | 12/12 |
| Cache-write input | 1696541 | 1945238 |
| Cache-read input | 11038816 | 9882208 |
| Output tokens | 216778 | 264161 |
| Published scores | 7/8, 8/8, 6/8 | 7/8, 7/8, 6/8 |
| Rate-limit / stream failures | 0 / 0 | 0 / 0 |

S2 uncached input: 115760. Checker reports 71211 thinking tokens, included in
output rather than additive. All 248 API request/response pairs report Opus 4.6
and join exactly to complete relay streaming records. S2 is 37.6 minutes longer
in this pair while generating fewer calls and more output. Different returned
content, repeated full-batch reviews, retained artifacts, relay builds and n=1
prevent attributing the runtime difference to orchestration alone. The prior
55.7-minute S2 abort is not a complete runtime or cost estimate. No new price
quote or billed-cost inference made here.

Relay capture contains 319 complete records, HTTP200, usage_status=complete,
observation_error=null, all on tanner-jc-personal: 248 Opus streaming generations,
63 Opus count requests, and eight tiny non-stream generations (four Haiku4.5,
four Sonnet4.5, each 22 input / 1 output). The tiny messages are outside the
job API pairs; exact caller remains unestablished, so keep them separate from
strategy usage. No 429, timeout, incomplete stream or cancellation. Twelve
Opus streams successfully exceed 120 seconds, maximum 276.825 seconds.

Final capture independently verifies and receipts are published:
`var/run-data/strat-workflow/markov-run-79d3241a/20261012T021947729737Z/`.
Complete/final=true, errors=[], 20 sources, 3029 files / 1711015450 bytes.
S2 has 497 browsable API files (496 bodies + index) and 2136 strace files,
with MLflow, Jira, Observatory, logs and full available system snapshots.
Launch context preserved separately. This authorized repeat is complete;
no extra inference run or S1/S2 code change.

### Comparison: completed Opus tier 2 S1 versus S2

Comparison uses relay-fixed S1 `markov-run-c5ba3904` and completed S2
`markov-run-79d3241a`: three identical RFE problem statements, one iteration
per design, preserved original design pins. The earlier S2 HTTP429 abort and
pre-fix S1 measurements are historical failures, excluded from the completed
pair. Both captures are verified. Different harness/relay source versions,
retained artifacts and stochastic model work limit controlled inference.

| Metric | S1 Workflow | S2 bash |
| --- | --- | --- |
| Job duration | 3070 s / 51.2 min | 5323 s / 88.7 min |
| Completed strategies/refinements/reviews | 3/3 each | 3/3 each |
| Runtime exit | 0 | 0 |
| Benchmark outcome | FAIL reviewer return gate | PASS |
| Transport / quota failures | 0 | 0 |
| Substantive specialist handoffs | 2/12 | 12/12 |
| Whole-batch scope drift | Both substantive returns | All 12 substantive returns |
| Captured Opus generations | 283 | 248 |
| Uncached input tokens | 1880 | 115760 |
| Cache-write input, 5-minute | 1696541 | 1945238 |
| Cache-read input | 11038816 | 9882208 |
| Output tokens, including thinking | 216778 | 264161 |
| Thinking subset, reported | 71296 | 71211 |
| API list-price equivalent | $21.55163925 | $24.28166650 |
| Equivalent per RFE | $7.18 | $8.09 |
| Published scores, strategies 1/2/3 | 7/8, 8/8, 6/8 | 7/8, 7/8, 6/8 |

Cost recomputed directly from archived eval-result usage and exact joined
relay generation IDs (283/283 and 248/248). Both record exclusively 5-minute
cache creation, zero 1-hour writes. Standard global Opus4.6 rates reconfirmed
2026-10-12: $5 uncached input, $6.25 cache writes, $0.50 cache reads and $25
output per million, [official pricing](https://platform.claude.com/docs/en/about-claude/pricing).
This is an API list-price equivalent for managed Claude OAuth workload, not
a measured subscription invoice or consumption of its five-hour allowance.
Provider Batch API discounts do not apply to this ordinary streaming batch.
Count operations and separately captured tiny non-Opus generations are excluded.

Cost components (uncached/write/read/output): S1
$0.009400/$10.603381/$5.519408/$5.419450; S2
$0.578800/$12.157738/$4.941104/$6.604025.
S2 has 12.4% fewer generation calls but 21.9% more output and more cache writes;
its equivalent cost is $2.73 / 12.7% higher. Aggregate input is 12.737M versus
11.943M, repeated across separate conversations, not a context-window size.
Thinking is already inside output; never add the subset a second time.

S2 takes 37.55 extra minutes / 73.4% longer in this pair. S1's two-worker
pipeline overlaps scoring/review work; its three review tasks take about
15.2/19.0/16.3 minutes individually. S2's archive index identifies three
successive review sessions (first/last response timestamps):
01:11:14–01:27:54, 01:28:21–01:50:50, 01:51:17–02:18:49 UTC.
Its first review starts after the three successive refinement sessions.
These are measured scheduling differences; returned content, scope duplication
and request latency also differ, so concurrency is not an isolated causal
estimate of the full 37.55-minute gap.

**Accuracy interpretation:** both satisfy artifact cardinality, labels/comment
agreement and cleanup checks. S2 demonstrably preserves 12 substantive
specialist returns while S1 delivers only two and loses ten handoffs. S1
nevertheless publishes complete-looking specialist sections; their existence
does not establish faithful incorporation of the forked assessments.
Neither passing handoffs nor passing the benchmark proves verbatim review
fidelity or technical truth. Every substantive handoff in this pair expands
beyond its per-strategy target. Reported rubric scores are model judgments
about different generated strategies, not independently scored accuracy.

Both designs publish aggregate approve despite at least one specialist revise:
S1 strategy1 testability=revise; S2 strategy1 testability=revise, strategy2
feasibility=revise, strategy3 testability=revise. Aggregate needs_attention=false
does not establish unanimous reviewer agreement. Third-strategy unresolved
implementation questions remain visible in prose. No ground-truth or independent
expert assessment has been performed for these outputs. The one-point
difference in strategy2's score does not establish greater accuracy in S1.

Interpretation: S1 is faster and cheaper in this pair, but fails the reviewer
handoff contract. S2 has stronger observed handoff correctness and a complete
benchmark pass, at longer duration and modestly greater equivalent cost.
Both need specialist scope isolation; factual strategy accuracy remains
unmeasured. No new run or implementation change performed for this comparison.

#### Scheduling confirmed from archived workflow code and exact request joins

S1's executed JavaScript is embedded in the local_workflow task_started prompt
in archived workflow/stream.jsonl. It explicitly calls `parallel()` for
per-strategy refinement and `pipeline()` for score then review. Actual request
intervals confirm two concurrent top-level strategy tasks; this is coordination
by the workflow JavaScript rather than repeated primary-model decisions.

S1 relay generation IDs joined through API index.jsonl give these UTC intervals:
refine1 17:08:21–17:15:31, refine2 17:08:24–17:14:48, refine3
17:14:48–17:20:40. Score1/2 begin together at 17:20:54/56. Score3 starts
17:23:18; review1 starts17:23:39 alongside it. Review2 starts17:26:30 after
score3; review3 starts17:38:51 after review1. Review ends respectively
17:38:51, 17:45:27, 17:55:10. Combined score/review span is about34.3min.

S2's archived API index and agent log show three sequential refinements followed
by three sequential review sessions, whose internal scoring is included in
each review. Review1/2/3 begin about01:11, 01:28, 01:51 UTC and end about
01:28, 01:51, 02:19. Combined score/review span is about68min.
The roughly34-minute phase-span difference accounts for most of the observed
37.55-minute wall gap, but does not isolate concurrency's causal contribution:
individual task durations and output content also differ, and S1 loses10/12
specialist handoffs. Bash can implement concurrency; the observed sequential
scheduling is a property of this pinned S2 implementation.

#### Insight: specialist completion and delivery of findings are separate

"Lost specialist handoffs" describes missing assessment content in the Skill
tool result delivered to the agent assembling a strategy's final review.
That receiving agent is a review step agent, rather than the outer S1 agent
that launched the JavaScript workflow. Each strategy invokes four specialists:
feasibility, testability, scope and architecture.

In relay-fixed S1 `markov-run-c5ba3904`, ten of twelve specialist calls return
only `Skill execution completed`; two return substantive assessments. The
specialists ran and their work is present in captured evidence, but those ten
tool results carry no findings, concerns or recommendation. Completed S2
`markov-run-79d3241a` returns substantive assessments through all twelve
expected handoffs. This separates task execution from result delivery.

S1 nevertheless publishes final documents containing specialist sections.
It remains unverified whether those sections faithfully incorporate the
specialists' findings through another route or are reconstructed by the
receiving agent. Missing tool-result prose does not establish that the
underlying assessment was deleted, nor that the published prose was fabricated.
Establishing provenance would require tracing alternate reads/messages and
comparing specialist findings with the final published sections.

Consequently, exit zero, task-completed notifications and APPROVE verdicts
cannot substitute for checking the returned assessment and its incorporation.
Execution, result delivery, target scope and final review fidelity are separate
properties. S1 fails the observed delivery check; S2 passes delivery while
still exhibiting whole-batch scope drift. Parallel scheduling alone does not
explain the handoff defect, and this evidence does not establish a causal link
between concurrency and missing findings.

Related: [reviewer output loss](../bugs/open/strat-workflow-reviewer-output-loss.md),
[reviewer scope drift](../bugs/open/strat-workflow-specialist-review-scope.md).

### Production recommendation after benchmark and binary investigation

Recommendation, awaiting an implementation decision: use the bash-based design
as the production foundation, with explicit agent invocations and externally
validated, persisted results. Preserve current benchmark pins; this is advice,
not authorization to modify S2 or deploy a new production pipeline. The current
S2 still requires hardening, especially specialist scope isolation.

The completed Opus pair favors S1 for speed/equivalent cost (51.2min/$21.55
versus 88.7min/$24.28), but favors S2 for observed delivery of specialist
assessments (12/12 versus 2/12). The GLM single-RFE pair reproduces the same
direction for reviewer delivery: S1 acknowledgement-only returns versus S2
four substantive results. These are limited observations rather than proof
of universal behavior or independent factual accuracy. Missing handoffs matter
more to production review integrity than the observed speed advantage.

Claude Workflow itself executes deterministic JavaScript and provides useful
parallel/pipeline helpers, journals and cached-prefix replay. Its core is not
an LLM choosing every scheduling decision. However, the tested integration
adds script-to-agent schemas, nested Skill returns, background completion and
session restoration boundaries. Binary controls show that rejected parallel
branches can become null while the outer workflow completes. Journal replay
is useful, but cross-process restoration/concurrent resume was not exercised;
the inspected local path had null total token budget and no separately
identified total workflow deadline. Those observations do not mean every
Claude invocation lacks timeout or budget controls.

An external script runner makes invocation status, output validation,
checkpointing, cancellation and publication rules directly inspectable and
testable. It still must implement them; neither exit zero nor prose that
looks complete proves the business task succeeded. Anthropic documents
programmatic CLI JSON output and schema-constrained results, which can support
these boundaries, without replacing application-level validation:
[headless interface](https://code.claude.com/docs/en/headless).

Recommended hardening before production:

- Persist each specialist assessment with run/strategy/role identity and
  validate target scope, required findings and completion before composition.
  Verify the final review incorporates those findings and explicit dissent.
- Add bounded concurrency for independent strategy stages, with separate
  artifact paths and controlled shared writes. S1's scheduling advantage can
  be adopted without requiring its native Workflow result boundaries; do not
  promise an unmeasured future speedup.
- Persist checkpoints and make publication idempotent; enforce external
  deadlines, bounded retries and quota-aware pause/resume. The earlier S2
  account429 is an infrastructure constraint, not a bash-specific defect.
- Retain the proven run archives and require validated business results,
  rather than process/workflow completion, to mark a pipeline successful.

Keep bash as a thin execution layer under the existing operational job/run
infrastructure; avoid growing a single shell script into the whole durable
workflow service. Reconsider native Claude Workflow after reproducible tests
establish faithful nested-result delivery, target isolation, fail-closed
handling, restart/cancellation behavior and enforced limits for the exact
deployed version. No extra model run or implementation change made here.

### 2026-10-12: Production-gap investigation, first two priorities

Twenty deterministic result-boundary matrix cases and a configured-agent
workaround now reproduce and explain missing specialist Skill returns in pinned
Claude2.1.296. Forks inherit the receiver's StructuredOutput tool/schema. A
tool-ending specialist loses earlier prose/structured fields through the Skill
last-assistant-text projection and returns an acknowledgement. Prose-ending
controls deliver. Ordinary CLI --json-schema also reproduces: this is not a
Workflow scheduling defect, and shell orchestration is not intrinsically immune.
A custom specialist agent with an explicit tool whitelist excluding
StructuredOutput returns prose while preserving the receiver's outer schema.
Direct schema assessment calls also avoid the nested projection. Both remain
subject to required-result and target validation; no S1/S2 edit was made.

Read-only provenance audit covers12S1/12S2 Opus and4S1/4S2 GLM calls. S1 Opus
ten acknowledgement-only endings use SO; its two delivered testability endings
use text. S2 Opus has no SO tool in inspected specialist requests and returns12
reports. S1 GLM explicitly recovers earlier text from native transcripts after
four missing expected returns: three full selected bodies and substantial
architecture prose arrive through Bash/Read. Some S1 Opus published sections
instead closely follow scorer material read before specialist launches.
Missing expected return prose does not establish fabricated published sections.
Expanded target keys reach the specialists; whole-batch scope drift is not
explained by dropped argument substitution. Independent accuracy and exhaustive
semantic fidelity remain unmeasured.

This narrows the original recommendation: explicit validated/persisted role
contracts are necessary with either execution path. Native Workflow's scheduling
can be retained if those contracts are enforced; an external runner's advantage
must be justified by durability/control boundaries, not by an assumed immunity
to nested Skill loss. The recovery/cancellation/limits/retry probes were then
completed and are recorded in the section below; do not treat any of this as
authorization to alter production or pins.
Maintained reports: [handoff diagnosis](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-specialist-handoff.md)
and [review provenance](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-review-provenance.md).

### 2026-10-12: Remaining workflow production controls completed

The handoff's remaining controls (crash recovery, cancellation/deadlines,
budget/concurrency, retries/incomplete streams, replay with changed shared
state) are now run and verified: twenty-three mock-only cases plus three
crash-resume completions against the pinned 2.1.296 binary, all checked by an
executable verifier. Maintained report:
[workflow operations](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md).

Findings that matter for the S1/S2 decision:

- **Recovery is at-least-once for un-journaled agents.** After SIGKILL, a
  fresh-process `resumeFromRunId` re-executes any agent without a journaled
  result from scratch, duplicating its tool side effects; journaled results
  are reused without re-execution. A truncated journal entry is treated as a
  missing result, not corruption, and also re-executes. Neither design gets
  exactly-once side effects for free; publication must be idempotent and
  externally validated either way.
- **Cancellation and the print background-wait ceiling terminate children.**
  `TaskStop`, SIGTERM and the ceiling all stopped an in-flight fixture shell
  with no late writes. The ceiling kills the workflow (state `killed`) rather
  than detaching it. SIGTERM and stall exhaustion still emit `success`-looking
  CLI result events while the workflow dies or fails — exit status alone does
  not establish workflow outcome, on either path.
- **The `--max-budget-usd` gate fires at agent launches and at completion.**
  A final agent can exceed the budget while the workflow still completes;
  the failure surfaces only in the CLI's final result and exit code. Nested
  Skill fork usage is counted. The concurrency override is honored and shared
  globally with nested workflows.
- **Request-level retries are side-effect safe; agent-level restarts are
  not.** Single 429/500/broken-stream faults retried without duplicating a
  counter; retry exhaustion and stall recovery (up to five iterations, six
  executions) restart the agent conversation and re-execute side effects.
- **Replay does not detect changed shared state.** Changed files,
  instructions and discovered skills are ignored when prompt/options match;
  the cached result is served. Freshness is the caller's responsibility.

These findings strengthen the existing recommendation (validated, persisted
role contracts and external result validation) without changing it: the
external runner's advantage is durability/control boundaries, not immunity to
side-effect duplication, which both paths exhibit under restart conditions.

### 2026-10-12: Network-fault taxonomy and the primary's exposure window

The retry engine was then recovered from the bundle and confirmed with five
further controls (persistent 429, connection reset, spend-limit 429, 529
overload, notification-turn fault); see the
[operations report](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md).
Points that matter for benchmark interpretation:

- **Spend/usage-limit 429s are classified non-retryable** and fail the
  request immediately — the mechanistic explanation for this benchmark's
  observed behavior that account usage-limit 429s fail jobs outright, while
  ordinary 429/5xx/network faults retry with backoff (300 first-party / 10
  third-party default retries, ~0.5 s exponential base) and then restart the
  agent conversation once, re-executing tool side effects.
- **The controller is quiescent while a background workflow executes**; its
  next API call is the notification-delivery turn. If that turn fails
  terminally, the CLI reports an API error with exit 1 *even though the
  workflow completed and its result is durably journaled* — job exit status
  alone can misreport workflow success, so benchmark evaluation should keep
  reading the workflow state/journal (as the run-data archives already do)
  rather than trusting the CLI result event.

### 2026-10-12: ANTHROPIC_LOG warning fixed for future jobs

User requested the deferred cleanup. Removed the incorrect directory-valued
ANTHROPIC_LOG defaults from Kubernetes and OpenShell dashboard launchers.
Raw API captures continue through OTEL_LOG_RAW_API_BODIES in runner wrappers.
Explicit valid extra_env log levels remain supported. Eighteen focused tests
pass; local native2.1.296 mock reproduces the old warning and verifies corrected
warning-free execution with one request/response dump and index in both cases.
No paid inference or extra benchmark. make host-rebuild-dashboard deploys the
fix; new pod healthy, source hashes and both environment builders verified.
No agent/relay rebuild or S1/S2 edit. Historical captures remain unchanged.
[Fix evidence](../tasks/done/fix-anthropic-log-directory-warning.md).

### 2026-10-12: Consolidated benchmark insights, with updated interpretation

This recap supersedes stronger historical interpretations where later evidence
resolved a mechanism or exposed a confound. Original measurements remain intact.

| Tested workload | S1 observed duration | S2 observed duration | Interpretation |
| --- | --- | --- | --- |
| Single-RFE Haiku, fixed architecture, 3 rounds/design | Mean21.8min | Mean13.3min | Harness smoke; S1 extra calls/reviewer reruns; incomplete relay repair |
| Single-RFE Opus, 3 successful rounds/design | Mean27.0min | Mean31.8min | Historical, unequal120s stream cuts; S2 third round required quota-reset repeat |
| Completed three-RFE Opus, repaired relay, 1/design | 51.2min | 88.7min | No transport errors; S1 handoff gate FAIL, S2 PASS; scheduling/content differ |
| Single-RFE GLM, 1/design | 40.4min | 46.1min | Both smoke PASS; S1 expected returns missing but transcript recovery observed; S2 stream recovery |

1. **Completion is insufficient.** Check cardinality, recorded phase completion,
   model identity, labels/comment agreement, lock release, returned assessments,
   target scope and final incorporation separately. Historical smoke PASS did
   not test all these properties. Markov reporting completion can legitimately
   contain a failed design result. Nonempty acknowledgement/error/progress text
   is not a substantive review. Aggregate APPROVE is not unanimous specialist
   approval or independent technical truth.
2. **Specialist loss now has a reproduced cause.** Parent schemas expose
   StructuredOutput to nested Skill forks. A final tool-only assistant record
   produces an empty text selection and completion fallback, dropping earlier
   prose and structured fields from that Skill result. This occurs in ordinary
   CLI --json-schema too; parallelism is not necessary. S1 Opus has10/12 affected
   returns and S2 has0/12 in the completed pair. A custom specialist tool whitelist
   or direct schema assessment avoids the boundary in mock controls. Neither
   remedy has been validated in a paid strategy run or deployed.
3. **Missing return does not settle provenance.** S1 GLM explicitly recovers
   earlier specialist text through transcript reads, with architecture/structured
   field completeness limits. Some S1 Opus sections reuse within-run scorer
   findings. One audited Opus feasibility section omits a distinct specialist
   routing concern. Broad claims of fabrication or complete loss of all findings
   are unsupported; delivery and semantic incorporation need separate evidence.
4. **Scope remains defective.** Distinct batch fixtures produce three distinct
   strategies without deduplication. Nevertheless every substantive specialist
   return in the completed Opus pair assesses all three despite individual
   targets. Expanded prompts contain the correct keys; arguments were not
   silently dropped. The extra review work and attribution problems remain.
5. **Structured shape is not semantic correctness.** Haiku's first S1 batch
   wrote a completed refinement but returned nested JSON as a string in recorded.
   A permissive schema accepted it; exact-key comparison rejected it and omitted
   that strategy from review. This distinguishes a model formatting error from
   an orchestration reconciliation gap; weaker reasoning is not proven by n=1.
6. **Scheduling changes batch performance.** S1 runs deterministic JS inside
   Claude and uses parallel refinement and pipelined scoring/review, observed
   with two top-level tasks. S2 serializes strategy stages. Combined score/review
   spans about34 versus68min in the completed batches. Single-RFE tests expose
   little cross-strategy parallelism. Individual content/latencies also differ;
   the whole37.55min wall gap cannot be assigned to concurrency alone.
7. **Calls, costs and context measure different things.** S2 has248 versus283
   completed batch generations but more output/cache writes. Standard Opus API
   equivalents are$24.28 versus$21.55, about13% more for S2, not measured OAuth
   invoices. S1 batching shows no clear per-RFE savings versus historical singles
   ($7.18 versus$6.95), with different fixtures/relay exposure. Thinking is already
   included in output; cache reads are repeated usage, not one giant context.
8. **Primary context stays small during delegated work.** S1 smoke primary
   input grows from about24k to30k, and repaired batch ends26.9k. No primary
   model calls during the long background wait; completion/artifact reads add
   bursts of context. Helpers have separate windows, sometimes100k–193k. The
   finding establishes primary isolation, not reduced aggregate helper cost.
   Exact API-pair inspection attributes the repaired S1 batch's 167579-token
   sample to the architecture reviewer (request 498a2999-abbf-4b4c-b745-0fefeae475ea,
   response d3f42734-07f7-479e-9297-882e4e503a4d). Its history contains 13 distinct
   architecture-context Read targets: LATEST_VERSION, PLATFORM.md and 11 component
   documents. This verifies the role and those reads; it does not establish that
   every architecture overlay was read.
9. **Infrastructure confounded early timing.** Managed relay accounts still
   had120s deadlines after the first configured600s change. Full repair allows
   successful streams beyond120s, including276.8s in S2. Earlier timings remain
   pre-fix observations; subtracting timeout seconds is not a new measurement.
   Shared-account quota aborts interrupted both the L1 campaign and an S2 batch.
   Record quota completion/delays, without treating call count as a fixed limit.
10. **Model substitutions change behavior.** Haiku finds plumbing defects but
    does not predict Opus timing, output volume, recovery or scores. GLM routing
    works with explicit helper/alias pinning and the private key retained on the
    relay. S2 GLM recovers from an incomplete stream/cancellation with same-model
    non-stream fallback. Provider pricing/context/cache semantics are unverified;
    its absent relay message-ID joins are a telemetry limitation, not missing
    job API evidence. No controlled GLM-versus-Opus quality comparison exists.
11. **Evidence preservation and isolation both matter.** The early wipe lost
    raw historical captures; all subsequent reset checkpoints require verified
    host archives/receipts. API indexes and unique tool IDs establish exact
    joins; aggregate session IDs, extracted mtimes or successful response dumps
    alone can mislead. Our MLflow setup does not cover all nested tool activity;
    strace cannot alone distinguish in-process agents. Retained shared files can
    enter later reviews, so future fixtures need scope/isolation controls.
12. **Specific plumbing fixes are complete.** Architecture snapshot refresh
    previously sparse-checked the enclosing strategy repository; the identical
    fix on both design pins preserves the repo and snapshot. Relay telemetry and
    managed deadlines were repaired. Invalid directory-valued ANTHROPIC_LOG
    defaults are now removed/deployed; raw captures remain enabled.

13. **Changes carry an evaluation burden.** Adding an intermediate script call
    to a Native Workflow introduces model-mediated invocation and result-transfer
    boundaries, even when the script itself is deterministic. It may change an
    existing agent task rather than create another agent. Check exact invocation,
    failures, returned data and downstream skill inputs with focused controls
    and live cases. A full old/new A/B campaign is needed to support comparative
    performance or quality claims, not every edit. Prior runs remain evidence for
    their tested version; changed paths need requalification before carrying
    forward reliability claims. Direct script execution can test routine steps
    without model decisions, but both designs still need live checks when agent
    prompts or inputs change. Maintenance/evaluation savings are an architectural
    implication, not a measured result. No additional paid run is authorized.

14. **Qualify the configured maximum, not just the average.** Production accepts
    ten RFEs every six hours, with roughly three on average. That average gives
    neither the most common batch size nor the frequency of full batches. Keep
    the ten-RFE limit: reducing it to three would lower nominal daily capacity
    from 40 to 12 RFEs before failures/delays. Preserve small-batch regression cases,
    but require distinct ten-RFE fixtures and 40 correctly attributed reviewer
    reports per design for full-size qualification. Level 3 now proposes ten
    paired ten-RFE batches, with larger confidence studies conditional on that
    workload; estimating ordinary production failure frequency also needs its
    actual batch-size mix. Linear scaling of the measured three-RFE pair gives
    roughly 84M tokens / $153 per ten-RFE pair, or 840M / $1530 for ten pairs, using
    rounded estimates. These are unmeasured Opus 4.6 API-equivalent projections;
    replace them with a full-size measurement before funding repeats. Applying
    the same ticket/repeat scaling to the 139.9-minute paired job duration gives
    about 78 active job hours for ten pairs and 466 for sixty pairs. This assumes
    each design's observed scheduling and sequential benchmark jobs; quota waits,
    collection and independent judging are additional. Full-size timing remains
    unmeasured. The registered R1 three-RFE retest is a scheduling comparison, not
    ten-RFE qualification. No new fixture, pipeline change or paid run is made
    by this documentation update.

15. **Level 5 separately evaluates strategy content.** Pipeline review
    calls are already included in producer usage. Post-run content evaluation
    adds a new budget, varied by judge model, rubric, context, samples and retries.
    The proposed 20 full-size jobs yield 200 final strategies if all artifacts
    exist. Two judge models and two samples give 800 combined-rubric assessments,
    or 400 per model; four separate criterion judges multiply that by four.
    Rejudge frozen outputs to compare judges without rerunning the producer.
    Keep a fixed primary judge across design/model variants and calibrate judge
    choices against human assessments, retaining errors, coverage and disagreement. Same-model
    judging is a baseline, not independent proof of technical correctness.
    agent-eval-harness at 21808e6 supports deterministic and LLM/agent judges,
    repeated scoring, pairwise comparison, opaque external CLI execution and
    Kubernetes/Harbor. It is broader than output-only model A/B testing, but our
    artifact mapping/execution integration is not implemented. Judge usage is
    separate from producer cost; SDK prices may be null and Anthropic summary
    input merges cache categories. Retain raw usage for priced API equivalents.
    Detailed [assessment](../notes/strat-workflow-content-eval-harness-assessment.md)
    contains source pins, limitations and a proposed integration. No paid judge
    call, producer rerun or integration deployment is authorized by this note.

The tested working baseline remains S2; S1 demonstrates useful concurrency and
lower observed batch cost. However, the confirmed return-contract defect is
shared by schema-constrained CLI and Workflow and has configuration remedies.
Production choice should prioritize validated, persisted assessment contracts,
scope/fidelity and operational durability rather than a blanket language winner.
Markov orchestrates these benchmark jobs; a native Markov strategy arm has not
been benchmarked. Current batch coverage is three new RFEs, not the full proposed
mixed-state/resume matrix. n=3 historical singles and n=1 completed batches/GLM
pairs do not establish general speed, cost or accuracy rankings. Independent
technical grading remains absent. No new run or pipeline redesign for this recap.
