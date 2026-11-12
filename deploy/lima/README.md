# Lima VM for Breadboard on Apple Silicon

This directory contains the Lima VM template (`breadboard-vm.yaml`) designed for
running the Breadboard integrated stack on macOS Apple Silicon (ARM64).

## Architecture

- **Virtualization Framework**: Apple Virtualization (`vmType: vz`) for native ARM64 performance
- **Rosetta Emulation**: `rosetta: { enabled: true, binfmt: true }` transparently runs x86_64 container layers and binaries (e.g., GitHub Actions runners, Fullsend releases) without QEMU overhead
- **OS**: Ubuntu 24.04 LTS (Noble Numbat) ARM64 cloud image
- **Resources**: 8 vCPUs, 20 GiB RAM, 100 GiB virtual disk
- **Mounts**: User home directory (`~`) mounted writable via `virtiofs`
- **Port Forwards**: Ports 80, 443, 5000, 6443 forwarded to `127.0.0.1`

## Prerequisites

Install Lima on macOS:

```bash
brew install lima
```

Ensure Rosetta 2 is installed on your Mac:

```bash
softwareupdate --install-rosetta --agree-to-license
```

## Quick Start (Makefile)

The root `Makefile` provides convenience targets:

```bash
# Start VM and ensure project symlinks (/breadboard and /vagrant)
make lima-up

# Enter shell inside VM (working directory matches repo on host)
make lima-shell

# Check VM and cluster status
make lima-status

# Configure Tailscale Split DNS responder (dnsmasq)
make lima-configure-dns BREADBOARD_DOMAIN=bb.internal

# Stop the VM
make lima-halt
```

## Manual Usage (`limactl`)

### 1. Start the VM

```bash
limactl start --name=breadboard deploy/lima/breadboard-vm.yaml
```

### 2. Open an Interactive Shell

```bash
limactl shell breadboard
```

Inside the VM, your host home directory is mounted at the identical path. The repo
is also symlinked at `/breadboard` and `/vagrant`.

### 3. Verify Rosetta Emulation (Breakpoint B1)

```bash
# Verify guest architecture is ARM64
limactl shell breadboard -- uname -m
# Output: aarch64

# Verify x86_64 container emulation via Rosetta binfmt
limactl shell breadboard -- sudo docker run --rm --platform linux/amd64 alpine uname -m
# Output: x86_64
```

### 4. Tailscale DMZ Node & Split DNS (Work Package 4)

The Lima VM joins the operator's Tailnet as a dedicated DMZ node:
- **Tailnet Node**: `breadboard-vm.tailc66a3b.ts.net`
- **Tailscale IPv4**: `100.115.60.69`
- **ACL Tag**: `tag:breadboard`

Joining the VM to Tailscale (one-time setup):

```bash
limactl shell breadboard -- sudo tailscale up \
  --authkey="<TS_AUTHKEY>" \
  --tags="tag:breadboard" \
  --hostname="breadboard-vm"
```

> **Security Note**: Never commit Tailscale auth keys or credentials to git.
> Use ephemeral or single-use tagged keys.

#### Split DNS Responder (`dnsmasq`)

A dedicated `dnsmasq` instance runs inside the VM listening on `100.115.60.69:53` (UDP + TCP):
- Resolves all `*.bb.internal` (and `*.${BREADBOARD_DOMAIN}`) queries to `100.115.60.69`.
- Uses `bind-dynamic` and binds strictly to `tailscale0` without conflicting with `systemd-resolved` on `127.0.0.53`.
- Exports the cluster CA certificate to `deploy/certs/ca.crt`.

To configure or restart the DNS responder:

```bash
make lima-configure-dns BREADBOARD_DOMAIN=bb.internal
```

In the Tailscale Admin Console (DNS -> Nameservers):
- Add a custom nameserver pointing `bb.internal` to `100.115.60.69` (Split DNS).
- Any client on the tailnet with access to `tag:breadboard` can then directly browse `https://dashboard.bb.internal`.

#### Trusting the Internal Cluster CA

The cluster's cert-manager uses an internal CA to issue TLS certificates for the configured external domain and internal Kubernetes service names. With `BREADBOARD_DOMAIN=bb.internal`, external certificate names use `*.bb.internal`; `.local` aliases are HTTP-only. With the default `local`, existing `.local` HTTPS names are retained. The certificate is automatically exported to `deploy/certs/ca.crt`.

To trust the certificate:
- **macOS**:
  ```bash
  sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain deploy/certs/ca.crt
  ```
- **Ubuntu/Debian**:
  ```bash
  sudo cp deploy/certs/ca.crt /usr/local/share/ca-certificates/breadboard-ca.crt
  sudo update-ca-certificates
  ```
- **Curl verification**:
  ```bash
  curl --cacert deploy/certs/ca.crt --resolve dashboard.bb.internal:443:100.115.60.69 https://dashboard.bb.internal/ -I
  ```

#### Verification & DMZ Isolation

1. **DNS Resolution**:
   ```bash
   dig @100.115.60.69 dashboard.bb.internal +short
   dig +tcp @100.115.60.69 github.bb.internal +short
   ```
2. **HTTPS Ingress**:
   ```bash
   curl --cacert deploy/certs/ca.crt --resolve dashboard.bb.internal:443:100.115.60.69 https://dashboard.bb.internal/ -I
   ```
3. **DMZ Lateral Movement Block**:
   Inside the VM, traffic to other internal Tailscale nodes is blocked by ACL, while outbound internet access is permitted:
   ```bash
   # Blocked by Tailscale ACL (times out):
   limactl shell breadboard -- timeout 3 bash -c 'cat < /dev/null > /dev/tcp/100.100.21.61/22'
   # Permitted (public internet egress):
   limactl shell breadboard -- curl -sI https://1.1.1.1
   ```

## Domain, trust, and upgrade notes

Pass `BREADBOARD_DOMAIN=bb.internal` to both `make lima-deploy-all` and
`make lima-configure-dns`. The default remains `local`. Use lowercase DNS labels;
paths, ports, whitespace inside names, and shell syntax are rejected by deploy scripts.
The VM addresses and Tailnet names above are examples; substitute your own address.
Tailnet ACLs must be configured separately; provisioning does not enforce DMZ isolation.

The CA private key remains in the Kubernetes `internal-ca-secret` Secret. Only its
public certificate is exported. Kubernetes administrators and any workload allowed
to read that Secret can issue certificates. Name constraints restrict DNS/IP names;
they do not restrict other certificate name types or replace Secret RBAC. Trust-anchor
constraint enforcement differs between client trust stores. Verify your actual browser
and OS behavior before installing this CA system-wide; prefer `curl --cacert` for testing.
Never copy `tls.key` to a client or publish the Secret.

Changing domains or adding constraints to an existing install changes the CA
certificate. Plan a maintenance window: inspect the issued CA with
`openssl x509 -in deploy/certs/ca.crt -text -noout`, verify its critical constraints,
renew affected leaf certificates, refresh the `internal-ca-cert` ConfigMap, rebuild
CA-bearing images, and replace the old client trust entry. Check every service with
hostname verification enabled. Do not assume `Ready` on an old Certificate proves
that new constraints or SANs have already been issued. Back up state and plan rollback
before changing a working install. No client trust-store changes run automatically.

Deployments rebuild images by default. `FORCE_REBUILD=0` is an explicit optimization
for unchanged source and unchanged CA only; cached tags do not detect either change.
For `scripts/bb` and the demo/CVE seeders, set `BREADBOARD_CA_FILE` to the verified
public CA file if it is not in the system trust store. `scripts/bb` uses the current
kubectl context and defaults to `local`; remote thermal inspection requires explicit
`RHEA_HOST`. Live CLI integration tests require `BREADBOARD_LIVE_TESTS=1`.

The CVE fixture uses synthetic advisory data and a deterministic dummy-runtime result.
That result tests plumbing; it is not a verified vulnerability or reachability assessment.
Only the native architecture of the built Fullsend binary is published as a release
asset. Running mixed architectures requires separately built and validated releases.
