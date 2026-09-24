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
  "${PROJECT_ROOT}/deploy/fullsend/patches/0011-address-the-configured-forge-in-the-github-commands.patch"
  "${PROJECT_ROOT}/deploy/fullsend/patches/0012-let-an-installation-name-its-runner.patch"
)
RUNNER_CONTEXT="${PROJECT_ROOT}/deploy/fullsend-runner-dev"
SANDBOX_CONTEXT="${PROJECT_ROOT}/deploy/fullsend-sandbox-dev"
SANDBOX_LOCAL_CONTEXT="${PROJECT_ROOT}/deploy/fullsend-sandbox-local"
RUNNER_IMAGE="fullsend-runner-dev:k3s"
SANDBOX_IMAGE="fullsend-sandbox-dev:k3s"
SANDBOX_LOCAL_IMAGE="fullsend-sandbox-local:k3s"
CODE_LOCAL_IMAGE="fullsend-code-local:k3s"

# The CA-bearing local images, each "<tag>|<harness file>|<base repository>".
# The base digest is not written here: it is read from the harness file that
# pins it, so the local image cannot quietly be built on a stale base when the
# harness moves. fullsend-sandbox backs triage; fullsend-code backs review and
# code, which pin the same digest.
AGENTS_HARNESS_DIR="${PROJECT_ROOT}/checkouts/fullsend-ai/agents/harness"
LOCAL_SANDBOX_IMAGES=(
  "${SANDBOX_LOCAL_IMAGE}|triage.yaml|ghcr.io/fullsend-ai/fullsend-sandbox"
  "${CODE_LOCAL_IMAGE}|review.yaml|ghcr.io/fullsend-ai/fullsend-code"
)

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

# The runner image ships gitleaks and pre-commit so the code stage's secret
# scan does not depend on the runner reaching the public internet. Those tools
# are also self-installed by the agent scripts at pinned versions, and the
# scripts skip their download when the tool is already on PATH — so the image
# silently wins. If the two drift, a run uses a version the library never
# verified, and nothing says so.
#
# Rather than trusting a comment to keep them in step, the versions and
# checksums are read out of the libraries that own them and compared.
echo "==> Checking the runner's pinned tools against the agent libraries"
GITLEAKS_LIB="${AGENTS_ROOT_LIB:-${PROJECT_ROOT}/checkouts/fullsend-ai/agents}/scripts/lib/gitleaks-install.lib.sh"
PRECOMMIT_LIB="${AGENTS_ROOT_LIB:-${PROJECT_ROOT}/checkouts/fullsend-ai/agents}/scripts/lib/precommit-gate.lib.sh"
RUNNER_CONTAINERFILE="${RUNNER_CONTEXT}/Containerfile"

for required_file in "${GITLEAKS_LIB}" "${PRECOMMIT_LIB}" "${RUNNER_CONTAINERFILE}"; do
  [[ -f "${required_file}" ]] || {
    echo "ERROR: ${required_file} is missing; cannot check pinned tool versions." >&2
    exit 1
  }
done

drift_check() {
  local label="$1" expected="$2" actual="$3" source_file="$4"
  if [[ -z "${expected}" ]]; then
    echo "ERROR: could not read ${label} from ${source_file}." >&2
    echo "       That file owns the value; this check cannot be skipped by guessing." >&2
    exit 1
  fi
  if [[ -z "${actual}" ]]; then
    echo "ERROR: could not read ${label} from ${RUNNER_CONTAINERFILE}." >&2
    exit 1
  fi
  if [[ "${expected}" != "${actual}" ]]; then
    echo "ERROR: ${label} has drifted." >&2
    echo "       ${source_file} says: ${expected}" >&2
    echo "       ${RUNNER_CONTAINERFILE} says: ${actual}" >&2
    echo "       The image wins at run time, because the agent scripts skip" >&2
    echo "       their own install when the tool is already on PATH. Update" >&2
    echo "       the Containerfile to match the library." >&2
    exit 1
  fi
  echo "  ${label}: ${actual}"
}

containerfile_arg() {
  sed -n "s/^ARG $1=\(.*\)$/\1/p" "${RUNNER_CONTAINERFILE}" | head -1
}

drift_check "gitleaks version" \
  "$(sed -n 's/^GITLEAKS_VERSION="\(.*\)"$/\1/p' "${GITLEAKS_LIB}" | head -1)" \
  "$(containerfile_arg GITLEAKS_VERSION)" "${GITLEAKS_LIB}"

drift_check "gitleaks linux_x64 sha256" \
  "$(sed -n 's/^[[:space:]]*linux_x64)[[:space:]]*echo "\([0-9a-f]\{64\}\)".*$/\1/p' "${GITLEAKS_LIB}" | head -1)" \
  "$(containerfile_arg GITLEAKS_SHA256_AMD64)" "${GITLEAKS_LIB}"

drift_check "gitleaks linux_arm64 sha256" \
  "$(sed -n 's/^[[:space:]]*linux_arm64)[[:space:]]*echo "\([0-9a-f]\{64\}\)".*$/\1/p' "${GITLEAKS_LIB}" | head -1)" \
  "$(containerfile_arg GITLEAKS_SHA256_ARM64)" "${GITLEAKS_LIB}"

drift_check "pre-commit version" \
  "$(sed -n 's/.*pre-commit==\([0-9][0-9.]*\)".*/\1/p' "${PRECOMMIT_LIB}" | head -1)" \
  "$(containerfile_arg PRECOMMIT_VERSION)" "${PRECOMMIT_LIB}"

echo "==> Building ${RUNNER_IMAGE}"
"${CONTAINER_CMD}" build -f "${RUNNER_CONTEXT}/Containerfile" -t "${RUNNER_IMAGE}" "${BUILD_CONTEXT}"

echo "==> Building ${SANDBOX_IMAGE}"
"${CONTAINER_CMD}" build -f "${SANDBOX_CONTEXT}/Containerfile" -t "${SANDBOX_IMAGE}" "${SANDBOX_CONTEXT}"

# The conformance sandboxes are Fullsend's own pinned images plus this
# cluster's internal CA. The supervisor reads its upstream TLS roots once at
# startup, so the CA has to be in the image rather than mounted afterwards, and
# the chart at this version exposes no way to inject one into sandbox pods.
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

for entry in "${LOCAL_SANDBOX_IMAGES[@]}"; do
  IFS='|' read -r local_image harness_file base_repo <<< "${entry}"
  harness_path="${AGENTS_HARNESS_DIR}/${harness_file}"
  [[ -f "${harness_path}" ]] || {
    echo "ERROR: ${harness_path} is missing; cannot read the base digest for ${local_image}." >&2
    exit 1
  }
  # Read the digest from the harness rather than repeating it here. If the
  # harness moves to a new image and this is not updated, the build stops
  # instead of silently producing a local image on last month's base.
  base_digest="$(sed -n "s|^image: ${base_repo}@\(sha256:[0-9a-f]\{64\}\)\s*$|\1|p" \
    "${harness_path}" | head -1)"
  if [[ -z "${base_digest}" ]]; then
    echo "ERROR: ${harness_file} does not pin ${base_repo} by digest." >&2
    echo "       Its image: line is:" >&2
    grep -n '^image:' "${harness_path}" >&2 || true
    echo "       Update LOCAL_SANDBOX_IMAGES in this script to match." >&2
    exit 1
  fi
  echo "==> Building ${local_image} FROM ${base_repo}@${base_digest} (pinned by ${harness_file})"
  "${CONTAINER_CMD}" build -f "${SANDBOX_LOCAL_CONTEXT}/Containerfile" \
    --build-arg "BASE_REPO=${base_repo}" \
    --build-arg "BASE_DIGEST=${base_digest}" \
    -t "${local_image}" "${SANDBOX_LOCAL_CONTEXT}"
done

for image in "${RUNNER_IMAGE}" "${SANDBOX_IMAGE}" "${SANDBOX_LOCAL_IMAGE}" "${CODE_LOCAL_IMAGE}"; do
  echo "==> Importing ${image} into k3s"
  sudo k3s ctr images rm "docker.io/library/${image}" "localhost/${image}" 2>/dev/null || true
  "${CONTAINER_CMD}" save "${image}" | sudo k3s ctr images import -
  sudo k3s ctr images tag "localhost/${image}" "docker.io/library/${image}" 2>/dev/null || true
done

echo "==> Imported Fullsend/OpenShell images"
sudo k3s ctr images ls | grep -E 'fullsend-(runner-dev|sandbox-dev|sandbox-local|code-local)'
