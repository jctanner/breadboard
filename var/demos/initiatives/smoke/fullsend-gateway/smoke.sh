#!/usr/bin/env bash
# CC-75 S2 smoke: strat-pipeline's job-owned Fullsend stack on the breadboard
# GitLab runner, without a model. Mirrors the parts of strat-creator's
# .fullsend/ci/run-fullsend.sh that precede `fullsend run`, then runs one
# sandbox command through strat-creator's own with-fullsend-gateway.sh.
set -Eeuo pipefail
export STRAT_PRIVATE_DIR="$CI_PROJECT_DIR/.private"
export FULLSEND_OUTPUT_DIR="$CI_PROJECT_DIR/smoke-output"
mkdir -p "$STRAT_PRIVATE_DIR/tools" "$FULLSEND_OUTPUT_DIR"
start=$(date +%s)
stamp() { echo "SMOKE_TIMING $1=$(( $(date +%s) - start ))s"; }

git clone -q --depth 1 --branch "$STRAT_CREATOR_REF" "$STRAT_CREATOR_URL" "$STRAT_PRIVATE_DIR/strat-creator"
git -C "$STRAT_PRIVATE_DIR/strat-creator" log -1 --format='SMOKE strat-creator %H'
set -a
# shellcheck disable=SC1091
. "$STRAT_PRIVATE_DIR/strat-creator/.fullsend/ci/fullsend-versions.env"
set +a
stamp clone

archive="$STRAT_PRIVATE_DIR/tools/fullsend.tar.gz"
curl -fsSL --retry 3 --output "$archive" \
  "https://github.com/fullsend-ai/fullsend/releases/download/v$FULLSEND_VERSION/fullsend_${FULLSEND_VERSION}_linux_amd64.tar.gz"
printf '%s  %s\n' "$FULLSEND_TARBALL_SHA256" "$archive" | sha256sum -c -
tar -xzf "$archive" -C "$STRAT_PRIVATE_DIR/tools" fullsend
export PATH="$STRAT_PRIVATE_DIR/tools:$PATH"
echo "SMOKE fullsend $(fullsend --version 2>&1 | head -1)"
stamp fullsend

cat >"$STRAT_PRIVATE_DIR/inner.sh" <<'EOF'
set -Eeuo pipefail
echo "SMOKE gateway ready; sandbox image $FULLSEND_SANDBOX_IMAGE"
openshell sandbox create --help >"$FULLSEND_OUTPUT_DIR/sandbox-create-help.txt" 2>&1 || true
t0=$(date +%s)
openshell sandbox create --name "smoke-$CI_JOB_ID" --from "$FULLSEND_SANDBOX_IMAGE" --no-keep \
  -- sh -c 'echo SANDBOX_OK; id -u; claude --version'
echo "SMOKE_TIMING sandbox=$(( $(date +%s) - t0 ))s"
EOF
bash "$STRAT_PRIVATE_DIR/strat-creator/.fullsend/ci/with-fullsend-gateway.sh" -- bash "$STRAT_PRIVATE_DIR/inner.sh"
stamp total
echo SMOKE_PASS
