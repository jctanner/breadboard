# Fullsend compatibility profile

Everything this deployment substitutes for Fullsend's production environment,
in one place, so the substitutions can be reviewed without reading twelve patch
headers and three seed scripts.

The rule this document answers to is decision 3 of the
[Fullsend integration conformance plan](../.ledger/plans/fullsend-integration-conformance-plan.md):

> The only allowed local substitutions are local image builds of the runner and
> sandbox, and emulator `.local` routing with development CA handling. Opaque
> mint tokens and a plain-HTTP mint are not allowed on the conformance path.

So this is a closed list, not a changelog. A deviation that is not here is
either a defect or something nobody wrote down; both are worth chasing. The
last section names the two credential substitutions that sit at the edge of
what decision 3 allows, because a compatibility profile that lists only the
comfortable deviations is not doing its job.

## What is *not* substituted

Worth stating first, since it is the claim the plan exists to support. The
runner executes Fullsend's own `fullsend.yaml` shim, which calls its own
`reusable-dispatch.yml`, which loads harnesses from the `fullsend-ai/agents`
tree. The agent, its skills, its pre and post scripts, its result schema and
its validation loop are all upstream files. Nothing is reimplemented, and no
Breadboard compatibility layer sits between Fullsend and the forge — decision 5
requires missing forge behaviour to be added to the emulator instead, which is
what happened every time.

## 1. Local image builds

Decision 3's first clause. Four images are built here rather than pulled.

| image | base | what the local layer adds |
| --- | --- | --- |
| `fullsend-runner-dev:k3s` | the emulator's Actions runner image | `gh`, `yq`, a Go toolchain, `gitleaks`, `pre-commit`, the `fullsend` and `openshell` binaries, the emulator's runner implementation |
| `fullsend-sandbox-local:k3s` | `ghcr.io/fullsend-ai/fullsend-sandbox` at the digest `harness/triage.yaml` pins | `ca-certificates` and this cluster's internal CA |
| `fullsend-code-local:k3s` | `ghcr.io/fullsend-ai/fullsend-code` at the digest `harness/review.yaml` pins | the same one layer; review and code pin the same digest |
| `fullsend-mint-dev:k3s` | built from `deploy/` | the development mint itself |

Two properties keep these honest, both enforced by
`deploy/scripts/05i-build-fullsend.sh` rather than by convention:

- **The sandbox base digests are read from the harness files that pin them**,
  not repeated in the build script. A harness that moves to a new image stops
  the build instead of quietly producing a local image on last month's base.
- **The tool versions the runner ships are compared against the agent
  libraries that also self-install them** — gitleaks against
  `gitleaks-install.lib.sh` including both per-arch checksums, pre-commit
  against `precommit-gate.lib.sh`. The scripts skip their own download when
  the tool is on `PATH`, so the image silently wins; a drift would mean a run
  using a version the library never verified. The build fails on a mismatch.

The CA layer exists because the sandbox supervisor reads its upstream TLS roots
from the system bundle once at startup, and the OpenShell chart at the deployed
version cannot inject a CA into sandbox pods. Uploading one afterwards does not
help. Drop this the day the chart gains CA injection, or the forge is served by
a publicly trusted certificate.

## 2. `.local` routing and development CA handling

Decision 3's second clause.

- `github.local`, `jira.local`, `gitlab.local` and the rest resolve to the
  in-cluster `ingress-proxy` service. Nothing leaves the cluster to reach them.
- Certificates come from a cert-manager internal CA. That CA is baked into the
  sandbox images (above) and trusted by the runner.
- `NO_SSL_VERIFY=1` is set for the Breadboard dashboard, which talks to those
  emulator endpoints.
- **Agents patch 0003** adds `github.local` to `fullsend-github-ro.yaml` and
  `fullsend-github-code.yaml`. A provider profile is the sandbox's network
  allowlist and Fullsend imports profiles verbatim, expanding no variables —
  correct for a policy file, and the reason a host that varies per environment
  can only be added by editing it. The read-only posture and the binary
  allowlist are unchanged, `curl` still excluded. **Local-only; not for
  upstream.**
- **Agents patch 0004** points the three harnesses at the CA-bearing local
  images described above. **Local-only; not for upstream.**

Those two are the only patches in the whole set marked `NOT FOR UPSTREAM`.

## 3. Patches that are fixes, not substitutions

The rest of the patch set is upstream-bound: each is a real defect that would
affect any GitHub Enterprise install, found here because an enterprise host is
what this stack is. They are listed so a reader can tell them apart from the
two substitutions above, not because they are deviations.

**Go source, applied before the binary is compiled** (`05i-build-fullsend.sh`):

| patch | fixes |
| --- | --- |
| 0005 | resolve the agents repo and status comments against the configured host |
| 0006 | allow a forge reachable only privately |
| 0007 | parse enterprise raw-content URLs |
| 0008 | scope the minted token on forges that are not github.com |
| 0009 | load the harness environment for dummy behaviour ops |
| 0010 | do not report success for a profile import that replaced nothing |
| 0011 | address the configured forge in the `github` subcommands |
| 0012 | let an installation name the runner its workflows target |

**Agents tree, applied to the mirror at seed time**
(`seed-upstream-agents.py`):

| patch | fixes |
| --- | --- |
| 0001 | accept an issue URL on the configured GitHub host (triage library) |
| 0002 | pass the forge host into the sandbox — all six GitHub overlays |
| 0005 | the same host assumption in the review, code and fix libraries |

**Fullsend mirror, applied to files a workflow reads at run time**
(`seed-upstream-fullsend.py`): patches 0003 and 0004, which honour
`GITHUB_API_URL`/`GITHUB_SERVER_URL` in the action and skip local sandbox host
setup when a gateway is configured.

A patch in the wrong one of those three lists does nothing, and does it
silently. The lists say so where they are defined.

### Retired

- **Go patch 0002, "allow an insecure dev mint URL"** — retired, as decision 3
  required once the mint was served over the stack's internal TLS. It only
  relaxed the HTTPS check for an `http://` URL, and nothing on any path uses
  one. The file is kept for the record; the gap in the numbering is deliberate.
- Two earlier patches (sandbox-name length, sticky-comment forge URL) were
  dropped because upstream fixes both natively.

## 4. Emulated marketplace actions

Not decision 3 substitutions: decision 5 requires forge behaviour the scaffold
needs to be added to the emulator rather than worked around. Three marketplace
actions have no network to be fetched from here, so the emulator's runner
implements them locally and says so in the log each time
(`Emulating <action> locally`):

- `actions/upload-artifact`
- `actions/setup-go`
- `google-github-actions/auth`

## 5. Runtime and model selection

Covered by decision 9, not decision 3. The harnesses pin `model: opus`; this
deployment selects otherwise at run time through repository Actions variables,
`FULLSEND_RUNTIME` and `FULLSEND_MODEL`. Nothing patches the harness. The
`dummy` runtime is used wherever a scripted sandbox operation suffices, and a
real model only where agentic behaviour is the thing under test.

## 6. Network posture

Not a substitution — a restriction, and the deployment is *more* confined than
production rather than less.

`deploy/k8s/27-fullsend-runner-egress.yaml` limits the two Fullsend runner
deployments to the pod and service CIDRs: CoreDNS, the API server, the emulator
through the ingress proxy, the mint, and the OpenShell gateway. No public
egress. The gateway keeps its own, since it is what reaches Vertex on the
sandbox's behalf under the provider profiles.

## 7. Credentials: two deviations, named separately

These are the substitutions most worth a reviewer's attention, and the first
draft of this document ran them together. They are unrelated.

### 7a. The development mint

Decision 4 permits "the emulator's OIDC issuer and key set **or** Fullsend's
standalone mint". This deployment runs the former: `deploy/fullsend-mint-dev/`
is a Breadboard component, not a Fullsend one.

What it verifies is real, and is the part the plan set out to prove:

- the assertion's signature must verify against a key the emulator publishes;
- `iss` must be the configured issuer and `aud` the configured audience;
- every repository named in `repos` must be the repository the token was issued
  for — so a run in one repository cannot mint for another.

What it returns is an emulator personal access token selected by role, from
`FULLSEND_ROLE_TOKENS`, rather than a short-lived GitHub App installation
token. That is the deviation. Its own header records why the checks above were
added: an earlier version trusted a shared secret, so anything holding that
secret could ask for any role on any repository, and nothing in the request was
checked.

Whether a static per-role token counts as one of the "opaque mint tokens"
decision 3 forbids is a judgement for someone other than its author. It is
scoped and it is earned by a verified claim, which is not what "opaque"
usually means — but it is not short-lived, and the plan should say so out loud
rather than leave a reader to infer it from a manifest.

### 7b. The dashboard onboarding credential

Separate path, separate deviation. `fullsend github setup` run from the
dashboard needs a credential that can write workflows and secrets to a
repository. The production answer is a short-lived App installation token; this
deployment holds no App private key, so it falls back to the emulator admin
token.

This one *is* labelled: `src/dashboard/fullsend_onboarding.py` returns
`emulator-admin-fallback` as the credential kind, and
`tests/test_fullsend_onboarding.py` asserts both that the label is returned and
that it appears in the operation's message. WP7 records the App token as open
by decision, with the missing private key as the reason.

The remedy for either, if a review judges them to exceed decision 3, is an App
private key in the deployment — not a rewording here.
