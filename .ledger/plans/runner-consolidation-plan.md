# Runner consolidation plan

Make this stack's runner layout match what Fullsend is actually designed for,
so the local layout stops being a deviation that has to be patched around.

Rewritten 2026-09-25. This replaces a version that went through three review
rounds (last at commit `e86baa1`); it was revised in place each time and each
time a detail that depended on the previous target survived. The target has
now changed in kind rather than degree, so this is a rewrite. The old version
stays in git as the record of how the target moved.

**What changed the target:** the previous version, and the discussion around
it, converged on an *org-mode* layout — a per-org `.fullsend` config repo with
its own agent runner, consumers reaching it through a shared router. Fullsend's
own docs say that model is deprecated. Everything below is built on what the
ADRs decide, and cites them, because the earlier drafts were built on reading
code and inferring intent.

## What upstream decides

| decision | where |
| --- | --- |
| Per-repo installation is **the sole supported deployment model** | `docs/architecture.md`, ADR 0033 |
| The org-level `<org>/.fullsend` config repo is **deprecated**, removal planned for v2.0 | ADR 0044 (Accepted; Phase 2 not yet landed in this checkout, v0.43.0-256) |
| Org-wide sharing of defaults is by **harness `base:` URLs** and `config.base.yaml` presets, not a config repo | ADR 0045, ADR 0069 |
| Stage jobs are **inlined into `reusable-dispatch.yml`**; the `workflow_dispatch` fan-out from `dispatch.yml` is the deprecated pattern | ADR 0062, `docs/architecture.md` |
| Agent jobs target **GitHub-hosted runners**: `DefaultGHRunner = "ubuntu-24.04"`, and `reusable-dispatch.yml`'s `runner_image` input defaults to the same | `internal/config/config.go`, `.github/workflows/reusable-dispatch.yml` |
| Cross-org minting exists, via `target_org` + `FULLSEND_FOREIGN_<role>_REPOS`, and needs the role App installed in the target org | `docs/architecture.md`, `mintcore/github.go` |
| `forge:` harness composition is deprecated but functional, superseded by CEL `overlays:` | ADR 0088 |

"Self-hosted" in Fullsend's docs means the mint and GitHub Apps. No document
describes self-hosted runners; every example is `ubuntu-24.04` or
`ubuntu-latest`. The action carries an `install-fullsend-cli` composite with
vendored and upstream modes and an `install-openshell.sh`, which is what you
write when every job lands on a clean machine.

## The deviation

This stack has no hosted runners, so per-repo mode was made to work by
diverging from the design in four places:

| | upstream | Breadboard |
| --- | --- | --- |
| `runs-on` for agent jobs | `ubuntu-24.04` | `fullsend`, via patch 0012's `FULLSEND_RUNNER_IMAGE` |
| runner OS | Ubuntu 24.04 | Debian 13 trixie (`python:3.12-slim`) |
| tooling | installed per job | baked into `fullsend-runner-dev` |
| runner scope | any repo (hosted) | repo-scoped to `triage-target` and `.fullsend` |

Three consequences, previously mistaken for independent defects:

- **G6** exists because nothing serves `ubuntu-24.04`.
- **G9** (`yq: command not found`) exists because the image is not a hosted
  image. GitHub's hosted Ubuntu images are believed to ship `yq` — believed,
  not verified against the hosted-image manifest.
- A **newly onboarded repository has no runner** until someone deploys one for
  it. `button-probe` queued forever on exactly that.

And one leftover that is not a deviation from upstream but from upstream's
*current* design: the seeded `fullsend-dev/.fullsend` config repo and
`fullsend-dev-config-runner` implement the deprecated org mode. Nothing has run
there since 2026-09-17, when `triage-target` moved to a per-repo shim. It was
abandoned by the conformance plan's design choice, not broken — G39 closed on
09-22, five days later.

## The target

Per-repo mode, as ADR 0033 says. Two runner tiers, two labels:

| tier | runner | scope | labels | serves |
| --- | --- | --- | --- | --- |
| **hosted stand-in** | upstream `actions/runner` on `ubuntu:24.04` | enterprise (site-wide) | `ubuntu-24.04`, `ubuntu-latest` (`fullsend-router` until phase 3) | generic CI only |
| **agent** | `runner.py` + compatibility layer + tooling, on `ubuntu:24.04` | **site** (`runner.py` supports `repository` and `site` only) | `fullsend` | every Fullsend job in every repository — routing included |

Routing is not a separate tier. Every job in `reusable-dispatch.yml` — `route`,
the stages, and `harness-dispatch` — runs on `inputs.runner_image`, so with
the override set to `fullsend` the routing job lands on the agent runner. Run
1509 shows exactly that. The `fullsend-router` label served only the
deprecated org-mode `.fullsend/dispatch.yml`; once phase 3 retires that, the
label is vestigial and comes off.

The two tiers need two labels. `runner.py` is not a job executor but a
compatibility layer — it injects `GH_HOST`, `GH_ENTERPRISE_TOKEN` and the OIDC
variables into every step and shims `google-github-actions/auth`,
`actions/setup-go` and `actions/upload-artifact`. Whether the upstream Actions
runtime, the actions themselves, or the emulator could supply equivalents is
**unverified**; missing logic in an entrypoint shows where the behaviour lives,
not what the full runtime supports. Keeping the proven layer avoids paying a
run per path to find out, and that is the whole argument. So **patch 0012
stays**, on a stated basis: a render-time runner label is structural to a
two-tier layout, not a deviation to remove. What the layout *does* remove is the per-repo runner
deployment, the Debian base, and the deprecated org-mode remnants.

Onboarding becomes what ADR 0033 describes: `fullsend github setup <owner/repo>`
(the dashboard button already does this), with the agent runner at site scope
so no deployment follows. Org-wide defaults, if wanted, are a `base:` URL in
each repo's harness — not a runner, not a config repo.

Not a goal: replacing the sandbox or the gateway; making the agent runner a
faithful hosted image; or reopening runner egress to install tooling per job
(see risks).

## Phases

Each phase ends somewhere real. Stop at the breakpoint and take a verdict.

### 1. The hosted stand-in

Rebase `src/runners/upstream/Dockerfile` (github-emulator checkout) on
`ubuntu:24.04`, review `libicu70` and other distro pins, add `ubuntu-24.04` to
`RUNNER_LABELS`, and drop `ubuntu-22.04` — a label list has to describe the
image. Keep `fullsend-router` for now: nothing in the per-repo path uses it, but the
deprecated `.fullsend/dispatch.yml` does until phase 3 retires it.

The agents mirror's own CI (183 jobs in the database asked for `ubuntu-24.04`)
will start running here rather than queueing. It may fail for want of `node`;
a legible failure is the correct outcome and is not this plan's problem to fix.

**Breakpoint:** a throwaway repo's `runs-on: ubuntu-24.04` job runs green
here and reports Ubuntu 24.04. Trigger it with a git push — the contents API
does not fire `push` events.

### 2. The agent runner

Rebase `src/runners/emulator/Dockerfile` (also the github-emulator checkout,
built by `05g-build-github-actions-runner.sh`) on `ubuntu:24.04` plus an
explicit Python, keeping `runner.py` and the tool inventory pinned in
`deploy/fullsend-runner-dev/Containerfile`. Register at **site scope**
(`RUNNER_SCOPE=site`), label `fullsend` only.

Carry the configuration the deployment already has and the router lacks:
`OPENSHELL_GATEWAY_ENDPOINT`, `OPENSHELL_GATEWAY_NAME`, `FULLSEND_MINT_URL`,
`FULLSEND_ALLOW_PRIVATE_FORGE`. Patch 0004 uses the gateway endpoint to skip
local Podman setup; without it a job tries to build a sandbox inside the
runner.

Apply `27-fullsend-runner-egress.yaml` **before** accepting the phase. It
selects on the pod `app` label — currently `github-actions-runner` and
`github-actions-config-runner` — and allows only `10.42.0.0/16` and
`10.43.0.0/16`. Registration scope does not affect it; a changed pod label
does, and a pod outside the selector has unrestricted egress with nothing
reporting it.

Update `github-actions-runner` **in place** rather than creating a new
deployment: the egress policy selects the pod `app` label, and an in-place
update keeps it applying without touching the policy.

During validation the old repo-scoped registrations still advertise
`fullsend`, so a green conformance run proves nothing about *which* runner
served it. Extend `24-run-conformance-triage.sh` to record `runner_name` from
the jobs endpoint it already calls (it captures `job_id` but not the runner),
and require it to name the new runner — or scale the old deployments to zero
for the duration.

Triage alone does not exercise the tool inventory the plan keeps: the code
path needs `gitleaks` and `pre-commit`, review needs the post-review tooling.
Before the old runners go, confirm the inventory in the new pod with
`command -v`, and run review and code once each on the new runner. Those are
paid runs, roughly $2 each on the last measurement.

**Breakpoint:** `make host-conformance` passes with the egress policy active
and the evidence names the new runner; a review and a code run each complete
on it; and a **fresh repository onboarded through the dashboard button
completes a triage** with no new deployment — the thing the current layout
cannot do.

### 3. Retire what the design no longer has

- `github-actions-config-runner` and the seeded `fullsend-dev/.fullsend`:
  deprecated upstream (ADR 0044), unused since 09-17. Retire explicitly and
  say why, rather than let them rot.
- `github-actions-runner` (repo-scoped): superseded by the site-scoped runner.
- The two repo-scoped registrations on the admin page, via the Remove button.

Before deleting any deployment, update its consumers:

- `deploy/scripts/17-deploy-github-actions-runner.sh` applies and restarts both;
- `deploy/scripts/25-reset-conformance.sh` defaults to them for gateway cleanup
  and cache clearing;
- `deploy/scripts/24-run-conformance-triage.sh` **skips its provider-profile
  comparison when `github-actions-runner` is absent** (line 88). Retiring the
  deployment without fixing this turns the staleness check into a no-op while
  `host-conformance` stays green.

**Breakpoint:** deploy, reset and conformance all work, *and* the profile
comparison is observed running rather than skipped.

### 4. Record

- Conformance plan: G6 **addressed through the retained override** — agent
  jobs still do not use the stock label, by design; G9 **addressed** by the
  pinned tool inventory, not resolved.
- Stage matrix: `forge:` is deprecated-but-functional (ADR 0088), not
  first-class; the org-mode analysis is withdrawn with a pointer here.
- Decision entry: why patch 0012 stays.
- The two fidelity findings below, as G-numbers.

## Findings carried, not fixed here

Both surfaced while working out whether org mode could serve other orgs. They
are not the same kind of problem and should not be filed together.

The first is **active**. The cross-repository dispatch used `github.token`
straight against the emulator's API; the mint was never in the path, so the
development mint's binding of minted tokens to the caller's repository does
not contain it. Any job on this stack can already start workflows in any
repository. It is an authorization defect in the emulator and deserves a
fix on its own timeline, not this plan's.

The second is dormant: the development mint ignores `job_workflow_ref`, so
it would matter only when a real mint were used.

1. **Job tokens are not repository-bound.** Proven by probe: a job in repo A
   declaring `actions: write` dispatched a workflow in repo B — `204`, run
   created. The same job with `actions: read` got `403`, so the B9 scope gate
   works; nothing checks the *repository*. `issue_job_token` binds only
   `job:{id}` and the run; `dispatch_workflow` performs no target-repo access
   check. Real GitHub job tokens cannot cross repositories.
2. **`job_workflow_ref` reports the caller, not the called workflow.**
   `oidc.py` sets it equal to `workflow_ref`, derived from the run's own
   repository. Our shim `uses:` the reusable workflow rather than vendoring it,
   so upstream expects the *called* repository there (ADR 0082). A real mint
   would refuse the token.

## Risks

**Concurrency.** One site-scoped agent runner serves every repository, and a
runner goes busy while running a job. Today two runners serve two repos. If
this bites, replicas need distinct `RUNNER_NAME`s — a StatefulSet, not
`replicas: 2`.

**Isolation, stated narrowly.** `PUSH_TOKEN` still never enters the sandbox
and tokens are still minted per job and per role. But the runner is a
persistent container with a reused workspace, so a compromised job can affect
later jobs, and site scope widens that from one repository to all. Workspace
cleanup is not a mitigation — a job can persist outside the workspace. The
options are replacing the execution environment per job, or accepting the
exposure explicitly in the compatibility profile. Finding 1 above makes the
same point from the other side: on this emulator any job can already reach any
repository's Actions API, so the runner boundary is not the outer one.

**Egress is closed and stays closed.** Installing tooling per job is the
production shape and is impossible here by policy since 2026-09-24. Tooling
stays baked, pinned, and drift-checked against the libraries that would
otherwise install it. This is a knowing deviation, recorded as such.

**Label drift.** GitHub moves `ubuntu-latest` between releases. The hosted
stand-in claims it honestly today; the label list needs an owner and a note
saying what the image actually is.

## Open questions

- Should the hosted stand-in and the router be one deployment or two? Same
  image class; the only argument for two is keeping routing unblocked by long
  CI jobs.
- Does anything depend on the agent runner being Debian? Nothing found; the
  rebase is where it would surface.
- The agents mirror seed triggers that repository's CI on every push. With
  phase 1 that CI runs instead of queueing. Whether the seeder should trigger
  it at all is a separate question and no longer a prerequisite.
- Verify the `yq`-on-hosted-images claim before phase 4 records G9.

## Review of the rewritten plan — 2026-09-25

The rewrite addresses several earlier findings, and `RUNNER_SCOPE=site` is
correct for the Python runner. Five issues remain:

1. **The routing tier does not match the workflow.** The target assigns
   dispatch routing to the upstream runner. But the `route` job in
   `checkouts/fullsend-ai/fullsend/.github/workflows/reusable-dispatch.yml`
   uses the same `inputs.runner_image` as agent jobs. With the override set to
   `fullsend`, routing also runs on the Python runner. Either describe that
   layout or explicitly plan a separate routing input.

2. **Phase 4 contradicts the decision to retain patch 0012.** It says G6 is
   resolved by serving the stock label. Fullsend still requires the `fullsend`
   override under this design; the runner serving `ubuntu-24.04` is deliberately
   unsuitable for agent jobs. Record G6 as addressed through the retained
   override.

3. **The cross-repository token defect is not dormant.** The findings section
   describes an already-successful cross-repository dispatch using a job token.
   That request bypasses the mint entirely, so the development mint's
   restrictions do not contain it. Separate this active authorization defect
   from the OIDC compatibility issue.

4. **Phase 2's conformance result could come from the old runner.** The plan
   validates the replacement before retiring old registrations, all serving
   `fullsend`. Require evidence that conformance ran on the new runner, or
   disable the old runners during validation. Also specify whether
   `github-actions-runner` is updated in place or replaced by a newly named
   deployment.

5. **Triage alone does not validate the promised tool inventory.** Phase 2
   tests triage, but the plan retains tools needed by code/review paths. Add
   targeted validation of those paths before retiring the existing runners.

The claim that the compatibility shims make upstream execution impossible also
remains stronger than the evidence: retaining the proven Python implementation
is justified, but missing logic in an entrypoint does not establish what the
full Actions runtime supports.

Review scope: the revised document and relevant local source. No runtime
probes were run and no implementation changes were made as part of this review.

## Response to the review of the rewrite — 2026-09-25

All five findings and the closing note accepted. Three were checked against
the source before being accepted; the rest stand on logic.

| # | verdict | what changed |
| --- | --- | --- |
| 1 routing tier | **accepted; verified** — every job in `reusable-dispatch.yml`, `route` included, runs on `inputs.runner_image`; run 1509 shows Route on `fullsend-dev-runner` | target table: hosted tier serves generic CI only; agent tier serves every Fullsend job, routing included; `fullsend-router` marked vestigial after phase 3, which `grep` confirms — nothing current references it |
| 2 G6 wording | accepted | phase 4: G6 addressed through the retained override, not resolved by the stock label |
| 3 active vs dormant | accepted | findings section split: the job-token defect bypasses the mint and is active; only `job_workflow_ref` is dormant |
| 4 which runner served conformance | **accepted; verified** — the evidence bundle records `job_id` but not `runner_name` | phase 2: update in place so the egress selector keeps applying; extend the script to record `runner_name` and require the new runner, or scale the old ones to zero |
| 5 tool inventory | accepted | phase 2: `command -v` in the new pod plus one review and one code run before retirement, with the measured cost stated |
| closing note | accepted, again | the necessity claim re-hardened in the rewrite; restated as unverified, with the argument being cost avoidance |

Finding 1 is the one that matters. The rewrite carried an assumption from the
org-mode discussion — that routing happens on the router — into a per-repo
design where it is false. It is the same failure shape as the earlier rounds,
a detail outliving the target it belonged to, surviving even a rewrite. The
verification was one grep and one run I already had.

Finding 3 corrects an error of mine that softened a real defect: calling a
mint-bypassing request "dormant on the mint" was a category mistake, and it
would have left an active authorization hole filed as a future concern.
