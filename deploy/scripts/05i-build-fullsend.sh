#!/usr/bin/env bash
# Build/import the Fullsend host launcher and local OpenShell sandbox images.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
FULLSEND_ROOT="${PROJECT_ROOT}/checkouts/fullsend-ai/fullsend"
OPENSHELL_ROOT="${PROJECT_ROOT}/checkouts/openshell"
# Only the patches that still apply against the canonical checkout survive
# here. Two prior patches (sandbox-name length, sticky-comment forge URL)
# were dropped because upstream now fixes both natively - see work package 1
# in .ledger/plans/fullsend-integration-conformance-plan.md.
# These patch Go source before the binary is compiled. Patches that change
# files a workflow reads at run time belong to MIRROR_PATCHES in
# deploy/fullsend/seed/seed-upstream-fullsend.py instead; a patch in the wrong
# list does nothing and does it silently.
FULLSEND_PATCHES=(
  "${PROJECT_ROOT}/deploy/fullsend/patches/0002-allow-insecure-dev-mint-url.patch"
  "${PROJECT_ROOT}/deploy/fullsend/patches/0005-resolve-agents-repo-against-configured-host.patch"
  "${PROJECT_ROOT}/deploy/fullsend/patches/0006-allow-a-privately-reachable-forge.patch"
  "${PROJECT_ROOT}/deploy/fullsend/patches/0007-parse-enterprise-raw-content-urls.patch"
  "${PROJECT_ROOT}/deploy/fullsend/patches/0008-scope-the-minted-token-on-enterprise-forges.patch"
  "${PROJECT_ROOT}/deploy/fullsend/patches/0009-load-the-harness-environment-for-behaviour-ops.patch"
  "${PROJECT_ROOT}/deploy/fullsend/patches/0010-do-not-cache-a-profile-import-that-never-replaced-anything.patch"
)
RUNNER_CONTEXT="${PROJECT_ROOT}/deploy/fullsend-runner-dev"
SANDBOX_CONTEXT="${PROJECT_ROOT}/deploy/fullsend-sandbox-dev"
SANDBOX_LOCAL_CONTEXT="${PROJECT_ROOT}/deploy/fullsend-sandbox-local"
RUNNER_IMAGE="fullsend-runner-dev:k3s"
SANDBOX_IMAGE="fullsend-sandbox-dev:k3s"
SANDBOX_LOCAL_IMAGE="fullsend-sandbox-local:k3s"

if command -v docker >/dev/null 2>&1; then
  CONTAINER_CMD=docker
elif command -v podman >/dev/null 2>&1; then
  CONTAINER_CMD=podman
else
  echo "ERROR: docker or podman is required" >&2
  exit 1
fi

for required in "${FULLSEND_ROOT}/go.mod" "${OPENSHELL_ROOT}/Cargo.toml" "${FULLSEND_PATCHES[@]}"; do
  if [[ ! -f "${required}" ]]; then
    echo "ERROR: required checkout file is missing: ${required}" >&2
    exit 1
  fi
done

RUNNER_SOURCE="${PROJECT_ROOT}/checkouts/github-emulator/src/runners/emulator/runner.py"
if [[ ! -f "${RUNNER_SOURCE}" ]]; then
  echo "ERROR: GitHub emulator runner source is missing: ${RUNNER_SOURCE}" >&2
  exit 1
fi

BUILD_CONTEXT="$(mktemp -d /tmp/fullsend-runner-build.XXXXXX)"
FULLSEND_BUILD_ROOT="$(mktemp -d /tmp/fullsend-source-build.XXXXXX)"
cleanup() { rm -rf "${BUILD_CONTEXT}" "${FULLSEND_BUILD_ROOT}"; }
trap cleanup EXIT

FULLSEND_REVISION="$(git -C "${FULLSEND_ROOT}" rev-parse HEAD)"
OPENSHELL_REVISION="$(git -C "${OPENSHELL_ROOT}" rev-parse HEAD)"
echo "==> Building Fullsend host launcher from ${FULLSEND_ROOT} (revision diagnostics, not a pin)"
echo "    fullsend  ${FULLSEND_REVISION}"
echo "    openshell ${OPENSHELL_REVISION}"
git -C "${FULLSEND_ROOT}" archive HEAD | tar -xf - -C "${FULLSEND_BUILD_ROOT}"
for patch in "${FULLSEND_PATCHES[@]}"; do
  patch_name="$(basename "${patch}")"
  if ! git -C "${FULLSEND_BUILD_ROOT}" apply --check --unidiff-zero "${patch}" 2>/dev/null; then
    echo "ERROR: patch ${patch_name} no longer applies against ${FULLSEND_ROOT} (${FULLSEND_REVISION})." >&2
    echo "       Rebase, replace, or drop it - see work package 1 in" >&2
    echo "       .ledger/plans/fullsend-integration-conformance-plan.md." >&2
    exit 1
  fi
  echo "==> Applying Fullsend patch ${patch_name}"
  git -C "${FULLSEND_BUILD_ROOT}" apply --unidiff-zero "${patch}"
done
(cd "${FULLSEND_BUILD_ROOT}" && GOTOOLCHAIN=auto go build -buildvcs=false -trimpath -ldflags '-s -w' -o "${BUILD_CONTEXT}/fullsend" ./cmd/fullsend)

# Keep a copy outside the throwaway build context. The conformance seed commits
# this binary into the target repository as Fullsend's vendored install, so the
# binary a run executes is provably the same one this image ships rather than a
# second build that merely resembles it.
VENDOR_DIR="${PROJECT_ROOT}/deploy/fullsend/vendor"
mkdir -p "${VENDOR_DIR}"
install -m 0755 "${BUILD_CONTEXT}/fullsend" "${VENDOR_DIR}/fullsend"
echo "==> Published vendorable binary to deploy/fullsend/vendor/fullsend"

# Fullsend pins the OpenShell version it expects, and its sandbox code passes
# arguments that only newer builds accept. Building whatever the checkout
# happens to be produces a binary that looks fine and then fails inside an
# agent with "unexpected argument", several minutes and three retries later.
# Compare the two and say so up front.
OPENSHELL_PIN="$(sed -n 's/^OPENSHELL_SHA=//p' "${FULLSEND_ROOT}/.github/scripts/openshell-version.sh" | tr -d '"' | head -1)"
OPENSHELL_PIN_VERSION="$(sed -n 's/^OPENSHELL_VERSION=//p' "${FULLSEND_ROOT}/.github/scripts/openshell-version.sh" | tr -d '"' | head -1)"
if [[ -n "${OPENSHELL_PIN}" && "${OPENSHELL_REVISION}" != "${OPENSHELL_PIN}" ]]; then
  echo "ERROR: the OpenShell checkout does not match the version Fullsend pins." >&2
  echo "       checkout: ${OPENSHELL_REVISION}" >&2
  echo "       pinned:   ${OPENSHELL_PIN} (${OPENSHELL_PIN_VERSION})" >&2
  echo "       Fetch and check out the pinned revision in checkouts/openshell," >&2
  echo "       or set FULLSEND_ALLOW_OPENSHELL_SKEW=1 to build anyway." >&2
  if [[ "${FULLSEND_ALLOW_OPENSHELL_SKEW:-}" != "1" ]]; then
    exit 1
  fi
  echo "       FULLSEND_ALLOW_OPENSHELL_SKEW=1 set; continuing with a skewed build." >&2
fi

echo "==> Building OpenShell CLI from pinned checkout"
(cd "${OPENSHELL_ROOT}" && cargo build --release -p openshell-cli)
cp "${OPENSHELL_ROOT}/target/release/openshell" "${BUILD_CONTEXT}/openshell"
cp "${RUNNER_SOURCE}" "${BUILD_CONTEXT}/runner.py"

echo "==> Building ${RUNNER_IMAGE}"
"${CONTAINER_CMD}" build -f "${RUNNER_CONTEXT}/Containerfile" -t "${RUNNER_IMAGE}" "${BUILD_CONTEXT}"

echo "==> Building ${SANDBOX_IMAGE}"
"${CONTAINER_CMD}" build -f "${SANDBOX_CONTEXT}/Containerfile" -t "${SANDBOX_IMAGE}" "${SANDBOX_CONTEXT}"

# The conformance sandbox is Fullsend's own pinned image plus this cluster's
# internal CA. The supervisor reads its upstream TLS roots once at startup, so
# the CA has to be in the image rather than mounted afterwards, and the chart
# at this version exposes no way to inject one into sandbox pods.
echo "==> Building ${SANDBOX_LOCAL_IMAGE}"
CA_OUT="${SANDBOX_LOCAL_CONTEXT}/internal-ca.crt"
if ! kubectl get configmap internal-ca-cert -n ai-pipeline \
      -o jsonpath='{.data.ca\.crt}' > "${CA_OUT}" 2>/dev/null || [[ ! -s "${CA_OUT}" ]]; then
  rm -f "${CA_OUT}"
  echo "ERROR: could not read the internal CA from the internal-ca-cert ConfigMap." >&2
  echo "       The cluster must be up; the sandbox image bakes that CA in." >&2
  exit 1
fi
# Fail here rather than shipping an image whose trust store is quietly wrong.
openssl x509 -in "${CA_OUT}" -noout -subject >/dev/null
"${CONTAINER_CMD}" build -f "${SANDBOX_LOCAL_CONTEXT}/Containerfile" \
  -t "${SANDBOX_LOCAL_IMAGE}" "${SANDBOX_LOCAL_CONTEXT}"

for image in "${RUNNER_IMAGE}" "${SANDBOX_IMAGE}" "${SANDBOX_LOCAL_IMAGE}"; do
  echo "==> Importing ${image} into k3s"
  sudo k3s ctr images rm "docker.io/library/${image}" "localhost/${image}" 2>/dev/null || true
  "${CONTAINER_CMD}" save "${image}" | sudo k3s ctr images import -
  sudo k3s ctr images tag "localhost/${image}" "docker.io/library/${image}" 2>/dev/null || true
done

echo "==> Imported Fullsend/OpenShell images"
sudo k3s ctr images ls | grep -E 'fullsend-(runner|sandbox)-dev'
