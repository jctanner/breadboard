import json
import time
import zipfile
from pathlib import Path

import httpx

base = "https://gitlab.local/api/v4"
client = httpx.Client(verify=False)
project_id = 1
branch = f"openshell-m2-validation-{int(time.time())}"
root = Path("var/demos/fullsend-entrypoint-poc/openshell-smoke")

token_response = client.post(
    f"{base}/admin/tokens",
    auth=("admin", "admin"),
    json={"login": "admin", "name": branch, "scopes": ["repo", "user", "admin:org"]},
)
token_response.raise_for_status()
headers = {"PRIVATE-TOKEN": token_response.json()["token"]}
response = client.post(
    f"{base}/projects/{project_id}/repository/branches",
    headers=headers,
    json={"branch": branch, "ref": "main"},
)
response.raise_for_status()

actions = []
for source, target in (
    ("gitlab-ci.yml", ".gitlab-ci.yml"),
    ("openshell-smoke.sh", "scripts/openshell-smoke.sh"),
    ("policy.yaml", "policy.yaml"),
):
    actions.append(
        {
            "action": "update" if target == ".gitlab-ci.yml" else "create",
            "file_path": target,
            "content": (root / source).read_text(encoding="utf-8"),
        }
    )
commit_response = client.post(
    f"{base}/projects/{project_id}/repository/commits",
    headers=headers,
    json={
        "branch": branch,
        "commit_message": "Add disposable OpenShell M2 smoke job",
        "actions": actions,
    },
)
if commit_response.is_error:
    raise RuntimeError(f"commit API failed: {commit_response.status_code} {commit_response.text}")
deadline = time.monotonic() + 60
pipeline_id = None
while time.monotonic() < deadline:
    pipelines_response = client.get(
        f"{base}/projects/{project_id}/pipelines",
        headers=headers,
        params={"ref": branch},
    )
    pipelines_response.raise_for_status()
    pipelines = pipelines_response.json()
    if pipelines:
        pipeline_id = max(pipelines, key=lambda item: item["id"])["id"]
        break
    time.sleep(2)
if pipeline_id is None:
    raise RuntimeError(f"GitLab did not create a push pipeline for {branch}")

deadline = time.monotonic() + 1800
job = None
while time.monotonic() < deadline:
    jobs_response = client.get(
        f"{base}/projects/{project_id}/pipelines/{pipeline_id}/jobs", headers=headers
    )
    jobs_response.raise_for_status()
    jobs = jobs_response.json()
    job = next((item for item in jobs if item["name"] == "openshell_podman_smoke"), None)
    if job and job["status"] in {"success", "failed", "canceled", "skipped"}:
        break
    time.sleep(5)
else:
    raise TimeoutError(f"pipeline {pipeline_id} did not finish")

trace_response = client.get(
    f"{base}/projects/{project_id}/jobs/{job['id']}/trace", headers=headers
)
trace_response.raise_for_status()
trace = trace_response.text
Path("/tmp/openshell-m2-job-trace.txt").write_text(trace, encoding="utf-8")
details_response = client.get(f"{base}/projects/{project_id}/jobs/{job['id']}", headers=headers)
details_response.raise_for_status()
details = details_response.json()
artifact_response = client.get(f"{base}/projects/{project_id}/jobs/{job['id']}/artifacts")
if artifact_response.is_success:
    archive_path = Path(f"/tmp/openshell-m2-{job['id']}-artifacts.zip")
    archive_path.write_bytes(artifact_response.content)
    with zipfile.ZipFile(archive_path) as archive:
        archive.extractall(f"/tmp/openshell-m2-{job['id']}-artifacts")
result = {
    "project": "admin/ci-testing",
    "branch": branch,
    "pipeline_id": pipeline_id,
    "job_id": job["id"],
    "job_status": job["status"],
    "runner": (details.get("runner") or {}).get("description"),
    "runner_tags": (details.get("runner") or {}).get("tag_list"),
    "artifacts_path": f"/tmp/openshell-m2-{job['id']}-artifacts",
    "trace": trace,
}
print(json.dumps(result, indent=2))
if job["status"] != "success" or "M2_SMOKE_PASS" not in trace:
    raise RuntimeError(f"OpenShell M2 job failed; see /tmp/openshell-m2-job-trace.txt")
