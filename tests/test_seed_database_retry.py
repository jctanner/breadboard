"""Retry only explicit emulator lock responses on replay-safe operations."""
import importlib.util
import io
import json
from pathlib import Path
from unittest import mock
import urllib.error

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("seed_retry", ROOT / "deploy/fullsend/seed/emulator.py")
helper = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(helper)


def locked(message="Database is busy, retry the request", status=503):
    return urllib.error.HTTPError("https://fixture.invalid", status, "busy", {},
        io.BytesIO(json.dumps({"message": message,
                              "errors": [{"code": "sqlite_locked"}]}).encode()))


@pytest.mark.parametrize(("method", "path"), [("GET", "/repos/o/r"), ("PUT", "/repos/o/r/config"), ("DELETE", "/repos/o/r/config"), ("POST", "/orgs"),
                                             ("POST", "/orgs/o/repos")])
def test_retry_explicit_lock(method, path):
    response = mock.MagicMock()
    response.__enter__.return_value = response
    response.status = 200
    response.read.return_value = b'{"ok":true}'
    with mock.patch("urllib.request.urlopen", side_effect=[locked(), response]) as request, \
            mock.patch.object(helper.time, "sleep") as sleep:
        assert helper.api_request(method, path) == (200, {"ok": True})
        assert request.call_count == 2
        sleep.assert_called_once_with(1)


@pytest.mark.parametrize(("method", "path", "message", "status"), [
    ("POST", "/repos/o/r/issues", "Database is busy, retry the request", 503),
    ("GET", "/repos/o/r", "Database was busy and the write cannot be replayed safely", 503),
    ("GET", "/repos/o/r", "Database is busy, retry the request", 401),
])
def test_do_not_replay_unsafe_or_nontransient_errors(method, path, message, status):
    with mock.patch("urllib.request.urlopen", side_effect=locked(message, status)) as request, \
            mock.patch.object(helper.time, "sleep") as sleep:
        assert helper.api_request(method, path)[0] == status
        assert request.call_count == 1
        sleep.assert_not_called()


def test_retry_limit_preserves_failure():
    with mock.patch("urllib.request.urlopen", side_effect=[locked() for _ in range(4)]) as request, \
            mock.patch.object(helper.time, "sleep") as sleep:
        assert helper.api_request("GET", "/orgs/o")[0] == 503
        assert request.call_count == 4
        assert [call.args[0] for call in sleep.call_args_list] == [1, 2, 4]


@pytest.mark.parametrize("kind", ["org", "repo"])
def test_conflict_requires_confirmed_resource(kind):
    function = helper.ensure_org if kind == "org" else helper.ensure_repo
    with mock.patch.object(helper, "api_request", side_effect=[(404, None), (422, {}), (404, None)]):
        with pytest.raises(RuntimeError, match="not confirmed"):
            function()
    with mock.patch.object(helper, "api_request", side_effect=[(404, None), (422, {}), (200, {"default_branch": "main"})]):
        function()


@pytest.mark.parametrize("payload", [b"maintenance", b"\xff", b'{"errors":7}', b'{"errors":[{"code":"unavailable"}]}'])
def test_non_lock_503_is_not_retried(payload):
    error = urllib.error.HTTPError("https://fixture.invalid", 503, "busy", {}, io.BytesIO(payload))
    with mock.patch("urllib.request.urlopen", side_effect=error) as request, \
            mock.patch.object(helper.time, "sleep") as sleep:
        assert helper.api_request("GET", "/orgs/o")[0] == 503
        assert request.call_count == 1
        sleep.assert_not_called()


def test_repo_conflict_without_branch_is_not_confirmed():
    with mock.patch.object(helper, "api_request", side_effect=[(404, None), (422, {}), (200, {})]):
        with pytest.raises(RuntimeError, match="default branch"):
            helper.ensure_repo()
