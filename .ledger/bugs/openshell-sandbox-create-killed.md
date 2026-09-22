# `openshell sandbox create` times out because the sandbox image cannot be pulled

## Status: Open — root cause diagnosed 2026-09-21

## Confirmed diagnosis

The original timing interpretation below was incorrect: the CLI's `[5.0s]`
is its last progress update, not the time it was killed. Gateway logs for run
1210 show creation and deletion separated by the configured 130-second timeout:

| Attempt | Create completed (UTC) | Delete completed (UTC) | Elapsed |
| --- | --- | --- | --- |
| 1 | 17:25:14.872 | 17:27:24.869 | 130.0s |
| 2 | 17:27:29.904 | 17:29:39.910 | 130.0s |
| 3 | 17:29:49.949 | 17:32:00.071 | 130.1s |

Kubernetes events for **all three** pod instances report:

```text
ErrImageNeverPull: Container image "ghcr.io/fullsend-ai/fullsend-sandbox@sha256:259605fea321353552fdefd3a6a55e8b5c260998dfc5a622ed143e41a429995a" is not present with pull policy of Never
```

`deploy/k8s/openshell-values.yaml:23` sets
`server.sandboxImagePullPolicy: Never`. This works for the imported default
`pipeline-agent:latest` image, but the Fullsend harness requests the GHCR image
above, which is absent from the node. The successful `Pulled` event belongs to
the **supervisor init container** (`supervisor:0.0.110`), not the Fullsend image.
The progress message therefore does not establish that the workload image is
available.

Fullsend's `createOnce` uses a background-derived context with a 120s timeout
plus a 10s buffer. The CLI waits for readiness until that deadline, then
`exec.CommandContext` kills it. The fallback `sandbox get` uses the same expired
context, so it cannot recover the existing sandbox; `CreateWithRetry` deletes
the sandbox and retries. No outer cancellation is needed to explain this.

A direct runner probe on 2026-09-21 at 17:46:46 UTC, using the report's command
without `--from`, returned exit 0 at 17:46:54 and reported `Phase: Ready`. Its
pod used the locally available `pipeline-agent:latest`. The temporary sandbox
`debug-g36-20260921` was deleted after inspection. This validates the default
image path, not the Fullsend image or full agent execution.

Fix options: import the exact pinned Fullsend image into K3s while retaining
`Never`, or allow missing sandbox images to be pulled with `IfNotPresent`.
The latter changes shared gateway behavior and requires applying the gateway
configuration. No deployment or code fix was applied during diagnosis.

Evidence was obtained from the original job 2359 log, retained Kubernetes
events for `default--fs-tri-89cc8f45ab5e`, gateway create/delete logs, the source
of `createOnce`, and the direct runner probe. The original investigation below
is retained as history; its short-lifetime premise and timeout exclusion are
superseded by these findings.

## Summary

The Fullsend triage agent gets as far as creating a real OpenShell sandbox in
the cluster, and then the `openshell` CLI process it shelled out to dies with
`signal: killed`. It happens on all three create attempts, three to five
seconds in, immediately after the CLI prints `Image pulled`. The sandbox
itself is created successfully and survives for roughly two minutes before
being cleaned up.

`signal: killed` is SIGKILL. Go's `exec.CommandContext` sends exactly that when
its context is cancelled, so a cancelled parent context is the leading
hypothesis, but nothing has been established. The obvious resource explanations
have been checked and ruled out (see **Ruled out**).

This is the last thing standing between the current state and an agent
actually running. Everything before it now works: event routing, authorization,
OIDC, the mint, the vendored CLI, harness resolution from the local forge, the
pre-script, and a status comment posted to the issue by `fullsend-triage[bot]`.

## Symptom

From the Triage job log (run 1210, job 2359,
`fullsend-dev/triage-target` in the GitHub emulator):

```
  • Creating sandbox: fs-tri-89cc8f45ab5e
  Sandbox creation attempt 1/3 failed (sandbox create failed: signal: killed (output: Created sandbox: fs-tri-89cc8f45ab5e

  [0.0s] Requesting compute...
  [4.5s] Sandbox allocated
  [5.0s] Image pulled)), retrying in 5s...
  Sandbox creation attempt 2/3 failed (... [4.0s] Image pulled)), retrying in 10s...
  ✗ Failed to create sandbox
Error: creating sandbox: sandbox creation failed after 3 attempts: sandbox create failed: signal: killed
```

The three attempts died at roughly 5.0s, 4.0s and 3.6s. The variation tracks
the CLI's own progress rather than a fixed wall clock, which argues against a
plain timer firing.

## The sandbox really is created

This is not a failure to create. The agent-sandbox controller shows a genuine
`Sandbox` custom resource and backing Pod:

```
kubectl logs -n agent-sandbox-system deploy/agent-sandbox-controller
  17:29:53  "Found Pod" Sandbox=ai-pipeline/default--fs-tri-89cc8f45ab5e
                        Pod.Name=default--fs-tri-89cc8f45ab5e
  17:32:00  "sandbox resource not found. Ignoring since object must be deleted"
```

Created at 17:29:53, gone by 17:32:00. So the CLI is killed while the resource
it created is alive, and something cleans up afterwards.

## Ruled out

Each of these was checked, not assumed. Please do not re-check them without
reason; if one is re-opened, say why.

| Hypothesis | How it was checked | Result |
| --- | --- | --- |
| Runner container hit its memory limit | `/sys/fs/cgroup/memory.peak` and `memory.events` inside the runner pod | peak 168 MiB of a 1 GiB limit, `oom_kill 0` |
| Node memory pressure | `kubectl top nodes` | node at 15% memory |
| Kernel OOM killer selected the process | host kernel log, `dmesg \| grep -i oom` | only kills present are the emulator's own cgroup from a separate, already-fixed issue (G34) |
| The create context timed out | Initially excluded by misreading progress timestamps | **Reopened and confirmed:** gateway timestamps show 130s per attempt; see diagnosis above |
| OpenShell version skew | rebuilt at Fullsend's pinned revision | fixed separately (G35); `--detach` is now accepted and the sandbox is created |

## Where the code is

Fullsend, `internal/sandbox/sandbox.go`:

- `CreateWithRetry` (line ~867) loops `DefaultMaxCreateAttempts` times calling
  `createOnce`, deleting the failed sandbox between attempts. This produces the
  "attempt N/3 failed … retrying in Ns" lines.
- `createOnce` (line ~958) builds the context:
  `context.WithTimeout(context.Background(), timeout+readyCtxBuffer)`, then
  `exec.CommandContext(ctx, "openshell", args...)` and `CombinedOutput()`.
- The command is
  `openshell sandbox create --name <n> --keep --no-auto-providers --no-tty [--from <image>] [--policy <p>] [--provider …] --detach -- sleep infinity`.
- Note the context is `context.Background()`-derived, so an outer cancellation
  should *not* reach it. That is worth verifying rather than trusting, since it
  is the main argument against the cancellation hypothesis.

OpenShell CLI: `checkouts/openshell`, currently at the Fullsend-pinned revision
`d1155aa70042d3e2ee49dbfa15346b108b7c1d92` (reports
`0.0.111-dev.65+gd1155aa7`; the crate version is not bumped in tree, so the
number looks older than the 0.0.116 Fullsend names).

## How to reproduce

The stack must be running (`kubectl get pods -n ai-pipeline`).

```bash
cd <projectroot>
curl -sk -X POST "https://github.local/api/v3/repos/fullsend-dev/triage-target/issues" \
  -H "Authorization: token ghp_admin_default_token" \
  -H "Content-Type: application/json" \
  -d '{"title":"sandbox repro","body":"The README does not explain what this repository is for."}'
```

Then find the newest `fullsend` run and read its Triage job:

```bash
curl -sk "https://github.local/api/v3/repos/fullsend-dev/triage-target/actions/runs?per_page=6" \
  -H "Authorization: token ghp_admin_default_token"
curl -sk "https://github.local/api/v3/repos/fullsend-dev/triage-target/actions/jobs/<id>/logs" \
  -H "Authorization: token ghp_admin_default_token"
```

The run takes several minutes and fails at the sandbox step. Watch the
controller at the same time:

```bash
kubectl logs -n agent-sandbox-system deploy/agent-sandbox-controller -f
kubectl get sandboxes -A -w
```

## Suggested next steps

Roughly in order of how much they would tell you per unit of effort.

1. **Run the command by hand in the runner pod.** This separates "the CLI dies
   on its own" from "Fullsend kills it", which is the single most valuable
   split available and nothing so far distinguishes them:
   ```bash
   kubectl exec -n ai-pipeline deploy/github-actions-runner -- \
     openshell sandbox create --name probe-1 --keep --no-auto-providers \
       --no-tty --detach -- sleep infinity; echo "exit=$?"
   ```
   If it survives, the CLI is fine and the caller is the problem. If it dies
   the same way, Fullsend is exonerated and the question moves to OpenShell and
   the gateway.
2. **Check the gateway's view.** `kubectl logs -n openshell-system openshell-0`
   around the attempt. The CLI talks to it over gRPC; a gateway-side abort may
   present as a dead client.
3. **Look for who signals.** If step 1 shows the CLI dying alone, inspect what
   the CLI spawns after the image pull, and whether a supervisor or the sandbox
   Pod's lifecycle takes the client down with it.
4. **Confirm the context really is detached.** `createOnce` derives from
   `context.Background()`, which should make external cancellation impossible.
   Verify that holds at run time before discarding the cancellation
   hypothesis entirely.

## Context you may want

- The full chain and everything already fixed to get here is in
  `.ledger/plans/fullsend-integration-conformance-plan.md`. This bug is G36 in
  that plan's gap list.
- Local deviations from upstream Fullsend are patches under
  `deploy/fullsend/patches/`, applied by three separate lists: Go source before
  compilation (`deploy/scripts/05i-build-fullsend.sh`), the Fullsend mirror
  (`deploy/fullsend/seed/seed-upstream-fullsend.py`), and the agents mirror
  (`deploy/fullsend/seed/seed-upstream-agents.py`). None of them touch sandbox
  creation.
- The sandbox runs on a shared OpenShell gateway in the cluster rather than a
  per-runner Podman, which is a deliberate decision recorded in the plan under
  the 2026-09-21 host-setup entry. The agent action's local host setup is
  skipped by patch `0004`.
