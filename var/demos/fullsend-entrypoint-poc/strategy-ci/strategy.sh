#!/usr/bin/env bash
set -Eeuo pipefail
: "${VERTEX_CREDENTIALS_JSON:?}" "${ANTHROPIC_VERTEX_PROJECT_ID:?}"
if [[ "${STRATEGY_MODE:-single-rfe}" == single-rfe ]]; then : "${RFE_KEY:?}"; fi
export BATCH_SIZE="${BATCH_SIZE:-}" BATCH_OFFSET="${BATCH_OFFSET:-}" BATCH_EXPECTED_KEYS="${BATCH_EXPECTED_KEYS:-}"
# Flags match the pinned harness and outrank ambient CI model overrides.
unset FULLSEND_MODEL FULLSEND_FALLBACK_MODELS ANTHROPIC_MODEL
export STRAT_CREATOR_ROOT="$CI_PROJECT_DIR/target"
export FULLSEND_BUILD_DIR="$CI_PROJECT_DIR/fullsend-build"
export FULLSEND_CI_ARTIFACTS_DIR="$CI_PROJECT_DIR/fullsend-ci-artifacts"
# Use a private, job-local file. Never archive the credential or target checkout.
export GOOGLE_APPLICATION_CREDENTIALS="$CI_PROJECT_DIR/.vertex-credentials.json"
trap 'rm -f "$GOOGLE_APPLICATION_CREDENTIALS"' EXIT
umask 077
python3 - <<'CREDENTIAL'
import base64,json,os
from pathlib import Path
raw=os.environ['VERTEX_CREDENTIALS_JSON']
try: credential=json.loads(raw)
except json.JSONDecodeError: credential=json.loads(base64.b64decode(raw))
if credential.get('type') != 'authorized_user':
    raise SystemExit('Expected the existing Breadboard Vertex ADC credential type')
Path(os.environ['GOOGLE_APPLICATION_CREDENTIALS']).write_text(json.dumps(credential))
CREDENTIAL
unset VERTEX_CREDENTIALS_JSON
agent=strategy
if [[ "${STRATEGY_MODE:-single-rfe}" == batch-discover ]]; then agent=batch-discover; fi

bash "$STRAT_CREATOR_ROOT/.fullsend/scripts/ci/with-openshell.sh" -- \
  fullsend run "$agent" --model claude-opus-4-6 --fullsend-dir "$STRAT_CREATOR_ROOT/.fullsend" \
  --target-repo "$STRAT_CREATOR_ROOT" --output-dir "$CI_PROJECT_DIR/fullsend-run-output" \
  2>&1 | python3 -u "$CI_PROJECT_DIR/ci-scripts/fullsend-redact.py" --stream
