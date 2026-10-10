# strat-workflow benchmark

Compares two designs for strat-creator's strategy pipeline on the same RFEs:

- **workflow:** the Claude Workflow from strat-creator PR #83, started with
  `scripts/run-workflow.sh`;
- **bash:** PR #80's bash entrypoint, `.fullsend/scripts/strategy-entrypoint.sh`.

Each design runs as it is, as a dashboard script job, with Model Relay,
MLflow, OTel, strace and API dumps. The plan, its pass criteria and all
results so far are in
[`.ledger/plans/strat-workflow-eval-plan.md`](../../../.ledger/plans/strat-workflow-eval-plan.md).

This directory is a Markov directory workflow. Markov runs on a runner pod.
Its steps call the dashboard API, watch the job pods with `k8s_job_wait`,
and run the checks. Every model call happens in the job pods.

## Running it from markovd

1. Push the change to `main` on GitHub. Jobs clone their scripts from
   Breadboard at the commit markovd imported, so it must be pushed.
2. In `markovd.local`, sync project 1 (Breadboard) and import
   `var/benchmarks/strat-workflow`. It appears as
   `var-benchmarks-strat-workflow`. markovd records the commit and passes it
   to every run as `workflow_source_commit`.
3. Start a run of the workflow. Useful settings (`vars.yaml`):

   | Setting | Default | Example |
   | --- | --- | --- |
   | `tier` | `smoke` | a tier in `vars/tiers.yaml` |
   | `only_tests` | all | `S1,S2` (haiku only) |
   | `repeats` | the tier's (3) | `1` |
   | `variants` | each test's own | `haiku,opus` (A/B) |
   | `wipe_at_start` | `true` | `false` keeps earlier artifacts and MLflow |
   | `job_timeout` | `7200` | seconds before a job is stopped |
   | `breadboard_ref` | the imported commit | another pushed commit |

The run refuses to start while any dashboard job is pending or running.

## What a run does

```text
main
  wipe                  artifacts volume, MLflow, Observatory (once)
  rounds                for_each: repeats | seq
    round               for_each: the tier's tests, for_each_when: only_tests
      test-variants     for_each: variants | csv | default: the test's own
        run-test        seed Jira, submit the design's job, wait, check
  summarize             summarize.py over every run's eval-result; summary.md and
                        eval-results.json saved to
                        /app/artifacts/benchmarks/strat-workflow/<markov run id>/
  review                gate (off by default: markovd can't resume a pause yet)
```

`run-test`, for one test under one variant:

1. `describe_run`: one `run` record (ID, test, arm, variant, model,
   commits, MLflow experiment), kept with the result.
2. Seed: a dashboard script job runs `seed_scenario.py` at the Breadboard
   commit, and `job_wait` watches it. The run reads the job's `seed.json`
   through the dashboard's file API and asserts the seed check passed.
3. Submit the design's job: the `submit` step calls the workflow
   `submit-{{ test.arm }}` (`submit-workflow.yaml` or `submit-bash.yaml`), each
   with its full request in the YAML.
4. `wait_for_run` is a `job_wait` with `ignore_errors`: a failed job is a
   failed test, recorded rather than raised. A job still running at the
   timeout is stopped before the next run resets Jira.
5. `check` runs `check_run.py`, which prints the run's eval-result.
   `write_file` saves it next to the job's artifacts as
   `/app/artifacts/scripts/<job>/eval-result.json`.

The Markov run fails only when the benchmark itself can't go on, for
example when seeding fails.

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

`check_run.py` and `summarize.py` use only the standard library. They read
`DASHBOARD_BASE` and `JIRA_BASE`, so they also run from the host:

```bash
cd var/benchmarks/strat-workflow/scripts
export DASHBOARD_BASE=https://dashboard.local JIRA_BASE=https://jira.local
python3 check_run.py '<run json>' <job name> RHAIRFE-1 completed
```

`reset_environment.py` does the full reset and seed from the host, with no
Markov run.

## Layout

- `vars.yaml`: run settings.
- `vars/tiers.yaml`: test lists per tier.
- `vars/arms.yaml`: each design's pinned commit and settings.
- `vars/models.yaml`: variant names to models.
- `workflows/`, `step_types/`, `rules.yaml` and `meta.yaml`: the Markov
  workflow.
- `scripts/`:
  - job side: `run-workflow.sh` and `seed_scenario.py`;
  - runner side: `check_run.py`, `summarize.py` and `benchlib.py`;
  - host side: `reset_environment.py`, `selfcheck.sh` and
    `snapshot-architecture-context.sh`.
- `data/scenarios/` and `data/rfe-templates/`: what the seed job creates in
  Jira.

Saving results needs markovd's default `pipeline-artifacts` mount
(`MARKOVD_JOB_VOLUMES` in `deploy/k8s/15-markovd.yaml`). This layout needs
Markov `7723016` or later, for templated workflow names, `write_file` and
`markov_run_id`, plus: `ignore_errors`,
`for_each_when`, `vars/`, step descriptions, native expressions in
`set_fact`, and the `csv` and `seq` filters.
