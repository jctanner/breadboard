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
own OIDC issuer and nothing else, and it answers with a one-hour GitHub App
installation token minted for the role's App, pinned to the repository the
assertion names and downscoped to the requested level.

## The exchange, step by step

```text
job (id-token: write)
  --request token-->  emulator  GET /actions/oidc/token?audience=fullsend-mint
  <--RS256 JWT------            claims derived from the job, 300 s lifetime
  --Bearer JWT + {role, repos}-->  mint  POST /v1/token
                                  verify signature, iss, aud, exp/nbf
                                  refuse any repo != token's repository claim
                                  sign a JWT as the role's App
                                  --> forge: installation on the owner, access_tokens
                                      (repositories: [the one], permissions: role at level)
  <--{ghs_ token, expires_at (1 h), granted_repos, granted_permissions, level}--
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
   Before any of that it checks **which workflow is asking**: the
   `job_workflow_ref` claim must name a workflow file in
   `FULLSEND_ALLOWED_WORKFLOW_FILES` hosted by `fullsend-ai/fullsend`
   (always accepted) or a repository in `FULLSEND_WORKFLOW_HOST_REPOS`,
   the same rule as Fullsend's `mintcore.ValidateWorkflowRef` in per-repo
   mode. Any other workflow, however valid its assertion, is `403`.
4. **The mint mints as the role's App.** Each role is a GitHub App on the
   emulator (`fullsend-triage`, `fullsend-scribe`, `fullsend-code`,
   `fullsend-review`, `fullsend-fix`, `fullsend-retro`,
   `fullsend-prioritize`, `fullsend`), installed on the seed
   organisation with repository selection "all". The mint holds the Apps'
   private keys in the `fullsend-mint-role-apps` Secret, mounted as one
   file. It signs a ten-minute JWT naming the role's App, finds that App's
   installation on the assertion's `repository_owner`, and asks the forge
   for an installation token for the one repository with the role's
   permissions at the requested `level`: `write` is the role's full set,
   `read` (the default when the level is omitted) has every write
   downgraded to read, as Fullsend ADR 0073 defines. The token is a `ghs_`
   token that expires in one hour. A role whose App is not installed on the
   owner, or a forge refusal, is a `502` naming the reason. Neither the
   request nor the response is logged; the mint's request logger is
   disabled.
5. **The runner uses it.** The token becomes `GH_TOKEN` for the checkout,
   `gh`, git pushes, and the post-script. The sandbox receives it through
   Fullsend's normal provider path and never sees an App key or an admin
   credential. It acts as the App's bot user (`fullsend-triage[bot]`), whose
   access on the emulator is exactly what its installation grants.

## What the mint trusts

| Trust | Where it is established | How it can be broken |
| --- | --- | --- |
| The emulator's signing key | Fetched from `https://github.local/.well-known/jwks.json` over the internal CA (`SSL_CERT_FILE`) | Anyone who can serve that URL to the mint, or who holds the emulator pod's memory, can sign assertions |
| The issuer and audience strings | `FULLSEND_OIDC_ISSUER`, `FULLSEND_OIDC_AUDIENCE` in `deploy/k8s/24-fullsend-mint-dev.yaml` | Misconfiguration only; the values are not secrets |
| The `repository` and `repository_owner` claims | Set by the emulator from the job, never from the caller | Only by forging the assertion, which needs the key above |
| The role Apps' private keys | `fullsend-mint-role-apps` Secret, written by `deploy/scripts/18-deploy-fullsend-mint-dev.sh` from the emulator's admin API | Anyone with `get secret` in the namespace can sign as any role's App and mint for any repository that App is installed on; the mint is not what protects the keys |
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
- **Role binding.** The token carries the role's permissions at the
  requested level and the emulator enforces them: an App's bot may write a
  repository's contents, refs, and git objects only when its installation
  grants `contents: write`, and the role bots hold no collaborator rows on
  the conformance target. Evidence: the trust-boundary workflow's step "The
  credential cannot write what its role does not grant" puts a file with the
  triage credential and asserts `403` (run 1756).
- **Levels.** `level` is honoured: unknown levels are `400`, an omitted
  level is `read`. The mint-token action sends `write`; the runner now
  applies that default (it used to arrive empty).
- **Short-lived credentials.** The installation token expires after one
  hour on the forge's side; nothing long-lived is issued.
- **Workflow provenance.** `job_workflow_ref` names the workflow that
  defined the job (`fullsend-ai/fullsend/.github/workflows/reusable-*.yml@main`
  for every stage job, since G46 was fixed), and the mint acts on it: only
  the seven reusable workflows and the trust check may mint. Evidence: the
  seeded workflow `fullsend-trust-check-unregistered.yaml`, deliberately
  absent from the allowed list, asks for the triage, coder, and fullsend
  roles with a valid assertion and is refused all three with
  `workflow file ... not in allowed list` (run 1777).
- **Short assertion lifetime.** 300 seconds, with a replay-resistant `jti`.
  The role token it is exchanged for is a different matter, below.

## What the mint does not cover

These are the gaps between this substitute and Fullsend's production mint.
Each is a deliberate simplification, listed so nobody reads a green
conformance run as proof of something it does not test.

| Production mint (Fullsend ADRs 0029, 0073, 0077, 0078) | Development mint |
| --- | --- |
| Mints a fresh GitHub App installation token per request, scoped to the requested repositories, expiring in about an hour | The same, since 2026-09-28 |
| Downscopes permissions to the role's named privilege level; `level` defaults to `read` | The same, for the two levels `read` and `write`; custom roles and level sets are not supported |
| Per-role permission sets enforced by the App installation | Enforced per token, on every route: the emulator answers for the token's own repositories (Not Found outside them) and permissions ("Resource not accessible by integration"), the git transport included, and refuses to mint a token wider than its installation |
| Checks `job_workflow_ref` against registered workflow prefixes | The same: upstream host always accepted, configured host repositories, allowed basenames, deny-all when unset |
| Org and per-repo allowlists (`ALLOWED_ORGS`, `PER_REPO_WIF_REPOS`) | None. Any repository on the emulator whose job can obtain an assertion may mint for itself |
| `["*"]` means installation-wide in the shapes ADR 0077 allows | Refused as an invalid repository name. Only bare names and `owner/name` are accepted |
| Audit log of every exchange | None. The mint logs nothing by design, to keep tokens out of pod logs |

What is still true, and worth saying plainly: within the allowed
workflows, the role is chosen by the request, not by the assertion. Any of
the seven reusable workflows may ask for any role, which is also how
Fullsend's production mint works; the gate answers "may this workflow mint
at all", not "which role". The level, on the other hand, binds: a token
minted at `read` carries the read set and the emulator enforces the token's
own permissions, so it cannot do what its installation could. Evidence: the
trust-boundary workflow's step "A read-level credential cannot write issues
either" mints triage at `read` and finds a comment refused `403` (run 1779).

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

`FULLSEND_ROLE_TOKENS`, the static per-role tokens, are no longer read by
the mint at all. They survive in the `fullsend-mint-dev-credentials` Secret
for one consumer: `deploy/k8s/25-fullsend-direct-token-smoke.yaml`, a named
legacy smoke that reads the `fullsend` token straight from the Secret to
exercise the CLI without a workflow. The conformance path, the onboarding
button, and the reusable workflows never touch it; they obtain every
credential through the exchange above. The runner egress policy
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
