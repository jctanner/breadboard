import httpx

response = httpx.post(
    "https://gitlab.local/api/v4/runners",
    json={
        "token": "runner-registration-token",
        "description": "openshell-m2-k8s-runner",
        "tag_list": "openshell-m2",
        "run_untagged": False,
        "locked": False,
    },
    verify=False,
)
response.raise_for_status()
print(response.json()["token"])
