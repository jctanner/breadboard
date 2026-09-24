# Using OpenShell in Breadboard

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

## Create a sandbox and launch an agent directly

You can use OpenShell without creating a GitHub issue or Actions run. The CLI
is installed in the Fullsend runner and already points at this stack's gateway.
Create a named sandbox in detached mode:

```bash
kubectl exec -n ai-pipeline deploy/github-actions-runner -- \
  openshell sandbox create --name direct-agent-demo --detach
```

Launch Claude Code in the sandbox with OpenShell's gRPC exec path:

```bash
kubectl exec -it -n ai-pipeline deploy/github-actions-runner -- \
  openshell sandbox exec --name direct-agent-demo --tty -- claude
```

The separate `kubectl exec -it` and `--tty` flags give both layers a terminal.
In this stack, `sandbox create -- ...` can create the sandbox and then fail on
its SSH attach step with `subsystem request failed on channel 0`; use `sandbox
exec --tty` to launch the command through the gateway instead. `sandbox
connect` also uses SSH.

This stack's sandbox does not inherit credentials from the runner. Check its
provider attachments with:

```bash
kubectl exec -n ai-pipeline deploy/github-actions-runner -- \
  openshell sandbox provider list direct-agent-demo
```

Configure and attach an OpenShell provider with usable model credentials before
expecting Claude Code to answer prompts. The existing `vertex-ai` provider in
this stack may have no credentials; `openshell provider get vertex-ai` shows
whether it does. See the [OpenShell Vertex AI provider guide](https://docs.nvidia.com/openshell/latest/providers/google-vertex-ai)
for setup. A direct launch does not run Fullsend's role selection, mint a
repository token, or create an Actions run.

For a manual run using this stack's Vertex setup, run the helper against the
sandbox you created:

```bash
./scripts/run-openshell-vertex-claude.sh
```

By default, the helper uses `direct-agent-demo` and `claude-haiku-4-5`; pass a
sandbox name and model as arguments to override them. It creates the sandbox
if missing, attaches the `vertex-ai` policy provider if needed, copies the
contents of the runner-mounted GCP credential file into the sandbox as a
regular file, verifies the upload, sources
`ANTHROPIC_VERTEX_PROJECT_ID` and `CLOUD_ML_REGION` from the project root's
`.env`, and starts Claude through OpenShell's interactive exec API.

This uses the mounted service account key in the sandbox, as the current
Fullsend harness does. The key is readable by processes in the sandbox; delete
the sandbox when finished to remove its workspace and copied credential. The
`vertex-ai` provider attaches the Fullsend network profile; it does not itself
copy the GCP key into the sandbox.

If Claude reports `403` from `api.anthropic.com`, it reached OpenShell's egress
proxy and the sandbox policy denied direct Anthropic access. That is expected
for an unconfigured direct sandbox: it has no provider attached and does not
inherit the Fullsend workflow's Vertex credentials or policy. Configure a
working Vertex provider and inference route for OpenShell before retrying; an
issue-triggered Fullsend job is already wired to use the stack's Vertex path.

When Claude Code opens and has a usable provider, give it a small task that
does not need private data.
For example, ask it to explain the contents of its working directory. Open a
second terminal to watch the sandbox appear and inspect its logs:

```bash
kubectl exec -n ai-pipeline deploy/github-actions-runner -- openshell sandbox list
kubectl exec -n ai-pipeline deploy/github-actions-runner -- openshell logs direct-agent-demo --tail
```

The sandbox is kept by default so you can run more commands and inspect it.
Delete this one sandbox when finished:

```bash
kubectl exec -n ai-pipeline deploy/github-actions-runner -- openshell sandbox delete direct-agent-demo
```

OpenShell starts sandboxes with the gateway's configured policy. The local
stack's default sandbox image and policies may differ from the Fullsend
workflow's role-specific provider profiles, workspace mounts, and egress rules.
The Fullsend path below is the way to observe those workflow integrations;
this direct path isolates basic sandbox creation and agent startup.

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
