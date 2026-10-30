#!/usr/bin/env bash
# Stock Fullsend, native Claude Workflow, one validation iteration.
set -Eeuo pipefail
MODE="${1:?usage: strategy.sh strat-single|strat-batch|preflight}"
case "$MODE" in strat-single|strat-batch|preflight) ;; *) exit 2 ;; esac
: "${CI_PROJECT_DIR:?}" "${CI_JOB_ID:?}" "${FULLSEND_VERSION:?}" "${FULLSEND_TARBALL_SHA256:?}"
: "${MODEL_RELAY_API_KEY:?}" "${JIRA_SERVER:?}" "${JIRA_USER:?}" "${JIRA_TOKEN:?}"
if [[ "$MODE" == strat-single ]]; then : "${RFE_KEY:?}"; fi
[[ "$JIRA_SERVER" == https://jira.local ]] || { echo 'Expected the local Jira fixture' >&2; exit 2; }
export CI_SCRIPTS="$CI_PROJECT_DIR/ci-scripts" TARGET="$CI_PROJECT_DIR/target"
export FULLSEND_CI_ARTIFACTS_DIR="$CI_PROJECT_DIR/fullsend-ci-artifacts"
export RUN_OUTPUT="$CI_PROJECT_DIR/fullsend-run-output"
TOOLS="$CI_PROJECT_DIR/.fullsend-tools"
mkdir -p "$FULLSEND_CI_ARTIFACTS_DIR" "$RUN_OUTPUT" "$TOOLS" "$CI_PROJECT_DIR/.sandbox-build"
cp "$CI_PROJECT_DIR/.ci-ca-bundle.pem" "$CI_PROJECT_DIR/.sandbox-build/ca-bundle.pem"
export SSL_CERT_FILE="$CI_PROJECT_DIR/.ci-ca-bundle.pem"
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE" GIT_SSL_CAINFO="$SSL_CERT_FILE"
# Do not inherit the previous POC's upstream credentials or model overrides.
unset FULLSEND_MODEL FULLSEND_FALLBACK_MODELS FULLSEND_RUNTIME ANTHROPIC_MODEL
unset VERTEX_CREDENTIALS_JSON RHAISTRAT_VERTEX_ADC GOOGLE_APPLICATION_CREDENTIALS
unset CLAUDE_CODE_USE_VERTEX ANTHROPIC_VERTEX_PROJECT_ID ANTHROPIC_VERTEX_BASE_URL
unset ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL

tarball="$TOOLS/fullsend_${FULLSEND_VERSION}_linux_amd64.tar.gz"
curl -fsSL --retry 3 -o "$tarball" \
  "https://github.com/fullsend-ai/fullsend/releases/download/v${FULLSEND_VERSION}/fullsend_${FULLSEND_VERSION}_linux_amd64.tar.gz"
echo "${FULLSEND_TARBALL_SHA256}  $tarball" | sha256sum -c -
tar -xzf "$tarball" -C "$TOOLS" fullsend
export PATH="$TOOLS:$PATH"
fullsend --version >"$FULLSEND_CI_ARTIFACTS_DIR/fullsend-version.txt"
sha256sum "$TOOLS/fullsend" >"$FULLSEND_CI_ARTIFACTS_DIR/fullsend-binary.sha256"
python3 -m pip install --quiet --disable-pip-version-check jsonschema==4.26.0 pyyaml==6.0.3 certifi==2026.4.22 diff-match-patch==20241021

export STRAT_RUN_ID="gitlab-job-$CI_JOB_ID"
export STRAT_STATE_DIR="$FULLSEND_CI_ARTIFACTS_DIR/strat-state"
export STRAT_CREATOR_REF="${STRAT_CREATOR_SHA:?}"
export STRAT_PUBLISH_DIR="$CI_PROJECT_DIR/strat-publish"
export RFE_KEY="${RFE_KEY:-}" BATCH_SIZE="${BATCH_SIZE:-}" BATCH_OFFSET="${BATCH_OFFSET:-}"
export BATCH_EXPECTED_KEYS="${BATCH_EXPECTED_KEYS:-}" STRAT_DRY_RUN="${STRAT_DRY_RUN:-0}"
export STRAT_PREVIOUS_PROGRESS="${STRAT_PREVIOUS_PROGRESS:-}"
# Reuse the benchmark's pinned subset, without cone-mode sibling symlinks to
# excluded versions. Skills keep RFE_SKIP_BOOTSTRAP=1 inside the sandbox.
export CONTEXT_SNAPSHOT_ROOT="$CI_PROJECT_DIR/.architecture-snapshots"
bash "$CI_SCRIPTS/workflow-snapshot-architecture-context.sh" "${ARCHITECTURE_CONTEXT_SHA:?}"
export STRAT_ARCHITECTURE_CONTEXT_PATH="$CONTEXT_SNAPSHOT_ROOT/$ARCHITECTURE_CONTEXT_SHA"
cp "$STRAT_ARCHITECTURE_CONTEXT_PATH/SNAPSHOT.json" "$FULLSEND_CI_ARTIFACTS_DIR/architecture-snapshot.json"
export RESULTS_REPO_URL="${RESULTS_REPO_URL:-}" RESULTS_GIT_USER="${RESULTS_GIT_USER:-}"
export RESULTS_PUSH_TOKEN="${RESULTS_PUSH_TOKEN:-}"
export ORG_PULSE_URL="${ORG_PULSE_URL:-}" ORG_PULSE_API_TOKEN="${ORG_PULSE_API_TOKEN:-}"
export WORKFLOW_MODEL="${WORKFLOW_MODEL:-claude-opus-4-6}"
export WORKFLOW_EFFORT="${WORKFLOW_EFFORT:-high}" WORKFLOW_CONCURRENCY="${WORKFLOW_CONCURRENCY:-10}"

redact() { python3 -u "$CI_SCRIPTS/workflow-redact.py" --stream; }
set +e
bash "$CI_SCRIPTS/workflow-gateway.sh" -- bash "$CI_SCRIPTS/workflow-launch.sh" "$MODE" 2>&1 | redact
run_rc=${PIPESTATUS[0]}
# Release only the claims recorded by this run, including on native failures.
bash "$TARGET/.fullsend/shared/release-locks.sh" "$STRAT_STATE_DIR" "$TARGET" 2>&1 | redact
release_rc=${PIPESTATUS[0]}
set -e
printf '{"fullsend_run_exit":%s,"release_locks_exit":%s}\n' "$run_rc" "$release_rc" \
  >"$FULLSEND_CI_ARTIFACTS_DIR/exit-status.json"
[[ "$run_rc" -eq 0 ]] || exit "$run_rc"
exit "$release_rc"
