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
make lima-configure-dns

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
make lima-configure-dns
```

In the Tailscale Admin Console (DNS -> Nameservers):
- Add a custom nameserver pointing `bb.internal` to `100.115.60.69` (Split DNS).
- Any client on the tailnet with access to `tag:breadboard` can then directly browse `https://dashboard.bb.internal`.

#### Trusting the Internal Cluster CA

The cluster's cert-manager uses an internal CA to issue TLS certificates for all services (`*.bb.internal` and `*.local`). The certificate is automatically exported to `deploy/certs/ca.crt`.

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
