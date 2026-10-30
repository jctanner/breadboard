# Workflow Dojo

Workflow Dojo is an **optional** Breadboard service for learning Claude Code
workflow scripts, the JavaScript the Workflow tool runs to orchestrate
subagents. `deploy-all.sh` does not deploy it.

Source: `checkouts/workflow-dojo/`, a separate repository
([jctanner/claude-workflow-dojo](https://github.com/jctanner/claude-workflow-dojo)),
cloned by `deploy/scripts/00-clone-component-repos.sh`. See its
`README.md` and `AGENTS.md`.

## What it does

- Presents LeetCode-style problems, both Create and Debug, judged by an
  in-browser simulator with mocked agents and a virtual clock. Judging is free.
- Provides a **live Claude shell**. The pod runs the real `claude` CLI in a PTY
  and bridges it to xterm.js over a WebSocket. The design is ported from
  `checkouts/context-inspector`: the server owns the session and browser tabs
  are detachable views. Each user has their own session, Claude config and
  workspace; at most `DOJO_MAX_SESSIONS` (4) run at once.
- Has **user accounts**. Progress (solved problems, saved code, submissions)
  is stored per user on the state volume, so it follows you between machines.
  The first login in a browser that has progress from before accounts existed
  uploads it into an account that has none yet. Admins manage users on the
  **Users** page; everyone can change their password on **Account**.
- **Run for real** saves the editor's script into the pod workspace and asks
  Claude to run it with the Workflow tool (`scriptPath`, plus the first test's
  `args`). **Ask Claude** requests a hint about the current script and verdict.

## Deployment

| Piece | Location |
| --- | --- |
| Image | `checkouts/workflow-dojo/Containerfile`, built by `deploy/scripts/05n-build-workflow-dojo.sh` (`CLAUDE_CODE_VERSION` build arg, default `latest`) |
| Manifest | `deploy/k8s/31-workflow-dojo.yaml`: Deployment (1 replica, Recreate, uid 1000, no service-account token), Service `workflow-dojo:8080`, PVC `workflow-dojo-state` mounted at `/home/node/dojo` |
| Route | `dojo.local` in `deploy/golang-reverse-proxy` (route and certificate SAN) |
| Relay key | Secret `workflow-dojo-relay` (`api-key`), managed by `deploy/scripts/workflow-dojo-relay-key.py` |
| Bootstrap login | Secret `workflow-dojo-admin` (`username`, `password`; `admin`/`admin`), created if missing by `deploy/scripts/workflow-dojo-admin-secret.sh` |

```bash
make host-deploy-dojo            # build, provision the key, deploy
make host-rebuild-ingress-proxy  # once, to add the dojo.local route
make host-rebuild-dojo           # after component changes
make host-dojo-relay-key         # re-check the key; ROTATE=1 issues a new one
make host-logs-dojo
```

Add `dojo.local` to the host's `/etc/hosts` line for the ingress address,
alongside `relay.local`.

Log in as `admin`/`admin` and change the password on the **Account** page.
The dojo uses the bootstrap Secret only to create that account when it
doesn't exist, so a changed password survives restarts and redeploys. To
start over, delete the `workflow-dojo-state` PVC, which also deletes all
users and progress.

## Model Relay credentials

Claude reaches the relay in-cluster at
`http://model-relay.ai-pipeline.svc.cluster.local:8080`, using
`ANTHROPIC_API_KEY` from the Secret. The model picker lists what that key
can see (`/v1/models`); the default is `claude-haiku-5-5`
(`DOJO_DEFAULT_MODEL`).

`workflow-dojo-relay-key.py` is idempotent:

- **Your own key:** to use a key created in the relay console, run
  `python3 deploy/scripts/workflow-dojo-relay-key.py --stdin` and paste it.
  It must authenticate. Later runs keep it while it still works.
- **No working key:** the script revokes earlier `workflow-dojo` credentials
  and issues a 90-day MaaS key with `catalog_models` access in
  `vertex-shim-local`.
- **Handling:** keys never appear in process arguments or output.

## Security notes

- Every API route and terminal socket needs a login. Passwords are stored as
  scrypt hashes in `users.json` on the state volume. Logins are HMAC-signed,
  HttpOnly, `SameSite=Strict` cookies that last 30 days (Secure behind the
  HTTPS proxy), with the signing key in `secret.key`. Writes also need an
  `X-Dojo: 1` header.
- All users share the one relay key, so any user can spend it. The default
  `admin`/`admin` password is only safe on a private network; change it.
- Claude runs with `--dangerously-skip-permissions`
  (`DOJO_SKIP_PERMISSIONS=1`), confined to the pod as uid 1000 with all
  capabilities dropped and no Kubernetes API token.
- The proxy clears its read and write deadlines for WebSocket upgrades only, so
  terminal sessions outlive the 30s/120s server timeouts.
