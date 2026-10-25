#!/usr/bin/env bash
# Build the webhook sink image from checkouts/webhook-sink-service and import
# it into k3s. The Dockerfile runs cargo fmt, clippy, and tests before the
# release build.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
SINK_DIR="${WEBHOOK_SINK_DIR:-${PROJECT_ROOT}/checkouts/webhook-sink-service}"

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

"${CONTAINER_CMD}" build -f "${SINK_DIR}/Dockerfile" -t webhook-sink:latest "${SINK_DIR}"
sudo k3s ctr images rm docker.io/library/webhook-sink:latest localhost/webhook-sink:latest 2>/dev/null || true
"${CONTAINER_CMD}" save webhook-sink:latest | sudo k3s ctr images import -
sudo k3s ctr images tag localhost/webhook-sink:latest docker.io/library/webhook-sink:latest 2>/dev/null || true
echo "Built and imported webhook-sink:latest"
