# Agent-led Fullsend strategy POC: CI fixtures

These files publish and drive the GitLab CI for the
[agent-led strategy POC](../../../.ledger/plans/fullsend-agent-led-strategy-poc.md).
Native Fullsend `strat-single` and `strat-batch` agents come from the
strat-creator fork branch `feat/fullsend-agent-led-strategy`, whose
`.fullsend/README.md` describes the agents themselves.

| File | Published as / use |
| --- | --- |
| `ci/gitlab-ci.yml` | `.gitlab-ci.yml` on `strat-pipeline` branch `feat/fullsend-agent-led-poc` |
| `ci/source.sh` | `ci-scripts/agent-led-source.sh`: clone the fork and pin `STRAT_CREATOR_SHA` |
| `ci/strategy.sh` | `ci-scripts/agent-led-strategy.sh`: install released Fullsend 0.43.0 (checksum-verified), prepare credentials and host state, run the agent, always release locks |
| `ci/gateway.sh` | `ci-scripts/agent-led-gateway.sh`: job-owned Podman + OpenShell gateway and teardown |
| `ci/redact.py` | `ci-scripts/agent-led-redact.py`: live and artifact credential redaction |
| `publish.py` | Create or update the branch, check shared variables by name, start a pipeline |
| `seed_rfe.py` | Seed one distinct, eligible RFE per scenario in local Jira |
| `test_ci.py` | Fixture checks, including that CI defines every host variable the harnesses reference |

## Usage

```sh
export GITLAB_ADMIN_USER=admin GITLAB_ADMIN_PASSWORD=admin   # emulator defaults
export GITLAB_CA_FILE=/path/to/local-ca.crt JIRA_CA_FILE=/path/to/local-ca.crt

uv run --with httpx python var/demos/fullsend-agent-led-poc/seed_rfe.py --scenario registry-serving-guard
uv run --with httpx python var/demos/fullsend-agent-led-poc/publish.py --publish      # branch + files only
uv run --with httpx python var/demos/fullsend-agent-led-poc/publish.py --rfe RHAIRFE-12
uv run --with httpx python var/demos/fullsend-agent-led-poc/publish.py --batch [--batch-size N --expected-keys "..."]
uv run --with pytest --with pyyaml --with httpx pytest var/demos/fullsend-agent-led-poc/test_ci.py
```

`publish.py` never creates or changes project variables, and it fails if
`main` or `feat/fullsend-strategy-poc` moves. The CI reuses the shared
project variables (`JIRA_*`, `VERTEX_CREDENTIALS_JSON`,
`ANTHROPIC_VERTEX_PROJECT_ID`, `RESULTS_PUSH_TOKEN`, `ORG_PULSE_API_TOKEN`)
and publishes to the existing `strat-pipeline-data` and strat-dashboard
`main`. `--context-path` and `--allow-invalid-rfe` exist only to exercise
failure paths.

After a run, CI job artifacts hold:
- `fullsend-ci-artifacts/`: source pin, binary checksum, image pins, the host
  run record (`strat-state/`), `agent-result.json`, `exit-status.json`, and
  gateway and cleanup logs;
- `fullsend-run-output/`: Fullsend's per-iteration output, transcripts,
  validation feedback and OpenShell logs.

The ledger task `tasks/current/agent-led-strategy-single-ci.md` (later
`done/`) has the run evidence.
