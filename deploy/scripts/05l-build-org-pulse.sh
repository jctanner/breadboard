#!/usr/bin/env bash
# Build and import the Org Pulse images for k3s.
#
# Org Pulse is two repositories layered into one application:
#
#   checkouts/org-pulse-core   the platform (Vue 3 + Express, the module
#                              system, the team-tracker module). Upstream
#                              publishes it as three images on quay.io: a
#                              backend, a frontend *builder* (deps + source,
#                              not yet built) and a frontend *runtime*
#                              (hardened nginx, no app code).
#   checkouts/rhai-org-pulse   the AI Engineering consumer. No platform code
#                              of its own: its two Dockerfiles start FROM the
#                              core images at a pinned tag and copy its nine
#                              modules and platform customisations on top.
#
# Upstream pulls the core images from quay.io. This stack builds them from
# the core checkout instead and tags them with the *exact* names the consumer
# Dockerfiles expect, so `FROM quay.io/org-pulse/org-pulse-core-backend:vX`
# resolves to the local build without a pull (podman's default pull policy
# prefers a present image of that name). CORE_TAG is derived from the core
# checkout's package.json the same way the consumer's own Makefile derives it
# from the installed npm package, so the two checkouts have to agree: the
# consumer pins `@org-pulse/core` to the version the core checkout is at.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
CORE_ROOT="${PROJECT_ROOT}/checkouts/org-pulse-core"
CONSUMER_ROOT="${PROJECT_ROOT}/checkouts/rhai-org-pulse"

if command -v docker >/dev/null 2>&1; then
  CONTAINER_CMD=docker
elif command -v podman >/dev/null 2>&1; then
  CONTAINER_CMD=podman
else
  echo "ERROR: Neither docker nor podman found" >&2
  exit 1
fi

for required in "${CORE_ROOT}/package.json" "${CONSUMER_ROOT}/package.json"; do
  if [ ! -f "${required}" ]; then
    echo "ERROR: ${required} not found. Clone the component repositories first (make host-clone-repos)." >&2
    exit 1
  fi
done

CORE_VERSION="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "${CORE_ROOT}/package.json")"
CORE_TAG="v${CORE_VERSION}"
WANTED="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['dependencies']['@org-pulse/core'])" "${CONSUMER_ROOT}/package.json")"
echo "==> Org Pulse core ${CORE_TAG} (the consumer pins @org-pulse/core ${WANTED})"
case "${WANTED}" in
  *"${CORE_VERSION}"*) ;;
  *)
    echo "WARNING: the consumer pins @org-pulse/core ${WANTED} but the core checkout is ${CORE_VERSION}." >&2
    echo "         Its Dockerfiles will layer onto core ${CORE_TAG} regardless; check out matching revisions if a module misbehaves." >&2
    ;;
esac

CORE_BACKEND="quay.io/org-pulse/org-pulse-core-backend:${CORE_TAG}"
CORE_BUILDER="quay.io/org-pulse/org-pulse-core-frontend-builder:${CORE_TAG}"
CORE_RUNTIME="quay.io/org-pulse/org-pulse-core-frontend-runtime:${CORE_TAG}"
BACKEND_IMAGE="org-pulse-backend:k3s"
FRONTEND_IMAGE="org-pulse-frontend:k3s"

echo "==> Building the core images from ${CORE_ROOT}"
cd "${CORE_ROOT}"
"${CONTAINER_CMD}" build -f deploy/core.backend.Dockerfile -t "${CORE_BACKEND}" .
"${CONTAINER_CMD}" build -f deploy/core.frontend-builder.Dockerfile -t "${CORE_BUILDER}" .
"${CONTAINER_CMD}" build -f deploy/core.frontend-runtime.Dockerfile -t "${CORE_RUNTIME}" .

echo "==> Building the AI Engineering images from ${CONSUMER_ROOT} on core ${CORE_TAG}"
cd "${CONSUMER_ROOT}"
"${CONTAINER_CMD}" build -f deploy/ai-eng.backend.Dockerfile --build-arg "CORE_TAG=${CORE_TAG}" -t "${BACKEND_IMAGE}" .
"${CONTAINER_CMD}" build -f deploy/ai-eng.frontend.Dockerfile --build-arg "CORE_TAG=${CORE_TAG}" -t "${FRONTEND_IMAGE}" .

for image in "${BACKEND_IMAGE}" "${FRONTEND_IMAGE}"; do
  echo "==> Importing ${image} into k3s"
  sudo k3s ctr images rm "docker.io/library/${image}" "localhost/${image}" 2>/dev/null || true
  "${CONTAINER_CMD}" save "${image}" | sudo k3s ctr images import -
  sudo k3s ctr images tag "localhost/${image}" "docker.io/library/${image}" 2>/dev/null || true
done

echo ""
echo "==> Org Pulse images built and imported"
sudo k3s ctr images ls | grep -E 'org-pulse-(backend|frontend):k3s' || echo "No org-pulse images found"
