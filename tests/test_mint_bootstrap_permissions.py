"""Bootstrap installations from API permissions, never the UI inventory shape."""
import contextlib
import io
import json
from pathlib import Path
import ssl
import urllib.error
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "deploy/scripts/18-deploy-fullsend-mint-dev.sh").read_text()
BLOCK = SOURCE.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]


@pytest.mark.parametrize("missing_permissions", [None, "missing", "empty", "installation_mismatch", "malformed", "existing_installation_mismatch", "rollback_failure", "rollback_network", "missing_id", "bool_id", "nondict", "selected", "bad_inventory", "broader_app"])
def test_installation_grants_from_api_metadata(monkeypatch, missing_permissions):
    monkeypatch.setenv("BREADBOARD_CA_FILE", "/fixture/public-ca.crt")
    grants = []
    writes = []
    deletes = []
    expected = {str(1000+i): {"metadata": "read", "contents": "write" if i % 2 else "read",
                             "issues": "write" if i % 4 < 2 else "read",
                             "checks": "write" if i < 4 else "read"} for i in range(1, 9)}
    monkeypatch.setenv("EXPECTED_APP_PERMISSIONS", json.dumps(expected))
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    def request(req, **kwargs):
        assert kwargs["context"] is context
        assert kwargs["timeout"] == 30
        url = req.full_url
        status = 200
        if url.endswith("/private-key"):
            body = {"private_key": "fixture-key"}
        elif req.get_method() == "DELETE":
            writes.append("DELETE")
            deletes.append(url)
            if missing_permissions == "rollback_network" and url.endswith("/77"):
                raise urllib.error.URLError("fixture network failure")
            status, body = (503, None) if missing_permissions == "rollback_failure" else (204, None)
        elif req.get_method() == "POST":
            writes.append("POST")
            body = json.loads(req.data)
            grants.append(body["permissions"])
            status = 200 if missing_permissions == "existing_installation_mismatch" else 201
            body = {"id": 77, "repository_selection": "selected" if missing_permissions == "selected" else "all", "permissions": {} if missing_permissions in {"installation_mismatch", "existing_installation_mismatch", "rollback_failure", "rollback_network", "missing_id", "bool_id"} else body["permissions"]}
            if missing_permissions == "missing_id":
                body.pop("id")
            elif missing_permissions == "bool_id":
                body["id"] = True
            elif missing_permissions == "nondict":
                body = []
        elif "/api/v3/admin/apps/" in url:
            app_id = url.rsplit("/", 1)[-1]
            body = None if missing_permissions == "malformed" else ({} if missing_permissions == "missing" else {"permissions": {} if missing_permissions == "empty" else expected[app_id]})
        else:
            body = {"installations": [] if missing_permissions in {"existing_installation_mismatch", "rollback_failure"} else [{"id": 1, "owner": "org", "repositories": ["org/old"]}]}  # Admin UI intentionally omits permissions.
        if missing_permissions == "bad_inventory" and "/admin/api/apps/" in url:
            body = {"installations": [None]}
        if missing_permissions == "broader_app" and "/api/v3/admin/apps/" in url:
            body = {"permissions": {**expected["1001"], "administration": "write"}}
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = status
        response.read.return_value = json.dumps(body).encode()
        return response

    with mock.patch("sys.argv", ["fixture", "https://fixture.invalid/api/v3", "https://fixture.invalid", "fixture", "org"]), \
            mock.patch("urllib.request.urlopen", side_effect=request), \
            mock.patch("ssl.create_default_context", return_value=context) as tls, \
            contextlib.redirect_stdout(io.StringIO()):
        if missing_permissions in {"missing", "empty", "malformed", "bad_inventory", "broader_app"}:
            with pytest.raises(SystemExit, match="invalid installation inventory" if missing_permissions == "bad_inventory" else "could not read permissions"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert not grants
            assert not writes
        elif missing_permissions in {"installation_mismatch", "selected"}:
            with pytest.raises(SystemExit, match="installation permissions do not match"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert writes == ["DELETE", "POST", "DELETE"]
            assert deletes == ["https://fixture.invalid/admin/api/apps/1001/installations/1",
                               "https://fixture.invalid/admin/api/apps/1001/installations/77"]
        elif missing_permissions == "existing_installation_mismatch":
            with pytest.raises(SystemExit, match="existing installation left unchanged"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert writes == ["POST"]
        elif missing_permissions == "rollback_failure":
            with pytest.raises(SystemExit, match="rollback failed: HTTP 503"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert writes == ["POST", "DELETE"]
        elif missing_permissions in {"rollback_network", "missing_id", "bool_id", "nondict"}:
            message = "rollback failed: network error" if missing_permissions == "rollback_network" else "new installation ID invalid"
            with pytest.raises(SystemExit, match=message):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            if missing_permissions == "rollback_network":
                assert deletes[-1].endswith("/77")
            else:
                assert deletes == ["https://fixture.invalid/admin/api/apps/1001/installations/1"]
        else:
            exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert grants == list(expected.values())
        tls.assert_called_once_with(cafile="/fixture/public-ca.crt")
        assert context.check_hostname
        assert context.verify_mode == ssl.CERT_REQUIRED
