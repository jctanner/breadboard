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

## The target — revised after review

**The first version of this plan aimed at the wrong runner.** It proposed
moving agent jobs onto the upstream router. Review found that the two runners
are not interchangeable in the way "install some binaries" implies, and
checking each claim confirmed it.

`src/runners/emulator/runner.py` injects `GH_HOST`, `GH_ENTERPRISE_TOKEN` and
the OIDC request variables into every step, and shims three marketplace
actions: `google-github-actions/auth`, `actions/setup-go` and
`actions/upload-artifact`. The upstream entrypoint does none of that — zero
matches for any of it. Moving agent jobs there would resurrect G7 and G8,
break Vertex authentication, and break the artifact shim built as G41. The
emulator's runner is a compatibility layer, not just a job executor.

So the target changes. Keep the compatibility layer; change what it runs on
and how it is scoped:

- rebase `fullsend-runner-dev` on **ubuntu:24.04** instead of
  `python:3.12-slim`, keeping `runner.py`;
- register it at **enterprise scope** so every repository can use it;
- label it **`ubuntu-24.04`**, which is what Fullsend's stock scaffold asks
  for.

That reaches the same three prizes without replacing the compatibility layer:
`runs-on: ubuntu-24.04` works unmodified so **patch 0012 can go**, onboarding
needs no per-repo deployment, and the Debian-vs-Ubuntu fidelity gap closes.

The upstream router stays exactly as it is, doing what it is good for:
exercising GitHub's real runner protocol for dispatch, and serving hosted-label
CI that wants a genuine Ubuntu machine.

Not a goal: replacing the sandbox, or making the emulator's runner a faithful
hosted image. "Hosted parity" was an overclaim in the first draft — adding
four tools does not make G9's class disappear. What replaces it is a stated
tool inventory, pinned in `deploy/fullsend-runner-dev/Containerfile`, validated
against the code and review paths rather than assumed.

## Phases

Each phase ends somewhere real. Stop at the breakpoint and take a verdict.

### 1. Rebase the agent runner on Ubuntu 24.04

Change `src/runners/emulator/Dockerfile` from `python:3.12-slim` to
`ubuntu:24.04` plus an explicit Python, keeping `runner.py` and the existing
tool inventory. Review the distro-dependent pins while doing it.

**Breakpoint:** `make host-conformance` passes unchanged on the rebased image.
Nothing about scope or labels has moved yet, so a failure here is purely the
base change.

### 2. Move it to enterprise scope and the stock label

Register at enterprise scope, label `ubuntu-24.04`, and carry over the
configuration the router does not have. That inventory is not optional and is
known to include `OPENSHELL_GATEWAY_ENDPOINT`, `OPENSHELL_GATEWAY_NAME`,
`FULLSEND_MINT_URL` and `FULLSEND_ALLOW_PRIVATE_FORGE`; patch 0004 uses the
gateway endpoint to skip local Podman setup, so without it jobs try to build a
sandbox inside the runner.

Apply `27-fullsend-runner-egress.yaml` to the new deployment **before**
accepting the phase. The policy currently selects the two agent runners by
name and allows only `10.42.0.0/16` and `10.43.0.0/16`; a renamed or
re-scoped deployment silently falls outside it and regains public egress.

**Breakpoint:** a triage job runs with `runs-on: ubuntu-24.04`, no
`FULLSEND_RUNNER_IMAGE` set, *with the egress policy active*.

### 3. Retire patch 0012 and the per-repo runners

Patch 0012 is a **Fullsend CLI patch** applied by
`deploy/scripts/05i-build-fullsend.sh`, not an agents-mirror patch. Removing it
means rebuilding the CLI, refreshing the vendored binary in
`deploy/fullsend/vendor/`, and regenerating affected scaffolds — reseeding the
mirror does nothing.

Then update every consumer of the retired deployments before deleting them:

- `deploy/scripts/17-deploy-github-actions-runner.sh` applies and restarts both;
- `deploy/scripts/25-reset-conformance.sh` defaults to them for gateway
  cleanup and cache clearing;
- `deploy/scripts/24-run-conformance-triage.sh` **skips its provider-profile
  comparison entirely when `github-actions-runner` is absent** (line 88).

That last one matters most: retiring the deployment without fixing the script
turns the staleness check into a no-op, and `host-conformance` would still
report green. The check exists because a gateway once served a 26-day-old
profile while every run reported importing it.

**Breakpoint:** deploy, reset and conformance all work, *and* the profile
comparison is observed running rather than skipped.

### 4. Record what changed

Update the stage matrix and the conformance plan: one patch fewer, G6 and G9
reclassified as consequences of a layout that no longer exists.

## Risks, recorded before starting

**Concurrency.** One replica, and a runner goes busy while running a job. Today
a long agent run blocks one repository; afterwards it blocks every repository.
More replicas need distinct `RUNNER_NAME`s, so it means a StatefulSet or a
name derived from the pod, not `replicas: 2`.

**Isolation — narrower claim than the first draft made.** That draft said the
credential boundary is unaffected. That is too strong. The runner is a
persistent container with a registration credential in its environment and a
workspace volume reused across jobs, so per-job minting does not by itself
protect a later job from an earlier compromised one. What is true: `PUSH_TOKEN`
still never enters the sandbox, and tokens are still minted per job and per
role. Consolidation widens the blast radius from one repository to all of them
and does not change the sandbox boundary. Either accept that explicitly in the
compatibility profile, or add workspace cleanup between jobs.

**Egress is already closed, not pending.** The first draft framed per-job tool
installation as pulling against F4's *future* aim. It is not future:
`27-fullsend-runner-egress.yaml` has restricted the agent runners to cluster
CIDRs since 2026-09-24. Installing tooling per job is therefore already
impossible on those runners, which is why `gitleaks` and `pre-commit` were
baked into the image — that was load-bearing, not merely defensive. The
production install-per-job shape is not reachable here without reopening
egress, and this plan does not propose to.

**Label drift.** GitHub moves `ubuntu-latest` between releases. The router
currently claims `ubuntu-latest` and `ubuntu-22.04` honestly; if its base is
ever bumped, `ubuntu-22.04` must go rather than be kept for compatibility. The
label list needs an owner and a note saying what the image actually is.

## Open questions

- Retire the per-repo runners, or keep one as an isolation override for work
  that should not share a workspace?
- Does anything depend on the agent runner being Debian? Nothing found, but it
  has never been asked, and the rebase is where it would surface.
- Should the router keep serving hosted-label CI at all, given a busy router
  delays dispatch? Its alternative is to stop the agents mirror seed triggering
  CI it was never meant to run.

## Accuracy and logic review — 2026-09-25

The direction is reasonable, but the plan needs corrections before
implementation. Review of the checked-out source, manifests, and scripts found
seven substantive issues:

1. **The migration changes runner behavior, not just the OS and labels.**
   Phase 2 omits that the existing agent runners execute the emulator's Python
   `runner.py`, while the router executes upstream `actions/runner`. The Python
   implementation supplies `GH_HOST`, enterprise token mappings, OIDC
   variables, and action shims such as `setup-go`. Phase 2 needs an explicit
   compatibility check for those behaviors; installing binaries alone does not
   establish equivalence. Evidence:
   `checkouts/github-emulator/src/runners/emulator/runner.py` and
   `checkouts/github-emulator/src/runners/upstream/entrypoint.sh`.

2. **The router lacks the configuration needed to use the existing sandbox
   gateway.** The plan promises to preserve the gateway, but
   `deploy/k8s/23c-github-actions-site-runner.yaml` lacks
   `OPENSHELL_GATEWAY_ENDPOINT`, `OPENSHELL_GATEWAY_NAME`, and the agent
   runners' other Fullsend settings. Patch 0004 uses the endpoint to skip local
   Podman and gateway setup. Without migrating that configuration, jobs attempt
   local setup inside the runner container. Phase 2 should inventory and
   transfer the required environment and mounts from
   `deploy/k8s/23-github-actions-runner.yaml` and its config-runner counterpart.

3. **F4 is already enforced on the old runners, and consolidation would bypass
   it.** The risk section describes egress confinement as something F4 wants to
   close. `deploy/k8s/27-fullsend-runner-egress.yaml` already restricts the two
   agent runners and explicitly excludes the router. Moving jobs there restores
   public egress unless the selector changes. Apply the policy to the
   replacement before acceptance, and require successful execution with that
   policy active.

4. **Phase 3 can break deployment and silently weaken conformance checks.**
   `deploy/scripts/17-deploy-github-actions-runner.sh` still applies and restarts
   both retired deployments. `deploy/scripts/25-reset-conformance.sh` defaults
   to those deployments for gateway cleanup and cache clearing.
   `deploy/scripts/24-run-conformance-triage.sh` skips its provider-profile
   comparison when `github-actions-runner` is absent. Update these consumers
   before retirement. Require deployment, reset, and conformance to work
   afterward; a green `host-conformance` alone could conceal a skipped check.

5. **Keeping `ubuntu-22.04` after rebasing to 24.04 contradicts the label
   contract.** Phase 1 explicitly retains both version labels. Remove
   `ubuntu-22.04` or provide a separate matching image. Also qualify the
   Dockerfile path: it lives under `checkouts/github-emulator/`, and its distro
   dependencies, including the explicit `libicu70` package, need review during
   the rebase.

6. **Patch 0012 belongs to the Fullsend CLI build, not the agents patch list.**
   Phase 3 identifies the wrong removal point. The patch is applied by
   `deploy/scripts/05i-build-fullsend.sh`. Removal needs to rebuild and
   redistribute the CLI, including the vendored binary, and regenerate affected
   scaffolds. Simply reseeding the agents mirror will not remove it.

7. **The isolation claim is stronger than the proposed design supports.**
   The risk section says the credential boundary is unaffected. The router is
   a persistent root container with a registration credential in its environment
   and a workspace volume shared across jobs. Per-job minting does not establish
   protection from a compromised earlier job. Specify cleanup or ephemeral
   execution, or explicitly accept persistent cross-repository exposure and
   narrow the credential claim. Evidence:
   `deploy/k8s/23c-github-actions-site-runner.yaml` and
   `checkouts/github-emulator/src/runners/upstream/entrypoint.sh`.

Two smaller accuracy corrections:

- The CLI installer has separate **vendored and upstream modes**, with
  release-to-source fallback inside upstream mode, rather than three successive
  fallbacks. See
  `checkouts/fullsend-ai/fullsend/.github/actions/install-fullsend-cli/action.yml`.
- Changing to Ubuntu and adding four tools does not establish hosted-image
  parity or make G9's entire class disappear. Define a supported tool inventory
  and validate the code/review paths, including their `gitleaks`, `pre-commit`,
  and validation dependencies. The current inventory and pins are recorded in
  `deploy/fullsend-runner-dev/Containerfile`.

Review scope: static inspection of checked-out source, manifests, and scripts.
No runtime tests were run and no implementation changes were made as part of
this review.

## Response to the review — 2026-09-25

Every substantive point was checked against the source and the running cluster
before being accepted. All seven held, and two of them changed the plan's
target rather than its detail.

| # | verdict | evidence |
| --- | --- | --- |
| 1 runner behaviour, not just OS | **accepted; changed the target** | `runner.py` injects `GH_HOST`, `GH_ENTERPRISE_TOKEN`, OIDC vars and shims `google-github-actions/auth`, `actions/setup-go`, `actions/upload-artifact`; `upstream/entrypoint.sh` matches none |
| 2 router lacks gateway config | accepted | router has no `OPENSHELL_*` or `FULLSEND_*` env at all; agent runner has four |
| 3 F4 already enforced | **accepted; corrected a false framing** | `fullsend-runner-egress` live since 2026-09-24, selects the two agent runners, allows only 10.42/16 and 10.43/16 |
| 4 phase 3 breaks consumers | accepted | `24-run-conformance-triage.sh:88` guards the profile check on the deployment existing |
| 5 label contract | accepted | 22.04 label must go when the base moves; `libicu70` is distro-pinned |
| 6 patch 0012 location | **accepted; my error** | applied by `05i-build-fullsend.sh:31`, a CLI patch, not an agents-mirror patch |
| 7 isolation overclaim | accepted | persistent container, registration credential in env, workspace reused across jobs |

The two corrections were right too: the CLI installer has vendored and upstream
modes with release-to-source fallback inside the latter, not three successive
fallbacks; and "hosted-image parity" was an overclaim that has been replaced
with a stated, validated tool inventory.

Point 1 is the one that matters. The first draft treated the two runners as
interchangeable given enough binaries. They are not: the emulator's runner is a
compatibility layer, and moving agent jobs onto the upstream runner would
resurrect G7 and G8, break Vertex authentication and break the G41 artifact
shim. The revised plan keeps that layer and changes its base, scope and label
instead — which reaches the same three goals and deletes less.

Point 3 is worth keeping visible because it corrects something said outside
this file as well: baking `gitleaks` and `pre-commit` into the runner image was
described at the time as removing a dependency on F4's *eventual* closure.
Egress was in fact already closed, so those self-installing tools were already
unreachable. The change was load-bearing, not defensive.

The review states it was static inspection with no runtime tests. Points 2 and
3 were additionally confirmed against the live cluster; the rest were confirmed
in source.
