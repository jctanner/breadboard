#!/usr/bin/env bash
# Build and import the upstream GitHub Actions runner compatibility image.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
RUNNER_CONTEXT="${PROJECT_ROOT}/checkouts/github-emulator/src/runners/upstream"
IMAGE="github-emulator-actions-real-runner:k3s"

if command -v docker >/dev/null 2>&1; then
  CONTAINER_CMD=docker
elif command -v podman >/dev/null 2>&1; then
  CONTAINER_CMD=podman
else
  echo "ERROR: docker or podman is required" >&2
  exit 1
fi

if [[ ! -f "${RUNNER_CONTEXT}/Dockerfile" ]]; then
  echo "ERROR: GitHub emulator real runner checkout is missing: ${RUNNER_CONTEXT}" >&2
  exit 1
fi

echo "==> Building ${IMAGE} with ${CONTAINER_CMD}"
BUILD_DIR="$(mktemp -d /tmp/runner-build.XXXXXX)"
cleanup() { rm -rf "${BUILD_DIR}"; }
trap cleanup EXIT
cp -r "${RUNNER_CONTEXT}"/* "${BUILD_DIR}/"
if [[ "$(uname -m)" == "aarch64" || "$(uname -m)" == "arm64" ]]; then
  sed -i "s/actions-runner-linux-x64/actions-runner-linux-arm64/g" "${BUILD_DIR}/Dockerfile"
fi
"${CONTAINER_CMD}" build -f "${BUILD_DIR}/Dockerfile" -t "${IMAGE}" "${BUILD_DIR}"

echo "==> Importing ${IMAGE} into k3s"
sudo k3s ctr images rm "docker.io/library/${IMAGE}" "localhost/${IMAGE}" 2>/dev/null || true
"${CONTAINER_CMD}" save "${IMAGE}" | sudo k3s ctr images import -
sudo k3s ctr images tag "localhost/${IMAGE}" "docker.io/library/${IMAGE}" 2>/dev/null || true

echo "==> Imported images"
sudo k3s ctr images ls | grep github-emulator-actions-real-runner
