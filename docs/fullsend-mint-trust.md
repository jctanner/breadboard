# What the development mint trusts and covers

The Fullsend token mint is the point where a workflow run turns into a
credential an agent can act with. In production that credential is a GitHub
App installation token, minted by Fullsend's central mint after it verifies
the run's OIDC assertion (Fullsend ADR 0029). This deployment runs a small
substitute, `deploy/fullsend-mint-dev/server.py`, because the emulator has no
GitHub App key exchange. This page states exactly what that substitute trusts,
what it covers, what it does not check, and where the evidence for each claim
lives. It is the reference for work package 3 of the conformance plan.

The one-line version: the mint trusts a signed assertion from the emulator's
own OIDC issuer and nothing else, and it hands out a pre-created bot token
whose role and repository are pinned by that assertion.

## The exchange, step by step

```text
job (id-token: write)
  --request token-->  emulator  GET /actions/oidc/token?audience=fullsend-mint
  <--RS256 JWT------            claims derived from the job, 300 s lifetime
  --Bearer JWT + {role, repos}-->  mint  POST /v1/token
                                  verify signature, iss, aud, exp/nbf
                                  refuse any repo != token's repository claim
  <--{token, expires_at, granted_repos, granted_permissions}--
  use as GH_TOKEN for checkout, gh, git, and the post-script
```

1. **The job asks the emulator for an assertion.** The composite action
   `mint-token` (and the CLI's own `mintclient` when a post-script re-mints)
   calls `ACTIONS_ID_TOKEN_REQUEST_URL` with the per-job request token. The
   emulator refuses unless the job declared `id-token: write`
   (`src/app/api/oidc.py`). The caller chooses only the audience. Every
   identifying claim is derived from the job the request token belongs to,
   so a workflow cannot ask for a token that describes another repository.
2. **The emulator signs it.** RS256, with a key pair generated at emulator
   start and published at `/.well-known/jwks.json`. Lifetime is 300 seconds.
   The subject is `repo:<owner>/<name>:ref:<ref>`, or
   `repo:<owner>/<name>:pull_request` for pull request events, the same
   shapes GitHub uses. Claims include `repository`, `repository_owner`,
   `run_id`, `workflow_ref`, `job_workflow_ref`, `event_name`, `actor`, and
   `runner_environment: self-hosted`.
3. **The mint verifies.** It fetches the emulator's JWKS, caches it for five
   minutes, and refetches on an unknown key id so an emulator restart does
   not strand it. It requires a valid signature, `iss` equal to
   `FULLSEND_OIDC_ISSUER` (`https://github.local`), `aud` equal to
   `fullsend-mint`, and current `exp`, `nbf`, `iat`. It then refuses the
   request if any repository in `repos` is not the token's `repository`
   claim. A bare name is resolved against the token's `repository_owner`.
4. **The mint answers with a role token.** The token is looked up by role
   from `FULLSEND_ROLE_TOKENS`, a JSON object held in the
   `fullsend-mint-dev-credentials` Secret. The response reports the granted
   repositories and the role's nominal permission set. Neither the request
   nor the response is logged; the mint's request logger is disabled.
5. **The runner uses it.** The token becomes `GH_TOKEN` for the checkout,
   `gh`, git pushes, and the post-script. The sandbox receives it through
   Fullsend's normal provider path and never sees the role registry or an
   admin credential.

## What the mint trusts

| Trust | Where it is established | How it can be broken |
| --- | --- | --- |
| The emulator's signing key | Fetched from `https://github.local/.well-known/jwks.json` over the internal CA (`SSL_CERT_FILE`) | Anyone who can serve that URL to the mint, or who holds the emulator pod's memory, can sign assertions |
| The issuer and audience strings | `FULLSEND_OIDC_ISSUER`, `FULLSEND_OIDC_AUDIENCE` in `deploy/k8s/24-fullsend-mint-dev.yaml` | Misconfiguration only; the values are not secrets |
| The `repository` and `repository_owner` claims | Set by the emulator from the job, never from the caller | Only by forging the assertion, which needs the key above |
| The role registry | `FULLSEND_ROLE_TOKENS` from the `fullsend-mint-dev-credentials` Secret, written by `deploy/scripts/18-deploy-fullsend-mint-dev.sh` | Anyone with `get secret` in the namespace holds every role token; the mint is not what protects them |
| The network path | The mint listens on TLS with a cert-manager certificate from the internal CA | There is no NetworkPolicy on the mint. Any pod in the cluster can reach it. The assertion is the only gate |

The mint does **not** trust: the caller's chosen subject (there is none), the
`level` field (ignored, see below), the `repos` list beyond checking it
against the claim, or any shared secret. The opaque `FULLSEND_DEV_OIDC_TOKEN`
that an earlier version accepted is gone; a request without a verifiable
assertion is answered `401`.

## What the mint covers

- **Repository binding.** A run in repository A cannot mint for repository B.
  This is the check that matters and it is enforced on every request.
  Evidence: the trust-boundary workflow seeded by
  `deploy/fullsend/seed/seed-trust-check.py` prints its own claims, exchanges
  them, and asserts the credential works on its own repository and is refused
  on a private one the roles are not collaborators on (breakpoint B4).
- **Role selection.** The `role` field selects one of `triage`, `scribe`,
  `coder`, `review`, `fix`, or `fullsend`. Unknown roles are `400`.
- **Provenance in the claims.** `job_workflow_ref` names the called reusable
  workflow (`fullsend-ai/fullsend/.github/workflows/reusable-*.yml@main`),
  not the caller, since G46 was fixed. The mint does not yet act on it, but
  the claim a production mint would check is present and correct.
- **Short assertion lifetime.** 300 seconds, with a replay-resistant `jti`.
  The role token it is exchanged for is a different matter, below.

## What the mint does not cover

These are the gaps between this substitute and Fullsend's production mint.
Each is a deliberate simplification, listed so nobody reads a green
conformance run as proof of something it does not test.

| Production mint (Fullsend ADRs 0029, 0073, 0077, 0078) | Development mint |
| --- | --- |
| Mints a fresh GitHub App installation token per request, scoped to the requested repositories, expiring in about an hour | Returns the same pre-created bot personal access token for a role every time. `expires_at` is reported as one hour ahead but the token does not expire |
| Downscopes permissions to the role's named privilege level; `level` defaults to `read` | Ignores `level`. The bot token carries the `repo`, `repo:status`, and `read:org` scopes regardless of role; the role's effective power is whatever the bot user can do on the repository |
| Per-role permission sets enforced by the App installation | Nominal only. `granted_permissions` in the response describes the role's intent, not what the token can do |
| Checks `job_workflow_ref` against registered workflow prefixes | Not checked |
| Org and per-repo allowlists (`ALLOWED_ORGS`, `PER_REPO_WIF_REPOS`) | None. Any repository on the emulator whose job can obtain an assertion may mint for itself |
| `["*"]` means installation-wide in the shapes ADR 0077 allows | Refused as an invalid repository name. Only bare names and `owner/name` are accepted |
| Audit log of every exchange | None. The mint logs nothing by design, to keep tokens out of pod logs |

The consequence that matters most: **role separation on this stack is
enforced by the emulator's collaborator permissions, not by the token.** On
the conformance target the `fullsend-triage[bot]`, `fullsend-code[bot]`, and
`fullsend-fix[bot]` users all hold push access; the review and scribe bots
are not collaborators at all. So a triage token can push, and a triage run
that asked the mint for the code role would simply get it, because the role
lookup is keyed by the caller's request rather than by anything in the
assertion. Nothing here should be read as proving the least-privilege claims
Fullsend makes about its production tokens; the repository binding is proven,
the role binding is not.

## Where each identity is recorded

The plan asks that actor, repository, role, workflow, mint exchange, and
downstream identity be recorded in evidence without secret values. Today
they are, but in three different places rather than one record:

| Identity | Recorded where | Secret-free |
| --- | --- | --- |
| Event actor | The run's trigger payload (`sender`) and the OIDC `actor` claim; the conformance evidence directory keeps `issue.json` | Yes |
| Repository | The OIDC `repository` claim; `granted_repos` in the mint response, echoed by the `mint-token` step as `Granted scope: repos=...` | Yes |
| Role and requested scope | The `mint-token` step logs `Requesting token: role=... level=... repos=...` | Yes; the token, the assertion, and the mint URL are masked |
| Workflow | `workflow_ref` and `job_workflow_ref` claims; `WorkflowJob.workflow_ref` in the emulator | Yes |
| Mint exchange outcome | The step's exit status and the `Granted scope` line; the trust check's assertions | Yes. The mint itself keeps no record |
| Downstream identity | Comments and labels are authored by the role's bot user (`fullsend-triage[bot]` in the conformance summary's `comment authors`); commits and pull requests by `fullsend-code[bot]` | Yes |

The conformance script gathers these into one record per run,
`var/conformance/run-<id>/identity.json` (schema
`breadboard.fullsend.identity/1`): the run's workflow path and the reusable
workflows it called (from the run API's `path` and `referenced_workflows`),
the trigger's author, each job's runner, permissions, and mint exchanges
(role asked, level, repositories requested and granted, permissions granted,
and the post-script re-mints with their expiry), and the downstream comment
authors and label actors. The exchange lines are parsed by exact shape from
the step logs, and the record is refused if anything token-shaped would
reach it. The script asserts on it: the triage job's exchange granted the
triage role on the target repository, every label was applied by the triage
bot, and the run names the reusable dispatch. The trust-boundary workflow
remains the only place the assertion's own claims are printed, because
ordinary runs mask the token before anything can decode it.

## Confinement to the legacy fixtures

Direct use of `FULLSEND_ROLE_TOKENS` is confined to two places: the mint
itself, and `deploy/k8s/25-fullsend-direct-token-smoke.yaml`, a named legacy
smoke that reads the `fullsend` token straight from the Secret to exercise the
CLI without a workflow. The conformance path, the onboarding button, and the
reusable workflows never touch the Secret; they obtain every credential
through the exchange above. The runner egress policy
(`deploy/k8s/27-fullsend-runner-egress.yaml`) confines the runner to the
cluster, so an assertion cannot be presented anywhere but this mint.

## Related

- [fullsend-integration.md](fullsend-integration.md) for the service topology
  and the sandbox boundary.
- [fullsend-compatibility-profile.md](fullsend-compatibility-profile.md) for
  every local substitution this deployment makes; the two credential rows
  there are the ones this page expands on.
- [fullsend-event-flow.mmd](architecture/diagrams/fullsend-event-flow.mmd)
  for the sequence.
- Fullsend ADRs 0029 (central mint), 0073 (privilege levels), 0077 (repos
  scope), 0078 (authorization policy) in the Fullsend checkout for the
  production contract this substitute stands in for.
