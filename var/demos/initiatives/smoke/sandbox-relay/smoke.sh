#!/usr/bin/env bash
# CC-75: reproduce strat-batch's sandboxed Claude auth through Model Relay without
# the Fullsend harness. Uses strat-creator cc75-emulator's own shared/policy.yaml
# (plus a probe-only python3 rule for the token endpoint), the CI File variables
# GOOGLE_APPLICATION_CREDENTIALS (external_account ADC) and CC75_RELAY_WORKLOAD_KEY,
# and the harness's in-sandbox paths. One `claude -p` call of a few tokens.
set -Eeuo pipefail
export STRAT_PRIVATE_DIR="$CI_PROJECT_DIR/.private"
export FULLSEND_OUTPUT_DIR="$CI_PROJECT_DIR/smoke-output"
mkdir -p "$STRAT_PRIVATE_DIR" "$FULLSEND_OUTPUT_DIR"
: "${GOOGLE_APPLICATION_CREDENTIALS:?}" "${CC75_RELAY_WORKLOAD_KEY:?}"
export GCP_PROJECT_ID="${GCP_PROJECT_ID:-cc75-initiatives}"
git clone -q --depth 1 --branch "$STRAT_CREATOR_REF" "$STRAT_CREATOR_URL" "$STRAT_PRIVATE_DIR/strat-creator"
SC="$STRAT_PRIVATE_DIR/strat-creator"
git -C "$SC" log -1 --format='SMOKE strat-creator %H'
set -a
# shellcheck disable=SC1091
. "$SC/.fullsend/ci/fullsend-versions.env"
set +a
pol="$STRAT_PRIVATE_DIR/policy.yaml"
cp "$SC/.fullsend/shared/policy.yaml" "$pol"
cat >>"$pol" <<'EOF'
  cc75_probe_python:
    name: cc75-probe-python
    endpoints:
    - host: model-relay.ai-pipeline.svc.cluster.local
      port: 8082
      tls: skip
    binaries:
    - path: '**/python3*'
EOF
grep -c "cc75-model-relay" "$pol" | sed 's/^/SMOKE relay policy groups: /'

cat >"$STRAT_PRIVATE_DIR/probe.sh" <<'EOF'
set -u
echo "$1" | base64 -d > /tmp/.cc75-relay-workload-key
echo "$2" | base64 -d > /tmp/.gcp-credentials.json
PROJECT="$3"
python3 - <<'PY'
import json, urllib.parse, urllib.request, urllib.error
adc = json.load(open("/tmp/.gcp-credentials.json"))
key = open(adc["credential_source"]["file"]).read().strip()
TT = "urn:ietf:params:oauth:token-type:access_token"
body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
    "scope": "https://www.googleapis.com/auth/cloud-platform", "requested_token_type": TT,
    "subject_token_type": TT, "audience": adc["audience"], "subject_token": key}).encode()
try:
    with urllib.request.urlopen(urllib.request.Request(adc["token_url"], data=body), timeout=20) as r:
        print("PROBE python_token_exchange", r.status, flush=True)
except urllib.error.HTTPError as e:
    print("PROBE python_token_exchange", e.code, flush=True)
except Exception as e:
    print("PROBE python_token_exchange ERR", type(e).__name__, str(e)[:150], flush=True)
PY
c=$(command -v claude || true)
echo "PROBE claude_path ${c:-missing} -> $(readlink -f "${c:-/dev/null}")"
echo "PROBE proxy_vars $(env | grep -i -E '^(https?|no|all)_proxy=' | cut -d= -f1 | sort | tr '\n' ' ')"
echo "PROBE no_proxy_has_cluster $(env | grep -i '^no_proxy=' | grep -c -E 'svc|cluster.local|model-relay')"
export CLAUDE_CODE_USE_VERTEX=1 ANTHROPIC_VERTEX_PROJECT_ID="$PROJECT" GOOGLE_CLOUD_PROJECT="$PROJECT" \
  CLOUD_ML_REGION=global GOOGLE_APPLICATION_CREDENTIALS=/tmp/.gcp-credentials.json NO_GCE_CHECK=true \
  METADATA_SERVER_DETECTION=none DISABLE_AUTOUPDATER=1 \
  ANTHROPIC_VERTEX_BASE_URL=http://model-relay.ai-pipeline.svc.cluster.local:8080/v1
cd /tmp && claude -p "Reply with the single word OK." --model claude-opus-5-5 --debug >/tmp/out.txt 2>/tmp/dbg.txt
echo "PROBE claude_exit $? output=$(head -c 40 /tmp/out.txt | tr '\n' ' ')"
dbgf=$(ls -t "$HOME"/.claude/debug/*.txt /sandbox/claude-config/debug/*.txt 2>/dev/null | head -1)
echo "PROBE debug_file ${dbgf:-none}"
[ -n "$dbgf" ] && grep -n -i -B3 -A3 -E "oauth|credential|external|sts|token_url|gaxios|ECONN|EAI_|proxy|fetch failed|403|401|subject" "$dbgf" \
  | grep -v -i -E "bearer [a-z0-9._-]{16,}|access_token\"?:|subject_token=" | head -40 | sed 's/^/PROBE dbg /' | cut -c1-300
# A/B: exchange in Python, hand Claude the short-lived token, skip Claude's own Google auth.
TOKEN=$(python3 - <<'PY'
import json, urllib.parse, urllib.request
adc = json.load(open("/tmp/.gcp-credentials.json")); TT = "urn:ietf:params:oauth:token-type:access_token"
key = open(adc["credential_source"]["file"]).read().strip()
body = urllib.parse.urlencode({"grant_type": "urn:ietf:params:oauth:grant-type:token-exchange",
    "scope": "https://www.googleapis.com/auth/cloud-platform", "requested_token_type": TT,
    "subject_token_type": TT, "audience": adc["audience"], "subject_token": key}).encode()
print(json.load(urllib.request.urlopen(urllib.request.Request(adc["token_url"], data=body), timeout=20))["access_token"])
PY
)
CLAUDE_CODE_SKIP_VERTEX_AUTH=1 ANTHROPIC_CUSTOM_HEADERS="Authorization: Bearer $TOKEN" \
  claude -p "Reply with the single word OK." --model claude-opus-5-5 >/tmp/out2.txt 2>/tmp/dbg2.txt
echo "PROBE claude_skip_auth_exit $? output=$(head -c 40 /tmp/out2.txt | tr '\n' ' ')"
unset TOKEN
EOF

cat >"$STRAT_PRIVATE_DIR/inner.sh" <<'EOF'
set -Euo pipefail
script=$(base64 -w0 "$STRAT_PRIVATE_DIR/probe.sh")
key=$(base64 -w0 "$CC75_RELAY_WORKLOAD_KEY")
adc=$(base64 -w0 "$GOOGLE_APPLICATION_CREDENTIALS")
openshell sandbox create --name "relay-$CI_JOB_ID" --from "$FULLSEND_SANDBOX_IMAGE" --no-keep \
  --policy "$STRAT_PRIVATE_DIR/policy.yaml" \
  -- sh -c 'echo "$0" | base64 -d > /tmp/p.sh && sh /tmp/p.sh "$1" "$2" "$3"' "$script" "$key" "$adc" "$GCP_PROJECT_ID" \
  || echo "SMOKE create_exit=$?"
EOF
bash "$SC/.fullsend/ci/with-fullsend-gateway.sh" -- bash "$STRAT_PRIVATE_DIR/inner.sh"
echo SMOKE_PASS
