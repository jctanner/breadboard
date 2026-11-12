# Lima VM for Breadboard on Apple Silicon

This directory contains the Lima VM template (`breadboard-vm.yaml`) designed for
running the Breadboard integrated stack on macOS Apple Silicon (ARM64).

## Architecture

- **Virtualization Framework**: Apple Virtualization (`vmType: vz`) for native ARM64 performance
- **Rosetta Emulation**: `rosetta: { enabled: true, binfmt: true }` transparently runs x86_64 container layers and binaries (e.g., GitHub Actions runners, Fullsend releases) without QEMU overhead
- **OS**: Ubuntu 24.04 LTS (Noble Numbat) ARM64 cloud image
- **Resources**: 8 vCPUs, 20 GiB RAM, 100 GiB virtual disk
- **Mounts**: Only the repository is mounted writable via `virtiofs`; the host home is not mounted
- **Port Forwards**: Ports 80, 443, 5000, 6443 forwarded to `127.0.0.1`

## Prerequisites

Install Lima on macOS:

```bash
brew install lima  # Lima 2 or newer
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

# Enter shell inside VM (working directory is / in the guest)
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
limactl start --name=breadboard --mount-only "$(pwd):w" deploy/lima/breadboard-vm.yaml
```

### 2. Open an Interactive Shell

```bash
limactl shell breadboard
```

Only the selected repository appears at the identical guest path. `make lima-up`
also creates `/breadboard` and `/vagrant` symlinks. Existing VMs need a matching
repository-only mount configured with `limactl edit --mount-only "$(pwd):w" breadboard`
while stopped; inspect their configuration before restarting.

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

The operator may join the Lima VM to a Tailnet. These are illustrative addresses,
not a preconfigured network or evidence of enforced isolation:
- **Tailnet Node**: `breadboard-vm.<your-tailnet>.ts.net`
- **Tailscale IPv4**: `100.64.0.10`
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

A dedicated `dnsmasq` instance runs inside the VM listening on `100.64.0.10:53` (UDP + TCP):
- Resolves all `*.bb.internal` (and `*.${BREADBOARD_DOMAIN}`) queries to `100.64.0.10`.
- Uses `bind-dynamic` and binds strictly to `tailscale0` without conflicting with `systemd-resolved` on `127.0.0.53`.
- Exports the cluster CA certificate to `deploy/certs/ca.crt`.

To configure or restart the DNS responder:

```bash
make lima-configure-dns BREADBOARD_DOMAIN=bb.internal
```

In the Tailscale Admin Console (DNS -> Nameservers):
- Add a custom nameserver pointing `bb.internal` to `100.64.0.10` (Split DNS).
- Any client on the tailnet with access to `tag:breadboard` can then directly browse `https://dashboard.bb.internal`.

#### Trusting the Internal Cluster CA

The cluster's cert-manager uses an internal CA to issue TLS certificates for the configured external domain and internal Kubernetes service names. With `BREADBOARD_DOMAIN=bb.internal`, external certificate names use `*.bb.internal`; `.local` aliases are HTTP-only. With the default `local`, existing `.local` HTTPS names are retained. When explicitly requested, Split DNS configuration exports the certificate to `deploy/certs/ca.crt`.

Prefer a tool-scoped trust setting, rather than adding this developer CA to the
system-wide trust store. First inspect the certificate fingerprint and critical
constraints using a trusted channel. If system trust is needed, use your OS's
administration procedure and explicitly remove obsolete unconstrained roots.

- **Curl verification**:
  ```bash
  curl --cacert deploy/certs/ca.crt --resolve dashboard.bb.internal:443:100.64.0.10 https://dashboard.bb.internal/ -I
  ```

#### Verification & DMZ Isolation

1. **DNS Resolution**:
   ```bash
   dig @100.64.0.10 dashboard.bb.internal +short
   dig +tcp @100.64.0.10 github.bb.internal +short
   ```
2. **HTTPS Ingress**:
   ```bash
   curl --cacert deploy/certs/ca.crt --resolve dashboard.bb.internal:443:100.64.0.10 https://dashboard.bb.internal/ -I
   ```
3. **DMZ Lateral Movement Block**:
   Inside the VM, traffic to other internal Tailscale nodes is blocked by ACL, while outbound internet access is permitted:
   ```bash
   # Blocked by Tailscale ACL (times out):
   limactl shell breadboard -- timeout 3 bash -c 'cat < /dev/null > /dev/tcp/100.64.0.20/22'
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
for unchanged source, unchanged domain, and unchanged CA only; cached tags do not detect either change.
For `scripts/bb` and the demo/CVE seeders, set `BREADBOARD_CA_FILE` to the verified
public CA file if it is not in the system trust store. `scripts/bb` uses the current
kubectl context and defaults to `local`; remote thermal inspection requires explicit
`RHEA_HOST`. Live CLI integration tests require `BREADBOARD_LIVE_TESTS=1`.

The CVE fixture uses synthetic advisory data and a deterministic dummy-runtime result.
That result tests plumbing; it is not a verified vulnerability or reachability assessment.
Only the native architecture of the built Fullsend binary is published as a release
asset. Running mixed architectures requires separately built and validated releases.

Split DNS is opt-in: run `make lima-configure-dns BREADBOARD_DOMAIN=bb.internal`
after installing dnsmasq with the guest package manager. For a direct host deployment,
`BREADBOARD_SPLIT_DNS=1` explicitly enables the final DNS setup step. It never installs
packages. `/etc/hosts` updates also require `BREADBOARD_UPDATE_HOSTS=1`; otherwise
configure host resolution separately before running seeders. The Make targets forward these opt-ins through sudo; when invoking scripts
directly, pass them explicitly through sudo.

The NameConstraints feature gate must be enabled in both cert-manager's controller
and webhook. `02-install-cert-manager.sh` does this; reinstalling cert-manager by
another method must preserve those flags. The CA retains its key (`rotationPolicy: Never`) during routine renewal; root key
changes require an explicit maintenance migration. Remove old unconstrained trust entries explicitly; a retained old root can
still validate old signatures. The default external constraints list actual Breadboard
service names, rather than trusting every mDNS host on the LAN.

Provisioning still runs the upstream HTTPS bootstrap installers for Tailscale, Rust,
and uv, and downloads Go from go.dev. Pinned installer hashes and an offline bootstrap
are deferred: this optional developer VM follows the repository's existing online
bootstrap model. Review these upstream scripts before running provisioning; do not
use it as a reproducible or hostile-code isolation boundary. Only mount a disposable
copy of the repo if the workloads are untrusted. No credentials outside that mount
should be made available to the guest.

CVE seeding refuses to delete an existing GitHub App installation by default.
Add the target repository through the emulator admin interface. The explicit
`FULLSEND_CVE_ALLOW_INSTALLATION_RECREATE=1` override is for a maintenance window
only: recreation changes the installation identity and can invalidate other tokens.
The conformance target intentionally bootstraps `runtime: dummy` when no scaffold
exists; it exercises scripted plumbing without consuming model credentials.

Deployment refuses an existing CA whose issued critical constraints do not exactly
match the requested manifest/domain. This guard runs before CA mutation; there is no
"skip verification" override. Existing unconstrained installs must first perform a
planned maintenance migration (rotate the root deliberately, reissue all leaves,
refresh the ConfigMap and CA-bearing images, replace client trust), or use a fresh
disposable cluster. Ordinary deployment is not a CA migration tool. After migration,
`deploy/validation/test-certificates.sh` verifies every issued leaf against the public
ConfigMap CA. Verify hostname coverage separately as described above.

The legacy direct-token smoke manifests/policies remain `.local` HTTP compatibility
fixtures; they do not claim custom-domain HTTPS coverage. Use the parameterized
Fullsend conformance/behaviour paths for that coverage.

The arm64 upstream runner Dockerfile rewrite has not been image-built on corsair.
Review any upstream architecture-specific checksums before building on Apple Silicon;
this needs the component checkout and disposable VM qualification. The copied build
context includes dotfiles such as `.dockerignore`.

The site runner's `FULLSEND_ALLOW_PRIVATE_FORGE=1` permits the intentionally private
emulator endpoint, and `FULLSEND_MINT_URL` identifies the internal HTTPS mint already
used by the role runner. They are local deployment settings, not permission to contact
arbitrary external forges or bypass token scopes.

During the explicit migration, back up state, remove the old root from client trust,
and delete **both** the old `internal-ca` Certificate and **`internal-ca-secret`**
before issuing a replacement. Deleting just the Certificate reuses the old key.
Perform these destructive steps only in the planned maintenance window. Generate a
new root/key, reissue every leaf, refresh the public ConfigMap, rebuild every image
that embeds the CA, and install only the new root on clients before restoring traffic.
Keep backups for an explicit rollback; do not leave both roots trusted indefinitely.

The current manifest permits only IPv4 CIDRs. Adding IPv6 requires extending and
testing the preflight's OpenSSL netmask parser first; unsupported input fails closed.

If first-time certificate setup was interrupted after the root became Ready but
before its public ConfigMap was published, preflight deliberately refuses to trust
an absent public root. Verify the root's critical constraints and fingerprint through
your authenticated Kubernetes connection, run `04-extract-ca-cert.sh` to publish that
verified public root, then retry setup. This is an explicit recovery step; do not
regenerate keys just to bypass the guard. Standalone emulator/Markovd deployment
scripts use the shared `03-setup-certificates.sh` bootstrap so a fresh setup publishes
the root before domain-bearing component manifests are applied.
