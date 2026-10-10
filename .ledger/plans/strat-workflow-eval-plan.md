# Testing the strat-creator Claude Workflow in Breadboard

Created 2026-10-09. Source: `eval-plan-workflow-vs-bash.md` in
`2026_10_09_strat_creator_workflow_debate/`.

## What we are trying to learn

strat-creator turns approved RFEs into strategy documents in three steps:
create, refine and review. Production runs those steps from a bash script.
gsun's PR #83 runs the same steps from a Claude Code **Workflow**: a small
JavaScript file that Claude runs. It starts one helper agent per step and
passes the results between them.

The question here is narrow: **does the Workflow version run the steps
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
| PR #83's Workflow | Pinned to the PR's commit `6b78355` and mirrored into the GitHub emulator, so every run uses exactly the same code. |
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
4. **Smoke tests use the real skills; the full tier mostly uses stubs.** A
   smoke test runs one real RFE with the real create, refine and review
   skills. PR #83 also ships stand-in versions of those skills that do the
   bookkeeping (write files, record progress) without real model reasoning.
   The full tier is about step order and record-keeping across many states,
   not writing quality, so most of it uses the stubs. They're much cheaper
   and faster. Real skills come back for a few confirmation runs.
5. **Our own checks decide pass or fail, not just the exit code.** A run can
   "succeed" and still post something wrong to Jira. That's how the known
   rfe-autofixer incident happened. After every run, a script reads the run's
   files and Jira and checks the list in "What counts as a pass".

## What we build first

**Pinned values so far** (2026-10-10):

| Item | Value |
| --- | --- |
| PR #83 (Claude Workflow) | `opendatahub-io/strat-creator` branch `pr-83` in the GitHub emulator, commit `6b78355ebc450ff4737fd10ba4857c26086ceac0` |
| PR #80 (bash entrypoint) | branch `pr-80`, commit `78ab3f1e97b09d02229bd03dd045a7eed97b0c33` |
| PR #81 (single agent, for later) | branch `pr-81`, commit `9350c89bcf1fd09acc0a3d1ef44ec6a59e47efe3` |
| Architecture snapshot | `/app/.context/snapshots/architecture-context/7d61f097a9220aeb1280837b66b532177ec558b6` (`rhoai-3.6-ea.2` and `overlays/`, 1,845 files, 88 MB) |
| Smoke scenario | `data/scenarios/smoke-one-rfe.yaml`: one eligible RFE, template `kserve-canary-rollback` |
| Eligibility at PR #83 | labels `strat-creator-3.6`, `rfe-creator-autofix-rubric-pass` and `rfe-creator-feasibility-pass`, checked against the commit's own discovery query |


| # | Piece | What it is |
| --- | --- | --- |
| 1 | Pinned PR code (done 2026-10-10) | Push PR #83's commit `6b78355` as branch `pr-83` of `opendatahub-io/strat-creator` in the GitHub emulator, which already hosts that repo. Jobs clone it at that exact commit. |
| 2 | Architecture snapshot (done 2026-10-10) | One fixed copy of the architecture-context documents on the shared `/app/.context` volume, so every run reads the same reference material and nothing is fetched from the internet mid-test. |
| 3 | Jira seeding (built 2026-10-10; real reset pending) | A script in `var/benchmarks/strat-workflow/scripts/` that resets the Jira emulator and creates the RFEs (and existing strategies, labels and comments) for one named scenario from `data/scenarios/`. It reuses `var/demos/fullsend-entrypoint-poc/jira-seed/prepare.py` and `var/demos/fullsend-agent-led-poc/seed_rfe.py`. |
| 4 | Script entrypoint in the job API (built 2026-10-10; [task](../tasks/current/strat-workflow-eval-script-mode.md)) | `/api/jobs/submit` accepts a script to run in place of `claude -p`, after the usual setup. Plus two arm scripts in `var/benchmarks/strat-workflow/scripts/`: one runs PR #83's Workflow, one runs PR #80's bash entrypoint. Details below. |
| 5 | MLflow experiment name per job (built 2026-10-10) | An explicit `mlflow_experiment` field on the job API. Today the name is built automatically from the skill and model. |
| 6 | Checks | A script that reads the run's result, progress file, artifacts and Jira, and writes `eval-result.json` with each check's pass or fail and the reason. |
| 7 | Test driver (Markov) | A Markov workflow that takes a list of tests (scenario, repeats) and one or more variants (named sets of model, skills and commit; see "A/B comparisons"). For each test, variant and repeat it seeds Jira, submits the job through the dashboard API, waits for the job, reads its `eval-result.json`, and adds the outcome to one summary table with the variants side by side. Details below. |
| 8 | markovd setup | Register Breadboard's GitHub repository as a markovd project, and patch markovd so git imports keep the helper scripts and record their commit. Details under "The Markov test driver". |

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
   - PR #83's commit (`6b78355`) and PR #80's head commit are pushed to
     `opendatahub-io/strat-creator` in the GitHub emulator first (piece 1).
   - The arm script clones that repository at the exact commit.
   - PR #83's Workflow is a file inside that clone,
     `.fullsend/plugins/strat-pipeline/workflows/strat-pipeline.js`, loaded
     with `claude --plugin-dir .fullsend/plugins/strat-pipeline`. Its
     prepare and check scripts are in `.fullsend/shared/`.
   - PR #80's entrypoint is `.fullsend/scripts/strategy-entrypoint.sh` in its
     clone.
   - Job pods can already clone from `github.local`: FQN skill jobs do it,
     with the internal CA trusted in the pod.
2. **Our scripts (arm scripts, checks, the `fullsend-claude` stand-in), from
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

**The two arm scripts:**

| Script | Runs | What it does |
| --- | --- | --- |
| `run-workflow.sh` | PR #83, Claude Workflow | Clone strat-creator at the pinned commit. Run `pre-strategy.sh`, which picks and locks the RFE; exit 78 means nothing to do. Run `claude --agent strat-single --plugin-dir .fullsend/plugins/strat-pipeline -p "Run the agent task"`. Run the PR's checker (`validate-output.sh`); on failure, run the Workflow once more with the feedback (two attempts, like fullsend). Then run our checks and release any locks. |
| `run-bash.sh` | PR #80, bash entrypoint | Clone strat-creator at PR #80's commit. Put a small `fullsend-claude` stand-in on the PATH, because PR #80 calls the helper that fullsend normally installs. Run `strategy-entrypoint.sh RHAIRFE-N`. Then run our checks and release any locks. |

**Things PR #80 needs adapted:**
- **Model:** its `strategy-model.sh` hard-codes `claude-opus-4-6` for every
  helper agent. The `fullsend-claude` stand-in has to apply the variant's
  model, or haiku runs would silently use opus.
- **Results push:** it requires `RESULTS_PUSH_TOKEN` and pushes results to a
  data repository. Point it at a throwaway repository in the GitLab
  emulator.
- **OTel:** it starts its own OTel collector, which may take over the OTel
  settings from step 1. The first smoke run shows whether Observatory still
  receives its traces; if not, the stand-in or the script needs to forward
  them.

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
  meta.yaml                required: entrypoint (main) and forks (1)
  vars.yaml                required: defaults (tier, repeats, pinned
                           strat-creator commit, dashboard URL, MLflow
                           experiment prefix)
  rules.yaml               required: gate rules (every check passed;
                           429 count under a threshold)
  step_types/
    dashboard.yaml         submit a job through /api/jobs/submit, and
                           wait for it (k8s_job_wait)
    jira.yaml              reset and seed the Jira emulator
  workflows/               one workflow per file, named by its name: field
    main.yaml              pick the tier or comparison, run it, summarize,
                           pause at the review gate
    tier1-smoke.yaml       the smoke tests S1–S4
    tier2-full.yaml        scenarios F1–F11 and the mixed batches
    ab-compare.yaml        one test list under two or more variants
    run-test.yaml          one test × variant × repeat: seed, submit,
                           wait, load eval-result.json, record
    summarize.yaml         build the summary table
  scripts/                 helpers run with script_exec
    seed_scenario.py       reset Jira and create one scenario's issues
    summarize.py           combine eval-result.json files into a table
  data/
    variants.yaml          named variants (opus, haiku, ...)
    tests/                 test lists: tier1.yaml, tier2.yaml, ab-*.yaml
    scenarios/             one seed definition per scenario (S3, F1–F11)
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

**What one test step does in Markov:**
1. Reset and seed the Jira emulator for the scenario.
2. Submit the "strat workflow" job with a `dashboard_api` step, which posts
   to `/api/jobs/submit`.
3. Wait for it with `k8s_job_wait`, which watches the job and keeps its
   logs.
4. Load the job's `eval-result.json` and record pass or fail per check.

**Loops:**
- `for_each` runs over tests × variants × repeats, sorted so variants
  alternate (A, B, A, B).
- Concurrency is 1, because every test resets the one shared Jira emulator.

**Resume:** Markov saves progress after each step. A tier 2 run that dies
after 6 hours resumes from the next test instead of starting over.

**Review stops** are Markov gates that pause the run until you resume it,
so they show in `markovd.local` with the summary so far.

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
| S1 | Claude Workflow (PR #83, `run-workflow.sh`) | haiku-5-5 | until it passes, then 3 | The script mode, the Workflow launch and all the wiring work; checks 1–6 pass on one RFE. |
| S2 | bash entrypoint (PR #80, `run-bash.sh`) | haiku-5-5 | until it passes, then 3 | The same for the bash design, including the `fullsend-claude` stand-in and the model override. |
| S3 | Claude Workflow | opus-4-6 | 3 | The real thing on the production model. Cost per RFE compared with production's ~$8. |
| S4 | bash entrypoint | opus-4-6 | 3 | The same for bash. S3 and S4 together are the first like-for-like cost and time comparison. |

**If S1 won't start,** PR #83's own stand-in-skill test (its pre-written
input, no Jira, dry run) is a cheaper way to debug just the Workflow
launch. It's a debugging aid, not one of the smoke tests.

**Smoke tier passes** when S1–S4 pass every check on every repeat. We also
note how many 429s the account returned. If they get in the way, switching
the relay to a Vertex upstream comes before tier 2.

## Tier 2: full tests (larger, mixed batches)

Goal: show the Workflow keeps its records straight across batch sizes and
the states RFEs are really in. Run it on haiku first to get the scenarios
and checks right, then on opus for the results that count.

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

**Runs:**

| Pass | Skills | Model | Repeats | Purpose |
| --- | --- | --- | --- | --- |
| T2a | stub | haiku | 1 | Get the scenarios, seeds and checks right |
| T2b | stub | opus | 3 | The main evidence: every scenario and batch passes every check, three times |
| T2c | real | opus | 3 | Confirmation on the scenarios that matter most: F1, F3, F6 and one batch of 3 |

**Tier 2 passes** when T2b and T2c pass every check on every repeat. Any
failure gets a written explanation from that run's files: transcript,
strace, API dumps and progress file.

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
- **Reliability:** T2b's scenarios on stub skills, `opus` vs `haiku`.
  Cheap, and it answers "can haiku drive the Workflow?"
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

These are estimates. Heavy 429s from the account would make the runs take
longer.

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
