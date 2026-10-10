#!/bin/bash
# Build and import markovd image for k3s

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"

if command -v docker &> /dev/null; then
  CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
  CONTAINER_CMD="podman"
else
  echo "ERROR: Neither docker nor podman found"
  exit 1
fi

echo "==> Building markovd image..."

if [ ! -d ${PROJECT_ROOT}/checkouts/markovd ]; then
  echo "ERROR: markovd repo not found at ${PROJECT_ROOT}/checkouts/markovd"
  exit 1
fi

cd ${PROJECT_ROOT}/checkouts/markovd

# markovd validates imported and uploaded workflows with the markov binary its
# Dockerfile copies from bin/markov. Build it from checkouts/markov so it is
# the same Markov the job image (05d-build-markov.sh) runs.
MARKOV_SRC="${PROJECT_ROOT}/checkouts/markov"
if [ ! -d "${MARKOV_SRC}" ]; then
  echo "ERROR: markov repo not found at ${MARKOV_SRC}"
  exit 1
fi
echo "  Building bundled markov from ${MARKOV_SRC} ($(git -C "${MARKOV_SRC}" rev-parse --short HEAD))..."
mkdir -p bin
if command -v go &> /dev/null; then
  (cd "${MARKOV_SRC}" && CGO_ENABLED=0 go build -o "${PROJECT_ROOT}/checkouts/markovd/bin/markov" ./cmd/markov)
else
  ${CONTAINER_CMD} run --rm -v "${MARKOV_SRC}:/src:ro,z" -v "${PROJECT_ROOT}/checkouts/markovd/bin:/out:z" \
    -w /src -e CGO_ENABLED=0 -e GOCACHE=/tmp/go-build docker.io/library/golang:1.25 \
    go build -buildvcs=false -o /out/markov ./cmd/markov
fi

${CONTAINER_CMD} build -t markovd:latest .

echo "  Importing markovd image into k3s..."
sudo k3s ctr images rm docker.io/library/markovd:latest localhost/markovd:latest 2>/dev/null || true
${CONTAINER_CMD} save markovd:latest | sudo k3s ctr images import -
sudo k3s ctr images tag localhost/markovd:latest docker.io/library/markovd:latest 2>/dev/null || true

echo "Successfully built and imported markovd:latest"
