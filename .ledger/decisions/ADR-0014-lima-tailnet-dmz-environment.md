# ADR-0014: Lima VM with Rosetta and Tailscale DMZ for Apple Silicon

## Status

Accepted, 2026-10-30.

## Context

The upstream Breadboard deployment stack assumes an x86_64 Linux host or a
libvirt-backed Vagrant VM on Ubuntu 24.04, binding ingress to `*.local`
hostnames on `127.0.0.1`.

Running Breadboard on Apple Silicon (arm64 macOS) creates two challenges:
1. **Architecture traps**: Components such as the GitHub Actions runner
   image (`checkouts/github-emulator/src/runners/upstream/Dockerfile`) and
   Fullsend release seeding hardcode `linux-x64` / `linux_amd64` binaries.
2. **Remote connectivity & mDNS**: Developing remotely over SSH and Tailscale
   makes `*.local` unreachable or slow due to macOS Bonjour (`mDNSResponder`)
   conflicts and lack of mDNS routing across Tailscale.

## Decision

1. **Virtualization**: Use an Ubuntu 24.04 ARM64 VM managed by Lima (`limactl`)
   using Apple's Virtualization framework (`vmType: vz`) with Rosetta for Linux
   enabled (`rosetta: { enabled: true, binfmt: true }`). This provides native
   ARM64 performance for container builds and K3s, while transparently executing
   x86_64 container layers and binaries via Rosetta emulation without QEMU overhead.
2. **Tailnet DMZ Isolation**: The VM joins the operator's Tailnet as a dedicated
   node tagged `tag:breadboard`. In Tailscale ACLs, this tag is isolated into a
   DMZ: operators and dev machines can connect into the VM, but the VM has
   zero network egress to any internal Tailnet peer (outbound egress permitted
   only to the public internet for package and image updates).
3. **Domain Parameterization**: Introduce `BREADBOARD_DOMAIN` across the reverse
   proxy, certificate provisioning, and dashboard links. It defaults to `local`
   to preserve 100% backward compatibility with upstream (`jctanner/breadboard`),
   but permits overriding to e.g. `bb.internal` for Tailscale Split DNS routing.

## Consequences

- Apple Silicon hosts run the full platform without modifying x86_64 binaries.
- Remote access from browsers over Tailscale works without port forwarding or
  fragile `/etc/hosts` synchronization on client devices.
- Upstream compatibility with `jctanner/breadboard` is strictly preserved.
