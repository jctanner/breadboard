#!/usr/bin/env python3
"""CC-75: Model Relay as an OpenShell provider; Jira as production does it (mirror branch only).

Kind: model-relay (OpenShell provider and profile for Model Relay; Jira kept on production's opaque tunnel)

Port of the proven corsair recipe in var/demos/fullsend-claude-workflow/ci/configure.py
(Fullsend 0.47.1) to strat-creator #124 on Fullsend 0.55.0:

  - providers/ + profiles/ for `model-relay` (ANTHROPIC_API_KEY <- ${CC75_RELAY_API_KEY}).
    OpenShell holds the key; the agent sees a placeholder. The profile allows the
    relay ingress only, TLS terminated, GET /v1/models and POST /v1/messages[...].
    Fullsend 0.55 loads providers from <fullsend-dir>/providers.
  - strat-single/batch/resume: host_files = only the CA bundle (no Google
    credential, no Vertex env file); providers [model-relay]; Messages API mode
    against the relay (CLAUDE_CODE_USE_VERTEX=0); STRAT_EXTRA_CA_FILE for the Jira
    client (Fullsend reserves SSL_CERT_FILE; see 0005).
  - Jira stays on production's own design (shared/policy.yaml: opaque `tls: skip`
    tunnel; "the repository's Python Jira client verifies the server certificate
    itself and sends JIRA_TOKEN"): add the in-cluster Jira emulator as one more
    opaque endpoint and keep JIRA_TOKEN in env.sandbox. The corsair recipe's
    TLS-terminating Jira provider fails here (CERTIFICATE_VERIFY_FAILED against the
    proxy certificate; S6 rerun, job 40).

Hosts: the relay's TLS ingress (relay-api.<domain>; the in-cluster relay port is
plain HTTP) and the Jira emulator's canonical URL jira.<domain> (cluster DNS
rewrites it to the TLS ingress), which matches JIRA_SERVER on host and sandbox.
It must be the canonical URL, as redhat.atlassian.net is in production: the
emulator returns attachment content URLs on its BASE_URL, and the live push
reads its attachment back (S7a, job 50: the in-cluster name was refused). The proxy verifies the relay with the CA baked
into the derived sandbox image (0004).
Usage: 0003-relay-jira-providers.py <tree> [domain]
"""
import sys
from pathlib import Path

import yaml

root = Path(sys.argv[1]) / ".fullsend"
domain = sys.argv[2] if len(sys.argv) > 2 else "w530.local"
RELAY_HOST = f"relay-api.{domain}"
JIRA_HOST = f"jira.{domain}"
AGENTS = ("strat-single", "strat-batch", "strat-resume")
MODEL_KEYS = ("ANTHROPIC_MODEL", "CLAUDE_CODE_SUBAGENT_MODEL", "ANTHROPIC_DEFAULT_OPUS_MODEL",
              "ANTHROPIC_DEFAULT_SONNET_MODEL", "ANTHROPIC_DEFAULT_HAIKU_MODEL", "ANTHROPIC_DEFAULT_FABLE_MODEL")

definitions = (
    ("model-relay", "local-model-relay", "ANTHROPIC_API_KEY", "CC75_RELAY_API_KEY", RELAY_HOST,
     ["**/claude", "**/node", "**/python3*", "/usr/lib/node_modules/@anthropic-ai/claude-code/bin/claude.exe"],
     [{"allow": {"method": "GET", "path": "/v1/models"}},
      {"allow": {"method": "POST", "path": "/v1/messages"}},
      {"allow": {"method": "POST", "path": "/v1/messages/count_tokens"}}]),
)
(root / "profiles").mkdir(exist_ok=True)
(root / "providers").mkdir(exist_ok=True)
for name, profile_id, env, source_env, host, binaries, rules in definitions:
    profile = {"id": profile_id, "display_name": name,
               "category": "inference" if name == "model-relay" else "data",
               "credentials": [{"name": env, "env_vars": [env], "required": True}],
               "endpoints": [{"host": host, "port": 443, "protocol": "rest",
                              "enforcement": "enforce", "rules": rules}],
               "binaries": binaries}
    (root / "profiles" / f"{name}.yaml").write_text(yaml.safe_dump(profile, sort_keys=False))
    (root / "providers" / f"{name}.yaml").write_text(yaml.safe_dump(
        {"name": name, "type": profile_id, "credentials": {env: "${" + source_env + "}"}}, sort_keys=False))

for agent in AGENTS:
    path = root / agent / f"{agent}.yaml"
    h = yaml.safe_load(path.read_text())
    model = h["model"]
    # No raw Google credential or Vertex env file; only the emulator CA for the Jira client.
    h["host_files"] = [{"src": "${CC75_SANDBOX_CA}", "dest": "/tmp/.cc75-ca.pem"}]
    h["providers"] = ["model-relay"]
    h["openshell"] = {"profiles": ["profiles/model-relay.yaml"]}
    sandbox = h["env"]["sandbox"]
    sandbox.update({
        "STRAT_EXTRA_CA_FILE": "/tmp/.cc75-ca.pem",
        "ANTHROPIC_BASE_URL": f"https://{RELAY_HOST}",
        "CLAUDE_CODE_USE_VERTEX": "0",
        "CLAUDE_CODE_USE_BEDROCK": "0",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY": "1",
        "ANTHROPIC_CUSTOM_HEADERS": "x-shim-run-id: ${STRAT_RUN_ID}",
    })
    for key in MODEL_KEYS:
        sandbox[key] = model
    path.write_text(yaml.safe_dump(h, sort_keys=False))

policy_file = root / "shared/policy.yaml"
text = policy_file.read_text()
if not text.rstrip().splitlines()[-1].startswith("    - path:"):
    raise SystemExit(f"{policy_file}: unexpected tail; review the patch")
policy_file.write_text(text.rstrip("\n") + f"""
  # CC-75 emulator mirror only: the in-cluster Jira emulator, as production treats Jira.
  cc75_jira_emulator:
    name: cc75-jira-emulator
    endpoints:
    - host: {JIRA_HOST}
      port: 443
      tls: skip
    binaries:
    - path: '**/python3*'
""")
print(f"strat-creator 0003-relay-provider: applied (relay provider {RELAY_HOST}; Jira opaque tunnel {JIRA_HOST})")
