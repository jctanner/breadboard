import json
import os
import subprocess

import httpx

NAMESPACE = "gitlab-runner"
RUNNER_NAME = "openshell-m42-k8s-runner"
BASE = os.environ.get("GITLAB_API_URL", "https://gitlab.local/api/v4")


def kubectl(*args, input_text=None):
    return subprocess.run(
        ["kubectl", *args], input=input_text, text=True, check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout


client = httpx.Client(verify=os.environ["GITLAB_CA_FILE"], timeout=20)
registered = client.post(
    f"{BASE}/runners",
    json={
        "token": os.environ["GITLAB_RUNNER_REGISTRATION_TOKEN"],
        "description": RUNNER_NAME,
        "tag_list": "m42-smoke",
        "run_untagged": False,
        "locked": False,
    },
)
registered.raise_for_status()
runner = registered.json()
runner_token = runner["token"]

jira_deployment = json.loads(kubectl("-n", "ai-pipeline", "get", "deployment", "jira-emulator", "-o", "json"))
env = {item["name"]: item.get("value") for item in jira_deployment["spec"]["template"]["spec"]["containers"][0]["env"]}
assert env.get("JIRA_USER") and env.get("JIRA_TOKEN"), "Jira credentials must be supplied from the deployed emulator"
credentials = {"apiVersion": "v1", "kind": "Secret", "metadata": {"name": "m42-jira-credentials", "namespace": NAMESPACE}, "stringData": {"credentials.json": json.dumps({"user": env["JIRA_USER"], "token": env["JIRA_TOKEN"]})}}
kubectl("apply", "-f", "-", input_text=json.dumps(credentials))

config = f'''concurrent = 1
check_interval = 3

[[runners]]
  name = "{RUNNER_NAME}"
  url = "https://gitlab-emulator.ai-pipeline.svc.cluster.local"
  token = "__RUNNER_TOKEN__"
  tls-ca-file = "/etc/gitlab-runner/certs/ca.crt"
  executor = "kubernetes"
  environment = ["GIT_SSL_CAINFO=/etc/gitlab-runner/certs/ca.crt", "JIRA_SERVER=https://jira.local", "M42_EXPECTED_JIRA_AUTH_MODE={env.get('AUTH_MODE', 'permissive')}"]

  [runners.kubernetes]
    namespace = "{NAMESPACE}"
    image = "quay.io/aipcc/agentic-ci/openshell:0.3.46"
    poll_timeout = 300
    service_account = "gitlab-runner"
    privileged = true

    [[runners.kubernetes.volumes.secret]]
      name = "gitlab-runner-ca"
      mount_path = "/etc/gitlab-runner/certs"
      read_only = true

    [[runners.kubernetes.volumes.secret]]
      name = "m42-jira-credentials"
      mount_path = "/var/run/secrets/jira"
      read_only = true

    [[runners.kubernetes.volumes.empty_dir]]
      name = "m42-podman-storage"
      mount_path = "/var/lib/containers"

    [[runners.kubernetes.volumes.empty_dir]]
      name = "m42-podman-run"
      mount_path = "/run/containers"
'''
config_map = {
    "apiVersion": "v1",
    "kind": "ConfigMap",
    "metadata": {"name": "openshell-m42-runner-config", "namespace": NAMESPACE},
    "data": {"config.toml": config},
}
secret = {
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {"name": "openshell-m42-runner-token", "namespace": NAMESPACE},
    "type": "Opaque",
    "stringData": {"token": runner_token},
}
deployment = {
    "apiVersion": "apps/v1",
    "kind": "Deployment",
    "metadata": {
        "name": "openshell-m42-gitlab-runner",
        "namespace": NAMESPACE,
        "labels": {"app.kubernetes.io/name": "openshell-m42-gitlab-runner"},
    },
    "spec": {
        "replicas": 1,
        "selector": {"matchLabels": {"app.kubernetes.io/name": "openshell-m42-gitlab-runner"}},
        "template": {
            "metadata": {"labels": {"app.kubernetes.io/name": "openshell-m42-gitlab-runner"}},
            "spec": {
                "serviceAccountName": "gitlab-runner",
                "containers": [{
                    "name": "gitlab-runner",
                    "image": "gitlab/gitlab-runner:v19.1.1",
                    "command": ["/bin/sh", "-ec"],
                    "args": [
                        "RUNNER_TOKEN=$(printf '%s' \"$OPENSHELL_M42_RUNNER_TOKEN\" | tr -d '\\r\\n'); sed \"s|__RUNNER_TOKEN__|$RUNNER_TOKEN|\" /runner-template/config.toml > /tmp/config.toml; exec gitlab-runner run --working-directory=/home/gitlab-runner --config=/tmp/config.toml --service=gitlab-runner --user=gitlab-runner"
                    ],
                    "env": [{
                        "name": "OPENSHELL_M42_RUNNER_TOKEN",
                        "valueFrom": {"secretKeyRef": {"name": "openshell-m42-runner-token", "key": "token"}},
                    }],
                    "volumeMounts": [
                        {"name": "runner-template", "mountPath": "/runner-template", "readOnly": True},
                        {"name": "runner-ca", "mountPath": "/etc/gitlab-runner/certs", "readOnly": True},
                    ],
                    "resources": {
                        "requests": {"memory": "128Mi", "cpu": "100m"},
                        "limits": {"memory": "256Mi", "cpu": "500m"},
                    },
                }],
                "volumes": [
                    {"name": "runner-template", "configMap": {"name": "openshell-m42-runner-config"}},
                    {"name": "runner-ca", "secret": {"secretName": "gitlab-runner-ca"}},
                ],
            },
        },
    },
}
documents = "\n---\n".join(json.dumps(item) for item in (config_map, secret, deployment))
kubectl("apply", "-f", "-", input_text=documents)
kubectl("-n", NAMESPACE, "rollout", "status", "deployment/openshell-m42-gitlab-runner", "--timeout=120s")
print(json.dumps({"runner": RUNNER_NAME, "registered": True, "temporary_jira_secret": "m42-jira-credentials"}))
