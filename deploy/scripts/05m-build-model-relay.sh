#!/usr/bin/env bash
# Build the Model Relay image from checkouts/model-relay and import it into k3s.
# The Dockerfile runs cargo fmt, tests, and clippy before the release build.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
RELAY_DIR="${MODEL_RELAY_DIR:-${PROJECT_ROOT}/checkouts/model-relay}"

if [ ! -f "${RELAY_DIR}/Dockerfile" ]; then
  echo "ERROR: ${RELAY_DIR}/Dockerfile not found" >&2
  exit 1
fi

if command -v docker >/dev/null 2>&1; then
  CONTAINER_CMD=docker
elif command -v podman >/dev/null 2>&1; then
  CONTAINER_CMD=podman
else
  echo "ERROR: Neither docker nor podman found" >&2
  exit 1
fi

"${CONTAINER_CMD}" build -f "${RELAY_DIR}/Dockerfile" -t model-relay:latest "${RELAY_DIR}"
sudo k3s ctr images rm docker.io/library/model-relay:latest localhost/model-relay:latest 2>/dev/null || true
"${CONTAINER_CMD}" save model-relay:latest | sudo k3s ctr images import -
sudo k3s ctr images tag localhost/model-relay:latest docker.io/library/model-relay:latest 2>/dev/null || true
echo "Built and imported model-relay:latest"
