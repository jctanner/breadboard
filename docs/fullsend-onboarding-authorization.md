# Who may start onboarding, and what credential it runs with

The dashboard's onboarding button runs Fullsend's own `github setup` for one
repository in the runner pod and returns the scaffold pull request. This page
answers the two questions work package 7 of the conformance plan left open:
who is allowed to press that button, and where the credential it runs with
comes from. The first is answered by the deployment and stated here as such.
The second is the short-lived App installation token the plan asks for,
minted per operation, with the admin token kept as a labelled fallback for a
stack seeded without the App.

## What the operation does

`POST /api/fullsend/onboard` with `{"repository": "OWNER/REPO"}`
(`src/dashboard/webapp.py`, `src/dashboard/fullsend_onboarding.py`):

1. Refuses anything that is not `OWNER/REPO`. An organisation on its own
   would put the CLI into per-org mode, which is a larger action.
2. Resolves a credential (below) and verifies it with one cheap call before
   the CLI runs, so a refused credential is reported as one rather than as
   an error minutes into the run.
3. Refuses if the repository already has an open scaffold pull request.
4. Runs `fullsend github setup OWNER/REPO ...` in the runner pod, where the
   CLI already lives with the forge's CA in its trust store, with
   `GH_TOKEN`, `GITHUB_API_URL`, `GITHUB_SERVER_URL`, and the runner image
   name in its environment.
5. Returns the command, exit code, output with the token redacted, the pull
   request number and a browse URL, the branch, and which kind of credential
   was used. Nothing token-shaped reaches the response; a test asserts it.

The CLI delivers through a pull request, so a maintainer reviews the
generated files before they activate. There is no direct-commit mode from the
button.

## Who may start onboarding

**Today: anyone who can reach the dashboard.** The dashboard has no user
model. `https://dashboard.local` is served through the host proxy and Traefik
with no authentication in front of it, and the onboarding route checks
nothing about the caller. The gate is therefore the deployment: the operation
needs a credential the backend holds in its environment and the browser never
sees, and the route is only reachable from a machine that resolves
`*.local` to this cluster. On the single-host K3s this stack runs on, that is
the operator.

That is the honest answer for a local development stack, and it is recorded
in the route's docstring as the current answer rather than the finished one.
It stops being adequate the moment the dashboard is exposed beyond one
operator's machine, because then "can reach the dashboard" and "may onboard a
repository" are different sets of people.

**What the answer should become**, in order of how little it adds:

1. **Authenticate at the proxy.** Put forward-auth or an OIDC middleware in
   front of `dashboard.local` in Traefik, so the dashboard stays without a
   user model and the proxy answers who the caller is. Cheapest, and enough
   for a shared development cluster.
2. **Check repository permission.** With an identity from the proxy, have
   the route ask the forge whether that user has `admin` or `maintain` on
   the target repository before running the CLI. That matches Fullsend's own
   authorization ADR 0054, which gates its automatic triggers on repository
   role, and it means onboarding needs the same standing as installing an
   App would on real GitHub.
3. **Record the caller.** Put the caller's login in the onboarding result
   and the operation log next to the credential kind, so the audit question
   "who onboarded this" has an answer that is not "whoever held the
   dashboard".

None of these is built. The first two are deployment work, not Fullsend
work, and they belong with the decision to expose the dashboard, which has
not been taken.

## What credential it runs with

`resolve_credential` returns a token and a kind, and the kind is surfaced in
the result and its message:

| Order | Source | Kind reported | Standing |
| --- | --- | --- | --- |
| 1 | `FULLSEND_ONBOARD_APP_TOKEN` | `app-installation` | A ready-made installation token handed in by the environment. Not populated here; kept for a deployment that mints elsewhere |
| 2 | The seeded onboarding App, from files under `FULLSEND_ONBOARD_APP_DIR` | `app-installation` | **What runs.** A ten-minute JWT signed with the App's mounted key, exchanged at the forge for a one-hour `ghs_` token scoped to the one repository being onboarded |
| 3 | `GITHUB_EMULATOR_TOKEN` | `emulator-admin-fallback` | The emulator admin token from the `github-actions-runner-credentials` Secret, for a stack seeded without the App. Labelled as the fallback it is |
| 4 | `GITHUB_TOKEN` | `personal-fallback` | The generic fallback; not used here |

The rule in the plan is: use a short-lived App installation token with repo
and workflow write scope only, never send it to the browser, never keep it
after the run, and treat a stored personal token as a deliberately scoped
local fallback. All four parts now hold on a seeded stack. A seeded App that
fails to mint is an error, not a reason to fall back: the fallback exists for
a stack with no App, and using it silently would hide a broken exchange
behind an admin credential.

## The App credential, as built

The emulator implements the GitHub App token flow end to end:

- an App has a private key, returned once on creation and again from
  `GET /admin/apps/{app_id}/private-key` or regenerated at
  `/private-key/regenerate` (admin token required);
- `POST /app/installations/{id}/access_tokens` accepts a JWT signed by that
  key and issues a `ghs_` token that expires in one hour, scoped to the
  installation's repositories and permissions, refusing any repository not
  installed.

On that, the credential the plan asks for is built as follows:

1. **An onboarding App of its own.** `deploy/fullsend/seed/seed-onboarding-app.py`
   seeds "Breadboard Onboarding" (`breadboard-onboarding[bot]`), separate
   from the seeded "Fullsend Triage" App whose installation carries only
   `contents: read`. It holds `contents`, `workflows`, `actions_variables`,
   `secrets`, and `pull_requests` to write and `metadata` to read, and it is
   installed on the seed organisation with repository selection "all", so a
   repository that does not exist yet when the seed runs can still be
   onboarded. The enrolment boundary is the organisation.
2. **The key in a Secret.** The seeder writes the App id, installation id,
   and private key to the `fullsend-onboarding-app` Secret, which the
   dashboard mounts as files. Files rather than environment values: the
   kubelet keeps a mounted Secret current, so a stack seeded after the
   dashboard started finds the App without a restart, and the key never
   appears in the pod's environment.
3. **Mint per operation.** `mint_installation_token` signs a JWT with the
   mounted key (`iss` the App id, ten minutes), calls `access_tokens` for
   the installation with `repositories: [the one being onboarded]`, and hands
   the resulting `ghs_` token to the CLI for that run only. It expires in an
   hour on its own; the dashboard discards it when the run ends.
4. **The label kept.** The kind is `app-installation`, and the admin
   fallback stays available and labelled for a stack seeded without the App.

Two emulator changes made it work rather than merely mint. A bot had no
repository access at all, because the emulator answered "not a
collaborator" for every bot: the permission endpoint returned 404 and a
push was refused. Now an installation on the repository's owner that covers
the repository, explicitly or as "all", grants its bot the installation's
`contents` permission, which is what GitHub does. And `access_tokens`
refused every repository of an "all" installation.

Verified by onboarding a throwaway repository through the dashboard
endpoint: the result named `app-installation`, the CLI logged
`User breadboard-onboarding[bot] has write access`, the scaffold pull
request and its commit were authored by that bot, three variables and two
secrets were set, and nothing token-shaped reached the response. The
repository was deleted afterwards. That closes the credential deviation in
the compatibility profile's section 7b.

## Related

- [fullsend-mint-trust.md](fullsend-mint-trust.md) for the other credential
  path, the run-time mint.
- [fullsend-compatibility-profile.md](fullsend-compatibility-profile.md),
  section 7b, for the deviation this page expands on.
- Fullsend ADR 0054 for the repository-role gate the second recommendation
  borrows.
