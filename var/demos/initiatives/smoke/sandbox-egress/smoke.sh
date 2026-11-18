#!/usr/bin/env bash
# CC-75 sandbox egress probe (no model). Builds strat-creator's per-job gateway
# and sandbox image, then starts sandboxes whose policy is strat-creator's own
# shared/policy.yaml plus candidate endpoints for the in-cluster Jira emulator
# and Model Relay, and probes them from inside. Variants differ only in how the
# plain-HTTP relay ports are declared.
set -Eeuo pipefail
export STRAT_PRIVATE_DIR="$CI_PROJECT_DIR/.private"
export FULLSEND_OUTPUT_DIR="$CI_PROJECT_DIR/smoke-output"
mkdir -p "$STRAT_PRIVATE_DIR/tools" "$FULLSEND_OUTPUT_DIR"
git clone -q --depth 1 --branch "$STRAT_CREATOR_REF" "$STRAT_CREATOR_URL" "$STRAT_PRIVATE_DIR/strat-creator"
SC="$STRAT_PRIVATE_DIR/strat-creator"
git -C "$SC" log -1 --format='SMOKE strat-creator %H'
set -a
# shellcheck disable=SC1091
. "$SC/.fullsend/ci/fullsend-versions.env"
set +a

# CA bundle for the sandbox: public roots plus the runner-mounted emulator CA.
roots=/etc/pki/tls/certs/ca-bundle.crt
[ -f "$roots" ] || roots=/etc/ssl/certs/ca-certificates.crt
cat "$roots" /etc/gitlab-runner/certs/ca.crt >"$STRAT_PRIVATE_DIR/cc75-ca.pem"

JIRA_HOST=jira-emulator.ai-pipeline.svc.cluster.local
RELAY_HOST=model-relay.ai-pipeline.svc.cluster.local
policy() {  # $1 = variant name, $2 = extra endpoint keys for the relay ports
  local out="$STRAT_PRIVATE_DIR/policy-$1.yaml"
  cp "$SC/.fullsend/shared/policy.yaml" "$out"
  cat >>"$out" <<EOF
  cc75_jira_emulator:
    name: cc75-jira-emulator
    endpoints:
    - host: $JIRA_HOST
      port: 443
      tls: skip
    binaries:
    - path: '**/python3*'
  cc75_model_relay:
    name: cc75-model-relay
    endpoints:
    - host: $RELAY_HOST
      port: 8080
$2
    - host: $RELAY_HOST
      port: 8082
$2
    binaries:
    - path: '**/claude'
    - path: '**/node'
    - path: '**/python3*'
EOF
  echo "$out"
}
P_SKIP=$(policy skip "      tls: skip")
P_DEFAULT=$(policy default "      protocol: rest")

cat >"$STRAT_PRIVATE_DIR/probe.py" <<'EOF'
import base64, json, os, ssl, sys, urllib.request, urllib.error
open("/tmp/cc75-ca.pem", "wb").write(base64.b64decode(sys.argv[1]))
ctx = ssl.create_default_context(cafile="/tmp/cc75-ca.pem")
def probe(name, url, data=None, context=None):
    try:
        req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
        with urllib.request.urlopen(req, timeout=20, context=context) as r:
            result = r.status
    except urllib.error.HTTPError as e:
        result = e.code
    except Exception as e:
        result = f"ERR {type(e).__name__}: {str(e)[:120]}"
    print(f"PROBE {name} {result}", flush=True)
probe("jira_https", "https://jira-emulator.ai-pipeline.svc.cluster.local/rest/api/2/serverInfo", context=ctx)
probe("relay_8080_health", "http://model-relay.ai-pipeline.svc.cluster.local:8080/health")
probe("relay_8082_token", "http://model-relay.ai-pipeline.svc.cluster.local:8082/v1/token", data=b"{}")
probe("denied_example", "https://example.com/", context=ctx)
print("PROBE proxy_env " + json.dumps({k: bool(os.environ.get(k)) for k in ("HTTPS_PROXY", "HTTP_PROXY", "https_proxy", "http_proxy", "NO_PROXY")}))
EOF

cat >"$STRAT_PRIVATE_DIR/inner.sh" <<'EOF'
set -Euo pipefail
echo "SMOKE policy flags:"; openshell sandbox create --help 2>&1 | grep -i -E "^\s*--policy|policy" | head -8 | sed 's/^/SMOKE   /'
ca_b64=$(base64 -w0 /etc/gitlab-runner/certs/ca.crt)
probe=$(cat "$STRAT_PRIVATE_DIR/probe.py")
for variant in skip default; do
  pol="$STRAT_PRIVATE_DIR/policy-$variant.yaml"
  echo "SMOKE variant=$variant"
  openshell sandbox create --name "egress-$variant-$CI_JOB_ID" --from "$FULLSEND_SANDBOX_IMAGE" --no-keep \
    --policy "$pol" \
    -- python3 -c "$probe" "$ca_b64" 2>&1 | sed "s/^PROBE /PROBE $variant /" || echo "SMOKE variant=$variant create_exit=$?"
done
EOF
bash "$SC/.fullsend/ci/with-fullsend-gateway.sh" -- bash "$STRAT_PRIVATE_DIR/inner.sh"
echo SMOKE_PASS
