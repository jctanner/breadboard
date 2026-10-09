#!/usr/bin/env bash
set -Eeuo pipefail
export STRAT_CREATOR_ROOT="$CI_PROJECT_DIR/target"
export FULLSEND_BUILD_DIR="$CI_PROJECT_DIR/fullsend-build"
export FULLSEND_CI_ARTIFACTS_DIR="$CI_PROJECT_DIR/fullsend-ci-artifacts"
# A no-model entrypoint runs the pinned fetch script under the unchanged
# strategy policy and image; it receives no Jira, results or Vertex credentials.
cp "$CI_PROJECT_DIR/ci-scripts/fullsend-architecture-fetch.py" "$STRAT_CREATOR_ROOT/.fullsend/scripts/architecture-fetch.py"
cat > "$STRAT_CREATOR_ROOT/.fullsend/scripts/architecture-fetch.sh" <<'SCRIPT'
#!/usr/bin/env bash
set -Eeuo pipefail
source "$PWD/.fullsend/scripts/ci/ca-bundle.sh"
fullsend_prepare_ca_bundle /tmp/architecture-fetch-ca.pem
python3 "$PWD/.fullsend/scripts/architecture-fetch.py"
SCRIPT
chmod +x "$STRAT_CREATOR_ROOT/.fullsend/scripts/architecture-fetch.sh"
cat >> "$STRAT_CREATOR_ROOT/.fullsend/config.yaml" <<'CONFIG'
  - name: architecture-fetch
    source: harness/architecture-fetch.yaml
CONFIG
image=$(sed -n 's/^image: //p' "$STRAT_CREATOR_ROOT/.fullsend/harness/strategy.yaml")
policy=$(sed -n 's/^policy: //p' "$STRAT_CREATOR_ROOT/.fullsend/harness/strategy.yaml")
cat > "$STRAT_CREATOR_ROOT/.fullsend/harness/architecture-fetch.yaml" <<HARNESS
entrypoint:
  command: [scripts/architecture-fetch.sh]
  stream_format: none
role: triage
description: Architecture-context fetch check, no model
image: ${image}
policy: ${policy}
timeout_minutes: 5
sandbox_timeout_seconds: 300
host_files:
  - src: /etc/gitlab-runner/certs/ca.crt
    dest: /tmp/gitlab-ca.crt
HARNESS
bash "$STRAT_CREATOR_ROOT/.fullsend/scripts/ci/with-openshell.sh" -- \
 fullsend run architecture-fetch --fullsend-dir "$STRAT_CREATOR_ROOT/.fullsend" \
 --target-repo "$STRAT_CREATOR_ROOT" --output-dir "$CI_PROJECT_DIR/fullsend-run-output" \
  2>&1 | python3 -u "$CI_PROJECT_DIR/ci-scripts/fullsend-redact.py" --stream
