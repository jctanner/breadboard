#!/usr/bin/env python3
"""Seed two M8 RFEs without resetting Jira or touching the M6 issues."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import httpx
import yaml

ROOT = Path(__file__).resolve().parents[4]
CHECKOUT = ROOT / "checkouts.fullsend_prototype/jctanner.strat-creator"
MARKER = "fullsend-entrypoint-poc-m8"


def main():
    server = os.environ.get("JIRA_SERVER", "https://jira.local")
    if server != "https://jira.local": raise SystemExit("Local Jira only")
    secret=json.loads(subprocess.check_output(["kubectl","-n","ai-pipeline","get","secret","fullsend-strategy-jira","-o","json"]))
    credentials={k:base64.b64decode(v).decode() for k,v in secret["data"].items()}
    settings=yaml.safe_load((CHECKOUT/"config/pipeline-settings.yaml").read_text())
    spec=importlib.util.spec_from_file_location("source",ROOT/"var/demos/strat-pipeline-replication/scripts/seed_single_rfe.py")
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    scenarios=[
        ("json-report", "Add rhai-cli diagnose JSON report export for support cases",
         "Extend the existing diagnose health checks with --output-file PATH and a versioned JSON schema. "
         "The file includes cluster version, each check status and remediation text. Write atomically with owner-only "
         "permissions; redact credentials and tokens; test JSON validation, unwritable destinations, and exit status. "
         "Human-readable output remains the default. No new health checks are required."),
        ("bounded-checks", "Add bounded per-check deadlines to rhai-cli diagnose",
         "Extend diagnose with --check-timeout SECONDS so unavailable routes cannot hang a health report. "
         "Cancel overdue checks, report a timeout warning with the check name, continue independent checks, "
         "and return nonzero for critical timeouts. Validate nonpositive values and test cancellation with a fake "
         "unresponsive endpoint. Preserve deterministic report order. No JSON file export is required.")]
    with httpx.Client(base_url=server,verify=os.environ["JIRA_CA_FILE"],timeout=30,
                      auth=(credentials["JIRA_USER"],credentials["JIRA_TOKEN"])) as client:
        def api(method,path,**kwargs):
            r=client.request(method,path,**kwargs);r.raise_for_status();return r.json() if r.content else None
        historical={key:api("GET","/rest/api/3/issue/"+key) for key in ("RHAIRFE-1","RHAISTRAT-1")}
        keys=[]
        for scenario,summary,extension in scenarios:
            label=MARKER+"-"+scenario
            found=api("GET","/rest/api/3/search",params={"jql":f'project = RHAIRFE AND labels = "{label}"',"maxResults":2})
            assert found["total"]<=1, "Duplicate M8 fixture"
            if found["issues"]:key=found["issues"][0]["key"]
            else:
                issue=api("POST","/rest/api/3/issue",json={"fields":{
                    "project":{"key":"RHAIRFE"},"issuetype":{"name":"Feature Request"},
                    "summary":summary,"description":source.DESCRIPTION+"\n\nh2. Scoped Extension\n\n"+extension,
                    "priority":{"name":"Major"},"components":[{"name":"CLI"}],
                    "labels":[MARKER,label,settings["jql"]["required_labels"][0],settings["jql"]["quality_labels"][0],"rfe-creator-feasibility-pass"]}})
                key=issue["key"]
            fields=api("GET","/rest/api/3/issue/"+key)["fields"]
            assert fields["summary"]==summary
            assert not fields.get("issuelinks") and not fields.get("attachment"), "Fixture already processed; inspect before any retry"
            assert not set(fields["labels"]) & {"strat-creator-processing","strat-creator-needs-attention","strat-creator-human-sign-off"}
            keys.append(key)
        for key,before in historical.items():assert api("GET","/rest/api/3/issue/"+key)==before, "Historical issue changed"
    sys.path.insert(0,str(CHECKOUT/"scripts"))
    import jira_utils
    jira_utils.ssl_ctx.load_verify_locations(os.environ["JIRA_CA_FILE"])
    env=dict(os.environ,JIRA_SERVER=server,JIRA_USER=credentials["JIRA_USER"],JIRA_TOKEN=credentials["JIRA_TOKEN"],SSL_CERT_FILE=os.environ["JIRA_CA_FILE"])
    r=subprocess.run([sys.executable,str(CHECKOUT/"scripts/list-rfe-ids.py"),"--jql-default","--batch-size","2","--verbose"],env=env,text=True,capture_output=True,check=True)
    discovered=r.stdout.split()
    assert discovered==keys, f"Unexpected discovery bound: {discovered} != {keys}"
    assert "RHAIRFE-1" not in discovered
    print(json.dumps({"keys":keys,"discovered":discovered,"historical_issues_unchanged":True,"historical_processed_rfe_excluded":True,"batch_size":2,"batch_offset":0,"expected_keys":" ".join(keys)},indent=2))


if __name__=="__main__":main()
