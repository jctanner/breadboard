#!/bin/bash
# The rfe-autofixer mirror's sandbox: agentic-ci's OpenShell backend, the claude-sandbox image
# with the emulator CA baked into its system trust (as the patched runner builds it), the relay
# and Jira endpoints. Claude Code calls the relay with a placeholder key: success is an auth
# error from the relay (no model call), not a TLS error.
set -u
unset KUBERNETES_SERVICE_HOST KUBERNETES_SERVICE_PORT KUBERNETES_PORT
: > /etc/subuid; : > /etc/subgid
printf '[storage]\ndriver = "vfs"\n' > /etc/containers/storage.conf
for b in /etc/pki/tls/certs/ca-bundle.crt /etc/ssl/certs/ca-certificates.crt; do [ -f "$b" ] && break; done
cat "$b" /etc/gitlab-runner/certs/ca.crt > /tmp/cc75-ca-bundle.pem
mkdir -p /tmp/work && echo probe > /tmp/work/README
printf 'endpoints:\n  - "jira.w530.local:443:read-write"\n  - "relay-api.w530.local:443:read-write"\n' > /tmp/policy.yml
export ANTHROPIC_API_KEY=cc75-placeholder-not-a-key CC75_SANDBOX_CA_SRC=/tmp/cc75-ca-bundle.pem
python3 - <<'PY'
import os, shutil, subprocess, tempfile
from agentic_ci.backends import create_backend
from agentic_ci.backends.openshell import sandbox
from agentic_ci.harness import create_harness
base = "quay.io/aipcc/agentic-ci/claude-sandbox:0.3.46"
image = "localhost/cc75-claude-sandbox:0.3.46-ca"
ctx = tempfile.mkdtemp()
shutil.copy(os.environ["CC75_SANDBOX_CA_SRC"], os.path.join(ctx, "ca-bundle.pem"))
with open(os.path.join(ctx, "Containerfile"), "w") as f:
    cc_img = "ghcr.io/fullsend-ai/fullsend-sandbox@sha256:2fc886b02c280ccf11f317662d182a56cefa6f9299ca9cbd54e780fced743ca7"
    cc = "/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
    f.write(f"FROM {cc_img} AS claude-code\nFROM {base}\nCOPY --from=claude-code {cc} /usr/local/sbin/claude\n"
            f"COPY --from=claude-code {cc} /usr/local/bin/claude\n"
            "COPY ca-bundle.pem /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem\n")
subprocess.run(["podman", "build", "--quiet", "-t", image, ctx], check=True)
print("SMOKE built", image)
backend = create_backend("openshell", harness=create_harness("claude-code"), workdir="/tmp/work",
                         image=image, extra_env={}, policy="/tmp/policy.yml")
ok = False
try:
    backend.setup()
    print("SMOKE sandbox created from local image")
    subprocess.run(["openshell", "policy", "update", "--wait", "--binary", "/usr/bin/curl",
                    "--add-endpoint", "relay-api.w530.local:443:read-write",
                    "--add-endpoint", "jira.w530.local:443:read-write", "ci"], check=True)
    sandbox.exec_cmd(["bash", "-c", "for u in https://relay-api.w530.local/v1/models https://jira.w530.local/rest/api/2/serverInfo; do "
                      "echo CURL_PROBE $u $(curl -s -o /tmp/b -w '%{http_code} verify=%{ssl_verify_result}' $u 2>&1) $(head -c 160 /tmp/b); done"])
    probe = r'''
echo "== claude: $(claude --version 2>&1 | head -1)"; echo "== trust has emulator CA:"; grep -c "BEGIN CERTIFICATE" /etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem
cd /tmp && ANTHROPIC_BASE_URL=https://relay-api.w530.local ANTHROPIC_API_KEY=cc75-placeholder-not-a-key \
  CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC=1 timeout 120 claude -p "reply ok" --model claude-opus-5-5 \
  --output-format json >/tmp/c.json 2>/tmp/c.err
echo "claude rc=$?"
echo "CLAUDE_STDOUT $(head -c 700 /tmp/c.json)"
echo "CLAUDE_STDERR $(grep -v -e backup -e "restore it" -e "^$" /tmp/c.err | tail -4 | tr "\n" " " | head -c 600)"
'''
    sandbox.exec_cmd(["bash", "-c", probe])
    ok = True
finally:
    backend.stop()
print("SMOKE_DONE" if ok else "SMOKE_FAIL")
PY
