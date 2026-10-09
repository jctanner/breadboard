import json
import sys
from urllib.parse import quote

import httpx

runner_token = sys.stdin.readline().strip()
if not runner_token:
    raise SystemExit("temporary runner token is required on stdin")

base = "https://gitlab.local/api/v4"
client = httpx.Client(verify=False)
unregister = client.request("DELETE", f"{base}/runners", json={"token": runner_token})
if unregister.status_code not in {200, 204}:
    raise RuntimeError(f"runner unregister failed: {unregister.status_code} {unregister.text}")

token_response = client.post(
    f"{base}/admin/tokens",
    auth=("admin", "admin"),
    json={
        "login": "admin",
        "name": "openshell-m2-cleanup",
        "scopes": ["repo", "user", "admin:org"],
    },
)
token_response.raise_for_status()
headers = {"PRIVATE-TOKEN": token_response.json()["token"]}
branches = client.get(f"{base}/projects/1/repository/branches", headers=headers)
branches.raise_for_status()

deleted = []
for item in branches.json():
    name = item.get("name", "")
    if name.startswith("openshell-m2-validation-"):
        response = client.delete(
            f"{base}/projects/1/repository/branches/{quote(name, safe='')}",
            headers=headers,
        )
        response.raise_for_status()
        deleted.append(name)

print(json.dumps({"runner_unregistered": True, "branches_deleted": deleted}, indent=2))
