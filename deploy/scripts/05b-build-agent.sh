#!/bin/bash
# Build pipeline-agent image (job runner with Claude CLI)

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
PROJECT_ROOT="$(cd -- "${PROJECT_ROOT}" >/dev/null && pwd -P)"

# Use docker or podman
if command -v docker &> /dev/null; then
  CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
  CONTAINER_CMD="podman"
else
  echo "ERROR: Neither docker nor podman found"
  exit 1
fi

echo "==> Building pipeline-agent image..."
cd "${PROJECT_ROOT}"

if [ ! -f deploy/pipeline-agent/Dockerfile ]; then
  echo "ERROR: deploy/pipeline-agent/Dockerfile not found"
  exit 1
fi

# Extract internal CA cert from ConfigMap so it can be baked into the image
echo "  Extracting CA certificate from ConfigMap..."
if ! CA_CERT=$(kubectl get configmap internal-ca-cert \
  -n ai-pipeline -o jsonpath='{.data.ca\.crt}'); then
  echo "ERROR: Could not read internal-ca-cert; refusing to build a CA-less agent" >&2
  exit 1
fi
if [ -z "$CA_CERT" ]; then
  echo "ERROR: internal-ca-cert is empty; refusing to build a CA-less agent" >&2
  exit 1
fi
command -v openssl >/dev/null || { echo "ERROR: openssl is required to validate the CA" >&2; exit 1; }
CA_CONTEXT_FILE="${PWD}/internal-ca.crt"
trap 'rm -f "${CA_CONTEXT_FILE}"' EXIT
CERT_COUNT=$(printf '%s\n' "$CA_CERT" | grep -c -- '-----BEGIN CERTIFICATE-----' || true)
ALL_CERT_COUNT=$(printf '%s\n' "$CA_CERT" | grep -Ec -- '-----BEGIN (TRUSTED |X509 )?CERTIFICATE-----' || true)
if [ "$CERT_COUNT" != "1" ] || [ "$ALL_CERT_COUNT" != "1" ]; then
  echo "ERROR: internal-ca-cert must contain exactly one certificate" >&2
  exit 1
fi
# Serialize only the public X509 certificate; discard any appended PEM data.
if ! printf '%s\n' "$CA_CERT" | openssl x509 -out internal-ca.crt; then
  echo "ERROR: internal-ca-cert is not a valid X509 certificate" >&2
  exit 1
fi
echo "  CA certificate extracted and validated successfully"

${CONTAINER_CMD} build ${DOCKER_BUILD_ARGS:-} -f deploy/pipeline-agent/Dockerfile -t pipeline-agent:latest .

# Clean up extracted cert
rm -f internal-ca.crt

# Import into k3s (remove old image first so containerd doesn't skip the import)
echo "  Removing old pipeline-agent image from k3s..."
sudo k3s ctr images rm docker.io/library/pipeline-agent:latest localhost/pipeline-agent:latest 2>/dev/null || true
echo "  Importing pipeline-agent image into k3s..."
${CONTAINER_CMD} save pipeline-agent:latest | sudo k3s ctr images import -
sudo k3s ctr images tag localhost/pipeline-agent:latest docker.io/library/pipeline-agent:latest 2>/dev/null || true

echo "✓ Successfully built and imported pipeline-agent:latest"
