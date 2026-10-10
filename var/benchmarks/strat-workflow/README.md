# strat-workflow benchmark

Compares two designs for strat-creator's strategy pipeline on the same RFEs:

- **workflow:** the Claude Workflow from strat-creator PR #83, started with
  `scripts/run-workflow.sh`;
- **bash:** PR #80's bash entrypoint, `.fullsend/scripts/strategy-entrypoint.sh`.

Each design runs as it is, as a dashboard script job, with Model Relay,
MLflow, OTel, strace and API dumps. The plan, its pass criteria and all
results so far are in
[`.ledger/plans/strat-workflow-eval-plan.md`](../../../.ledger/plans/strat-workflow-eval-plan.md).

This directory is a Markov directory workflow. Markov runs on a runner pod
and only seeds Jira, submits jobs through the dashboard and checks their
results. Every model call happens in the job pods.

## Running it from markovd

1. Push the change to `main` on GitHub. Jobs clone their scripts from
   Breadboard at the commit markovd imported, so it must be pushed.
2. In `markovd.local`, sync project 1 (Breadboard) and import
   `var/benchmarks/strat-workflow`. markovd records the commit, and passes
   it to every run as `workflow_source_commit`.
3. Start a run of the workflow. Useful settings:

   | Setting | Default | Example |
   | --- | --- | --- |
   | `tier` | `smoke` | test list `data/tests/<tier>.yaml` |
   | `only_tests` | all | `S1,S2` (haiku only) |
   | `repeats` | the tier's (3) | `1` |
   | `variants` | each test's own | `haiku,opus` (A/B) |
   | `wipe_at_start` | `yes` | `no` keeps earlier artifacts and MLflow |
   | `job_timeout` | `7200` | seconds before a job is stopped |
   | `breadboard_ref` | the imported commit | another pushed commit |

The run refuses to start while any dashboard job is pending or running.

## What a run does

1. **Plan** (`plan_runs.py`): tests × variants × repeats, in rounds, so the
   designs alternate.
2. **Wipe once** (`wipe`): the artifacts volume, MLflow and Observatory. The
   context volume, which holds the pinned architecture snapshot, is kept.
3. **For each run** (`run-test`, one at a time):
   - reset Jira and seed the scenario, then check the seed;
   - submit the design's job and wait for it;
   - check the result (`check_run.py`).
4. **Summarize** (`summarize.py`): a Markdown table per run and per test.
   It's the `summarize` step's output in the run.
5. **Review gate:** off by default (`review_stop: "no"`), since markovd can't
   resume a paused run yet.

A failed job is a failed test, not a failed Markov run. The Markov run fails
only when the benchmark itself can't proceed, for example when seeding
fails.

## Checks

`check_run.py` runs these script checks on one new RFE:

| Check | Passes when |
| --- | --- |
| `finished` | the job completed (exit 0) |
| `one_strategy` | exactly one RHAISTRAT, cloned from the RFE |
| `steps_done` | the strategy was created, refined and pushed, and has a verdict label |
| `one_review` | exactly one review comment |
| `records_agree` | the comment's verdict matches the verdict label |
| `no_half_done` | no review comment without a refined, pushed strategy |
| `locks_released` | no `strat-creator-processing` label is left |

It also records the following, without pass or fail:

- wall time;
- the model calls, tokens and error responses, including 429s, summed from
  the job's API dumps.

Relay telemetry is lossy under load, so it isn't used.

## Running pieces by hand

The runner-side scripts use only the standard library, plus PyYAML for
`plan_runs.py`. They read `DASHBOARD_BASE` and `JIRA_BASE`, so they also run
from the host:

```bash
cd var/benchmarks/strat-workflow/scripts
export DASHBOARD_BASE=https://dashboard.local JIRA_BASE=https://jira.local
python3 plan_runs.py --tier smoke --breadboard-ref <sha> --only S1,S2
python3 check_run.py '<run json>' <job name> RHAIRFE-1
```

`reset_environment.py` does the full reset and seed from the host, with no
Markov run.

## Layout

- `data/arms.yaml`: each design's script source, pinned strat-creator commit
  and job settings.
- `data/variants.yaml`: named model variants.
- `data/tests/`: test lists per tier.
- `data/scenarios/` and `data/rfe-templates/`: what gets seeded into Jira.
- `scripts/`: job-side scripts (`run-workflow.sh`, `seed_scenario.py`) and
  runner-side scripts (the rest).
- `workflows/`, `step_types/`, `meta.yaml`, `vars.yaml` and `rules.yaml`: the
  Markov workflow.
