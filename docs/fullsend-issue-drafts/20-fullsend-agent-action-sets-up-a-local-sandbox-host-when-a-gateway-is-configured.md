<!-- Draft for review. Not filed. -->
# action: agent action sets up a local sandbox host even when an OpenShell gateway endpoint is configured

**Repository:** fullsend-ai/fullsend
**Parent:** none

---

### What happens

The agent action (`action.yml`) turns every runner into a sandbox host
before it runs the agent. These steps have no `if:` condition on
`origin/main`:

- `Install Podman` (line 390) runs `.github/scripts/install-podman.sh`.
- `Configure rootless Podman` (line 394) requires cgroups v2, runs
  `sudo usermod --add-subuids ...` when the user has no `/etc/subuid` entry,
  then `podman system migrate`, `podman info` and
  `systemctl --user start podman.socket`.
- `Configure OpenShell gateway` (line 404) writes
  `$HOME/.config/openshell/gateway.env` and `gateway.toml` with
  `compute_driver = "podman"`.
- `Install OpenShell CLI` (line 424) runs `.github/scripts/install-openshell.sh`,
  which pipes the upstream `install.sh` from `raw.githubusercontent.com`
  into `sh`. The script's header says it needs sudo.
- `Install validation dependencies` (line 428) runs
  `pip install --quiet "jsonschema>=4.18.0"`.

That is the right setup for a GitHub-hosted runner, which starts as a fresh
virtual machine with none of it. It is the wrong setup for a runner that
uses an OpenShell gateway running somewhere else. Fullsend already supports
that arrangement: `ensureContainerGatewayOverride` in
`internal/sandbox/gateway_endpoint.go` (line 60) respects an explicit
`OPENSHELL_GATEWAY_ENDPOINT` and does not change it. On such a runner:

- Sandboxes are created on the remote gateway, so the runner does not need
  Podman. The `gateway.toml` written on the runner configures a local gateway
  that is not used. It does not reach the gateway it is meant to configure.
- On a runner that is a container rather than a virtual machine, the Podman
  steps fail because `sudo usermod` and `systemctl --user` are not available.
  The job then fails before the agent starts.
- The OpenShell CLI installer runs even when `openshell` is already on
  `PATH`. It needs sudo and network access to reinstall what the image
  already has.
- `pip install` fails on an image whose Python is an externally managed
  environment, even when `jsonschema` already imports.

### What should happen

When the runner is configured for an existing OpenShell gateway
(`OPENSHELL_GATEWAY_ENDPOINT` is set), the action does not install or
configure a local container runtime or a local gateway. It does not reinstall
tools that the runner already has. A runner that hosts its own sandboxes,
such as a GitHub-hosted runner, works as it does today.

### How to reproduce

1. Run a self-hosted runner as a container whose user cannot use `sudo` or a
   systemd user session, for example a Kubernetes pod. Use an image that
   already includes the `openshell` CLI and `jsonschema`.
2. Set `OPENSHELL_GATEWAY_ENDPOINT` in the runner's environment so that it
   points at a reachable OpenShell gateway.
3. Run any workflow that uses the agent action on that runner.
4. The action runs `Install Podman` and `Configure rootless Podman`. The job
   fails at `Configure rootless Podman` before `Run fullsend`. The run never
   uses the gateway that the endpoint names.

### Context

Found while running Fullsend end to end against a local GitHub API emulator.
The emulator's self-hosted Actions runners are containers, and they use an
OpenShell gateway that runs as a separate service.

Related: #5262, which added the `OPENSHELL_GATEWAY_ENDPOINT` override in
`gateway_endpoint.go` for a containerised CLI that cannot reach the gateway
on loopback.

---

## Draft notes (not part of the issue)

- **Local patch:** `deploy/fullsend/patches/0004-skip-local-sandbox-host-setup.patch`
- **Checked against:** fullsend-ai/fullsend@e82eda3ec (origin/main, 2026-10-30)
- **Evidence:** The step list and line numbers come from
  `git show origin/main:action.yml` (lines 390-430). The sudo requirement and
  the `raw.githubusercontent.com` installer come from
  `origin/main:.github/scripts/install-openshell.sh`. The explicit-endpoint
  handling comes from `origin/main:internal/sandbox/gateway_endpoint.go:60`.
  The failure modes come from the patch header:
  - the steps fail on a non-VM runner because `sudo usermod` and
    `systemctl --user` are unavailable in a container;
  - a gateway config written on the runner never reaches the remote gateway;
  - the CLI installer needs sudo and a CDN;
  - pip refuses an externally managed environment.

  The header does not quote exact error text, so the issue quotes none.
  Repro step 4 reads the header's "fail" claim against the step order. By
  inspection, `usermod` runs only when `/etc/subuid` has no entry, but
  `systemctl --user` always runs, so the job always reaches a step that
  fails.
- **Duplicate search (section 0004):** no duplicate.
  - #5262 (closed PR): related, linked in Context. It is the origin of the
    `OPENSHELL_GATEWAY_ENDPOINT` override.
  - #8287, #8293, #8297, #8510 (inference gateway route): unrelated. That is
    the model-inference gateway, not the OpenShell gateway.
  - #6961, #8533, #8679, #8717: unrelated.
- **Open questions for the reviewer:**
  - The action does not read or pass `OPENSHELL_GATEWAY_ENDPOINT` itself. The
    variable comes from the runner's environment. Upstream may prefer a
    different signal, such as an action input. The issue names the variable
    only as the existing supported mechanism and does not suggest a fix.
  - The pip and CLI-reinstall points are smaller and could be dropped if the
    reviewer wants a single-issue focus.
