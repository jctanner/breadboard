import json
import sys
from urllib.parse import quote

import httpx

runner_token = sys.stdin.readline().strip()
if not runner_token:
    raise SystemExit("runner token is required on stdin")

base = "http://127.0.0.1:8000/api/v4"
unregister = httpx.request("DELETE", f"{base}/runners", json={"token": runner_token})
if unregister.status_code not in {200, 204}:
    raise RuntimeError(f"runner unregister failed: {unregister.status_code} {unregister.text}")

token_response = httpx.post(
    f"{base}/admin/tokens",
    auth=("admin", "admin"),
    json={"login": "admin", "name": "podman-m1-cleanup", "scopes": ["repo", "user", "admin:org"]},
)
token_response.raise_for_status()
headers = {"PRIVATE-TOKEN": token_response.json()["token"]}

deleted = []
branches = httpx.get(f"{base}/projects/1/repository/branches", headers=headers)
branches.raise_for_status()
for item in branches.json():
    name = item.get("name", "")
    if name.startswith("podman-m1-validation"):
        response = httpx.delete(
            f"{base}/projects/1/repository/branches/{quote(name, safe='')}",
            headers=headers,
        )
        response.raise_for_status()
        deleted.append(name)

print(json.dumps({"runner_unregistered": True, "branches_deleted": deleted}))
