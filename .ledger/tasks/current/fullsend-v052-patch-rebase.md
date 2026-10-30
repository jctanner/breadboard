# Rebase the Fullsend patch set onto v0.52.0

## Goal

Bring `checkouts/fullsend-ai/fullsend` and `checkouts/fullsend-ai/agents`
up to current upstream and carry Breadboard's patch set forward: rebase each
patch, drop the ones upstream has made unnecessary, and record which ones
changed shape. This is breakpoint U3 (rebase report) of the
[upstreaming plan](../../plans/fullsend-upstreaming-plan.md).

## Starting point (2026-10-29)

| checkout | was | now | behind |
| --- | --- | --- | --- |
| fullsend | `a734637c` (2026-09-16, v0.43.0) | `932adbc94` (2026-10-30, v0.52.0) | 2,616 commits |
| agents | `6ffe9c7` (2026-09-16) | `f4acd03` (2026-10-29, v0.52.0) | 620 commits |

Against the new `main`, 5 of 13 fullsend patches and 1 of 5 agents patches
still applied.

## Method

Both checkouts' `main` were fast-forwarded to `origin/main` (both were clean
with no local commits). Each patch was replayed as one commit on a local
`breadboard/patches` branch in each checkout, conflicts resolved there, and
the patch files regenerated from those commits. The regenerated series was
then applied to clean `origin/main` trees exactly as
`deploy/scripts/05i-build-fullsend.sh` and the seed scripts apply it
(`git apply --unidiff-zero`, in order), and the result compared file for file
against the branches: identical for both repositories. The 05i patch list was
then compiled with the 05i `go build` command.

## Rebase report — fullsend

| patch | outcome |
| --- | --- |
| 0002 | still retired (unchanged) |
| 0003, 0004 | applied clean (mirror list) |
| 0005 | reworked: the status-comment client moved behind `statusNewForgeClientFn`, which now uses `newGitHubLiveClient` |
| 0006 | applied clean after 0005 (3-way) |
| 0007 | applied clean |
| 0008 | reworked: upstream now also scopes `GITHUB_TOKEN` (#8530, `agentTokenEnvVars`); the enterprise variables are added to that list. Still needed |
| 0009 | reworked: upstream moved `checkout_branch`'s remote access onto the runner (#8773); its in-sandbox command is wrapped with `withHarnessEnv`, and the real-shell test helper gets the empty env file at its new location |
| **0010** | **dropped — upstream fixed it.** #7973 verifies the gateway's exported profile against the file before treating "already exists" as success, and does not cache otherwise |
| 0011 | reworked: only `github setup` and `github set` remain in `github.go`; status/uninstall/sync-scaffold moved to `foreign.go`, which already uses `newGitHubLiveClient`. Header updated |
| 0012 | reworked: `RenderOptionsForInstall` lost its `perRepo` parameter; same change against the new signature |
| 0013 | reworked: `NewOrgConfig` is gone (org mode removed); its test now targets the per-repo defaults |
| 0014 | applied clean |
| **0015** | **new, upstream-bound.** `fullsend dispatch --route` (run by `reusable-dispatch.yml` for every CEL route) and `fullsend lint` were added after 0005 and build the agents-repo fallback client with a bare `gh.New`; the offline cache scan and the dispatch label matched only github.com's prefix. With tests |
| **0016** | **new, local only.** The `fullsend-github-ro` profile moved from agents into the fullsend binary (embedded, reserved id), so the emulator half of agents 0003 for triage/review moved here. Also carries the `github-ro` half of agents 0002: `GH_ENTERPRISE_TOKEN: "${GH_TOKEN}"` on the provider, accepted by the profile; `TestScaffoldProviderCredentialsMatchProfiles` updated to the local shape |

## Rebase report — agents

| patch | outcome |
| --- | --- |
| 0001 | applied clean |
| **0002** | **replaced by a local-only patch** (decided 2026-10-29): `0002-local-pass-the-forge-host-into-the-sandbox.patch`. See below |
| 0003 | split: only `fullsend-github-code` remains here (code, fix); the read-only half is fullsend 0016 |
| 0004 | reapplied: new pinned digests; same three harnesses (triage, review, code). `fix.yaml` now pins the same `fullsend-code` digest but is not substituted |
| 0005 | reworked: pre/post scripts are now bundled from `*.src.sh` (`make script-build`); library conflicts resolved, bundles regenerated, `make check-bundle` clean |

### Agents 0002: why it cannot be rebased

Upstream #1407 (agents `1271dab`) stopped expanding real forge tokens into the
sandbox. The `github-*` providers inject an `openshell:resolve:env:GH_TOKEN`
placeholder and the gateway substitutes the credential on egress to the
profile's endpoints; `scripts/sandbox-credential-boundary-test.sh` denylists
`GH_TOKEN` in `env.sandbox`. The old 0002 passed `GH_ENTERPRISE_TOKEN:
"${GH_ENTERPRISE_TOKEN}"` through `env.sandbox` — the real minted token,
which is exactly what #1407 removed.

The sandbox still needs `GH_HOST` (not a secret) and, for gh on a non-
github.com host, a `GH_ENTERPRISE_TOKEN`. Candidate: declare
`GH_ENTERPRISE_TOKEN: "${GH_TOKEN}"` as a second credential on the
`github-ro` (fullsend, embedded) and `github-code` (agents) provider
definitions so it arrives as a placeholder too, and pass only `GH_HOST`
through `env.sandbox`.

**Decision (user, 2026-10-29): local-only, not upstream** — keep Breadboard
working with Fullsend rather than drop sandbox access to the emulator.
Implemented without putting a real token in the sandbox. OpenShell 0.1.4
rejects a provider credential its profile does not declare
(`crates/openshell-server/src/grpc/provider.rs`, "provider credentials are not
declared by profile"), and a profile credential accepts every name in its
`env_vars`, so: the `github-code` (agents 0002) and `github-ro` (fullsend 0016)
providers declare `GH_ENTERPRISE_TOKEN: "${GH_TOKEN}"`, their profiles list
`env_vars: [GH_TOKEN, GH_ENTERPRISE_TOKEN]`, and only `GH_HOST` goes through
`env.sandbox` in the GitHub block of triage, review, code, fix, prioritize
and retro. Whether the in-sandbox `gh` then authenticates against the
emulator is proven only by the conformance run.

## Other findings

- **OpenShell → 0.1.4** (decided by the user 2026-10-29). v0.52.0 pins
  OpenShell 0.1.4 (`5a7728c`); v0.43.0 pinned 0.0.116 and the gateway ran
  0.0.110. `checkouts/openshell` moved from `cc14afc` (v0.1.6-pre) to
  `5a7728c`; `deploy/dependencies.json` updated. The 0.1.x chart (RFC 0012
  architecture) renamed its keys, so `deploy/k8s/openshell-values.yaml` uses
  `global.image.tag: "0.1.4"` (gateway, supervisor, new sandbox runtime) and
  `sandbox.image.*` in place of `server.sandboxImage`/`sandboxImagePullPolicy`;
  `supervisor.sideloadMethod` no longer exists. `helm template` renders
  (offline, preflight disabled) with the same namespace, storage class,
  default image and pull policy. All three 0.1.4 images exist on ghcr.io. The
  dashboard's OpenShell backend builds against this checkout's Python SDK;
  every client method and proto field it uses exists in 0.1.4. Not deployed.
- OpenShell 0.1.x's chart has `upstreamProxy.caBundle`, which stages a CA
  into each sandbox's supervisor bootstrap. If it applies to direct upstream
  TLS as well as a proxy, agents 0004 (CA-bearing images) can be dropped.
  Untested.
- Remaining bare `gh.New` callers not on the conformance path and left alone:
  `agent.go` (URL agents), `inference_openai.go` (repo variable setter),
  `mint_setup.go` (GCP mint role setup).
- `docs/fullsend-compatibility-profile.md` updated: local patches (agents
  0002–0004, fullsend 0016), 0015, and the retired 0010 and old agents 0002.

## Evidence

- Fullsend Go: `go build ./...` and `go vet` clean; `go test ./...` all
  packages pass except `internal/wranglerprep` `TestNpmCI` (file-order
  assertion, untouched by any patch) and `internal/cli`, which exceeded the
  default 10-minute timeout; rerun with `-timeout 60m` on the final tree:
  `internal/cli` ok (1032 s), `internal/scaffold` ok, `internal/sandbox` ok.
  After the 0016 credential change: `internal/scaffold`, `internal/sandbox`
  and the provider/profile subset of `internal/cli` pass.
- Agents: `make check-bundle` clean; `github-host-validation-test.sh`,
  `sandbox-credential-boundary-test.sh` and `harness/triggertest` pass. Two
  failures also fail on clean `origin/main`: `post-fix-test.sh`
  `push-forge-conflict-precommit-gate-first-parent`, and
  `gitlint-forbidden-type-scope-test.sh` (gitlint not installed).
- Exported series applied to clean `origin/main` trees reproduces both
  branches exactly; the 05i list compiles.

## Acceptance criteria

- [x] Checkouts on current upstream
- [x] Every fullsend patch rebased, dropped, or replaced, with reasons
- [x] Agents 0002 redesigned and decided (local-only)
- [x] OpenShell pinned to 0.1.4 (checkout, manifest, chart values)
- [x] OpenShell 0.1.4 gateway deployed
- [x] `make host-conformance-reset && make host-conformance` passes on the
  rebased set
- [x] `docs/fullsend-compatibility-profile.md` updated

## Deploy log (2026-10-30)

- `16-deploy-openshell.sh` fixes: `PROJECT_ROOT` defaults to the repo root
  (was `/vagrant`); under sudo, `KUBECONFIG` defaults to
  `/etc/rancher/k3s/k3s.yaml` (root's `~/.kube/config` is a 44-byte stub, so
  helm reached `localhost:8080`); a pre-0.1 StatefulSet is orphan-deleted
  because the 0.1.x chart renamed the immutable `serviceName`
  (`openshell` → `openshell-peer`). PVC kept.
- Gateway 0.1.4 then crash-loops: `provider policy composition startup
  preflight failed: list sandboxes failed: protobuf decode error ...
  NetworkEndpoint.enforcement ... invalid wire type`. The 0.0.110 database
  held two stale sandbox records (`fs-rha-*`, Sandbox CRs 29 days old) that
  0.1.4 cannot decode. With the user's approval the gateway started on a fresh
  database; the old one is kept on the PVC as `openshell.db*.0.0.110-bak`, and
  the two Sandbox CRs were deleted. Providers, profiles and the dashboard's
  `breadboard` workspace are recreated on use.
- 05i rebuilt cleanly; runner reports `openshell 0.1.4`. Seeding hit transient
  emulator `sqlite_locked` 503s; the remaining seed steps passed on retry.
- Run 1813 failed at Route: v0.52.0's `reusable-dispatch.yml` checks out with
  `sparse-checkout-cone-mode: false` and `/OWNERS` patterns; the emulator's
  built-in checkout always used cone mode. Fixed in
  `checkouts/github-emulator/src/runners/emulator/runner.py` (uncommitted).
- Run 1814 failed the sandbox's GitHub connectivity check (EOF; policy
  allowed, `NET:FAIL github.local:443`). Cause: from 0.1.x the supervisor runs
  in its own image and verifies upstream TLS with that image's bundle, so the
  agents 0004 CA no longer reaches it. `upstreamProxy.caBundle` was tried and
  crash-looped the gateway (`proxy_ca_bundle is set but no https_proxy is
  configured`); reverted (helm rollback to rev 10). Fix: local
  `openshell-supervisor-local:k3s` (pinned supervisor + internal CA), built in
  05i, selected in `openshell-values.yaml`.
- Conformance script drift: `25-reset-conformance.sh` used the removed
  `provider list-profiles` and could not delete a profile in use by a
  provider (0.1.x); it now lists with `-o json` and deletes the providers
  first. `24-run-conformance-triage.sh` read the mirror's 404 body as a
  profile; it now fetches with `curl -f` and skips the profiles that ship in
  the fullsend binary.
- **Run 1816 passed**: conclusion success on `fullsend-agent-runner`, labels
  `documentation` and `triaged` applied by `fullsend-triage[bot]`, minted
  triage token, 132 KB artifact. Evidence: `var/conformance/run-1816`.
  Supervisor log shows gh REST and `/api/graphql` to `github.local` allowed
  through `_provider_github_ro`, and Vertex `streamRawPredict` for
  `claude-haiku-4-5`.

- 2026-10-30, after conformance: the first **code-stage** run on 0.1.4
  (experiment/testrepo2 #5, run 1835) never got a sandbox. OpenShell 0.1.x's
  Kubernetes `workspace-init` seeds `/sandbox` as uid 10001, and upstream's
  `fullsend-code` image has `/sandbox/.cache/gopls` 0700 owned by uid 998:
  `Permission denied (os error 13)`, sandbox stuck in Provisioning, `fullsend
  run` kills `sandbox create` at its ready timeout (`signal: killed`). Fixed
  locally with `chmod -R a+rX /sandbox` in `deploy/fullsend-sandbox-local/Containerfile`;
  a code-image probe with `policies/base.yaml` then reached Ready. Recorded
  in the compatibility profile §1; upstream draft
  `docs/fullsend-issue-drafts/26-…`. Conformance covers triage only, which is
  why it passed; the code stage end to end is still unverified until #5 is
  re-triggered.

## Status

Current — deployed and conformance passes. Open: the supervisor-local build
step in 05i has not itself been run (the image was built by hand with the
same commands); whether agents 0004 is still needed is untested; the
emulator checkout fix is uncommitted in its checkout.
