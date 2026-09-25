# Runner consolidation plan

Make this stack serve the runner Fullsend actually asks for, so the local
runner layout stops being a deviation that has to be patched around.

Started 2026-09-25, out of a question about why the admin runners page shows
three runners with three different jobs. The answer turned out to be a design
divergence worth removing rather than documenting.

## The deviation, stated precisely

Fullsend targets **GitHub-hosted runners**. Its own defaults say so:

```go
// internal/config/config.go
DefaultGHRunner = "ubuntu-24.04"
```
```yaml
# .github/workflows/reusable-dispatch.yml
runner_image:
  default: "ubuntu-24.04"
```

Every agent job renders `runs-on: ${{ inputs.runner_image }}`, and the action
carries an `install-fullsend-cli` composite with three fallbacks — vendored
binary, download from release, clone and build from source — plus
`install-openshell.sh`. You only write that if you land on a clean ephemeral
machine every job.

This stack has no hosted runners, so it diverged in three places at once:

| | upstream expects | Breadboard has |
| --- | --- | --- |
| `runs-on` | `ubuntu-24.04` (hosted) | `fullsend` (patch 0012) |
| runner OS | Ubuntu 24.04 | Debian 13 trixie (`python:3.12-slim`) |
| tooling | installed per job, on a hosted image | baked into `fullsend-runner-dev` |
| scope | any repo, hosted | repo-scoped to two repositories |

Three known gaps are consequences of that divergence rather than independent
defects:

- **G6** exists only because nothing serves `ubuntu-24.04`. Patch 0012 adds
  `FULLSEND_RUNNER_IMAGE` so an installation can name its own runner.
- **G9** (`yq: command not found`) exists only because our image is not a
  hosted image. GitHub's ubuntu runners ship `yq`; upstream never hits it.
- **`button-probe` queued forever** because `fullsend` is repo-scoped: a newly
  onboarded repository has no runner until someone deploys one for it, which
  is precisely what ledger M12-024 said should not be necessary.

## The target

One enterprise-scoped runner that looks enough like GitHub's `ubuntu-24.04`
image for Fullsend to run on it unmodified, serving every repository. Then:

- `runs-on: ubuntu-24.04` works from the stock scaffold, so **patch 0012 can
  be dropped** — a local patch removed rather than carried.
- Onboarding a repository needs no new deployment.
- G9's class disappears: tooling parity with the hosted image is the contract,
  not a list of binaries we add when a run fails.

Not a goal: replacing the sandbox. The heavyweight custom piece in Fullsend is
the sandbox image and the OpenShell gateway, and both stay exactly as they are.
This is only about the machine the *job* runs on.

## Phases

Each phase ends somewhere real. Stop at the breakpoint and take a verdict
before starting the next.

### 1. Rebase the router on 24.04

Bump `src/runners/upstream/Dockerfile` to `ubuntu:24.04`, keep upstream
actions/runner, and add `ubuntu-24.04` to `RUNNER_LABELS` alongside the
`ubuntu-latest`/`ubuntu-22.04` already there.

**Breakpoint:** a throwaway repo with `runs-on: ubuntu-24.04` runs green on
`breadboard-enterprise-router`, and the job reports Ubuntu 24.04. Use a git
push — the contents API does not fire `push` events here.

### 2. Tooling parity

Give the router what a hosted ubuntu image gives a job: at minimum `yq`, `gh`,
`node`, `go`. Decide per tool whether to bake it or let the action install it.

Prefer the action's own install path where it exists (`install-fullsend-cli`,
`install-openshell.sh`): using it exercises what production exercises, and a
baked binary is a second deviation. Bake only where the install path needs
egress we are trying to remove — see the F4 note below.

**Breakpoint:** a Fullsend triage job completes on the router with
`runs-on: ubuntu-24.04`, no `FULLSEND_RUNNER_IMAGE` set anywhere.

### 3. Drop patch 0012 and the per-repo runners

With the router serving the stock label, remove `FULLSEND_RUNNER_IMAGE` from
the dashboard and the deployment, drop patch 0012 from the agents patch list,
reseed, and retire `github-actions-runner` and `github-actions-config-runner`.

**Breakpoint:** `make host-conformance` passes, and a freshly onboarded
repository runs a triage without anyone deploying a runner for it. That second
half is the thing the current layout cannot do at all.

### 4. Record what changed

Update the stage matrix and the conformance plan: patch count down by one, G6
and G9 reclassified as consequences of a layout that no longer exists.

## Risks, recorded before starting

**Concurrency.** One replica, and a runner goes busy while running a job. Today
a long agent run blocks one repository; afterwards it blocks routing and every
repository. This is the main reason the phases end where they do — phase 3 is
reversible up until the per-repo runners are retired. Mitigation if it bites:
more replicas need distinct `RUNNER_NAME`s, so it means a StatefulSet or a
name derived from the pod, not `replicas: 2`.

**Isolation.** Per-repo runners mean a compromised job reaches one repository's
workspace. A shared runner widens that to all of them. The credential boundary
is unaffected — tokens are still minted per job and per role, and `PUSH_TOKEN`
still never enters the sandbox — but the *workspace* boundary genuinely
narrows. Worth stating in the compatibility profile rather than discovering
later.

**F4 tension.** Installing tooling per job is the production shape and needs
runner egress, which F4 wants to close. Baking tooling avoids the egress and
recreates the deviation this plan exists to remove. These pull opposite ways
and the plan does not pretend otherwise: phase 2 decides tool by tool, and the
reasoning goes in the manifest next to each choice.

**`ubuntu-latest` drift.** GitHub moves `ubuntu-latest` between releases. A
runner claiming both `ubuntu-latest` and `ubuntu-24.04` is honest today and
becomes a lie on the next bump. Whatever phase 1 does, the label list needs an
owner and a note saying what the image actually is.

## Open questions

- Should the agent runners be retired, or kept as an override for work that
  wants isolation? Retiring them is cleaner; keeping one is cheap insurance.
- Does anything depend on the agent runner being Debian? Nothing found, but it
  has never been asked.
- Is `install-openshell.sh` usable against a gateway on the same cluster, or
  does it assume a released artefact this stack cannot reach?
