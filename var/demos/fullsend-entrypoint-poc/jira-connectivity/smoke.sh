#!/usr/bin/env bash
set -Eeuo pipefail
if [[ "${1:-}" == --inside ]]; then
  openshell settings set --global --key ocsf_json_enabled --value true --yes
  set +e
  fullsend run jira-probe --fullsend-dir "$STRAT_CREATOR_ROOT/.fullsend" --target-repo "$STRAT_CREATOR_ROOT" --output-dir "$CI_PROJECT_DIR/fullsend-run-output" >"$CI_PROJECT_DIR/fullsend-ci-artifacts/fullsend-run.log" 2>&1 &
  fullsend_pid=$!
  for attempt in {1..90}; do
    container=$(podman --url unix:///run/podman/podman.sock ps --format "{{.ID}} {{.Names}}" | awk '/fs-jir/ {print $1; exit}')
    if [[ -n "$container" ]]; then
      podman --url unix:///run/podman/podman.sock logs -f "$container" >"$CI_PROJECT_DIR/fullsend-ci-artifacts/supervisor-raw.log" 2>&1 &
      logs_pid=$!
      break
    fi
    sleep 1
  done
  wait "$fullsend_pid"
  rc=$?
  if [[ -n "${logs_pid:-}" ]]; then wait "$logs_pid"; fi
  timeout 30 podman --url unix:///run/podman/podman.sock run --rm \
    --network "$FULLSEND_OPENSHELL_NETWORK_NAME" \
    -v /etc/gitlab-runner/certs/ca.crt:/tmp/m42-ca.pem:ro \
    --entrypoint /bin/sh \
    ghcr.io/fullsend-ai/fullsend-sandbox@sha256:259605fea321353552fdefd3a6a55e8b5c260998dfc5a622ed143e41a429995a \
    -lc 'getent ahostsv4 jira.local; curl --cacert /tmp/m42-ca.pem -fsS -o /dev/null -w "%{http_code}\n" --max-time 8 https://jira.local/rest/api/3/serverInfo' \
    >"$CI_PROJECT_DIR/fullsend-ci-artifacts/unfiltered-container-network.txt" 2>&1
  printf '%s\n' "$?" >"$CI_PROJECT_DIR/fullsend-ci-artifacts/unfiltered-container-network-exit.txt"
  set -e
  cat "$CI_PROJECT_DIR/fullsend-ci-artifacts/fullsend-run.log"
  printf '%s\n' "$rc" >"$CI_PROJECT_DIR/fullsend-ci-artifacts/fullsend-run-exit.txt"
  exit "$rc"
fi
ROOT="$CI_PROJECT_DIR"
TARGET="$ROOT/target"
mkdir -p "$TARGET/.fullsend/scripts/ci" "$TARGET/.fullsend/profiles" "$TARGET/.fullsend/policies" "$TARGET/.fullsend/harness" "$TARGET/.fullsend/providers" "$TARGET/scripts" "$ROOT/fullsend-ci-artifacts"
cp "$ROOT/scripts/with-openshell.sh" "$ROOT/scripts/ca-bundle.sh" "$TARGET/.fullsend/scripts/ci/"
cp "$ROOT/scripts/m42-probe.py" "$TARGET/.fullsend/scripts/"
cp "$ROOT/scripts/jira_utils.py" "$TARGET/scripts/"
cp "$ROOT/policy.yaml" "$TARGET/.fullsend/policies/strategy.yaml"
cat >"$TARGET/.fullsend/config.yaml" <<'EOF'
version: "1"
agents:
  - name: jira-probe
    source: harness/jira-probe.yaml
EOF
cat >"$TARGET/.fullsend/scripts/m42-entrypoint.sh" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail
source "$PWD/.fullsend/scripts/ci/ca-bundle.sh"
fullsend_prepare_ca_bundle /tmp/m42-ca-bundle.pem
python3 "$PWD/.fullsend/scripts/m42-probe.py"
EOF
cat >"$TARGET/.fullsend/harness/jira-probe.yaml" <<'EOF'
entrypoint:
  command: [scripts/m42-entrypoint.sh]
  stream_format: none
role: triage
description: M4.2 read-only Jira connectivity verification
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
    M42_EXPECTED_JIRA_AUTH_MODE: "${M42_EXPECTED_JIRA_AUTH_MODE}"
EOF
chmod +x "$TARGET/.fullsend/scripts/m42-entrypoint.sh"
export FULLSEND_BUILD_DIR="$ROOT/fullsend-build"
export FULLSEND_CI_ARTIFACTS_DIR="$ROOT/fullsend-ci-artifacts"
export CI_JOB_ID="m42-$CI_JOB_ID"
export STRAT_CREATOR_ROOT="$TARGET"
export M42_EXPECTED_JIRA_AUTH_MODE="${M42_EXPECTED_JIRA_AUTH_MODE:-permissive}"
# The maintained runner receives credentials through masked project CI variables.
# Keep the old mounted-secret fallback for explicitly isolated experiments.
if [[ -r /var/run/secrets/jira/credentials.json ]]; then
  export JIRA_USER="$(python3 -c 'import json; print(json.load(open("/var/run/secrets/jira/credentials.json"))["user"])')"
  export JIRA_TOKEN="$(python3 -c 'import json; print(json.load(open("/var/run/secrets/jira/credentials.json"))["token"])')"
fi
: "${JIRA_USER:?Supply the restored Jira bot through masked CI variables}"
: "${JIRA_TOKEN:?Supply the restored Jira bot through masked CI variables}"
getent ahostsv4 jira.local >"$ROOT/fullsend-ci-artifacts/runner-dns.txt"
curl --cacert /etc/gitlab-runner/certs/ca.crt -fsS https://jira.local/rest/api/3/serverInfo >"$ROOT/fullsend-ci-artifacts/runner-jira.json"
bash "$TARGET/.fullsend/scripts/ci/with-openshell.sh" -- bash "$ROOT/scripts/m42-smoke.sh" --inside
