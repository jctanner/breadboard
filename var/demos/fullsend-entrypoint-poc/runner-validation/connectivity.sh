#!/usr/bin/env bash
set -Eeuo pipefail
export M6_HOLD_SECONDS="${M6_HOLD_SECONDS:-0}"
export STRAT_CREATOR_ROOT="$CI_PROJECT_DIR/target"
export FULLSEND_BUILD_DIR="$CI_PROJECT_DIR/fullsend-build"
export FULLSEND_CI_ARTIFACTS_DIR="$CI_PROJECT_DIR/fullsend-ci-artifacts"
if [[ -n "${M6_REDACTION_TEST_SECRET:-}" ]]; then
  printf '%s\n' "$M6_REDACTION_TEST_SECRET" > "$FULLSEND_CI_ARTIFACTS_DIR/redaction-fixture.txt"
fi
# An additional diagnostic entrypoint uses the unchanged fetched strategy policy.
cp "$CI_PROJECT_DIR/ci-scripts/fullsend-connectivity.py" "$STRAT_CREATOR_ROOT/.fullsend/scripts/connectivity.py"
cat > "$STRAT_CREATOR_ROOT/.fullsend/scripts/connectivity.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -Eeuo pipefail
source "$PWD/.fullsend/scripts/ci/ca-bundle.sh"
fullsend_prepare_ca_bundle /tmp/m6-ca-bundle.pem
python3 "$PWD/.fullsend/scripts/connectivity.py"
SCRIPT
chmod +x "$STRAT_CREATOR_ROOT/.fullsend/scripts/connectivity.sh"
cat >> "$STRAT_CREATOR_ROOT/.fullsend/config.yaml" <<'CONFIG'
  - name: connectivity
    source: harness/connectivity.yaml
CONFIG
cat > "$STRAT_CREATOR_ROOT/.fullsend/harness/connectivity.yaml" <<'HARNESS'
entrypoint:
  command: [scripts/connectivity.sh]
  stream_format: none
role: triage
description: M6 read-only connectivity check
image: ghcr.io/fullsend-ai/fullsend-sandbox@sha256:259605fea321353552fdefd3a6a55e8b5c260998dfc5a622ed143e41a429995a
policy: policies/strategy.yaml
timeout_minutes: 5
sandbox_timeout_seconds: 300
host_files:
  - src: /etc/gitlab-runner/certs/ca.crt
    dest: /tmp/gitlab-ca.crt
env:
  sandbox:
    JIRA_SERVER: "${JIRA_SERVER}"
    JIRA_USER: "${JIRA_USER}"
    JIRA_TOKEN: "${JIRA_TOKEN}"
    RESULTS_PUSH_TOKEN: "${RESULTS_PUSH_TOKEN}"
    M6_HOLD_SECONDS: "${M6_HOLD_SECONDS}"
HARNESS
if [[ "${M6_LIFECYCLE:-}" == timeout ]]; then
  sed -i 's/timeout_minutes: 5/timeout_minutes: 1/' "$STRAT_CREATOR_ROOT/.fullsend/harness/connectivity.yaml"
fi
bash "$STRAT_CREATOR_ROOT/.fullsend/scripts/ci/with-openshell.sh" -- \
 fullsend run connectivity --fullsend-dir "$STRAT_CREATOR_ROOT/.fullsend" \
 --target-repo "$STRAT_CREATOR_ROOT" --output-dir "$CI_PROJECT_DIR/fullsend-run-output" \
  2>&1 | python3 -u "$CI_PROJECT_DIR/ci-scripts/fullsend-redact.py" --stream
