import json
import time
from urllib.parse import quote

import httpx

base = "http://127.0.0.1:8000/api/v4"
project_id = 1  # admin/ci-testing
branch = f"podman-m1-validation-{int(time.time())}"
timeout_seconds = 600

token_response = httpx.post(
    f"{base}/admin/tokens",
    auth=("admin", "admin"),
    json={"login": "admin", "name": branch, "scopes": ["repo", "user", "admin:org"]},
)
token_response.raise_for_status()
headers = {"PRIVATE-TOKEN": token_response.json()["token"]}

branch_response = httpx.post(
    f"{base}/projects/{project_id}/repository/branches",
    headers=headers,
    json={"branch": branch, "ref": "main"},
)
branch_response.raise_for_status()

for path, local_path in (
    (".gitlab-ci.yml", "/tmp/podman-m1-gitlab-ci.yml"),
    ("scripts/podman-smoke.sh", "/tmp/podman-m1-smoke.sh"),
):
    with open(local_path, encoding="utf-8") as source:
        method = "put" if path == ".gitlab-ci.yml" else "post"
        response = getattr(httpx, method)(
            f"{base}/projects/{project_id}/repository/files/{quote(path, safe='')}",
            headers=headers,
            json={
                "branch": branch,
                "content": source.read(),
                "commit_message": "Add temporary Podman M1 smoke job",
            },
        )
        response.raise_for_status()

pipeline_response = httpx.post(
    f"{base}/projects/{project_id}/pipeline",
    headers=headers,
    json={"ref": branch},
)
pipeline_response.raise_for_status()
pipeline_id = pipeline_response.json()["id"]

deadline = time.monotonic() + timeout_seconds
job = None
while time.monotonic() < deadline:
    jobs_response = httpx.get(
        f"{base}/projects/{project_id}/pipelines/{pipeline_id}/jobs",
        headers=headers,
    )
    jobs_response.raise_for_status()
    jobs = jobs_response.json()
    job = next((item for item in jobs if item["name"] == "podman_smoke"), None)
    if job and job["status"] in {"success", "failed", "canceled", "skipped"}:
        break
    time.sleep(3)
else:
    raise TimeoutError(f"pipeline {pipeline_id} did not finish")

if not job or job["status"] != "success":
    raise RuntimeError(f"Podman M1 GitLab job failed: {json.dumps(job)}")

trace_response = httpx.get(
    f"{base}/projects/{project_id}/jobs/{job['id']}/trace", headers=headers
)
trace_response.raise_for_status()
trace = trace_response.text
required_markers = (
    "nested-podman-ok",
    "nested-dns-https-ok",
    "M1_SMOKE_PASS",
)
missing = [marker for marker in required_markers if marker not in trace]
if missing:
    raise RuntimeError(f"job trace missing markers {missing}:\n{trace}")

job_response = httpx.get(f"{base}/projects/{project_id}/jobs/{job['id']}", headers=headers)
job_response.raise_for_status()
details = job_response.json()
print(
    json.dumps(
        {
            "project": "admin/ci-testing",
            "project_id": project_id,
            "branch": branch,
            "pipeline_id": pipeline_id,
            "job_id": job["id"],
            "job_status": job["status"],
            "runner": (details.get("runner") or {}).get("description"),
            "runner_tags": (details.get("runner") or {}).get("tag_list"),
            "trace": trace,
        },
        indent=2,
    )
)
