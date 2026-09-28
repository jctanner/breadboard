# Who may start onboarding, and what credential it runs with

The dashboard's onboarding button runs Fullsend's own `github setup` for one
repository in the runner pod and returns the scaffold pull request. This page
answers the two questions work package 7 of the conformance plan left open:
who is allowed to press that button, and where the credential it runs with
comes from. The first is answered by the deployment and stated here as such.
The second is answered by a labelled fallback today, with the short-lived App
credential the plan asks for now a concrete path rather than a missing piece.

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
| 1 | `FULLSEND_ONBOARD_APP_TOKEN` | `app-installation` | The plan's rule: a short-lived App installation token with repository and workflow write scope. Not populated in this deployment |
| 2 | `GITHUB_EMULATOR_TOKEN` | `emulator-admin-fallback` | What runs today: the emulator admin token from the `github-actions-runner-credentials` Secret. Labelled as the fallback it is |
| 3 | `GITHUB_TOKEN` | `personal-fallback` | The generic fallback; not used here |

The rule in the plan is: use a short-lived App installation token with repo
and workflow write scope only, never send it to the browser, never keep it
after the run, and treat a stored personal token as a deliberately scoped
local fallback. The first and third parts hold; the second and fourth are
what the fallback is a fallback from. The admin token can do anything on the
emulator, and it lives in the dashboard pod's environment for as long as the
pod does.

## The App credential is now a concrete path

The compatibility profile records "this deployment holds no App private key"
as the reason the fallback is used. That was true when written and is no
longer the whole story. The emulator now implements the GitHub App token
flow end to end:

- an App has a private key, returned once on creation and again from
  `GET /admin/apps/{app_id}/private-key` or regenerated at
  `/private-key/regenerate` (admin token required);
- `POST /app/installations/{id}/access_tokens` accepts a JWT signed by that
  key and issues a `ghs_` token that expires in one hour, scoped to the
  installation's repositories and permissions, refusing any repository not
  installed.

So providing the credential the plan asks for is deployment and dashboard
work, in this order:

1. **Seed an onboarding App**, separate from the seeded "Fullsend Triage"
   App, whose installation carries only `contents: read`. Onboarding writes
   workflows, variables, and secrets, so its App needs `contents: write`,
   `workflows: write`, `actions_variables: write`, and `secrets: write`, and
   its installation must list the repositories that may be onboarded, or the
   organisation, as the enrolment boundary.
2. **Hold the key in a Secret**, not in the dashboard's environment as a
   token. `seed-github-app.py` already creates Apps idempotently and can
   write the key to a Kubernetes Secret the dashboard mounts.
3. **Mint per operation.** Replace the first row of the table with: sign a
   JWT with the mounted key, call `access_tokens` for the installation with
   `repositories: [the one being onboarded]`, and use the result for that run
   only. It expires in an hour on its own; the dashboard discards it when
   the run ends, as it discards the fallback today.
4. **Keep the label.** The kind becomes `app-installation` and the fallback
   stays available and labelled for a stack seeded without the App.

That closes the credential deviation in the compatibility profile without a
rewording, which is what its section 7b asks for. It is not done; the plan's
checkbox stays open with this as its content.

## Related

- [fullsend-mint-trust.md](fullsend-mint-trust.md) for the other credential
  path, the run-time mint.
- [fullsend-compatibility-profile.md](fullsend-compatibility-profile.md),
  section 7b, for the deviation this page expands on.
- Fullsend ADR 0054 for the repository-role gate the second recommendation
  borrows.
