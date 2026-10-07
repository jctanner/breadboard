#!/usr/bin/env bash
# Run one native strat-creator agent with released Fullsend, then always
# release the locks the host pre-script recorded.
#
# Usage: strategy.sh strat-single|strat-batch
set -Eeuo pipefail

AGENT="${1:?usage: strategy.sh strat-single|strat-batch}"
case "$AGENT" in strat-single|strat-batch) ;; *) echo "unknown agent $AGENT" >&2; exit 2 ;; esac
: "${CI_PROJECT_DIR:?}" "${CI_JOB_ID:?}" "${FULLSEND_VERSION:?}" "${FULLSEND_TARBALL_SHA256:?}"
: "${VERTEX_CREDENTIALS_JSON:?}" "${ANTHROPIC_VERTEX_PROJECT_ID:?}"
: "${JIRA_SERVER:?}" "${JIRA_USER:?}" "${JIRA_TOKEN:?}"
if [[ "$AGENT" == strat-single ]]; then : "${RFE_KEY:?}"; fi

CI_SCRIPTS="$CI_PROJECT_DIR/ci-scripts"
TARGET="$CI_PROJECT_DIR/target"
ARTIFACTS="$CI_PROJECT_DIR/fullsend-ci-artifacts"
RUN_OUTPUT="$CI_PROJECT_DIR/fullsend-run-output"
TOOLS="$CI_PROJECT_DIR/.fullsend-tools"
mkdir -p "$ARTIFACTS" "$RUN_OUTPUT" "$TOOLS"
export FULLSEND_CI_ARTIFACTS_DIR="$ARTIFACTS"

# The harness pins the model; ambient CI overrides must not outrank it.
unset FULLSEND_MODEL FULLSEND_FALLBACK_MODELS ANTHROPIC_MODEL

# Released Fullsend, verified against the published checksum.
tarball="$TOOLS/fullsend_${FULLSEND_VERSION}_linux_amd64.tar.gz"
curl -fsSL --retry 3 -o "$tarball" \
  "https://github.com/fullsend-ai/fullsend/releases/download/v${FULLSEND_VERSION}/fullsend_${FULLSEND_VERSION}_linux_amd64.tar.gz"
echo "${FULLSEND_TARBALL_SHA256}  $tarball" | sha256sum -c -
tar -xzf "$tarball" -C "$TOOLS" fullsend
export PATH="$TOOLS:$PATH"
fullsend --version | tee "$ARTIFACTS/fullsend-version.txt"
sha256sum "$TOOLS/fullsend" | tee "$ARTIFACTS/fullsend-binary.sha256"

# Host-side Python dependencies for the validator (preflight_check) and helpers.
python3 -m pip install --quiet --disable-pip-version-check jsonschema pyyaml certifi diff-match-patch

# Host run state: the pre-script's run and lock record. Retained as evidence;
# it holds RFE keys only, never credentials. Not mounted in the sandbox.
export STRAT_RUN_ID="gitlab-job-$CI_JOB_ID"
export STRAT_STATE_DIR="$ARTIFACTS/strat-state"
export STRAT_LOCAL_CA_FILE=/etc/gitlab-runner/certs/ca.crt
export STRAT_PUBLISH_DIR="$CI_PROJECT_DIR/strat-publish"
export GOOGLE_CLOUD_PROJECT="${GOOGLE_CLOUD_PROJECT:-$ANTHROPIC_VERTEX_PROJECT_ID}"
export CLOUD_ML_REGION="${CLOUD_ML_REGION:-global}"
# Fullsend 0.43.0 rejects any ${VAR} the harness references that is unset on
# the host (empty is allowed), so define every optional one explicitly.
export RFE_KEY="${RFE_KEY:-}"
export BATCH_SIZE="${BATCH_SIZE:-}" BATCH_OFFSET="${BATCH_OFFSET:-}" BATCH_EXPECTED_KEYS="${BATCH_EXPECTED_KEYS:-}"
export STRAT_ARCHITECTURE_CONTEXT_PATH="${STRAT_ARCHITECTURE_CONTEXT_PATH:-}"
export RESULTS_REPO_URL="${RESULTS_REPO_URL:-}" RESULTS_GIT_USER="${RESULTS_GIT_USER:-}"
export RESULTS_PUSH_TOKEN="${RESULTS_PUSH_TOKEN:-}"
export ORG_PULSE_URL="${ORG_PULSE_URL:-}" ORG_PULSE_API_TOKEN="${ORG_PULSE_API_TOKEN:-}"
# Host Python (pre/post/validator) must trust both public and local CAs.
export SSL_CERT_FILE="$CI_PROJECT_DIR/.ci-ca-bundle.pem"
export REQUESTS_CA_BUNDLE="$SSL_CERT_FILE" GIT_SSL_CAINFO="$SSL_CERT_FILE"

# Job-local credential file, mounted into the sandbox by the harness.
export GOOGLE_APPLICATION_CREDENTIALS="$CI_PROJECT_DIR/.vertex-credentials.json"
trap 'rm -f "$GOOGLE_APPLICATION_CREDENTIALS"' EXIT
(
  umask 077
  python3 - <<'CREDENTIAL'
import base64, json, os
from pathlib import Path
raw = os.environ['VERTEX_CREDENTIALS_JSON']
try:
    credential = json.loads(raw)
except json.JSONDecodeError:
    credential = json.loads(base64.b64decode(raw))
if credential.get('type') not in ('authorized_user', 'service_account'):
    raise SystemExit('Unsupported Vertex credential type')
Path(os.environ['GOOGLE_APPLICATION_CREDENTIALS']).write_text(json.dumps(credential))
print(f"vertex credential type: {credential['type']}")
CREDENTIAL
)
unset VERTEX_CREDENTIALS_JSON

redact() { python3 -u "$CI_SCRIPTS/agent-led-redact.py" --stream; }

set +e
bash "$CI_SCRIPTS/agent-led-gateway.sh" -- \
  fullsend run "$AGENT" \
    --fullsend-dir "$TARGET/.fullsend" \
    --target-repo "$TARGET" \
    --output-dir "$RUN_OUTPUT" 2>&1 | redact
run_rc=${PIPESTATUS[0]}
echo "fullsend run exit status: $run_rc"

# Always release what the host recorded, whatever happened above.
bash "$TARGET/.fullsend/shared/release-locks.sh" "$STRAT_STATE_DIR" "$TARGET" 2>&1 | redact
release_rc=${PIPESTATUS[0]}
set -e
echo "release-locks exit status: $release_rc"

# Surface the outcome record next to the other job artifacts.
if [[ -f "$STRAT_STATE_DIR/preflight-result.json" ]]; then
  cp "$STRAT_STATE_DIR/preflight-result.json" "$ARTIFACTS/agent-result.json"
  echo "pre-script skipped the run; see agent-result.json"
else
  result="$(find "$RUN_OUTPUT" -path '*/iteration-*/output/agent-result.json' -type f 2>/dev/null | sort | tail -1)"
  [[ -z "$result" ]] || cp "$result" "$ARTIFACTS/agent-result.json"
fi
printf '{"fullsend_run_exit": %s, "release_locks_exit": %s}\n' "$run_rc" "$release_rc" \
  > "$ARTIFACTS/exit-status.json"

if [[ "$run_rc" -ne 0 ]]; then exit "$run_rc"; fi
exit "$release_rc"
