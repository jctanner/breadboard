#!/usr/bin/env bash
# Build the Workflow Dojo image from checkouts/workflow-dojo and import it into k3s.
# CLAUDE_CODE_VERSION pins the bundled Claude Code CLI (default: latest).
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
DOJO_DIR="${WORKFLOW_DOJO_DIR:-${PROJECT_ROOT}/checkouts/workflow-dojo}"

if [ ! -f "${DOJO_DIR}/Containerfile" ]; then
  echo "ERROR: ${DOJO_DIR}/Containerfile not found" >&2
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

"${CONTAINER_CMD}" build -f "${DOJO_DIR}/Containerfile" \
  --build-arg "CLAUDE_CODE_VERSION=${CLAUDE_CODE_VERSION:-latest}" \
  -t workflow-dojo:latest "${DOJO_DIR}"
sudo k3s ctr images rm docker.io/library/workflow-dojo:latest localhost/workflow-dojo:latest 2>/dev/null || true
"${CONTAINER_CMD}" save workflow-dojo:latest | sudo k3s ctr images import -
sudo k3s ctr images tag localhost/workflow-dojo:latest docker.io/library/workflow-dojo:latest 2>/dev/null || true
echo "Built and imported workflow-dojo:latest"
