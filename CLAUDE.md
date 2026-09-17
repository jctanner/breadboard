# Breadboard

Breadboard is the integration and deployment repository for an AI-native
software engineering platform. It combines the Python pipeline and dashboard
with Kubernetes manifests, local Jira/GitHub/GitLab emulators, workflow
services, runners, observability services, and the Fullsend agent execution
path.

The repository supports two related execution paths:

- the Python CLI and pipeline agent, which run the bug, RFE, and strategy
  phases and can launch Kubernetes jobs; and
- the integrated service stack, which runs Markov workflows, emulated source
  systems, CI runners, Observatory, MLflow, and Fullsend in a resettable local
  K3s environment.

The current reference workflow is still represented by:

```text
RFE -> quality gate -> strategy -> review -> epics -> investigation/codegen
```

## Working rules

- Treat `checkouts/` and `checkouts.tmp/` as separate, ignored component
  repositories. Read their local `AGENTS.md` or `CLAUDE.md` before changing
  anything there.
- `deploy/k8s/` and `deploy/scripts/deploy-all.sh` are the authoritative
  deployment inventory. Older material under `deploy/docs/` may describe
  superseded architecture.
- Keep project work notes, plans, bugs, decisions, and tasks under `.ledger/`.
  The documentation tree is for maintained product and architecture docs.
- Before creating or updating anything in `.ledger/`, read
  `.ledger/agentic_work_ledger.md` for the full ledger instructions.
- Do not commit `.env`, credentials, generated issue/workspace data, logs,
  runtime state, or ignored component checkouts.
- Run `git diff --check` after documentation or code edits. Run the smallest
  relevant test or compile check before reporting completion.

## Quick reference

```bash
uv sync
python main.py <command> [options]
python main.py dashboard --port 5000

make host-deploy-all
make host-status
make host-rebuild-dashboard
make host-rebuild-fullsend-dashboard
make security
```

The integrated stack uses the `ai-pipeline` Kubernetes namespace and exposes
the local services through the host proxy. The main user interfaces are
`https://dashboard.local`, `https://fullsend.local`, `https://github.local`,
`https://gitlab.local`, `https://jira.local`, `https://markov.local`, and
`https://observatory.local` when the stack is running.

## Prerequisites and environment

- Python 3.13+
- `uv`
- Podman or Docker for image builds; Podman is required by patch validation
- K3s and `kubectl` for the integrated stack
- Google Cloud credentials when running Vertex-backed agents
- Jira credentials when using the production Jira API rather than the emulator

Create a gitignored `.env` in the project root as needed:

```text
CLAUDE_CODE_USE_VERTEX=1
CLOUD_ML_REGION=global
ANTHROPIC_VERTEX_PROJECT_ID=<gcp-project-id>
JIRA_SERVER=https://issues.redhat.com
JIRA_USER=<email>
JIRA_TOKEN=<api-token>
ATLASSIAN_MCP_URL=http://127.0.0.1:8081/sse
```

The integrated deployment also reads service-specific credentials and tokens
from Kubernetes secrets. Do not add those values to manifests or documentation.

## CLI commands

The Python entry point is `main.py`. Available phase groups include:

| Group | Commands |
| --- | --- |
| Bug analysis | `bug-fetch`, `bug-completeness`, `bug-context-map`, `bug-fix-attempt`, `bug-test-plan`, `bug-write-test`, `bug-all` |
| RFE | `rfe-create`, `rfe-review`, `rfe-split`, `rfe-submit`, `rfe-speedrun`, `rfe-all` |
| Strategy | `strat-create`, `strat-refine`, `strat-review`, `strat-submit`, `strat-security-review`, `strat-all` |

Common options include `--model`, `--max-concurrent`, repeatable `--issue`,
`--limit`, `--force`, and `--component`. Phase outputs are validated against
the schemas in `src/cli/schemas.py`; invalid outputs are retained with an
`.invalid` suffix so a rerun can replace them.

## Repository layout

```text
main.py                         CLI dispatcher
pyproject.toml                  Python dependencies
src/cli/                        Phase orchestration and agent execution
src/dashboard/                  Breadboard dashboard and APIs
src/fullsend-dashboard/         Read-only Fullsend operations dashboard
scripts/                        Standalone utilities and cleanup scripts
deploy/k8s/                     Kubernetes resources
deploy/scripts/                 Build, bootstrap, and deployment automation
deploy/dashboard/               Breadboard dashboard image
deploy/pipeline-agent/          Pipeline job image
deploy/golang-reverse-proxy/    Host-facing *.local proxy
docs/                           Maintained architecture and deployment docs
.ledger/                        Project plans, tasks, bugs, decisions, notes
var/markov-workflows/           Markov workflow definitions
var/demos/                      Resettable scenarios and integration demos
```

The dashboard contains both the original pipeline views and the current
ticket browser. The root page queries the Jira, GitHub, and GitLab emulators,
combines issues, pull requests, and merge requests, fetches all available
pages before applying filters, and defaults to hiding closed, done, resolved,
merged, and completed work. GitHub links use the emulator's `/ui/` prefix.

The dashboard implementation is centered in `src/dashboard/webapp.py` and
`src/dashboard/ticket_data.py`; its shared layout and ticket browser are in
`src/dashboard/templates/` and `src/dashboard/static/js/`.

## Integrated services

The active deployment includes:

| Service | Purpose |
| --- | --- |
| Breadboard dashboard | Combined live ticket browser, pipeline jobs, artifact views, and service links |
| Markov and markovd | Declarative workflows, run state, approvals, and job orchestration |
| Observatory | Trace and artifact collection, claim extraction, verification, and quality reporting |
| MLflow | Agent traces and experiment data |
| Jira emulator | Jira-compatible issues, UI, snapshots, and MCP-compatible operations |
| GitHub emulator | REST/GraphQL, Git transport, web UI, Actions, and admin APIs |
| GitLab emulator | GitLab API, Git transport, issues, merge requests, and CI APIs |
| GitLab Runner | Kubernetes-executor runner for emulator CI jobs |
| GitHub Actions runners | Runners for emulator Actions workflows, including Fullsend workflows |
| Fullsend Mint | Exchanges development OIDC assertions for scoped GitHub credentials |
| Fullsend runner and OpenShell | Runs role-specific agent work inside the sandbox boundary |
| Fullsend dashboard | Read-only operational view of Actions, jobs, pods, and events |
| Traefik, cert-manager, and host proxy | Internal TLS and `*.local` service routing |

Fullsend is GitHub-first. Its current development flow starts from the
`fullsend-dev/triage-target` repository in the GitHub emulator. It uses Actions,
OIDC, Fullsend Mint, OpenShell, and a sandbox runner; the Fullsend dashboard
observes that flow but does not dispatch agent work. See
[`docs/fullsend-integration.md`](docs/fullsend-integration.md) and its three
Mermaid diagrams for the service topology, event flow, and sandbox boundary.

The Kubernetes manifests and deployment scripts define the current stack. Do
not infer deployed services from the contents of `checkouts/`; that directory
also contains source and dependency repositories that are not deployed.

## Development and deployment

Host targets are defined in `Makefile`. Useful targets include:

- `host-deploy-all` for a complete deployment;
- `host-status` and `kubectl get pods -A` for cluster inspection;
- `host-rebuild-dashboard` for the Breadboard dashboard;
- `host-rebuild-fullsend-dashboard` for the Fullsend operations dashboard;
- `host-rebuild-agent`, `host-rebuild-markov`, and the emulator rebuild targets
  for component changes; and
- `security` for the repository security scan.

Use the component's own build or deployment target when changing a checkout.
For a dashboard-only Python change, `python main.py dashboard --port 5000`
is sufficient for local development; a deployed image requires the matching
host rebuild target.

## Generated and ignored data

The following locations are runtime or generated data and should not be
treated as source documentation:

- `issues/` — fetched Jira data and phase outputs;
- `workspace/` — per-issue repositories and model outputs;
- `logs/` — activity and phase logs;
- `.context/` — cloned architecture context;
- `remote_skills/rfe-creator/` — external RFE/strategy skill repository;
- `checkouts/` and `checkouts.tmp/` — external component repositories; and
- generated security review and requirement artifacts.

## Skills, workflows, and validation

Local skills live under `.claude/skills/`. External RFE and strategy skills are
configured through `var/pipeline-skills.yaml`; the registry is staged in
`var/skills-registry.yaml`. Markov workflow definitions live under
`var/markov-workflows/`.

Bug phases run concurrently through `src/cli/phases.py`, and fix attempts can
use Podman recipes from `odh-tests-context`. Validation feedback can be fed
back into retry prompts with `--validation-retries`. The dashboard receives
pipeline activity through Server-Sent Events and can submit Kubernetes jobs.

The resettable end-to-end scenario is under `var/demos/end-to-end/`. Read its
README and workflow definitions before changing the scenario or its service
contracts.

## Documentation and ledger

[`docs/README.md`](docs/README.md) is the documentation index. It links to
architecture, deployment, reference, and Fullsend integration material.

`.ledger/` is the project work ledger. Its top-level location is
`<PROJECTROOT>/.ledger`; keep plans, tasks, bugs, decisions, and notes there.
Read [`<PROJECTROOT>/.ledger/agentic_work_ledger.md`](.ledger/agentic_work_ledger.md)
for the full ledger instructions before creating or updating ledger material.
Do not add ledger planning material back under `docs/`.

## Current conventions

- Jira projects used by the phase pipelines are `RHOAIENG`, `RHAIRFE`, and
  `RHAISTRAT`.
- RFE and strategy artifacts use YAML frontmatter.
- The `--model` value determines the bug workspace subdirectory.
- MCP servers are configured per phase in `var/pipeline-skills.yaml`.
- Read the deployment manifests before changing service names, routes, ports,
  or credentials; local UI paths and API paths are intentionally different for
  some emulators.
