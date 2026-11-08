# Fullsend behaviour tests on Breadboard

Run Fullsend's own behaviour-test suite (BT: `e2e/behaviour/`, Fullsend ADR
0066) against Breadboard's GitHub emulator, Actions runners and Fullsend Mint,
so the conformance path is checked by upstream's scenarios rather than only by
Breadboard's hand-built smoke runs.

Started 2026-11-07. Related:
[conformance plan](fullsend-integration-conformance-plan.md) (closed; found the
host defects), [upstreaming plan](fullsend-upstreaming-plan.md) and the
[PR status note](../notes/fullsend-upstream-pr-status-20261106.md) (the
campaign landing those fixes). This plan consumes their patch stack; it does
not change how that campaign files or verifies anything.

## What the suite is

- 64 Gherkin scenarios in 34 feature files: `dispatch/`, `platform/`,
  `runtime/`, `triage/`, `code/`, `actors/`. Run by godog through
  `make behaviour-test` (`go test -tags behaviour -race -timeout 45m
  ./e2e/behaviour/`), 12 scenarios concurrently by default.
- Each scenario leases a fresh `(org, test-repo-NN)` slot (the claim creates
  the repo), installs Fullsend into it with `fullsend github setup --direct
  --vendor --runtime dummy --mint-url … --app-set …`, commits a dummy-agent
  script to `.fullsend/behaviour/current-scenario.yaml`, drives the forge
  (issue, label, PR, comment), waits for the workflow run by file name,
  downloads its logs and artifacts, asserts on `behaviour-results.json`,
  `metrics.json` and forge state, then deletes the repo.
- The dummy runtime replaces the model with a scripted op table (write
  fixture, read file, fetch URL, assert env, checkout branch, HTTP probe) run
  inside the real OpenShell sandbox. Everything else is real: dispatch,
  harness, post-scripts, mint exchange, pushes.
- Forge and CI are pluggable (`BEHAVIOUR_SCM=github|gitlab`,
  `BEHAVIOUR_CI=githubactions|gitlabci`); the install driver is chosen by
  `ENVIRONMENT`.

Guides: upstream `docs/guides/dev/behaviour-testing.md` and
`behaviour-drivers.md`.

## What already fits Breadboard (read 2026-11-07, upstream `709ec1b`)

- **Credentials.** Outside GitHub Actions the suite takes `GH_TOKEN` /
  `GITHUB_TOKEN` (`e2etest.resolveLocalToken`); it mints an `e2e` role token
  only when `GITHUB_ACTIONS=true`. A host run needs no `e2e` App.
- **Inference.** `RunGitHubSetupWithOpts` resolves the inference WIF provider
  only when `E2E_GCP_PROJECT_ID` is set. Unset means no GCP call. (Earlier
  session notes listed this as a gap; it is not one.)
- **Mint.** `install.NewRepoPoolExternalMint` already exists: it uses
  `FULLSEND_MINT_URL` and never deploys or tears down a mint. Nothing selects
  it yet.
- **CLI host.** Upstream's `internal/cli/github_client.go` honours
  `GITHUB_API_URL`; Breadboard's patches 0011/0014 cover the rest of the CLI.
  The vendored binary the suite builds comes from the patched checkout.
- **Emulator.** github-emulator #17–#21 closed the API gaps the drivers and
  steps hit (workflow lookup by file name, run and artifact lists, org
  variables, app/installation lookups, review threads, `updateRefs`).
- **Patch 0009** (dummy-runtime ops load the harness env) merged upstream as
  fullsend#9055 on 2026-11-07 and can be dropped.

## Gaps

Harness (Fullsend test code; no Breadboard patch touches it today):

| ID | Gap | Where |
| --- | --- | --- |
| BT-H1 | `e2etest.NewLiveClient` never sets a base URL, so every suite-side forge call goes to `api.github.com` | `internal/e2etest/testutil.go` |
| BT-H2 | Raw `https://api.github.com/...` URLs in cleanup and repo checks | `internal/e2etest/cleanup.go` (5), `testutil.go:482` |
| BT-H3 | `installFactoryFor` knows only `dev`/`stage` (both Cloudflare mints); no way to pick `RepoPoolExternalMint` | `pkg/behaviourtest/select.go` |
| BT-H4 | Pool layout fixed: `dev` = 22 orgs `halfsend-01…22`, `stage` = one org `halfsend`; only slots per org is configurable | `drivers/install/slotpool.go` |
| BT-H5 | Shell scripts embedded in steps call `api.github.com` (bot actors, mint probe workflow) | `steps/bot_actors.go`, `steps/mint_probe_workflow.yml` |
| BT-H6 | Two runtime features assert github.com tree URLs for skills | `features/runtime/{agent-settings,skill-overrides}.feature` (gated, out of scope) |

Breadboard / stack (to confirm in the spike; each is a question, not a
finding yet):

| ID | Question |
| --- | --- |
| BT-S1 | Does `github setup --direct --vendor --app-set <set>` work against the emulator? Breadboard's onboarding uses `--skip-app-setup` without `--direct`/`--vendor`, so these paths are unexercised here. `--vendor` may also fetch from github.com (`internal/e2etest/buildargs.go` names the upstream repo URL). |
| BT-S2 | Mint policy: `FULLSEND_ALLOWED_ORGS` is a static list (`fullsend-dev,experiment`), and `FULLSEND_WORKFLOW_HOST_REPOS` lists only `fullsend-dev/triage-target`. Does a vendored per-repo install host its reusable workflows in the repo itself, and so need every `test-repo-NN` listed? |
| BT-S3 | Runner selection: installed workflows target the default runner label unless patch 0012's setting is given. Can `BEHAVIOUR_CONFIG_PRESET` carry it, plus `FULLSEND_RUNNER_IMAGE`? |
| BT-S4 | Actors: write, triage and outsider users with personal tokens (`TEST_ACTOR_*_PAT`), plus a role App set installed on the pool org. |
| BT-S5 | Repo churn: create, install, run and delete one repo per scenario; check the emulator, runners and sandbox controller keep up at concurrency 1 and then 4. |

## Approach

- **Run from the host first, then make it repeatable.** The spike runs
  `go test` from the patched checkout on the host, using the host proxy names
  and the Breadboard CA. Once a tier passes, wrap seeding, run and collection
  in a Markov workflow driven with `markovd-cli`, per Breadboard practice.
- **Harness changes are patches in the existing stack.** Add `0017+` under
  `deploy/fullsend/patches/`, marked as behaviour-test patches, applied by the
  same build path. BT-H1/H2 are host-assumption defects that can go upstream
  as problem-only issues through the campaign. BT-H3/H4 are test-infra options
  that may stay local; the owner decides, with the other session.
- **Keep scenarios unedited.** Select with tags (`GODOG_TAGS`) and
  `BEHAVIOUR_CAPABILITIES`. Never edit a feature file to make it pass. A
  scenario that cannot run here gets a recorded reason, not a fork.
- **New emulator gaps are filed against the emulator** (problem-only issues
  like #17–#21) and fixed there, not worked around in the harness.

## Scenario tiers

| Tier | Scope | Needs |
| --- | --- | --- |
| T1 | `triage/triage.feature` (1 scenario): label → triage → sandbox block + fixture → `ready-to-code` | H1–H4, S1–S3 |
| T2 | Ungated `dispatch/*` and `code/branch-namespace`: routing, fork dispatch, owners auth, fix authorization, reactions, hooks, URL dispatch | T1 + S4 (actors) |
| T3 | `platform/*`: actor and bot authorization, mint scope, mint status | T2 + H5, mint probe hosts, mint status auth |
| Out | Real-model and gateway runtime features, `jira-poll-dispatch` (needs its own Jira wiring; a later candidate given the Jira emulator), `@playback`, GitLab | — |

## Breakpoints

Each stops with something runnable or visible; wait for go or pivot.

- **BT-B0 — current stack, rebuilt.** Fast-forward both fullsend checkouts to
  upstream main, drop 0009, `git apply --check` the rest, rebuild
  (`host-rebuild-*` for runner/agent images), and pass the existing Fullsend
  conformance smoke. *Show:* patch-apply report and a green smoke run.
- **BT-B1 — install spike, no suite.** By hand, against one seeded pool org on
  the emulator: run `fullsend github setup <org>/test-repo-01 --direct
  --vendor --runtime dummy --mint-url <bb mint> --app-set <set>`, then open an
  issue and label it `ready-for-triage`. Answers BT-S1–S3. *Show:* the
  installed repo in `github.local/ui/`, the dispatch and triage runs, and their
  logs in the Fullsend dashboard. Pivot point: if `--direct`/`--vendor` cannot
  work here, decide between fixing it (new findings) and a Breadboard install
  driver that uses the onboarding path instead.
- **BT-B2 — harness patches (local).** Write as patches in the existing
  stack; none is offered upstream as a Breadboard feature:
  - BT-H1/H2: `GITHUB_API_URL` in `NewLiveClient` and the raw cleanup and
    repo-check URLs. These are host-assumption defects in their own right;
    whether they go upstream as problem-only issues is the campaign's call;
  - BT-H3: an `ENVIRONMENT` value (e.g. `external`) selecting
    `RepoPoolExternalMint`, with the install mode chosen the upstream way —
    vendored by default (the PR path, built from the tree under test), and
    `--fullsend-ref <ref>` on request (the stage path);
  - BT-H4: pool org name(s) and count from env;
  - pass the runner label (`FULLSEND_RUNNER_IMAGE`, S3) through to setup.
  Unit tests pass (`go test ./pkg/behaviourtest/... ./internal/e2etest/...`).
  Codex review before commit. *Show:* the patches and test output.
- **BT-B3 — T1 green, both modes.** Seed script for the pool org(s), Apps and
  runner preset that also generates the mint's `FULLSEND_WORKFLOW_HOST_REPOS`
  from the pool layout (as `mint_groups.go` does upstream). One entry point
  (e.g. `make bt-run`) builds the tree under test and runs a `GODOG_TAGS`
  selection. Run the triage scenario at `GODOG_CONCURRENCY=1`, vendored, then
  with `--fullsend-ref main`. *Show:* godog output for each mode, the run's
  artifacts, the slot repo created and deleted.
- **BT-B4 — T2 green or itemised.** Add actors (S4), run T2 at concurrency 1
  then 4 (S5). Every failure is a bug file (harness, emulator, stack or
  upstream) with its tier and scenario. *Show:* a pass/fail table per
  scenario.
- **BT-B5 — repeatable.** Markov workflow (seed, run tier, collect redacted
  artifacts) driven by `markovd-cli`; results visible in the dashboard or
  Observatory. *Show:* one run launched from the CLI end to end.
- **BT-B6 — T3**, only after B5, if wanted.

## Inventory

Each gap row above becomes a bug file when work starts on it
(`.ledger/bugs/open/conformance-bt-*`), and each breakpoint is a task file.
Harness patches name their gap ID in the patch header. This is a first slice
of the conformance inventory discussed 2026-11-07; the upstream campaign keeps
its own tracking.

## Risks

- `--direct --vendor` is the install path upstream tests and Breadboard does
  not; B1 may surface a new cluster of host findings before any scenario runs.
- Repo-per-scenario churn is heavy for a single-node emulator and runner pool;
  keep concurrency low until B4 measures it.
- The suite moves fast upstream; pin the checkout SHA per run and record it
  with results.
- Fork scenarios need a second account that can fork into its own namespace;
  confirm the emulator's fork support covers what `fork.go` does.

## Status notes

### 2026-11-07 BT-B0: stack on current upstream, conformance passes

- Checkouts fast-forwarded: fullsend `932adbc94` → `1d00009b1`, agents
  `f4acd03` → `e41be7b4` (both clean, no local commits).
- Patch series: 0005, 0006 and 0015 regenerated for context drift only (3-way
  replay, headers kept); 0007, 0008, 0011–0014, 0016 and mirror 0003/0004
  unchanged. **0009 retired**: upstream merged the same fix as fullsend#9055
  (#9046, `877c381b5`); file deleted, removed from 05i with a comment. agents
  0004 updated to the v0.54.0-rc.1 image digests; agents 0001–0003 and 0005
  unchanged. The regenerated series, applied to clean `origin/main` the way
  05i applies it, is identical to the replay branch. No new hard-coded
  github.com call sites upstream.
- Checks: `fullsend` builds; `go test` passes for `internal/fetch`, `forge`,
  `config`, `scaffold`, `runtime`; agents `make check-bundle` and
  `github-host-validation-test.sh` pass. `internal/cli` exceeded the default
  10-minute `go test` timeout; rerun with `-timeout 30m` passes (1,216 s), so
  the package is slow, not hung.
- 05i rebuilt and imported all five images; `22-seed-fullsend.sh` hit one
  transient emulator `sqlite_locked` 503, remaining steps passed on resume.
- Run 1934 failed: v0.54 rejects `create_issues` in `.fullsend/config.yaml`.
  Three repos onboarded under the old CLI carried it (`fullsend-dev/triage-target`,
  `fullsend-dev/button-probe`, `experiment/testrepo2`); migrated by hand to
  `tracker.github.allowed_targets` per upstream's migration guide (parsed
  before/after: same targets, nothing else changed). No seed writes the key.
- **Run 1936 passed**: success on `fullsend-agent-runner`, labels
  `documentation` and `triaged` by `fullsend-triage[bot]`, minted triage token,
  114 KB artifact. Evidence: `var/conformance/run-1936`.

### 2026-11-07 BT-B1: install spike

Spike repos `experiment/bt-spike-01` (vendored) and `experiment/bt-spike-02`
(non-vendored), created in an org the mint already admits and where the role
Apps are installed org-wide, so no mint or manifest change. Setup ran from the
host with the patched binary, `GH_TOKEN`=emulator admin token,
`GITHUB_API_URL`/`GITHUB_SERVER_URL`, and `SSL_CERT_FILE` set to
`deploy/fullsend-sandbox-local/internal-ca.crt`. The older
`deploy/pipeline-agent/internal-ca.crt` no longer verifies `github.local`.

- **S1 answered.** `github setup --direct --vendor --runtime dummy --app-set
  fullsend` works against the emulator (46 files, 5 variables;
  `FULLSEND_REVIEW_CLIENT_ID` resolved via `GET /apps/{slug}`). `--vendor`
  needs `--fullsend-source` (a dev build cannot fetch its own source); in a
  suite run that is the checkout, so it must carry Breadboard's patches.
  `--fullsend-ref main` (non-vendored) needs no source tree and pushes 3 files.
- **S3 answered.** The default render targets `ubuntu-24.04`, which no Breadboard
  runner serves. `FULLSEND_RUNNER_IMAGE=fullsend` (patch 0012) renders
  `runs-on: fullsend`. The suite must pass it through to setup.
- **S2 answered, vendored fails.** Runs 1941 and 1942 failed at "Mint triage
  token" with 403s. The mint audit says `job_workflow_ref does not reference an
  allowed workflow host repo`, and the ref was
  `/.github/workflows/reusable-dispatch.yml@refs/heads/main`. Two causes:
  - the mint's `FULLSEND_WORKFLOW_HOST_REPOS` lists only `triage-target`;
  - an emulator bug, BT-E1.
- **Non-vendored passes.** Runs 1943/1944: Route, Triage and Harness dispatch
  succeed. Every behaviour op succeeds, `metrics.json` reports `runtime: dummy`
  from the repo config, and `fullsend-triage[bot]` labels and comments.
  The dispatch uses the emulator's patched `fullsend-ai/fullsend` mirror at
  `main`, which the mint always admits.

New emulator gaps (file against github-emulator, fix there):

| ID | Gap |
| --- | --- |
| BT-E1 | A local reusable-workflow call (`./.github/workflows/x.yml`) leaves `called_full_name` empty in `_resolve_reusable_workflow` (`src/app/services/workflow_service.py:307`), so the OIDC `job_workflow_ref` has no `owner/repo` and the job's `_workflow_repository` is empty. GitHub reports `owner/repo/.github/workflows/x.yml@refs/heads/<ref>`. |
| BT-E2 | The triage artifact uploads under the literal name `${{ inputs.artifact-name \|\| format('fullsend-{0}', inputs.agent) }}`; the expression is not evaluated. The suite's CI driver selects artifacts by `fullsend-<agent>`, so every artifact assertion would miss. |

Both are fixed in github-emulator `dd2588f` (2026-11-07). That commit
deploys through `make host-rebuild-github` for the server and through
`05i-build-fullsend.sh` plus a `github-actions-runner` restart for the runner,
whose image embeds `runner.py`. Live checks:

- **BT-E1.** bt-spike-01 runs 1949/1950 still fail at "Mint triage token", but
  the mint now sees
  `experiment/bt-spike-01/.github/workflows/reusable-dispatch.yml@refs/heads/main`.
  It refuses only because of the host list.
- **BT-E2.** bt-spike-02 run 1952 uploads its triage artifact as
  `fullsend-triage`.

With BT-E1 fixed, the vendored path (b) is blocked only by the mint's
`FULLSEND_WORKFLOW_HOST_REPOS`.

**Decision (B1 pivot, 2026-11-07): both, vendored first.** Upstream CI runs
the suite in two modes: vendored on pull requests (dev; the PR's own build
installed into each slot) and `--fullsend-ref main` on push to main (stage).
Both deploy their own mint and set its `WORKFLOW_HOST_REPOS` to every pool
repo (`mint_groups.go`). Vendored is the path that tests a change (the
tree under test is what gets installed), so it comes first; non-vendored is
the cheap stage-parity check. The host list is generated from the pool
layout, as upstream does, rather than edited by hand. B2 below is rewritten
to match. The harness work stays local patches: this is Breadboard's way of
running the suite, not a proposal to Fullsend.

### 2026-11-07 BT-B2: harness patches

Two test-only patches under `deploy/fullsend/patches/`, written on upstream
`1d00009b1` plus the build list (0005–0016):

| Patch | Gap | Change |
| --- | --- | --- |
| `0017-address-the-configured-forge-in-the-behaviour-harness` | BT-H1, BT-H2 | `NewLiveClient` and the six raw REST calls (`cleanup.go`, `testutil.go`) take the API root from `GITHUB_API_URL`, else api.github.com. Hosted runs are unchanged, because Actions sets it to api.github.com. |
| `0018-local-run-the-behaviour-suite-against-an-external-mint` | BT-H3 | `ENVIRONMENT=external` selects `RepoPoolExternalMint` (`FULLSEND_MINT_URL`) with the one-org stage layout. Install is vendored by default, or `--fullsend-ref $BEHAVIOUR_FULLSEND_REF` when that is set; `--app-set $BEHAVIOUR_APP_SET` is passed when set. |

Findings that shrank the patch set:

- **BT-H4 needs no patch.** `external` uses the single `halfsend` org;
  `BEHAVIOUR_POOL_SIZE` already sets the slot count. B3 seeds an emulator
  org named `halfsend`.
- **The runner label needs no patch.** The CLI subprocess inherits the
  environment (`testutil.go`), so `FULLSEND_RUNNER_IMAGE=fullsend` and
  `GITHUB_API_URL` reach `github setup` as they are.
- **`--fullsend-source` is not needed.** The suite runs inside the checkout,
  so the vendored install auto-detects its source. B1 needed the flag only
  because it ran outside one.
- **TLS needs no code.** Go honours `SSL_CERT_FILE`; B3 points it at the
  stack CA.

Neither patch is in the build list in `05i-build-fullsend.sh`, because
nothing in them is compiled into the binary. The B3 entry point applies them
on top of that list. Checks:

- `git apply --check` passes on the stack, and the result is identical to the
  authored tree;
- `go test ./pkg/behaviourtest/... ./internal/e2etest/...` passes, including
  new tests for the base URL, `external` selection, the layout and the
  install options;
- the suite compiles (`go vet -tags behaviour ./e2e/behaviour/`);
- Codex review: no findings.

Still open, for later tiers (BT-H5): `steps/bot_actors.go` and
`steps/mint_probe_workflow.yml` call api.github.com, and `base_dispatch.go`
and `url_dispatch.go` build raw.githubusercontent.com URLs. T1 (triage) uses
none of them.
