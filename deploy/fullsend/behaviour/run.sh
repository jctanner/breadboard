#!/usr/bin/env bash
# Run Fullsend's behaviour-test suite against Breadboard's GitHub emulator and
# Fullsend Mint (plan: .ledger/plans/fullsend-behaviour-tests-plan.md).
#
# The suite runs from a scratch git worktree of the Fullsend checkout, carrying
# the same patches the stack is built from, plus the test-only patches:
#
#   1. the build list in deploy/scripts/05i-build-fullsend.sh (0005-0016);
#   2. the mirror list in deploy/fullsend/seed/seed-upstream-fullsend.py
#      (0003, 0004), which the emulator's fullsend-ai/fullsend mirror carries;
#   3. BT_PATCHES below (0017-0020), which only the harness uses.
#
# The result is committed in the worktree. Two things depend on that: the
# vendored install copies the tree under test into each slot, and the
# harness stamps the CLI with HEAD only when HEAD is published upstream, which
# a local commit is not.
#
# Prerequisites: the stack is running and `make bt-seed` has been run, so the
# pool organisation, its App installations and the mint's allowlists exist.
#
# Environment (all optional):
#   BT_FEATURES      godog paths relative to e2e/behaviour, space-separated
#                    (default: every feature)
#   BT_TAGS          GODOG_TAGS expression
#   BT_CONCURRENCY   GODOG_CONCURRENCY (default 1)
#   BT_TIMEOUT       go test -timeout (default 45m, upstream's CI budget;
#                    a whole tier at concurrency 1 needs longer)
#   BT_FULLSEND_REF  install non-vendored at this ref (the stage path);
#                    unset installs vendored (the pull-request path)
#   BT_SOURCE        Fullsend checkout to test (default: checkouts/fullsend-ai/fullsend)
#   BT_WORKDIR       scratch directory (default: ${TMPDIR:-/tmp}/breadboard-bt)
#   BT_GITHUB_TOKEN  act as this token's user instead of the e2e App's bot
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)}"
BT_SOURCE="${BT_SOURCE:-${PROJECT_ROOT}/checkouts/fullsend-ai/fullsend}"
BT_WORKDIR="${BT_WORKDIR:-${TMPDIR:-/tmp}/breadboard-bt}"
# Absolute, because git -C resolves a relative path against the checkout.
mkdir -p "${BT_WORKDIR}"
BT_WORKDIR="$(cd "${BT_WORKDIR}" && pwd)"
TREE="${BT_WORKDIR}/tree"
# One run per scratch directory: the next run replaces the worktree, which
# the running suite and its vendored builds are still using.
exec 9>"${BT_WORKDIR}/run.lock"
if ! flock -n 9; then
  echo "ERROR: another behaviour-test run is using ${BT_WORKDIR}; wait for it or set BT_WORKDIR" >&2
  exit 1
fi
PATCH_DIR="${PROJECT_ROOT}/deploy/fullsend/patches"
BT_PATCHES=(
  "${PATCH_DIR}/0017-address-the-configured-forge-in-the-behaviour-harness.patch"
  "${PATCH_DIR}/0018-local-run-the-behaviour-suite-against-an-external-mint.patch"
  "${PATCH_DIR}/0019-local-select-behaviour-features-from-the-environment.patch"
  "${PATCH_DIR}/0020-build-raw-urls-for-the-configured-forge-in-the-behaviour-harness.patch"
)

# The stack's endpoints, as the host proxy and the cluster name them. The
# mint URL is written into each slot's repository variables, so it is the
# in-cluster name the runners reach.
GITHUB_URL="https://github.local"
MINT_URL="https://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080"
CA_FILE="${PROJECT_ROOT}/deploy/fullsend-sandbox-local/internal-ca.crt"

# shellcheck source=/dev/null
source "${PROJECT_ROOT}/deploy/fullsend/behaviour/pool.env"

# The human test actors' tokens (TEST_ACTOR_WRITE_PAT, _TRIAGE_PAT,
# _OUTSIDER_PAT), written by `make bt-seed`. Without them the scenarios that
# act as those users fail with "TEST_ACTOR_..._PAT not set".
ACTORS_ENV="${PROJECT_ROOT}/deploy/fullsend/behaviour/.env.actors"
unset TEST_ACTOR_WRITE_PAT TEST_ACTOR_TRIAGE_PAT TEST_ACTOR_OUTSIDER_PAT
if [[ -f "${ACTORS_ENV}" ]]; then
  set -a
  # shellcheck source=/dev/null
  source "${ACTORS_ENV}"
  set +a
else
  echo "WARNING: ${ACTORS_ENV} is missing; run \`make bt-seed\` for the test actors" >&2
fi

python3 "${PROJECT_ROOT}/deploy/fullsend/behaviour/mint-pool.py" check

# The harness's own identity. In CI it acts as the e2e App's bot through an
# org-wide installation token, and dispatch routes on that: a bot's issue
# does not start triage, a bot's pull request goes straight to review. So it
# acts as the same App here (seeded by `make bt-seed`), with a token issued
# for this run, unless BT_GITHUB_TOKEN names someone else.
if [[ -n "${BT_GITHUB_TOKEN:-}" ]]; then
  HARNESS_TOKEN="${BT_GITHUB_TOKEN}"
else
  HARNESS_TOKEN="$(python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-behaviour-pool.py" e2e-token)"
fi

# The sandbox image the features' custom harnesses name. OpenShell creates
# sandbox pods with imagePullPolicy Never, so an image missing from k3s's
# store fails every harness run with ErrImageNeverPull after a two-minute
# wait. Serve it from the image the stack's own triage harness uses: the
# upstream sandbox plus the internal CA (deploy/fullsend-sandbox-local),
# built by 05i.
BT_SANDBOX_IMAGE="ghcr.io/fullsend-ai/fullsend-sandbox:latest"
LOCAL_SANDBOX_IMAGE="docker.io/library/fullsend-sandbox-local:k3s"
if ! sudo -n k3s ctr images tag --force "${LOCAL_SANDBOX_IMAGE}" "${BT_SANDBOX_IMAGE}" >/dev/null; then
  echo "tagging ${LOCAL_SANDBOX_IMAGE} as ${BT_SANDBOX_IMAGE} in k3s failed;" \
    "run deploy/scripts/05i-build-fullsend.sh, and allow sudo for k3s ctr" >&2
  exit 1
fi

# --- The tree under test -----------------------------------------------------
if git -C "${BT_SOURCE}" worktree list --porcelain | grep -qx "worktree ${TREE}"; then
  git -C "${BT_SOURCE}" worktree remove --force "${TREE}"
elif [[ -e "${TREE}" ]]; then
  echo "ERROR: ${TREE} exists but is not a worktree of ${BT_SOURCE}; remove it or set BT_WORKDIR" >&2
  exit 1
fi
git -C "${BT_SOURCE}" worktree prune
git -C "${BT_SOURCE}" worktree add --quiet --detach "${TREE}" HEAD
echo "==> Testing ${BT_SOURCE} at $(git -C "${TREE}" rev-parse --short HEAD)"

# The build list, read from 05i itself so the two never disagree.
FULLSEND_PATCHES=()
eval "$(sed -n '/^FULLSEND_PATCHES=(/,/^)/p' "${PROJECT_ROOT}/deploy/scripts/05i-build-fullsend.sh")"
if [[ ${#FULLSEND_PATCHES[@]} -eq 0 ]]; then
  echo "ERROR: could not read FULLSEND_PATCHES from 05i-build-fullsend.sh" >&2
  exit 1
fi
mapfile -t MIRROR_PATCHES < <(python3 - "${PROJECT_ROOT}/deploy/fullsend/seed/seed-upstream-fullsend.py" <<'PY'
import ast, re, sys
source = open(sys.argv[1]).read()
match = re.search(r"^MIRROR_PATCHES = (\([^)]*\))", source, re.MULTILINE)
for name in ast.literal_eval(match.group(1)):
    print(name)
PY
)

apply_patch() {
  local patch="$1"
  if ! git -C "${TREE}" apply --check --unidiff-zero "${patch}" 2>/dev/null; then
    echo "ERROR: $(basename "${patch}") does not apply to ${BT_SOURCE}" >&2
    exit 1
  fi
  git -C "${TREE}" apply --unidiff-zero "${patch}"
  echo "    applied $(basename "${patch}")"
}
echo "==> Applying the build, mirror and behaviour-test patches"
for patch in "${FULLSEND_PATCHES[@]}"; do apply_patch "${patch}"; done
for name in "${MIRROR_PATCHES[@]}"; do apply_patch "${PATCH_DIR}/${name}"; done
for patch in "${BT_PATCHES[@]}"; do apply_patch "${patch}"; done
git -C "${TREE}" add -A
git -C "${TREE}" -c user.name=breadboard -c user.email=breadboard@local \
  commit --quiet --no-verify -m "Breadboard patches for the behaviour-test run"

# --- TLS -----------------------------------------------------------------------
# Go trusts SSL_CERT_FILE alone when it is set, and the run still needs public
# roots (the module proxy, for the vendored cross-compile), so the stack CA is
# added to the system bundle rather than replacing it.
SYSTEM_BUNDLE=""
for candidate in /etc/pki/tls/certs/ca-bundle.crt /etc/ssl/certs/ca-certificates.crt; do
  [[ -f "${candidate}" ]] && SYSTEM_BUNDLE="${candidate}" && break
done
CA_BUNDLE="${BT_WORKDIR}/ca-bundle.pem"
cat ${SYSTEM_BUNDLE:+"${SYSTEM_BUNDLE}"} "${CA_FILE}" > "${CA_BUNDLE}"

# --- The run -------------------------------------------------------------------
# -buildvcs=false: the harness and the vendored install both run go build in
# the worktree, and Go's VCS stamping can pick the wrong repository root (a
# stray .git directory above the scratch directory is enough to fail every
# build). Nothing reads the stamp; the harness reads HEAD with git itself.
ARTIFACT_DIR="${BT_WORKDIR}/artifacts"
LOG="${BT_WORKDIR}/behaviour-test.log"
rm -rf "${ARTIFACT_DIR}"
mkdir -p "${ARTIFACT_DIR}"

if [[ -n "${BT_FULLSEND_REF:-}" ]]; then
  echo "==> Installing non-vendored at ${BT_FULLSEND_REF} (stage path)"
else
  echo "==> Installing vendored from the tree under test (pull-request path)"
fi

cd "${TREE}"
set +e
env -u GITHUB_ACTIONS -u GITHUB_TOKEN -u E2E_GCP_PROJECT_ID \
  ENVIRONMENT=external \
  GITHUB_API_URL="${GITHUB_URL}/api/v3" \
  GITHUB_SERVER_URL="${GITHUB_URL}" \
  GH_TOKEN="${HARNESS_TOKEN}" \
  FULLSEND_MINT_URL="${MINT_URL}" \
  FULLSEND_RUNNER_IMAGE=fullsend \
  BEHAVIOUR_APP_SET=fullsend \
  BEHAVIOUR_POOL_SIZE="${BT_POOL_SIZE}" \
  BEHAVIOUR_FULLSEND_REF="${BT_FULLSEND_REF:-}" \
  BEHAVIOUR_FEATURES="${BT_FEATURES:-}" \
  BEHAVIOUR_CAPABILITIES="" \
  BEHAVIOUR_ARTIFACT_DIR="${ARTIFACT_DIR}" \
  GODOG_TAGS="${BT_TAGS:-}" \
  GODOG_CONCURRENCY="${BT_CONCURRENCY:-1}" \
  SSL_CERT_FILE="${CA_BUNDLE}" \
  GOTOOLCHAIN=auto \
  GOFLAGS="${GOFLAGS:+${GOFLAGS} }-buildvcs=false" \
  go test -tags behaviour -race -v -count=1 -timeout "${BT_TIMEOUT:-45m}" ./e2e/behaviour/ 2>&1 | tee "${LOG}"
status=${PIPESTATUS[0]}
set -e
echo "==> Log: ${LOG}"
echo "==> Artifacts: ${ARTIFACT_DIR}"
exit "${status}"
