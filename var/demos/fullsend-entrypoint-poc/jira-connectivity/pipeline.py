import json, os, time, zipfile
from pathlib import Path
import httpx

base = os.environ.get("GITLAB_API_URL", "https://gitlab.local/api/v4")
client = httpx.Client(verify=os.environ["GITLAB_CA_FILE"], timeout=30)
project_id = 1
branch = f"openshell-m42-validation-{int(time.time())}"
root = Path(__file__).resolve().parents[4]
fixture = Path(__file__).resolve().parent
checkout = Path(os.environ.get("STRAT_CREATOR_CHECKOUT", str(root / "checkouts.fullsend_prototype/jctanner.strat-creator"))) / ".fullsend"
resp = client.post(f"{base}/admin/tokens", auth=(os.environ["GITLAB_ADMIN_USER"], os.environ["GITLAB_ADMIN_PASSWORD"]), json={"login":"admin","name":branch,"scopes":["repo","user","admin:org"]})
resp.raise_for_status()
headers = {"PRIVATE-TOKEN":resp.json()["token"]}
variable = client.post(f"{base}/projects/{project_id}/variables",headers=headers,json={"key":"FULLSEND_GITLAB_ANALYST_TOKEN","value":"invalid-m42-smoke-credential","masked":False,"protected":False})
if variable.status_code not in (201, 400): variable.raise_for_status()
resp=client.post(f"{base}/projects/{project_id}/repository/branches",headers=headers,json={"branch":branch,"ref":"main"}); resp.raise_for_status()
files = {
  ".gitlab-ci.yml": (fixture/"gitlab-ci.yml").read_text(),
  "scripts/build-fullsend.sh": (checkout/"scripts/ci/build-fullsend.sh").read_text(),
  "scripts/with-openshell.sh": (checkout/"scripts/ci/with-openshell.sh").read_text(),
  "scripts/ca-bundle.sh": (checkout/"scripts/ci/ca-bundle.sh").read_text(),
  "scripts/jira_utils.py": (checkout.parent/"scripts/jira_utils.py").read_text(),
  "scripts/m42-probe.py": (fixture/"probe.py").read_text(),
  "scripts/m42-smoke.sh": (fixture/"smoke.sh").read_text(),
  "policy.yaml": (checkout/"policies/strategy.yaml").read_text(),
}
actions=[{"action":"update" if path == ".gitlab-ci.yml" else "create","file_path":path,"content":content} for path,content in files.items()]
resp=client.post(f"{base}/projects/{project_id}/repository/commits",headers=headers,json={"branch":branch,"commit_message":"Run M4.2 reference image smoke validation","actions":actions})
if resp.is_error: raise RuntimeError(f"commit failed {resp.status_code}: {resp.text[:1000]}")
resp.raise_for_status()
deadline=time.monotonic()+90
pipeline=None
while time.monotonic()<deadline:
 resp=client.get(f"{base}/projects/{project_id}/pipelines",headers=headers,params={"ref":branch}); resp.raise_for_status()
 found=resp.json()
 if found: pipeline=max(found,key=lambda p:p["id"]); break
 time.sleep(2)
if not pipeline: raise TimeoutError("GitLab did not create M4.2 pipeline")
pid=pipeline["id"]
deadline=time.monotonic()+2700
jobs=[]
while time.monotonic()<deadline:
 resp=client.get(f"{base}/projects/{project_id}/pipelines/{pid}/jobs",headers=headers); resp.raise_for_status(); jobs=resp.json()
 if len(jobs)>=2 and all(j["status"] in {"success","failed","canceled","skipped"} for j in jobs): break
 time.sleep(5)
else: raise TimeoutError(f"pipeline {pid} timed out")
for job in jobs:
 trace=client.get(f"{base}/projects/{project_id}/jobs/{job['id']}/trace",headers=headers); trace.raise_for_status()
 Path(f"/tmp/m42-job-{job['id']}-trace.txt").write_text(trace.text)
 if job["name"]=="openshell_m42_smoke":
  art=client.get(f"{base}/projects/{project_id}/jobs/{job['id']}/artifacts",headers=headers)
  if art.is_success:
   zpath=Path(f"/tmp/m42-job-{job['id']}-artifacts.zip"); zpath.write_bytes(art.content)
   with zipfile.ZipFile(zpath) as z: z.extractall(f"/tmp/m42-job-{job['id']}-artifacts")
 print(json.dumps({"job_id":job["id"],"name":job["name"],"status":job["status"],"trace_path":f"/tmp/m42-job-{job['id']}-trace.txt"}))
print(json.dumps({"branch":branch,"pipeline_id":pid,"jobs":[{"id":j["id"],"name":j["name"],"status":j["status"]} for j in jobs]}))

if any(job["status"] != "success" for job in jobs):
    raise SystemExit(1)
