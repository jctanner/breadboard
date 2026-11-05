#!/usr/bin/env python3
"""Seed demo issues, projects, and merge requests into Jira and GitLab emulators.

Idempotently populates:
1. Jira (https://jira.bb.internal):
   - RHAIRFE: 4 realistic RFEs from benchmark templates
   - RHAISTRAT: 3 realistic strategy initiatives/epics linked to RFEs
   - RHOAIENG: 4 realistic engineering bugs/tasks
2. GitLab (https://gitlab.bb.internal):
   - rhoai/odh-dashboard: 3 issues, 2 merge requests
   - rhoai/kserve: 3 issues, 2 merge requests
Does NOT touch GitHub repositories.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import urllib3
import yaml

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


DEFAULT_JIRA_URL = os.getenv("JIRA_URL", "https://jira.bb.internal")
DEFAULT_GITLAB_URL = os.getenv("GITLAB_URL", "https://gitlab.bb.internal")
DEFAULT_DASHBOARD_URL = os.getenv("DASHBOARD_URL", "https://dashboard.bb.internal")


def load_yaml_template(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class JiraSeeder:
    def __init__(self, base_url: str, auth: tuple[str, str] = ("admin", "admin")):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = auth
        self.session.verify = False
        self.session.headers.update({"Content-Type": "application/json"})

    def get_existing_issues_for_project(self, project_key: str) -> list[dict[str, Any]]:
        url = f"{self.base_url}/rest/api/2/search"
        payload = {
            "jql": f'project = "{project_key}" ORDER BY created DESC',
            "maxResults": 100,
            "fields": ["summary", "status", "priority", "issuetype", "labels", "project"],
        }
        res = self.session.post(url, json=payload, timeout=20)
        res.raise_for_status()
        return res.json().get("issues", [])

    def ensure_issue(
        self,
        project_key: str,
        issue_type: str,
        summary: str,
        description: str,
        priority: str,
        labels: list[str],
    ) -> tuple[str, bool]:
        """Returns (issue_key, created_boolean)."""
        existing = self.get_existing_issues_for_project(project_key)
        for issue in existing:
            fields = issue.get("fields", {})
            if fields.get("summary", "").strip() == summary.strip():
                return issue["key"], False

        payload = {
            "fields": {
                "project": {"key": project_key},
                "issuetype": {"name": issue_type},
                "summary": summary,
                "description": description,
                "priority": {"name": priority},
                "labels": labels,
            }
        }
        res = self.session.post(f"{self.base_url}/rest/api/2/issue", json=payload, timeout=20)
        res.raise_for_status()
        created_key = res.json()["key"]
        return created_key, True

    def link_issues(self, inward_key: str, outward_key: str, link_type: str = "Cloners") -> bool:
        """Create an issue link (e.g. inward was cloned by outward)."""
        url = f"{self.base_url}/rest/api/2/issueLink"
        payload = {
            "type": {"name": link_type},
            "inwardIssue": {"key": inward_key},
            "outwardIssue": {"key": outward_key},
        }
        try:
            res = self.session.post(url, json=payload, timeout=20)
            return res.status_code in (200, 201)
        except Exception:
            return False


class GitLabSeeder:
    def __init__(self, base_url: str, auth: tuple[str, str] = ("admin", "admin")):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.auth = auth
        self.session.verify = False
        self.session.headers.update({"Content-Type": "application/json"})

    def ensure_group(self, group_path: str, group_name: str) -> int:
        res = self.session.get(f"{self.base_url}/api/v4/groups/{group_path}", timeout=20)
        if res.status_code == 200:
            return res.json()["id"]

        create_res = self.session.post(
            f"{self.base_url}/api/v4/groups",
            json={"name": group_name, "path": group_path},
            timeout=20,
        )
        create_res.raise_for_status()
        return create_res.json()["id"]

    def ensure_project(
        self,
        group_id: int,
        project_name: str,
        project_path: str,
        description: str,
    ) -> int:
        full_path = f"rhoai/{project_path}"
        encoded_path = quote(full_path, safe="")
        res = self.session.get(f"{self.base_url}/api/v4/projects/{encoded_path}", timeout=20)
        if res.status_code == 200:
            return res.json()["id"]

        payload = {
            "name": project_name,
            "path": project_path,
            "namespace_id": group_id,
            "description": description,
            "visibility": "public",
            "initialize_with_readme": True,
        }
        create_res = self.session.post(
            f"{self.base_url}/api/v4/projects",
            json=payload,
            timeout=20,
        )
        create_res.raise_for_status()
        return create_res.json()["id"]

    def ensure_issue(
        self,
        project_id: int,
        title: str,
        description: str,
        labels: list[str],
    ) -> tuple[int, bool]:
        res = self.session.get(
            f"{self.base_url}/api/v4/projects/{project_id}/issues",
            params={"state": "all", "per_page": 100},
            timeout=20,
        )
        res.raise_for_status()
        for issue in res.json():
            if issue.get("title", "").strip() == title.strip():
                return issue.get("iid", issue.get("id")), False

        payload = {
            "title": title,
            "description": description,
            "labels": labels,
        }
        create_res = self.session.post(
            f"{self.base_url}/api/v4/projects/{project_id}/issues",
            json=payload,
            timeout=20,
        )
        create_res.raise_for_status()
        created = create_res.json()
        return created.get("iid", created.get("id")), True

    def ensure_branch(self, project_id: int, branch_name: str, ref: str = "main") -> bool:
        res = self.session.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/branches/{quote(branch_name, safe='')}",
            timeout=20,
        )
        if res.status_code == 200:
            return False

        create_res = self.session.post(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/branches",
            json={"branch": branch_name, "ref": ref},
            timeout=20,
        )
        create_res.raise_for_status()
        return True

    def commit_file_change(
        self,
        project_id: int,
        file_path: str,
        branch_name: str,
        commit_message: str,
        content: str,
    ) -> None:
        encoded_file = quote(file_path, safe="")
        url = f"{self.base_url}/api/v4/projects/{project_id}/repository/files/{encoded_file}"
        check = self.session.get(url, params={"ref": branch_name}, timeout=20)
        payload = {
            "branch": branch_name,
            "commit_message": commit_message,
            "content": content,
        }
        if check.status_code == 200:
            self.session.put(url, json=payload, timeout=20).raise_for_status()
        else:
            self.session.post(url, json=payload, timeout=20).raise_for_status()

    def ensure_merge_request(
        self,
        project_id: int,
        title: str,
        source_branch: str,
        target_branch: str,
        description: str,
        labels: list[str],
        file_path: str,
        file_content: str,
    ) -> tuple[int, bool]:
        res = self.session.get(
            f"{self.base_url}/api/v4/projects/{project_id}/merge_requests",
            params={"state": "all", "per_page": 100},
            timeout=20,
        )
        res.raise_for_status()
        for mr in res.json():
            if mr.get("title", "").strip() == title.strip():
                return mr.get("iid", mr.get("id")), False

        # Ensure branch exists and has a commit
        self.ensure_branch(project_id, source_branch, ref=target_branch)
        self.commit_file_change(
            project_id=project_id,
            file_path=file_path,
            branch_name=source_branch,
            commit_message=f"feat: {title}",
            content=file_content,
        )

        payload = {
            "title": title,
            "source_branch": source_branch,
            "target_branch": target_branch,
            "description": description,
            "labels": labels,
        }
        create_res = self.session.post(
            f"{self.base_url}/api/v4/projects/{project_id}/merge_requests",
            json=payload,
            timeout=20,
        )
        create_res.raise_for_status()
        created = create_res.json()
        return created.get("iid", created.get("id")), True


def seed_jira(
    jira_url: str,
    templates_dir: Path,
) -> list[dict[str, Any]]:
    seeder = JiraSeeder(jira_url)
    results: list[dict[str, Any]] = []

    # 1. RHAIRFE templates
    rfe_specs = [
        {
            "template": "connection-credential-rotation.yaml",
            "priority": "Major",
            "labels": [
                "strat-creator-3.6",
                "rfe-creator-autofix-rubric-pass",
                "rfe-creator-feasibility-pass",
                "security",
                "connections",
            ],
        },
        {
            "template": "kserve-canary-rollback.yaml",
            "priority": "Critical",
            "labels": [
                "strat-creator-3.6",
                "rfe-creator-autofix-rubric-pass",
                "rfe-creator-feasibility-pass",
                "model-serving",
                "kserve",
            ],
        },
        {
            "template": "workbench-cull-exemption.yaml",
            "priority": "Major",
            "labels": [
                "strat-creator-3.6",
                "rfe-creator-feasibility-pass",
                "workbenches",
                "resource-management",
            ],
        },
        {
            "template": "dsp-retention.yaml",
            "priority": "Normal",
            "labels": [
                "strat-creator-3.6",
                "rfe-creator-autofix-rubric-pass",
                "rfe-creator-feasibility-pass",
                "pipelines",
                "storage",
            ],
        },
    ]

    rfe_keys: dict[str, str] = {}
    for spec in rfe_specs:
        data = load_yaml_template(templates_dir / spec["template"])
        summary = data["summary"].strip()
        description = data["description"]
        key, created = seeder.ensure_issue(
            project_key="RHAIRFE",
            issue_type="Feature Request",
            summary=summary,
            description=description,
            priority=spec["priority"],
            labels=spec["labels"],
        )
        rfe_keys[spec["template"]] = key
        results.append({
            "project": "RHAIRFE",
            "key": key,
            "type": "Feature Request",
            "priority": spec["priority"],
            "summary": summary,
            "created": created,
        })

    # 2. RHAISTRAT epics/initiatives
    strat_specs = [
        {
            "summary": "Strategy: Model Serving Canary Rollout & Automated Degradation Rollback",
            "type": "Initiative",
            "priority": "Major",
            "labels": [
                "strat-creator-3.6",
                "strat-creator-rubric-pass",
                "strategy-initiative",
                "kserve",
                "observability",
            ],
            "linked_rfe": "kserve-canary-rollback.yaml",
            "description": (
                "h2. Executive Summary\n\n"
                "Establish platform-level canary rollout management for KServe inference services, "
                "integrating Prometheus-based error budget and latency monitoring with automated "
                "traffic diversion upon SLA breaches.\n\n"
                "h2. Technical Approach\n\n"
                "Keep canary threshold configuration beside the InferenceService spec. Use the "
                "controller that reconciles serving revisions to evaluate CanaryEvaluation metrics "
                "over an observation window. Divert traffic back to stable revision upon error spikes.\n\n"
                "h2. Scope & Technical Architecture\n\n"
                "Integrate with OpenShift Service Mesh / Istio virtual services managed by KServe. "
                "Deliver a dedicated canary controller reconciling CanaryEvaluation custom resources."
            ),
        },
        {
            "summary": "Strategy: Secret Lifecycle & Safe Credential Rotation for Data Science Projects",
            "type": "Epic",
            "priority": "Critical",
            "labels": [
                "strat-creator-3.6",
                "strat-creator-rubric-pass",
                "strategy-epic",
                "security-hardening",
                "platform-foundations",
            ],
            "linked_rfe": "connection-credential-rotation.yaml",
            "description": (
                "h2. Architecture Strategy\n\n"
                "Define standard lifecycle transitions for Kubernetes secrets backing OpenShift AI "
                "connection profiles. Implement stage-validate-activate-retire workflow preventing "
                "disruption to running workbench pods and pipeline tasks.\n\n"
                "h2. Security Impact\n\n"
                "Eliminates hardcoded credentials and unbounded stale token caching across multi-tenant clusters. "
                "Validation checks access before activation."
            ),
        },
        {
            "summary": "Strategy: Configurable Artifact Lifecycle Management for Data Science Pipelines",
            "type": "Epic",
            "priority": "Major",
            "labels": [
                "strat-creator-3.6",
                "strat-creator-needs-attention",
                "strategy-epic",
                "pipelines",
                "storage",
            ],
            "linked_rfe": "dsp-retention.yaml",
            "description": (
                "h2. Architecture Strategy\n\n"
                "Extend Data Science Pipelines operator with an artifact retention controller that "
                "interfaces with S3 object storage. Automatically reconcile run records with registered "
                "models to prevent premature deletion of audit-critical artifacts."
            ),
        },
    ]

    for spec in strat_specs:
        key, created = seeder.ensure_issue(
            project_key="RHAISTRAT",
            issue_type=spec["type"],
            summary=spec["summary"],
            description=spec["description"],
            priority=spec["priority"],
            labels=spec["labels"],
        )
        if spec.get("linked_rfe") and spec["linked_rfe"] in rfe_keys:
            rfe_key = rfe_keys[spec["linked_rfe"]]
            seeder.link_issues(inward_key=rfe_key, outward_key=key, link_type="Cloners")
        results.append({
            "project": "RHAISTRAT",
            "key": key,
            "type": spec["type"],
            "priority": spec["priority"],
            "summary": spec["summary"],
            "created": created,
        })

    # 3. RHOAIENG engineering bugs and tasks
    eng_specs = [
        {
            "summary": "KServe InferenceService canary traffic shift fails when revision name exceeds 63 characters",
            "type": "Bug",
            "priority": "Major",
            "labels": ["kserve", "model-serving", "controller", "triage-passed"],
            "description": (
                "h2. Description\n\n"
                "When creating an InferenceService with a canary traffic split and a revision name longer "
                "than 63 characters, Knative Service creation fails due to Kubernetes label/name validation limits.\n\n"
                "h2. Steps to Reproduce\n\n"
                "1. Deploy an InferenceService with a long model release tag (> 45 chars).\n"
                "2. Update predictor to split traffic 80/20.\n"
                "3. Controller logs: `Invalid value: must be no more than 63 characters`.\n\n"
                "h2. Expected Result\n\n"
                "Controller truncates or hashes revision names conforming to RFC 1123 DNS subdomains."
            ),
        },
        {
            "summary": "Pipeline run artifacts fail to clean up when S3 storage bucket enforces Object Lock",
            "type": "Bug",
            "priority": "Normal",
            "labels": ["pipelines", "dsp", "object-storage", "bug-verified"],
            "description": (
                "h2. Description\n\n"
                "Data Science Pipelines persistence agent errors out with `AccessDenied: Object is locked` "
                "when attempting to delete expired run artifacts in buckets with S3 Object Lock retention enabled.\n\n"
                "h2. Expected Result\n\n"
                "Retention worker gracefully detects WORM/Object Lock constraints and marks artifacts as "
                "retention-managed without failing the reconciliation loop."
            ),
        },
        {
            "summary": "Workbench idle-culler detects spurious activity when terminal WebSocket remains open",
            "type": "Bug",
            "priority": "Minor",
            "labels": ["workbenches", "notebook-controller", "culling"],
            "description": (
                "h2. Description\n\n"
                "Workbenches with an open but dormant terminal session keep emitting WebSocket ping frames, "
                "causing the activity tracker to treat the pod as actively in-use and preventing idle cull.\n\n"
                "h2. Expected Result\n\n"
                "Activity monitor distinguishes application traffic from control keep-alive frames."
            ),
        },
        {
            "summary": "Implement health check plugin for Model Registry TLS certificates in rhai-cli",
            "type": "Task",
            "priority": "Major",
            "labels": ["cli", "day2-ops", "diagnostics", "model-registry"],
            "description": (
                "h2. Objective\n\n"
                "Add a diagnostic plugin under `pkg/diagnostics/checks/model_registry.go` that verifies "
                "the TLS certificate SANs, validity window, and ingress cert chain for model-registry endpoints."
            ),
        },
    ]

    for spec in eng_specs:
        key, created = seeder.ensure_issue(
            project_key="RHOAIENG",
            issue_type=spec["type"],
            summary=spec["summary"],
            description=spec["description"],
            priority=spec["priority"],
            labels=spec["labels"],
        )
        results.append({
            "project": "RHOAIENG",
            "key": key,
            "type": spec["type"],
            "priority": spec["priority"],
            "summary": spec["summary"],
            "created": created,
        })

    return results


def seed_gitlab(gitlab_url: str) -> list[dict[str, Any]]:
    seeder = GitLabSeeder(gitlab_url)
    results: list[dict[str, Any]] = []

    group_id = seeder.ensure_group("rhoai", "OpenShift AI")

    # Project 1: rhoai/odh-dashboard
    p1_id = seeder.ensure_project(
        group_id=group_id,
        project_name="odh-dashboard",
        project_path="odh-dashboard",
        description="OpenShift AI User Interface and Dashboard Service",
    )

    p1_issues = [
        {
            "title": "Dashboard displays blank canvas when connection secret has empty annotations",
            "description": (
                "When browsing project connection settings, if a Kubernetes secret lacks expected "
                "metadata annotations, the React component throws TypeError: Cannot read properties "
                "of undefined (reading 'annotations') and renders a white screen."
            ),
            "labels": ["bug", "ui", "frontend", "severity::high"],
        },
        {
            "title": "Add support for canary rollout percentage slider in Model Serving view",
            "description": (
                "Provide an intuitive UI control in the Model Serving revision tab allowing model "
                "owners to adjust canary traffic distribution (0% - 100%) in 5% increments."
            ),
            "labels": ["feature", "model-serving", "enhancement"],
        },
        {
            "title": "Culling countdown indicator shows incorrect timezone on workbench cards",
            "description": (
                "The idle culling timestamp displayed on the workbench card assumes UTC instead of "
                "browser local timezone, causing confusion for users in negative UTC offsets."
            ),
            "labels": ["bug", "workbenches", "ui"],
        },
    ]

    for spec in p1_issues:
        iid, created = seeder.ensure_issue(
            project_id=p1_id,
            title=spec["title"],
            description=spec["description"],
            labels=spec["labels"],
        )
        results.append({
            "project": "rhoai/odh-dashboard",
            "type": "Issue",
            "key": f"rhoai/odh-dashboard#{iid}",
            "title": spec["title"],
            "created": created,
        })

    p1_mrs = [
        {
            "title": "feat(serving): add canary traffic slider and health metrics panel",
            "source_branch": "feature/canary-traffic-slider",
            "target_branch": "main",
            "file_path": "frontend/src/components/CanarySlider.tsx",
            "file_content": (
                "import React from 'react';\n\n"
                "export const CanarySlider: React.FC<{ value: number; onChange: (v: number) => void }> = "
                "({ value, onChange }) => {\n"
                "  return (\n"
                "    <div className='canary-control'>\n"
                "      <label>Canary Split: {value}%</label>\n"
                "      <input type='range' min='0' max='100' step='5' value={value} "
                "onChange={(e) => onChange(Number(e.target.value))} />\n"
                "    </div>\n"
                "  );\n"
                "};\n"
            ),
            "description": (
                "Implements the canary percentage slider component and integrates real-time "
                "Prometheus error rate charts into the Model Serving deployment modal."
            ),
            "labels": ["frontend", "review-pending", "serving"],
        },
        {
            "title": "fix(connections): safely handle empty secret annotations in connection form",
            "source_branch": "fix/empty-secret-annotations",
            "target_branch": "main",
            "file_path": "frontend/src/pages/connections/ConnectionDetails.tsx",
            "file_content": (
                "export function parseSecretAnnotations(metadata?: { annotations?: Record<string, string> }) {\n"
                "  return metadata?.annotations ?? {};\n"
                "}\n"
            ),
            "description": "Adds optional chaining and fallback empty object when inspecting secret metadata annotations.",
            "labels": ["bugfix", "ready-to-merge"],
        },
    ]

    for spec in p1_mrs:
        iid, created = seeder.ensure_merge_request(
            project_id=p1_id,
            title=spec["title"],
            source_branch=spec["source_branch"],
            target_branch=spec["target_branch"],
            description=spec["description"],
            labels=spec["labels"],
            file_path=spec["file_path"],
            file_content=spec["file_content"],
        )
        results.append({
            "project": "rhoai/odh-dashboard",
            "type": "Merge Request",
            "key": f"rhoai/odh-dashboard!{iid}",
            "title": spec["title"],
            "created": created,
        })

    # Project 2: rhoai/kserve
    p2_id = seeder.ensure_project(
        group_id=group_id,
        project_name="kserve",
        project_path="kserve",
        description="Standardized Serverless ML Inference Platform on Kubernetes",
    )

    p2_issues = [
        {
            "title": "Canary rollout controller should evaluate metrics over configurable observation window",
            "description": (
                "Currently the canary evaluation interval is fixed to 60 seconds. We should make "
                "`evaluationPeriod` and `minimumRequestCount` configurable in the InferenceService spec."
            ),
            "labels": ["enhancement", "controller", "v2-dataplane"],
        },
        {
            "title": "InferenceService status does not propagate underlying Knative revision failure",
            "description": (
                "When a container fails to start due to ImagePullBackOff or CrashLoopBackOff, the parent "
                "InferenceService remains in `PredictorReady: Unknown` instead of transitioning to "
                "`PredictorReady: False` with descriptive message."
            ),
            "labels": ["bug", "controller", "high-priority"],
        },
        {
            "title": "Add support for vLLM speculative decoding runtime template",
            "description": (
                "Add a default ServingRuntime YAML definition pre-configured for vLLM with speculative decoding "
                "(`--speculative-model` and `--num-speculative-tokens`)."
            ),
            "labels": ["feature", "serving-runtime", "llm"],
        },
    ]

    for spec in p2_issues:
        iid, created = seeder.ensure_issue(
            project_id=p2_id,
            title=spec["title"],
            description=spec["description"],
            labels=spec["labels"],
        )
        results.append({
            "project": "rhoai/kserve",
            "type": "Issue",
            "key": f"rhoai/kserve#{iid}",
            "title": spec["title"],
            "created": created,
        })

    p2_mrs = [
        {
            "title": "feat(controller): support configurable evaluation window for canary rollouts",
            "source_branch": "feature/configurable-canary-window",
            "target_branch": "main",
            "file_path": "pkg/controller/inferenceservice/canary.go",
            "file_content": (
                "package inferenceservice\n\n"
                "import \"time\"\n\n"
                "type CanaryConfig struct {\n"
                "    EvaluationPeriod  time.Duration `json:\"evaluationPeriod\"`\n"
                "    MinimumRequests   int           `json:\"minimumRequests\"`\n"
                "}\n"
            ),
            "description": (
                "Exposes `spec.predictor.canary.evaluationPeriod` and validates against Knative metrics provider."
            ),
            "labels": ["controller", "enhancement"],
        },
        {
            "title": "fix(status): propagate Knative revision pod failure reason to InferenceService status",
            "source_branch": "fix/revision-failure-propagation",
            "target_branch": "main",
            "file_path": "pkg/controller/inferenceservice/status.go",
            "file_content": (
                "package inferenceservice\n\n"
                "func PropagateRevisionFailure(conditionStatus string, reason string) string {\n"
                "    if reason == \"CrashLoopBackOff\" || reason == \"ImagePullBackOff\" {\n"
                "        return \"PredictorFailed: \" + reason\n"
                "    }\n"
                "    return conditionStatus\n"
                "}\n"
            ),
            "description": "Watches Knative Service status conditions and translates container failures into actionable InferenceService conditions.",
            "labels": ["bugfix", "needs-review"],
        },
    ]

    for spec in p2_mrs:
        iid, created = seeder.ensure_merge_request(
            project_id=p2_id,
            title=spec["title"],
            source_branch=spec["source_branch"],
            target_branch=spec["target_branch"],
            description=spec["description"],
            labels=spec["labels"],
            file_path=spec["file_path"],
            file_content=spec["file_content"],
        )
        results.append({
            "project": "rhoai/kserve",
            "type": "Merge Request",
            "key": f"rhoai/kserve!{iid}",
            "title": spec["title"],
            "created": created,
        })

    return results


def verify_dashboard_tickets(dashboard_url: str) -> dict[str, Any]:
    url = f"{dashboard_url.rstrip('/')}/api/tickets?page_size=100"
    res = requests.get(url, verify=False, timeout=25)
    res.raise_for_status()
    data = res.json()
    tickets = data.get("tickets", [])

    sources_count: dict[str, int] = {}
    web_url_domains: set[str] = set()

    for t in tickets:
        src = t.get("source", "unknown")
        sources_count[src] = sources_count.get(src, 0) + 1
        u = t.get("url", "")
        if u.startswith("https://") or u.startswith("http://"):
            domain = u.split("/")[2]
            web_url_domains.add(domain)

    return {
        "total": data.get("total", len(tickets)),
        "count": len(tickets),
        "by_source": sources_count,
        "domains": sorted(web_url_domains),
        "tickets": tickets,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed demo issues and MRs into Jira and GitLab")
    parser.add_argument("--jira-url", default=DEFAULT_JIRA_URL)
    parser.add_argument("--gitlab-url", default=DEFAULT_GITLAB_URL)
    parser.add_argument("--dashboard-url", default=DEFAULT_DASHBOARD_URL)
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=Path("var/benchmarks/strat-workflow/data/rfe-templates"),
    )
    args = parser.parse_args()

    print(f"[*] Seeding Jira at {args.jira_url}...")
    jira_results = seed_jira(args.jira_url, args.templates_dir)
    print(f"[+] Jira seeding complete: {len(jira_results)} issues processed.")

    print(f"[*] Seeding GitLab at {args.gitlab_url}...")
    gitlab_results = seed_gitlab(args.gitlab_url)
    print(f"[+] GitLab seeding complete: {len(gitlab_results)} items processed.")

    print(f"[*] Verifying Breadboard Dashboard tickets at {args.dashboard_url}...")
    verification = verify_dashboard_tickets(args.dashboard_url)
    print(f"[+] Verification: Total tickets = {verification['total']}")
    print(f"[+] Counts by source: {verification['by_source']}")
    print(f"[+] Observed domains: {verification['domains']}")


if __name__ == "__main__":
    main()
