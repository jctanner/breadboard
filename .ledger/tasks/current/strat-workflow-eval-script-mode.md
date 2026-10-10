# Script entrypoint mode for dashboard jobs

Plan: [Testing the strat-creator Claude Workflow](../../plans/strat-workflow-eval-plan.md),
piece 4 ("Script entrypoint in the job API").

## Status

Current. Script mode is built and deployed and its image path is verified
live. The clone path is unit-tested only. The two arm scripts
(`run-workflow.sh`, `run-bash.sh`) are not written yet.

## What was built (2026-10-10)

- **API:** `/api/jobs/submit` accepts `script` (`path`, `args`, optional
  `repo` + `ref`) and `args.mlflow_experiment`. The experiment override
  works for every job type. Script jobs run only on Kubernetes, and a script
  can't be combined with `command`, `fqn` or `prompt`.
- **Validation** in `src/dashboard/job_scripts.py`:
  - an image script must be under `var/benchmarks/`;
  - a clone needs an https URL on github.com, github.local or gitlab.local,
    without credentials, plus a full 40-character commit;
  - paths must be relative, with no `..`;
  - at most 32 arguments, each up to 4096 characters;
  - unknown fields are rejected.
- **Orchestrator:** a script job runs `/app/scripts/run_script.sh`, with
  phase `script-<name>` and runner label `script`. The spec is stored in the
  `script` annotation; job details and the job list return it.
- **`scripts/run_script.sh`:** shared setup, then the script.
  - The setup comes from `scripts/lib/job_setup.sh`: CA bundle, Vertex
    settings, MLflow hooks, shared directory links, model pinning, OTel and
    API dumps, strace.
  - With `repo`/`ref` it clones at the exact commit and checks HEAD; the
    script must resolve inside its root.
  - The script gets `SCRIPT_ROOT`, `JOB_ARTIFACT_DIR`
    (`/app/artifacts/scripts/<job>`), `PIPELINE_MODEL` and
    `PIPELINE_JOB_NAME`.
  - The script runs under `strace -ff` when strace is on, and its exit
    status becomes the job's.
- **Model pinning:** a full model ID such as `claude-haiku-5-5` also pins
  `CLAUDE_CODE_SUBAGENT_MODEL` and every `ANTHROPIC_DEFAULT_*_MODEL` alias. An
  alias such as `opus` sets only `ANTHROPIC_MODEL`.
- **Jobs page:** script jobs show their script path in the table and the
  details window. Their button is **Re-run**, which submits the same script
  and settings again; there's no form tab for scripts.
- **`var/benchmarks/strat-workflow/scripts/selfcheck.sh`:** a wiring check
  with no model call by default (`--call-model` adds one).
- `run_skill.sh` still has its own copies of the setup blocks. Moving it onto
  `job_setup.sh` is a follow-up.

## Verification

- `PYTHONPATH=. uv run --with pytest python -m pytest scripts/test_job_scripts.py scripts/test_dashboard_job_names.py`:
  17 passed. These cover spec validation, the command, the phase, and the
  manifest: command, labels, annotation, MLflow experiment, strace and relay
  env. Existing `tests/test_openshell_orchestrator.py`,
  `tests/test_fullsend_dashboard.py` and
  `scripts/test_bound_mlflow_claude_hooks.py` still pass.
- `make host-rebuild-agent` and `make host-rebuild-dashboard`, then
  through the live API:
  - `script-selfcheck-all-claude-haiku-5-5-1010-004431-f154ff`: Complete;
    selfcheck **14/14 PASS**. That covers relay base URL and project,
    relay health, model pinned for the session, subagents and aliases, the
    MLflow experiment and hooks, Vertex settings, the OTel endpoint, the API
    dump directory, running under strace, the artifact directory, the GitHub
    emulator and the claude CLI (2.1.296).
  - `script-does-not-exist-all-claude-haiku-5-5-1010-004453-1e1884`:
    Failed, with `ERROR: script not found`.
  - A non-benchmark image path and a disallowed repository host were both
    rejected with HTTP 400.
- Jobs page, checked on a local dashboard: the script job's details window
  shows the path and **Re-run**. With `fetch` stubbed, Re-run posted the
  identical script and args.

- Clone path verified live (2026-10-10):
  `script-selfcheck-all-claude-haiku-5-5-1010-005608-42be35` cloned
  Breadboard at `6ffba40`, ran selfcheck from the clone and passed.

## Pieces 1–3 (2026-10-10)

- **Piece 1:** PR heads pushed to the GitHub emulator's
  `opendatahub-io/strat-creator` as `pr-83` (`6b78355`), `pr-80` (`78ab3f1`)
  and `pr-81` (`9350c89`). Anonymous shallow fetch by commit works; that's
  how PR #83's prepare step clones.
- **Piece 2:** `snapshot-architecture-context.sh` ran as script job
  `script-snapshot-architecture-context-all-cla-1010-010018-7e3619` from
  Breadboard `08449af`. Snapshot at
  `/app/.context/snapshots/architecture-context/7d61f097a9220aeb1280837b66b532177ec558b6`:
  `rhoai-3.6-ea.2`, 1,845 files, 88 MB.
- **Piece 3:** `seed_scenario.py` and `data/scenarios/smoke-one-rfe.yaml`.
  The dry run against the live emulator at PR #83's commit passed. It built
  the labels and the discovery query and reached both projects; 17 RFEs
  are currently discoverable, all agent-led POC data. **A real seed resets
  Jira**, which wipes that POC data. Waiting for a go-ahead.

## Next
- Write `run-workflow.sh` (PR #83) for smoke test S1, after pieces 1–3:
  PR commits in the GitHub emulator, the architecture snapshot and Jira
  seeding.
