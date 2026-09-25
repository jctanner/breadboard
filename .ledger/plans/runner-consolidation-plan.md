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
carries an `install-fullsend-cli` composite with a vendored mode and an
upstream mode, the latter falling back from release download to a source
build, plus `install-openshell.sh`. You only write that if you land on a clean
ephemeral machine every job.

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
`actions/upload-artifact`. The upstream entrypoint contains none of that.

What that establishes is where the logic lives, not that the upstream runner
fails without it: those behaviours could in principle be supplied by the runner
binary, by the actions themselves, or server-side by the emulator. So the
honest statement is that moving agent jobs onto the upstream runner carries
**unverified compatibility risk** against the paths G7, G8 and G41 exist to
fix — enterprise host and token handling, Vertex authentication, and artifact
upload — and that verifying it would cost a run per path. Keeping the known
compatibility layer avoids paying that, which is the argument for the revised
target; it is not a claim that the alternative is broken.

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
accepting the phase. The policy selects on the pod `app` label — currently
`github-actions-runner` and `github-actions-config-runner`, which happen to
match the deployment names — and allows only `10.42.0.0/16` and
`10.43.0.0/16`. Registration scope has nothing to do with it; what breaks the
selection is changing the pod template's `app` label, which a rename would
normally do. A pod outside the selector has unrestricted egress and nothing
reports it, so the acceptance check runs with the policy active.

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

**Breakpoint:** two things, not one. Deploy, reset and conformance all work,
*and* the profile comparison is observed running rather than skipped. Then a
**newly onboarded repository completes a triage** using the stock label and the
enterprise runner, with no new deployment and no `FULLSEND_RUNNER_IMAGE`
override — that is the goal the whole plan exists for, and the current layout
cannot do it at all.

### 4. Record what changed

Update the stage matrix and the conformance plan: one patch fewer; **G6
resolved** by serving the stock label; **G9 addressed** by the explicit,
validated tool inventory rather than resolved — the missing-tool class does not
disappear, it gains an owner and a list.

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
and does not change the sandbox boundary. Workspace cleanup between jobs reduces carryover but is not a
guarantee: a compromised job in a long-lived container can persist outside the
workspace. The real options are to replace the execution environment between
jobs, or to accept the residual exposure explicitly in the compatibility
profile. Cleanup alone should not be recorded as a mitigation.

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

## Follow-up review — 2026-09-25

The revised plan addresses the main migration concerns by keeping the Python
emulator runner, rebasing it on Ubuntu 24.04, and giving it enterprise scope
and the stock `ubuntu-24.04` label. The upstream router remains separate.
The phases now explicitly preserve gateway configuration, enforce the existing
egress policy, remove patch 0012 from the CLI build, and update deployment,
reset, and conformance consumers. The narrower tool-inventory and isolation
claims also improve the plan.

Six issues remain:

1. **The installer description is still inconsistent.** The introduction still
   says "three fallbacks," although the response accepts the correction.
   Update it to describe separate vendored and upstream modes, with
   release-to-source fallback inside upstream mode.

2. **Phase 4 still overstates the resolution of G9.** It reclassifies G9 as a
   consequence of a layout that no longer exists, while the revised target
   correctly withdraws the claim that the entire missing-tool class disappears.
   Record G6 as resolved by serving the stock label and G9 as addressed by the
   explicit tool inventory and validation.

3. **Registration scope does not control network-policy selection.** Phase 2
   says a renamed or re-scoped deployment silently falls outside the policy.
   The policy selects pod `app` labels. Changing registration scope alone does
   not affect it; changing the selected pod labels can. State the dependency
   precisely and retain the acceptance check with the policy active.

4. **Workspace cleanup is insufficient as an isolation guarantee.** A
   compromised job can persist changes elsewhere in a long-lived container.
   Cleanup can reduce workspace carryover, but it does not provide a fresh
   execution environment. Explicitly accept that residual exposure or require
   replacement of the execution environment between jobs.

5. **The upstream-runner failure claims exceed the evidence stated.** Absence
   of shim logic in `upstream/entrypoint.sh` does not establish that the upstream
   runner's authentication or artifact paths fail: those behaviors may live in
   the runner, actions, or emulator service. Keeping the known compatibility
   layer is a reasonable migration choice, but claims that Vertex authentication
   and artifact upload would break require validation of those paths. Describe
   them as unverified compatibility risks until that evidence exists.

6. **Restore the fresh-repository onboarding acceptance check.** It disappeared
   from the revised breakpoints even though onboarding without deploying a
   repository-specific runner remains a central goal. Require a newly onboarded
   repository to complete triage using the stock label and enterprise runner,
   with no new runner deployment or runner-image override.

Follow-up scope: review of the updated document against the earlier source
inspection. No new runtime tests or independent live-cluster checks were run.

## Response to the follow-up review — 2026-09-25

All six accepted and applied.

| # | what it was | fix |
| --- | --- | --- |
| 1 | intro still said "three fallbacks" after the correction was accepted | reworded to vendored and upstream modes, release-to-source inside the latter |
| 2 | phase 4 still called G9 resolved | G6 **resolved**, G9 **addressed** — the class gains an owner and a list, it does not vanish |
| 3 | conflated registration scope with policy selection | the policy selects the pod `app` label; scope is irrelevant, a rename is what breaks it |
| 4 | offered workspace cleanup as an isolation mitigation | cleanup is not a guarantee; the options are replacing the environment per job or accepting the exposure |
| 5 | stated upstream-runner breakage as fact | restated as unverified compatibility risk, with what the evidence does and does not establish |
| 6 | dropped the fresh-repository breakpoint | restored to phase 3, alongside the profile-comparison check |

Three of these — 1, 2 and 6 — were inconsistencies between what the revision
argued and what it left behind: a claim withdrawn in one section and still
standing in another, and an acceptance criterion silently lost in a rewrite.
Worth noting because they are the failure mode of revising a document under
review rather than rewriting it, and the same shape as the defects this project
keeps finding in code: the fix landed, the thing that pointed at the old
behaviour did not move with it.

Number 5 is the substantive one. The evidence — that the shim and injection
logic lives in `runner.py` and not in `upstream/entrypoint.sh` — establishes
where the behaviour is implemented, not that the upstream runner fails without
it. Stating it as breakage was an overclaim of exactly the kind this plan is
supposed to catch. It now reads as risk, with the cost of resolving it named: a
run per path.

Neither review ran the code. Points 2 and 3 of the first review were confirmed
against the live cluster; the network-policy selector in point 3 here was
confirmed too. Everything else in both rounds was confirmed in source. No claim
in this plan is backed by a run of the thing it describes, because nothing in
it has been built yet.
