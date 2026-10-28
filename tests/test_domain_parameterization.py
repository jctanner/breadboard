"""Unit tests for BREADBOARD_DOMAIN ingress parameterization."""

import importlib.util
import os
from pathlib import Path
from unittest import mock

import pytest

from src.dashboard.job_scripts import (
    get_allowed_script_hosts,
    normalize_script_spec,
)
from src.dashboard.ticket_data import TicketAggregator
from src.dashboard.webapp import create_app, get_breadboard_domain, get_service_urls
from src.dashboard.fullsend_onboarding import OnboardingConfig

RENDER_SCRIPT = Path(__file__).parents[1] / "deploy/scripts/render_domain_manifest.py"
RENDER_SPEC = importlib.util.spec_from_file_location("render_domain_manifest", RENDER_SCRIPT)
RENDER_MODULE = importlib.util.module_from_spec(RENDER_SPEC)
assert RENDER_SPEC and RENDER_SPEC.loader
RENDER_SPEC.loader.exec_module(RENDER_MODULE)
transform_manifest = RENDER_MODULE.transform_manifest

MODULE_PATH = Path(__file__).parents[1] / "src/fullsend-dashboard/app.py"
SPEC = importlib.util.spec_from_file_location("fullsend_dashboard_app", MODULE_PATH)
FS_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(FS_MODULE)
FullsendCollector = FS_MODULE.FullsendCollector


def test_breadboard_domain_helper():
    with mock.patch.dict(os.environ, {}, clear=True):
        assert get_breadboard_domain() == "local"

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "local"}):
        assert get_breadboard_domain() == "local"

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "bb.internal"}):
        assert get_breadboard_domain() == "bb.internal"

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": " .foo.bar. "}):
        assert get_breadboard_domain() == "foo.bar"


def test_service_urls():
    with mock.patch.dict(os.environ, {}, clear=True):
        urls = get_service_urls()
        assert urls["github"] == "https://github.local"
        assert urls["jira"] == "https://jira.local"
        assert urls["gitlab"] == "https://gitlab.local"
        assert urls["mlflow"] == "http://mlflow.local"
        assert urls["markovd"] == "http://markovd.local"
        assert urls["observatory"] == "https://observatory.local"
        assert urls["fullsend"] == "https://fullsend.local"
        assert urls["orgpulse"] == "https://orgpulse.local"
        assert urls["relay"] == "https://relay.local"
        assert urls["hooksink_admin"] == "https://hooksink-admin.local"

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "bb.internal"}, clear=True):
        urls = get_service_urls()
        assert urls["github"] == "https://github.bb.internal"
        assert urls["jira"] == "https://jira.bb.internal"
        assert urls["gitlab"] == "https://gitlab.bb.internal"
        assert urls["mlflow"] == "http://mlflow.bb.internal"
        assert urls["markovd"] == "http://markovd.bb.internal"
        assert urls["observatory"] == "https://observatory.bb.internal"
        assert urls["fullsend"] == "https://fullsend.bb.internal"
        assert urls["orgpulse"] == "https://orgpulse.bb.internal"
        assert urls["relay"] == "https://relay.bb.internal"
        assert urls["hooksink_admin"] == "https://hooksink-admin.bb.internal"

    # Explicit URL override takes precedence
    with mock.patch.dict(
        os.environ,
        {"BREADBOARD_DOMAIN": "bb.internal", "GITHUB_UI_URL": "https://custom.github.com"},
        clear=True,
    ):
        urls = get_service_urls()
        assert urls["github"] == "https://custom.github.com"
        assert urls["jira"] == "https://jira.bb.internal"


def test_ticket_data_collector_domain():
    with mock.patch.dict(os.environ, {}, clear=True):
        collector = TicketAggregator()
        assert collector.github_ui == "https://github.local"
        assert collector.jira_ui == "https://jira.local"
        assert collector.gitlab_ui == "https://gitlab.local"

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "bb.internal"}, clear=True):
        collector = TicketAggregator()
        assert collector.github_ui == "https://github.bb.internal"
        assert collector.jira_ui == "https://jira.bb.internal"
        assert collector.gitlab_ui == "https://gitlab.bb.internal"


def test_job_scripts_allowed_hosts():
    with mock.patch.dict(os.environ, {}, clear=True):
        hosts = get_allowed_script_hosts()
        assert "github.com" in hosts
        assert "github.local" in hosts
        assert "gitlab.local" in hosts
        assert "github.bb.internal" not in hosts

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "bb.internal"}, clear=True):
        hosts = get_allowed_script_hosts()
        assert "github.com" in hosts
        assert "github.local" in hosts
        assert "gitlab.local" in hosts
        assert "github.bb.internal" in hosts
        assert "gitlab.bb.internal" in hosts

        commit = "a" * 40
        spec = normalize_script_spec({
            "repo": "https://github.bb.internal/org/repo",
            "ref": commit,
            "path": "script.sh",
        })
        assert spec["repo"] == "https://github.bb.internal/org/repo"

    # In default mode, bb.internal is rejected
    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "local"}, clear=True):
        commit = "a" * 40
        with pytest.raises(ValueError, match="script.repo host must be one of"):
            normalize_script_spec({
                "repo": "https://github.bb.internal/org/repo",
                "ref": commit,
                "path": "script.sh",
            })


def test_fullsend_onboarding_domain():
    with mock.patch.dict(os.environ, {}, clear=True):
        cfg = OnboardingConfig()
        assert cfg.server_url == "https://github.local"
        assert cfg.ui_url == "https://github.local"

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "bb.internal"}, clear=True):
        cfg = OnboardingConfig()
        assert cfg.server_url == "https://github.bb.internal"
        assert cfg.ui_url == "https://github.bb.internal"


def test_fullsend_collector_domain():
    with mock.patch.dict(os.environ, {}, clear=True):
        collector = FullsendCollector()
        assert collector.github_ui == "https://github.local"

    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "bb.internal"}, clear=True):
        collector = FullsendCollector()
        assert collector.github_ui == "https://github.bb.internal"


def test_dashboard_layout_navbar_links():
    with mock.patch.dict(os.environ, {"BREADBOARD_DOMAIN": "bb.internal"}, clear=True):
        app = create_app()
        client = app.test_client()
        resp = client.get("/")
        assert resp.status_code == 200
        html = resp.get_data(as_text=True)
        assert 'href="https://github.bb.internal"' in html
        assert 'href="https://jira.bb.internal"' in html
        assert 'href="https://gitlab.bb.internal"' in html
        assert 'href="http://mlflow.bb.internal"' in html
        assert 'href="https://observatory.bb.internal"' in html
        assert 'href="https://fullsend.bb.internal"' in html
        assert 'href="https://orgpulse.bb.internal"' in html
        assert 'href="https://relay.bb.internal"' in html
        assert 'href="https://hooksink-admin.bb.internal"' in html


def test_transform_manifest_noop_for_local():
    sample = """apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: github-emulator-tls
spec:
  dnsNames:
    - github-emulator.ai-pipeline.svc.cluster.local
    - github.local
"""
    assert transform_manifest(sample, "local") == sample
    assert transform_manifest(sample, "") == sample


def test_transform_manifest_certificates():
    sample = """apiVersion: cert-manager.io/v1
kind: Certificate
spec:
  dnsNames:
    - "*.ai-pipeline.svc.cluster.local"
    - "*.local"
    - github-emulator.ai-pipeline.svc.cluster.local
    - github.local
"""
    result = transform_manifest(sample, "bb.internal")
    assert '- "*.ai-pipeline.svc.cluster.local"' in result
    assert "- github-emulator.ai-pipeline.svc.cluster.local" in result
    assert "- github.local" in result
    assert "- github.bb.internal" in result
    assert '- "*.local"' in result
    assert '- "*.bb.internal"' in result
    # Invariant: cluster.local must NEVER be modified
    assert "github-emulator.ai-pipeline.svc.cluster.bb.internal" not in result


def test_transform_manifest_ingress():
    sample = """apiVersion: networking.k8s.io/v1
kind: Ingress
spec:
  tls:
  - hosts:
    - github-emulator.ai-pipeline.svc.cluster.local
    - github.local
  rules:
  - host: github-emulator.ai-pipeline.svc.cluster.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: github-emulator
            port:
              number: 443
  - host: github.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: github-emulator
            port:
              number: 443
"""
    result = transform_manifest(sample, "bb.internal")
    assert "- github.local" in result
    assert "- github.bb.internal" in result
    assert "- host: github.local" in result
    assert "- host: github.bb.internal" in result
    assert "- host: github-emulator.ai-pipeline.svc.cluster.local" in result


def test_transform_manifest_coredns():
    sample = """apiVersion: v1
kind: ConfigMap
data:
  fullsend-local.override: |
    rewrite stop name exact github.local ingress-proxy.ai-pipeline.svc.cluster.local answer auto
"""
    result = transform_manifest(sample, "bb.internal")
    assert "rewrite stop name exact github.local ingress-proxy.ai-pipeline.svc.cluster.local answer auto" in result
    assert "rewrite stop name exact github.bb.internal ingress-proxy.ai-pipeline.svc.cluster.local answer auto" in result


def test_transform_manifest_env_vars():
    sample = """apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: proxy
        env:
        - name: BREADBOARD_DOMAIN
          value: "local"
        - name: GITHUB_UI_URL
          value: https://github.local
"""
    result = transform_manifest(sample, "bb.internal")
    assert 'name: BREADBOARD_DOMAIN\n          value: "bb.internal"' in result
    assert 'name: GITHUB_UI_URL\n          value: https://github.bb.internal' in result

