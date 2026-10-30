#!/usr/bin/env bash
# Configure Tailscale Split DNS responder (dnsmasq) inside Lima VM.
# Listens on <tailscale0 IP>:53 (UDP + TCP) and resolves *.bb.internal
# (and *.${BREADBOARD_DOMAIN}) to the VM's Tailscale IP.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

echo "==> Configuring Tailscale Split DNS responder (dnsmasq)..."

# Detect tailscale0 interface IPv4 address
if ! ip link show dev tailscale0 >/dev/null 2>&1; then
  echo "WARNING: tailscale0 interface not found. Ensure Tailscale is running inside the VM."
  exit 0
fi

TS_IP=$(ip -4 -o addr show dev tailscale0 | awk '{split($4,a,"/"); print a[1]}')
if [ -z "${TS_IP}" ]; then
  echo "ERROR: Could not detect IPv4 address on tailscale0."
  exit 1
fi

echo "  Detected Tailscale IP: ${TS_IP}"

# Ensure dnsmasq is installed
if ! command -v dnsmasq >/dev/null 2>&1 || ! dpkg -s dnsmasq >/dev/null 2>&1; then
  echo "  Installing dnsmasq..."
  apt-get update -qq
  DEBIAN_FRONTEND=noninteractive apt-get install -y dnsmasq
fi

# Ensure ubuntu-fan configuration does not conflict with bind-dynamic
if [ -f /etc/dnsmasq.d/ubuntu-fan ]; then
  sed -i 's/^bind-interfaces/#bind-interfaces/' /etc/dnsmasq.d/ubuntu-fan
fi

# Determine configured domains
DOMAIN="${BREADBOARD_DOMAIN:-bb.internal}"

# Write dnsmasq configuration for breadboard
cat <<EOF > /etc/dnsmasq.d/breadboard.conf
# Breadboard Tailscale Split DNS responder
listen-address=${TS_IP}
bind-dynamic
except-interface=lo
no-resolv
no-hosts
address=/.bb.internal/${TS_IP}
EOF

if [ "${DOMAIN}" != "bb.internal" ] && [ -n "${DOMAIN}" ] && [ "${DOMAIN}" != "local" ]; then
  cat <<EOF >> /etc/dnsmasq.d/breadboard.conf
address=/.${DOMAIN}/${TS_IP}
EOF
fi

echo "  Enabling and restarting dnsmasq..."
systemctl enable --now dnsmasq
systemctl restart dnsmasq

# Extract cluster CA certificate to deploy/certs/ca.crt if k3s is available
if command -v kubectl >/dev/null 2>&1 && kubectl get secret -n ai-pipeline internal-ca-secret >/dev/null 2>&1; then
  mkdir -p "${PROJECT_ROOT}/deploy/certs"
  kubectl get secret -n ai-pipeline internal-ca-secret -o jsonpath='{.data.tls\.crt}' | base64 -d > "${PROJECT_ROOT}/deploy/certs/ca.crt"
  chmod 644 "${PROJECT_ROOT}/deploy/certs/ca.crt"
  echo "  Cluster CA exported to ${PROJECT_ROOT}/deploy/certs/ca.crt"
fi

# Self-test DNS resolution inside VM
echo "  Testing DNS resolution on ${TS_IP}:53..."
if command -v dig >/dev/null 2>&1; then
  RESOLVED_IP=$(dig @${TS_IP} dashboard.bb.internal +short || true)
  if [ "${RESOLVED_IP}" = "${TS_IP}" ]; then
    echo "  ✓ Local DNS query verified: dashboard.bb.internal -> ${RESOLVED_IP}"
  else
    echo "  WARNING: Local DNS query returned '${RESOLVED_IP}', expected '${TS_IP}'"
  fi
fi

echo "==> Tailscale Split DNS configured successfully."
echo "    Nameserver: ${TS_IP}"
echo "    Domain:     *.bb.internal -> ${TS_IP}"
if [ "${DOMAIN}" != "bb.internal" ] && [ -n "${DOMAIN}" ] && [ "${DOMAIN}" != "local" ]; then
  echo "    Domain:     *.${DOMAIN} -> ${TS_IP}"
fi
