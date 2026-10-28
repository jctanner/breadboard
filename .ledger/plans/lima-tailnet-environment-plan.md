# Lima VM and Tailnet DMZ Replication Plan

## Context

Breadboard's integrated stack runs a single-node K3s cluster orchestrating ~15
microservices (emulators, workflows, runners, sandboxes, observability, gateways).
The upstream deployment targets an x86_64 Ubuntu 24.04 environment (either via
Vagrant + libvirt or bare-metal Linux host), binding edge ingress to `*.local`
hostnames on `127.0.0.1`.

On Apple Silicon (macOS arm64), two constraints arise:
1. Hardcoded x86 binaries (e.g. GitHub Actions runner `actions-runner-linux-x64`,
   Fullsend release asset `fullsend_*_linux_amd64.tar.gz`).
2. Remote development over SSH and Tailscale makes `*.local` inaccessible
   to remote client browsers due to mDNS / Bonjour limits.

## Goals

1. Define a version-controlled Lima template (`deploy/lima/breadboard-vm.yaml`)
   running Ubuntu 24.04 on Apple Virtualization (`vz`) with Rosetta enabled.
2. Isolate the VM on Tailscale with an ACL tag (`tag:breadboard`) as a DMZ.
3. Parameterize the ingress domain via `BREADBOARD_DOMAIN` (default: `local`).
4. Replicate the full stack deployment (`make host-deploy-all`) inside the VM.
5. Provide seamless browser access over Tailscale via Split DNS or wildcard routing.

## Invariants

- **Upstream parity**: The default domain remains `local`. All existing `vagrant-*`
  and `host-*` targets must work identically when `BREADBOARD_DOMAIN` is unset.
- **Zero credential leaks**: No Tailscale auth keys, tokens, or `.env` secrets
  committed to git.
- **Strict DMZ isolation**: The VM must not have network access to other machines
  on the operator's tailnet.

---

## Work Packages and Breakpoints

### WP1: Lima VM Definition & Rosetta Verification

Create `deploy/lima/breadboard-vm.yaml` configuring:
- `vmType: vz` with `rosetta: { enabled: true, binfmt: true }`
- 8 vCPUs, 24–28 GiB RAM, 100 GiB disk
- Writable mount for the Breadboard repository root
- Port forwards for 80, 443, 5000, 6443
- Guest provisioner installing Docker, build tools, curl, and `uv`

**Breakpoint B1 (Rosetta & Prerequisites)**:
- Start VM with `limactl start deploy/lima/breadboard-vm.yaml`.
- Inside VM: verify `uname -m` reports `aarch64`.
- Run an x86_64 container image:
  `docker run --rm --platform linux/amd64 alpine uname -m`
  asserting output is `x86_64` (Rosetta binfmt active).

### WP2: Ingress Domain Parameterization

Parameterize domain routing across edge and service definitions:
1. `deploy/golang-reverse-proxy/main.go`:
   - Read `BREADBOARD_DOMAIN` from environment (default: `local`).
   - Register route map dynamically using `fmt.Sprintf("%s.%s", service, domain)`.
2. `deploy/k8s/02-certificates.yaml` & `deploy/scripts/03-setup-certificates.sh`:
   - Template SAN hostnames using the configured domain.
3. `deploy/k8s/05-ingress-routes.yaml` and `deploy/k8s/08-ingress-https.yaml`:
   - Use parameterized host rules.
4. Dashboard and ticket links (`src/dashboard/`):
   - Reference `BREADBOARD_DOMAIN` for external service URLs.

**Breakpoint B2 (Configurable Ingress)**:
- Build Go reverse proxy and test routing with `BREADBOARD_DOMAIN=local`
  and `BREADBOARD_DOMAIN=bb.internal`.
- Assert certificates mint without error for the configured domain.

### WP3: Full Stack Deployment in Lima

Run the deployment inside the Lima VM mounting repository root:
1. Run `deploy/scripts/01-install-k3s-host.sh` inside the VM.
2. Execute `make host-deploy-all`.
3. Validate cluster stability and pod readiness.

**Breakpoint B3 (Stack Healthy)**:
- `make host-status` shows all pods in `ai-pipeline` Running/Completed.
- Run `deploy/validation/test-cluster.sh` and `test-certificates.sh`.
- Run Fullsend direct token smoke test (`deploy/scripts/19-run-fullsend-direct-token-smoke.sh`).

### WP4: Tailnet DMZ Integration & Remote Verification

1. Provision Tailscale in guest with an ephemeral/reusable auth key:
   `tailscale up --authkey=... --tags=tag:breadboard --hostname=breadboard-vm`
2. Configure Tailscale ACL for `tag:breadboard`:
   - Ingress permitted from operator devices.
   - Egress restricted to internet only (no lateral movement).
3. Set up Split DNS in Tailscale Admin Console:
   - Route `*.bb.internal` to the VM's Tailscale IP (`100.x.y.z`).
4. Validate access from client browser (e.g. from `proteus` over Tailscale).

**Breakpoint B4 (Remote Browser Access)**:
- Open `https://dashboard.bb.internal` from remote browser.
- Verify dashboard loads, SSE activity streams, and emulator links resolve.
- Run egress test from VM to confirm lateral access to other tailnet IPs is blocked.

---

## Daily Log

### 2026-10-28 Plan established

Fork set up (`durandom/breadboard` origin, `jctanner/breadboard` upstream).
Analyzed x86_64 dependencies across checkouts and emulators.
ADR-0014 recorded. Plan drafted with 4 verifiable breakpoints.
Next step: Draft `deploy/lima/breadboard-vm.yaml` and parameterize reverse proxy.
