import httpx

response = httpx.post(
    "http://127.0.0.1:8000/api/v4/runners",
    json={
        "token": "runner-registration-token",
        "description": "podman-m1-k8s-runner",
        "tag_list": "podman-m1",
        "run_untagged": False,
        "locked": False,
    },
)
response.raise_for_status()
print(response.json()["token"])
