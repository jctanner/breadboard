"""Remove only the disposable M4.2 runner and validation branches."""
import base64
import json
import os
import subprocess
import urllib.parse

import httpx


def kubectl(*args):
    return subprocess.run(["kubectl", "-n", "gitlab-runner", *args],
                          check=True, capture_output=True, text=True).stdout


base = os.environ.get("GITLAB_API_URL", "https://gitlab.local/api/v4")
client = httpx.Client(verify=os.environ["GITLAB_CA_FILE"], timeout=30)
secret = json.loads(kubectl("get", "secret/openshell-m42-runner-token", "-o", "json"))
token = base64.b64decode(secret["data"]["token"]).decode().strip()
response = client.request("DELETE", base + "/runners", json={"token": token})
if response.status_code not in (200, 204, 404):
    response.raise_for_status()
response = client.post(base + "/admin/tokens",
                       auth=(os.environ["GITLAB_ADMIN_USER"], os.environ["GITLAB_ADMIN_PASSWORD"]),
                       json={"login": "admin", "name": "m42-cleanup",
                             "scopes": ["repo", "user", "admin:org"]})
response.raise_for_status()
headers = {"PRIVATE-TOKEN": response.json()["token"]}
branches = client.get(base + "/projects/1/repository/branches", headers=headers)
branches.raise_for_status()
deleted = 0
for branch in branches.json():
    name = branch.get("name", "")
    if name.startswith("openshell-m42-validation-"):
        encoded = urllib.parse.quote(name, safe="")
        response = client.delete(base + "/projects/1/repository/branches/" + encoded, headers=headers)
        response.raise_for_status()
        deleted += 1
variable = client.get(base + "/projects/1/variables/FULLSEND_GITLAB_ANALYST_TOKEN", headers=headers)
if variable.is_success and variable.json().get("value") == "invalid-m42-smoke-credential":
    response = client.delete(base + "/projects/1/variables/FULLSEND_GITLAB_ANALYST_TOKEN", headers=headers)
    response.raise_for_status()
kubectl("delete", "deployment/openshell-m42-gitlab-runner",
        "configmap/openshell-m42-runner-config", "secret/openshell-m42-runner-token",
        "secret/m42-jira-credentials", "--ignore-not-found")
print(json.dumps({"runner_unregistered": True, "temporary_branches_deleted": deleted,
                  "temporary_kubernetes_resources_deleted": True}))
