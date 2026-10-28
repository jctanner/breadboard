# Lima VM for Breadboard on Apple Silicon

This directory contains the Lima VM template (`breadboard-vm.yaml`) designed for
running the Breadboard integrated stack on macOS Apple Silicon (ARM64).

## Architecture

- **Virtualization Framework**: Apple Virtualization (`vmType: vz`) for native ARM64 performance
- **Rosetta Emulation**: `rosetta: { enabled: true, binfmt: true }` transparently runs x86_64 container layers and binaries (e.g., GitHub Actions runners, Fullsend releases) without QEMU overhead
- **OS**: Ubuntu 24.04 LTS (Noble Numbat) ARM64 cloud image
- **Resources**: 8 vCPUs, 28 GiB RAM, 100 GiB virtual disk
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

### 4. Tailscale DMZ Join Template (Work Package 4)

Tailscale is pre-installed during provisioning. To join the node to your tailnet
under the DMZ isolation tag:

```bash
limactl shell breadboard -- sudo tailscale up \
  --authkey="<TS_AUTHKEY>" \
  --tags="tag:breadboard" \
  --hostname="breadboard-vm"
```

> **Security Note**: Never commit Tailscale auth keys or credentials to git.
> Use ephemeral or single-use tagged keys.
