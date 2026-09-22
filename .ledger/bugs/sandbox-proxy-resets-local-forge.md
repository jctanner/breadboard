# Sandbox egress proxy resets the connection to the local forge

## Status: Open — root cause confirmed 2026-09-21

## Confirmed diagnosis and control experiment

The sandbox supervisor's upstream TLS trust store lacks Breadboard's internal
CA. Adding that CA **before supervisor startup** fixes the proxied request on
the existing 0.0.110 gateway and supervisor. DNS and version skew are not the
cause of this reproduced reset.

Created disposable sandbox `debug-g38-20260921` through the runner with the
same pinned Fullsend image, `--provider github-ro`, `--no-auto-providers`, and
`--detach -- sleep infinity`. No issue or agent workflow was dispatched.
The read-only probe used a non-secret placeholder token:

```bash
openshell sandbox exec --name debug-g38-20260921 -- \
  env GH_HOST=github.local GH_ENTERPRISE_TOKEN=diagnostic-placeholder \
  gh api /rate_limit
```

Evidence:

- At 18:25:34 UTC the probe reproduced the exact read-side connection reset.
  `/var/log/openshell.2026-09-21.log` inside the sandbox recorded
  `ALLOWED /usr/bin/gh -> github.local:443 [policy:_provider_github_ro engine:opa]`
  followed by `NET:FAIL`. The available shorthand log did not include the TLS
  exception text; the CA-only control below establishes the cause.
- From the supervisor's pod network namespace (direct `kubectl exec`, distinct
  from the sandboxed agent), `getent hosts github.local` returned `10.43.17.62`.
  A direct HTTPS curl failed with exit 60, `unable to get local issuer
  certificate`. The same diagnostic request with `-k` returned HTTP 200.
  Certificate verification was not disabled in the proxied probe.
- Modified only the disposable Sandbox CR's pod template: mounted ConfigMap
  `internal-ca-cert`, key `ca.crt`, and appended its public CA to
  `/etc/ssl/certs/ca-certificates.crt` before executing the supervisor. Recreated
  only that diagnostic pod. The image lacks `update-ca-certificates`, so the
  control used a direct bundle append in its startup command.
- At 18:27:38 and 18:27:47 UTC the identical proxied `gh` request succeeded
  with exit 0 and rate-limit JSON. Logs recorded
  `HTTP:GET ... ALLOWED GET http://github.local:443/api/v3/rate_limit
  [policy:_provider_github_ro engine:l7]`. The logged normalized URL does not
  mean the client's HTTPS request was changed to cleartext transport.

The deployed v0.0.110 source in `openshell-supervisor-network/src/run.rs`
reads the system bundle before constructing upstream TLS state. Its
`l7/tls.rs` overlays system CAs on bundled roots (or uses native roots in the
alternative build). That TLS source file has no diff between v0.0.110 and the
CLI's pinned commit. Merely changing agent environment variables or uploading
a CA after supervisor startup does not refresh the in-memory upstream roots.

The relevant trust store is in the **sandbox pod**, where the supervisor runs;
mounting a CA only into the gateway pod will not fix it. The v0.0.110 chart
values expose no general sandbox CA/volume injection setting. A durable fix
must arrange operator-owned CA injection into sandbox pods before supervisor
startup, or use an appropriately CA-configured sandbox image. Preserve TLS
verification and the existing provider allowlist/L7 enforcement.

No runner cleanup modification was needed: keeping a manual diagnostic
sandbox allowed reading its logs directly. The temporary sandbox was removed
after the experiment. No production deployment or image fix was applied;
full triage execution remains unverified.

## Summary

An agent running inside an OpenShell sandbox cannot reach the GitHub emulator.
The sandbox's egress proxy accepts the request and then resets it:

```
Error: pre-flight connectivity check: GitHub API connectivity check failed (exit 1):
Get "https://github.local/api/v3/rate_limit": read tcp 10.200.0.2:35364->10.200.0.1:3128: read: connection reset by peer
```

`10.200.0.1:3128` is the proxy inside the sandbox's network namespace. The
reset happens on **read**, after the request was accepted, which puts the
failure below the allowlist and most likely on the proxy's own upstream
connection to `github.local`.

This is the last thing between the current state and an agent actually running.
Everything before it works: the sandbox bootstraps, the project code is copied
in, the target-repo context scan and the pre-agent security scan both pass.

## What has already been fixed, so do not re-do it

Two earlier causes of "sandbox cannot reach the forge" were found and patched.
Both are confirmed working and are **not** this bug.

| Cause | Fix | Evidence it works |
| --- | --- | --- |
| `gh` in the sandbox had no `GH_HOST`, so it addressed github.com | `deploy/fullsend/patches/agents/0002-pass-the-forge-host-into-the-sandbox.patch` passes `GH_HOST` and `GH_ENTERPRISE_TOKEN` through | the error now names `https://github.local/api/v3/rate_limit` |
| The sandbox network allowlist listed only `api.github.com` and `github.com`, so the proxy refused CONNECT with 403 | `deploy/fullsend/patches/agents/0003-local-allow-the-emulator-in-the-github-profile.patch` adds the forge host | the 403 is gone; the failure is now a reset |

The allowlist lives in a **provider profile**, which is the sandbox's network
policy. Fullsend imports profiles verbatim and expands no variables in them,
deliberately, so an environment variable cannot widen what a sandbox may reach.
That is why patch 0003 is marked local-only rather than upstream-bound.

## Leading hypothesis

The proxy terminates TLS and makes its own upstream connection. `github.local`
is served by the cluster's internal CA (cert-manager, `internal-ca-issuer`), and
nothing configures the gateway or the proxy to trust it.
`deploy/k8s/openshell-values.yaml` has no CA, certificate or trust-store key at
all; the only TLS setting is `disableTls: true`, which governs the gateway's own
listener, not what it trusts upstream.

If that is right, the proxy's handshake to `github.local` fails and it drops
the client, which is exactly what a read-side reset looks like.

The alternative is name resolution: the proxy may resolve differently from the
rest of the namespace. `github.local` does resolve in-cluster, confirmed from
another pod, but that does not prove the proxy's resolver sees it.

## Version skew worth checking first

The gateway and supervisor run **0.0.110** (`deploy/k8s/openshell-values.yaml`,
`image.tag` and `supervisor.image.tag`), while the CLI is built from the commit
Fullsend pins for **0.0.116** (`d1155aa70042d3e2ee49dbfa15346b108b7c1d92`).

A version skew between the CLI and the gateway already caused one bug in this
chain (`--detach` not being accepted). Whether the proxy behaviour differs
across those versions has not been checked, and it is cheap to rule in or out
before digging into TLS.

## Two obstacles to investigating

Both cost time if discovered the hard way.

1. **The gateway pod is distroless.** `kubectl exec -n openshell-system
   openshell-0 -- sh` fails with `exec: "sh": executable file not found`. Its
   logs are available and show only gRPC request lines at INFO; nothing about
   the proxy.
2. **The run collects OpenShell logs and then they are deleted.** The job log
   says `Collected 2 OpenShell log source(s) to
   /runner-root/workspace/output/<sandbox>/logs`, but the emulator runner
   removes its whole workdir when the job ends
   (`execute_job` in `checkouts/github-emulator/src/runners/emulator/runner.py`,
   the `shutil.rmtree(WORKDIR)` at the end). Those logs are the most direct
   evidence available and they are currently thrown away.

## Suggested next steps

1. **Keep the collected OpenShell logs.** Easiest change with the highest
   payoff: temporarily skip the workdir cleanup in the runner, or copy
   `output/<sandbox>/logs` somewhere durable before the job ends, then read
   what the proxy actually said. Everything below is guesswork until this is
   done.
2. **Separate TLS from DNS.** From inside a live sandbox, or from a throwaway
   sandbox created by hand, try the forge by IP and by name, and try a plain
   HTTP endpoint as well as HTTPS. A name that fails and an IP that works means
   resolution; both failing on HTTPS while HTTP succeeds means trust.
3. **Check whether the proxy can be given the internal CA.** If it is a trust
   problem, the fix is configuration rather than code: mount or inject the
   cluster's CA (`internal-ca-cert` ConfigMap in `ai-pipeline`) into the
   proxy's trust store. Check the OpenShell chart for a supported key before
   inventing one.
4. **Rule the version skew in or out** by aligning the gateway and supervisor
   tags with the CLI's pinned revision, if the chart allows it.

## How to reproduce

The stack must be running.

```bash
cd <projectroot>
curl -sk -X POST "https://github.local/api/v3/repos/fullsend-dev/triage-target/issues" \
  -H "Authorization: token ghp_admin_default_token" \
  -H "Content-Type: application/json" \
  -d '{"title":"proxy repro","body":"The README does not explain what this repository is for."}'
```

Find the newest `fullsend` run with event `issues`, then read its Triage job
log. The failure is in the "Run triage agent" step, a couple of minutes in. The
sandbox is deleted automatically afterwards.

```bash
kubectl logs -n openshell-system openshell-0 -f          # gateway, gRPC only
kubectl get sandboxes -A -w                              # sandbox lifecycle
```

## Context

- This is G38 in `.ledger/plans/fullsend-integration-conformance-plan.md`,
  which carries the full chain and everything fixed to get here.
- Local deviations live in `deploy/fullsend/patches/` across three lists: Go
  source before compilation, the Fullsend mirror, and the agents mirror. Each
  patch header says whether it is upstream-bound.
- The sandbox image is Fullsend's own pinned digest, imported into K3s. The
  repository also builds `fullsend-sandbox-dev:k3s`, which wires five
  certificate-bundle variables to a CA bundle. That image is **not** in use
  here, and its certificate handling is worth reading as a description of what
  this environment needs:
  `deploy/fullsend-sandbox-dev/Containerfile`.
