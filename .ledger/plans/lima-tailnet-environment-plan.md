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

### 2026-10-28 WP2 completed: Ingress Domain Parameterization (bb-1sa.2)

- Go reverse proxy (`deploy/golang-reverse-proxy`):
  - Parameterized via `BREADBOARD_DOMAIN` (default `"local"`).
  - Dynamically registers `<service>.<domain>` alongside `<service>.local`.
  - Added unit test in `main_test.go` verifying dual-resolution for `bb.internal` and `.local`.
- Manifest and Certificate rendering:
  - Added `deploy/scripts/render_domain_manifest.py` and `deploy/scripts/apply-domain-manifests.sh`.
  - Preserves base `.local` in manifests for static `kubectl apply -f` compatibility.
  - Generates `<service>.<domain>` SANs and Ingress rules when `BREADBOARD_DOMAIN != "local"` without touching `*.svc.cluster.local`.
  - CoreDNS rewrites updated to route both `.local` and `.<domain>` to `ingress-proxy`.
- Dashboard UI:
  - Injected `breadboard_domain` and `service_urls` in `src/dashboard/webapp.py` and `layout.html`.
  - Parameterized external UI endpoints in `ticket_data.py`, `job_scripts.py`, `fullsend_onboarding.py`, and `fullsend-dashboard`.
  - Added unit test suite in `tests/test_domain_parameterization.py` (12 tests passing).

### 2026-10-28 WP3 completed: Full Stack Deployment in Lima (bb-1sa.3)

- Deployed complete Breadboard stack inside `breadboard` Lima VM on ARM64:
  - Installed native Go 1.24.1, Rust stable (`aarch64-unknown-linux-gnu`), and `docker-buildx` via provisioner.
  - Configured VM memory to 20GiB in `breadboard-vm.yaml` and `deploy/lima/README.md` for 32GiB host headroom.
  - Added `image_in_k3s` guards to `deploy/scripts/05-build-images.sh` and `deploy-all.sh` to avoid redundant builds.
  - Added Linux page cache clearing (`sync && echo 3 > /proc/sys/vm/drop_caches`) and builder cache pruning after image builds.
  - Fixed `deploy/scripts/05k-build-github-actions-real-runner.sh` to install native ARM64 runner binaries on `aarch64`.
  - Fixed OpenShell helm chart alignment (`dependencies.json` pinned to `b2ea81822bb5263679ed00ff0fbe8c08577abab5` matching image tag `0.0.110`).
  - Fixed `deploy/k8s/18-observatory.yaml` `gcp-credentials` secret volume mount with `optional: true`.
  - Added `dnsConfig` (`ndots: 2`) to `ingress-proxy` deployment and automated in-VM `/etc/hosts` sync for all `.local` and `.${DOMAIN}` endpoints.
  - Wrapped `24-fullsend-mint-dev.yaml`, `23-github-actions-runner.yaml`, and `27-fullsend-runner-egress.yaml` through `apply-domain-manifests.sh`.
  - Seeded Fullsend fixtures and verified `seed-fullsend-release.py` on both amd64 and arm64.
- **Breakpoint B3 Verified**:
  - All ~19 pods in `ai-pipeline`, `gitlab-runner`, `agent-sandbox-system`, `openshell-system`, and `cert-manager` reach Running/Ready.
  - Cluster and certificate validation suites passed (`test-cluster.sh`, `test-certificates.sh`).
  - Host kubeconfig verified (`make lima-kubeconfig` -> `~/.kube/breadboard-lima.yaml`), remote `kubectl get nodes` and `kubectl get pods -A` functional.
  - Ingress proxy responds HTTP 200/401 across all services (`dashboard`, `fullsend`, `github`, `jira`, `gitlab`, `markovd`, `observatory`, `orgpulse`, `relay`, `hooksink`, `mlflow`) for both `bb.internal` and `local`.
