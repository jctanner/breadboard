#!/usr/bin/env bash
# Build the webhook sink image from checkouts/hooksink and import
# it into k3s. The Dockerfile runs cargo fmt, clippy, and tests before the
# release build.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
SINK_DIR="${HOOKSINK_DIR:-${PROJECT_ROOT}/checkouts/hooksink}"

if [ ! -f "${SINK_DIR}/Dockerfile" ]; then
  echo "ERROR: ${SINK_DIR}/Dockerfile not found" >&2
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

"${CONTAINER_CMD}" build -f "${SINK_DIR}/Dockerfile" -t hooksink:latest "${SINK_DIR}"
sudo k3s ctr images rm docker.io/library/hooksink:latest localhost/hooksink:latest 2>/dev/null || true
"${CONTAINER_CMD}" save hooksink:latest | sudo k3s ctr images import -
sudo k3s ctr images tag localhost/hooksink:latest docker.io/library/hooksink:latest 2>/dev/null || true
echo "Built and imported hooksink:latest"
