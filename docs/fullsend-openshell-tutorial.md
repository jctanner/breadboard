# Running Fullsend jobs through OpenShell

This tutorial walks through a real Fullsend agent run in the local Breadboard
stack and shows where to watch the GitHub Actions job, OpenShell sandbox, and
result. In this deployment, OpenShell is the sandbox service; Fullsend jobs
reach it through the GitHub Actions runner. You do not submit an application
job directly to the OpenShell gateway.

## Before you start

The integrated stack must be deployed and running. It needs the GitHub emulator,
the `fullsend-dev/triage-target` repository, the `github-actions-runner`, the
Fullsend Mint, and OpenShell. A model credential must also be configured for
the runner if you want the agent to call the model. The host proxy should make
these pages available:

- `https://github.local` — GitHub emulator
- `https://fullsend.local` — read-only Fullsend operations dashboard

Check the services from the repository root:

```bash
kubectl get pods -n ai-pipeline
kubectl get pods -n openshell-system
kubectl get pods -n agent-sandbox-system
```

The Fullsend runner image includes the OpenShell CLI, already configured to
talk to the in-cluster gateway. From the host, run CLI commands inside that
runner with `kubectl exec`:

```bash
kubectl exec -n ai-pipeline deploy/github-actions-runner -- openshell sandbox list
```

An empty list is normal before the first agent run.

## Run the repeatable triage demo

The conformance command creates a fresh issue in the seeded target repository,
waits for its real `fullsend` Actions workflow to finish, downloads the run
evidence, and closes the issue. From the repository root:

```bash
make host-conformance
```

The command can take up to 15 minutes while the workflow and agent run. It
prints the issue and run identifiers, then reports the evidence directory,
usually `var/conformance/run-<run-id>/`. The directory contains the issue and
comments, workflow run details, job log, artifact index, downloaded artifact,
and a summary of the source revisions. The job log is named
`triage-job.log`.

To leave the issue open for inspection, call the script directly:

```bash
PROJECT_ROOT="$PWD" bash deploy/scripts/24-run-conformance-triage.sh --keep-issue
```

Each run files a new issue. It does not reset OpenShell or clear existing
issues. `make host-conformance-reset` is a separate reset operation: it deletes
all OpenShell sandboxes, removes user-scoped Fullsend provider profiles,
clears runner profile caches, and closes open issues in the target repository.
Use it only when you intend to reset that state.

## Watch the run

Open `https://fullsend.local` while the job is running. The dashboard refreshes
every five seconds and shows recent workflow runs and jobs, Fullsend/OpenShell
pods, Kubernetes jobs, and related events. Select the GitHub run or job link to
open its detail page in the emulator. The dashboard is an observer; issue
events and the Actions workflow start the work.

In another terminal, watch pods appear and change state:

```bash
kubectl get pods -n ai-pipeline -w
```

The OpenShell sandbox workloads are created in `ai-pipeline` by the sandbox
controller. List sandboxes through the runner's configured OpenShell client:

```bash
kubectl exec -n ai-pipeline deploy/github-actions-runner -- openshell sandbox list
```

When a sandbox is listed, put its name in `SANDBOX_NAME` and stream its
OpenShell logs:

```bash
SANDBOX_NAME='paste-sandbox-name-here'
kubectl exec -n ai-pipeline deploy/github-actions-runner -- openshell logs "$SANDBOX_NAME" --tail
```

You can also inspect Kubernetes events and the gateway/controller pods:

```bash
kubectl get events -n ai-pipeline --sort-by=.lastTimestamp
kubectl get pods -n openshell-system -w
kubectl get pods -n agent-sandbox-system -w
```

The workflow job log shows the Fullsend steps around sandbox creation and
agent execution. The OpenShell log stream shows sandbox activity and policy
decisions. Together they let you follow the handoff from Actions runner to
sandbox and back to the workflow result.

## Trigger a run from the GitHub emulator

You can also submit an issue yourself instead of using the conformance helper:

1. Open `https://github.local` and navigate to
   `fullsend-dev/triage-target`.
2. Create a new issue with a small, clearly stated triage request.
3. Open the `fullsend` workflow run started by the `issues` event. The
   Fullsend dashboard links to the run and job pages.
4. Watch the Actions job, the dashboard's sandbox and event rows, and the
   OpenShell CLI logs as described above.

The issue is processed by the seeded repository's Fullsend workflow and
configured triage agent. The agent may label the issue and add comments. Do not
put secrets or private data in the issue, and use the seeded target repository
for experiments.

## What the run demonstrates

An issue event starts the GitHub Actions workflow. A self-hosted runner claims
the job, obtains a short-lived repository-scoped token through Fullsend Mint,
and invokes the Fullsend CLI. Fullsend asks OpenShell to create a sandbox with
the checked-out workspace, event payload, credentials, and the role's policy.
The agent runs inside that sandbox; Fullsend then returns its result to the
workflow, which can publish comments, labels, and artifacts.

The local OpenShell gateway is configured for this trusted development
cluster: TLS is disabled and unauthenticated users are allowed on the in-cluster
service. Keep it inside the cluster and do not expose its gateway directly to
an untrusted network. See [Fullsend Integration](fullsend-integration.md) for
the service and sandbox diagrams.
