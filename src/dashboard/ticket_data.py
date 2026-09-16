"""Live ticket aggregation for the Breadboard landing page."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import quote, urlsplit

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning


@dataclass
class TicketResult:
    tickets: list[dict[str, Any]] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)


def _base_url(value: str, *suffixes: str) -> str:
    result = value.rstrip("/")
    for suffix in suffixes:
        if result.endswith(suffix):
            result = result[: -len(suffix)]
            break
    return result.rstrip("/")


class TicketAggregator:
    """Fetch and normalize all Jira, GitHub, and GitLab work items."""

    CLOSED_STATES = {"closed", "done", "resolved", "merged", "completed"}

    def __init__(self) -> None:
        self.verify_tls = os.getenv("NO_SSL_VERIFY", "0") != "1"
        if not self.verify_tls:
            urllib3.disable_warnings(InsecureRequestWarning)
        self.session = requests.Session()
        self.timeout = float(os.getenv("BREADBOARD_TICKET_TIMEOUT", "10"))
        self.max_pages = max(1, int(os.getenv("BREADBOARD_TICKET_MAX_PAGES", "100")))
        self.errors: list[dict[str, str]] = []

        jira = os.getenv(
            "BREADBOARD_JIRA_URL",
            "https://jira-emulator.ai-pipeline.svc.cluster.local",
        )
        self.jira_url = _base_url(jira, "/rest/api/2", "/rest/api/3")
        self.jira_ui = os.getenv("JIRA_UI_URL", "https://jira.local").rstrip("/")

        self.github_api = os.getenv(
            "GITHUB_API_URL",
            "https://github-emulator.ai-pipeline.svc.cluster.local/api/v3",
        ).rstrip("/")
        self.github_ui = os.getenv("GITHUB_UI_URL", "https://github.local").rstrip("/")

        self.gitlab_api = os.getenv(
            "GITLAB_API_URL",
            "https://gitlab-emulator.ai-pipeline.svc.cluster.local/api/v4",
        ).rstrip("/")
        self.gitlab_ui = os.getenv("GITLAB_UI_URL", "https://gitlab.local").rstrip("/")

        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.gitlab_token = os.getenv("GITLAB_TOKEN", "")

    def _get(self, source: str, url: str, **params: Any) -> Any:
        headers: dict[str, str] = {}
        if source == "github" and self.github_token:
            headers["Authorization"] = f"token {self.github_token}"
        elif source == "gitlab" and self.gitlab_token:
            headers["PRIVATE-TOKEN"] = self.gitlab_token
        try:
            response = self.session.get(
                url,
                params=params,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_tls,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            self.errors.append({"source": source, "message": str(exc)})
            return None

    def _jira(self) -> list[dict[str, Any]]:
        auth = None
        jira_user = os.getenv("BREADBOARD_JIRA_USER", os.getenv("JIRA_USER", ""))
        jira_token = os.getenv("BREADBOARD_JIRA_TOKEN", os.getenv("JIRA_TOKEN", ""))
        if jira_user and jira_token:
            auth = (jira_user, jira_token)

        start_at = 0
        tickets: list[dict[str, Any]] = []
        for _ in range(self.max_pages):
            try:
                response = self.session.post(
                    f"{self.jira_url}/rest/api/2/search",
                    json={
                        "jql": "ORDER BY updated DESC",
                        "startAt": start_at,
                        "maxResults": 100,
                        "fields": [
                            "summary", "status", "priority", "issuetype", "project",
                            "labels", "assignee", "reporter", "created", "updated",
                        ],
                    },
                    auth=auth,
                    timeout=self.timeout,
                    verify=self.verify_tls,
                )
                response.raise_for_status()
                payload = response.json()
            except (requests.RequestException, ValueError) as exc:
                self.errors.append({"source": "jira", "message": str(exc)})
                break

            raw = payload.get("issues", []) if isinstance(payload, dict) else []
            for issue in raw:
                fields = issue.get("fields", {})
                project = fields.get("project") or {}
                issue_type = fields.get("issuetype") or {}
                status = fields.get("status") or {}
                priority = fields.get("priority") or {}
                tickets.append({
                    "source": "jira",
                    "type": issue_type.get("name", "Issue"),
                    "category": "issue",
                    "key": issue.get("key", ""),
                    "title": fields.get("summary", ""),
                    "state": status.get("name", ""),
                    "labels": fields.get("labels") or [],
                    "project": project.get("key", ""),
                    "project_name": project.get("name", ""),
                    "repository": "",
                    "priority": priority.get("name", ""),
                    "author": (fields.get("reporter") or {}).get("displayName", ""),
                    "assignee": (fields.get("assignee") or {}).get("displayName", ""),
                    "created": fields.get("created", ""),
                    "updated": fields.get("updated", ""),
                    "url": f"{self.jira_ui}/issue/{quote(issue.get('key', ''))}",
                })

            total = payload.get("total", 0) if isinstance(payload, dict) else 0
            start_at += len(raw)
            if not raw or start_at >= total:
                break
        return tickets

    def _github_repositories(self) -> list[dict[str, Any]]:
        configured = [
            item.strip() for item in os.getenv("GITHUB_REPOS", "").split(",") if item.strip()
        ]
        if configured:
            return [{"full_name": item} for item in configured]

        repos: list[dict[str, Any]] = []
        endpoints = ["user/repos", "repositories"] if self.github_token else ["repositories"]
        payload = None
        for endpoint in endpoints:
            errors_before = len(self.errors)
            payload = self._get(
                "github", f"{self.github_api}/{endpoint}", page=1, per_page=100
            )
            if isinstance(payload, list):
                break
            # A placeholder or insufficient token should not prevent the
            # public repository inventory from being used as a fallback.
            del self.errors[errors_before:]

        if not isinstance(payload, list):
            return repos
        selected_endpoint = endpoint
        repos.extend(payload)
        if len(payload) < 100:
            return repos
        for page in range(1, self.max_pages + 1):
            if page == 1:
                continue
            payload = self._get(
                "github", f"{self.github_api}/{selected_endpoint}", page=page, per_page=100
            )
            if not isinstance(payload, list) or not payload:
                break
            repos.extend(payload)
            if len(payload) < 100:
                break
        return repos

    def _github(self) -> list[dict[str, Any]]:
        tickets: list[dict[str, Any]] = []
        for repo in self._github_repositories():
            full_name = repo.get("full_name", "")
            if not full_name:
                continue
            for page in range(1, self.max_pages + 1):
                payload = self._get(
                    "github",
                    f"{self.github_api}/repos/{full_name}/issues",
                    state="all",
                    page=page,
                    per_page=100,
                )
                if not isinstance(payload, list) or not payload:
                    break
                for item in payload:
                    is_pr = bool(item.get("pull_request"))
                    default_path = (
                        f"/{full_name}/"
                        f"{'pulls' if is_pr else 'issues'}/{item.get('number', '')}"
                    )
                    api_url = item.get("html_url", "")
                    item_path = urlsplit(api_url).path if api_url else default_path
                    item_path = item_path or default_path
                    if not item_path.startswith("/ui/"):
                        item_path = f"/ui{item_path}"
                    tickets.append({
                        "source": "github",
                        "type": "Pull request" if is_pr else "Issue",
                        "category": "pull_request" if is_pr else "issue",
                        "key": f"{full_name}#{item.get('number', '')}",
                        "title": item.get("title", ""),
                        "state": item.get("state", ""),
                        "labels": [label.get("name", "") for label in item.get("labels", [])],
                        "project": "",
                        "project_name": "",
                        "repository": full_name,
                        "priority": "",
                        "author": (item.get("user") or {}).get("login", ""),
                        "assignee": (item.get("assignee") or {}).get("login", ""),
                        "created": item.get("created_at", ""),
                        "updated": item.get("updated_at", ""),
                        "url": f"{self.github_ui}{item_path}",
                    })
                if len(payload) < 100:
                    break
        return tickets

    def _gitlab_projects(self) -> list[dict[str, Any]]:
        configured = [
            item.strip() for item in os.getenv("GITLAB_PROJECTS", "").split(",") if item.strip()
        ]
        if configured:
            return [{"id": item, "path_with_namespace": item} for item in configured]

        projects: list[dict[str, Any]] = []
        for page in range(1, self.max_pages + 1):
            payload = self._get(
                "gitlab", f"{self.gitlab_api}/projects", page=page, per_page=100
            )
            if not isinstance(payload, list) or not payload:
                break
            projects.extend(payload)
            if len(payload) < 100:
                break
        return projects

    def _gitlab(self) -> list[dict[str, Any]]:
        tickets: list[dict[str, Any]] = []
        for project in self._gitlab_projects():
            project_ref = project.get("id") or project.get("path_with_namespace", "")
            project_name = project.get("path_with_namespace", str(project_ref))
            encoded_ref = quote(str(project_ref), safe="")
            for kind, endpoint, type_name in (
                ("issues", "issues", "issue"),
                ("merge_requests", "merge_requests", "merge_request"),
            ):
                for page in range(1, self.max_pages + 1):
                    payload = self._get(
                        "gitlab",
                        f"{self.gitlab_api}/projects/{encoded_ref}/{endpoint}",
                        state="all",
                        page=page,
                        per_page=100,
                    )
                    if not isinstance(payload, list) or not payload:
                        break
                    for item in payload:
                        iid = item.get("iid", item.get("id", ""))
                        tickets.append({
                            "source": "gitlab",
                            "type": "Merge request" if type_name == "merge_request" else "Issue",
                            "category": type_name,
                            "key": f"{project_name}!{iid}" if type_name == "merge_request" else f"{project_name}#{iid}",
                            "title": item.get("title", ""),
                            "state": item.get("state", ""),
                            "labels": item.get("labels") or [],
                            "project": str(project_ref),
                            "project_name": project_name,
                            "repository": project_name,
                            "priority": "",
                            "author": (item.get("author") or {}).get("username", ""),
                            "assignee": ((item.get("assignees") or [{}])[0]).get("username", "") if item.get("assignees") else "",
                            "created": item.get("created_at", ""),
                            "updated": item.get("updated_at", ""),
                            "url": item.get("web_url") or (
                                f"{self.gitlab_ui}/{project_name}/-/"
                                f"{'merge_requests' if type_name == 'merge_request' else 'issues'}/{iid}"
                            ),
                        })
                    if len(payload) < 100:
                        break
        return tickets

    def collect(
        self,
        *,
        query: str = "",
        source: str = "",
        type_name: str = "",
        category: str = "",
        state: str = "",
        label: str = "",
        project: str = "",
    ) -> TicketResult:
        tickets = self._jira() + self._github() + self._gitlab()
        query_lower = query.strip().lower()
        label_lower = label.strip().lower()
        project_lower = project.strip().lower()
        filtered = []
        for ticket in tickets:
            searchable = " ".join([
                ticket.get("key", ""), ticket.get("title", ""), ticket.get("source", ""),
                ticket.get("project", ""), ticket.get("project_name", ""),
                ticket.get("repository", ""), " ".join(ticket.get("labels", [])),
            ]).lower()
            if query_lower and query_lower not in searchable:
                continue
            if source and ticket["source"] != source:
                continue
            if type_name and type_name.lower() not in ticket.get("type", "").lower():
                continue
            if category and ticket.get("category", "") != category:
                continue
            if not state and ticket.get("state", "").strip().lower() in self.CLOSED_STATES:
                continue
            if state and ticket["state"].lower() != state.lower():
                continue
            if label_lower and label_lower not in {item.lower() for item in ticket["labels"]}:
                continue
            if project_lower and project_lower not in (
                ticket.get("project", "") + " " + ticket.get("project_name", "") + " " + ticket.get("repository", "")
            ).lower():
                continue
            filtered.append(ticket)
        filtered.sort(key=lambda item: item.get("updated", ""), reverse=True)
        return TicketResult(filtered, self.errors)
