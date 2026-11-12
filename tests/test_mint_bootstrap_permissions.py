"""Bootstrap installations from API permissions, never the UI inventory shape."""
import contextlib
import io
import json
from pathlib import Path
import ssl
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "deploy/scripts/18-deploy-fullsend-mint-dev.sh").read_text()
BLOCK = SOURCE.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]


@pytest.mark.parametrize("missing_permissions", [None, "missing", "empty", "installation_mismatch", "malformed", "existing_installation_mismatch", "rollback_failure"])
def test_installation_grants_from_api_metadata(monkeypatch, missing_permissions):
    monkeypatch.setenv("BREADBOARD_CA_FILE", "/fixture/public-ca.crt")
    grants = []
    writes = []
    expected = {str(1000+i): {"metadata": "read", "contents": "write" if i % 2 else "read",
                             "issues": "write" if i % 4 < 2 else "read",
                             "checks": "write" if i < 4 else "read"} for i in range(1, 9)}
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

    def request(req, **kwargs):
        assert kwargs["context"] is context
        url = req.full_url
        status = 200
        if url.endswith("/private-key"):
            body = {"private_key": "fixture-key"}
        elif req.get_method() == "DELETE":
            writes.append("DELETE")
            status, body = (503, None) if missing_permissions == "rollback_failure" else (204, None)
        elif req.get_method() == "POST":
            writes.append("POST")
            body = json.loads(req.data)
            grants.append(body["permissions"])
            status = 200 if missing_permissions == "existing_installation_mismatch" else 201
            body = {"id": 1, "permissions": {} if missing_permissions in {"installation_mismatch", "existing_installation_mismatch", "rollback_failure"} else body["permissions"]}
        elif "/api/v3/admin/apps/" in url:
            app_id = url.rsplit("/", 1)[-1]
            body = None if missing_permissions == "malformed" else ({} if missing_permissions == "missing" else {"permissions": {} if missing_permissions == "empty" else expected[app_id]})
        else:
            body = {"installations": [] if missing_permissions in {"existing_installation_mismatch", "rollback_failure"} else [{"id": 1, "owner": "org", "repositories": ["org/old"]}]}  # Admin UI intentionally omits permissions.
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = status
        response.read.return_value = json.dumps(body).encode()
        return response

    with mock.patch("sys.argv", ["fixture", "https://fixture.invalid/api/v3", "https://fixture.invalid", "fixture", "org"]), \
            mock.patch("urllib.request.urlopen", side_effect=request), \
            mock.patch("ssl.create_default_context", return_value=context) as tls, \
            contextlib.redirect_stdout(io.StringIO()):
        if missing_permissions in {"missing", "empty", "malformed"}:
            with pytest.raises(SystemExit, match="could not read permissions"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert not grants
            assert not writes
        elif missing_permissions == "installation_mismatch":
            with pytest.raises(SystemExit, match="installation permissions do not match"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert writes == ["DELETE", "POST", "DELETE"]
        elif missing_permissions == "existing_installation_mismatch":
            with pytest.raises(SystemExit, match="existing installation left unchanged"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert writes == ["POST"]
        elif missing_permissions == "rollback_failure":
            with pytest.raises(SystemExit, match="rollback failed: HTTP 503"):
                exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert writes == ["POST", "DELETE"]
        else:
            exec(compile(BLOCK, "mint-bootstrap", "exec"), {})
            assert grants == list(expected.values())
        tls.assert_called_once_with(cafile="/fixture/public-ca.crt")
        assert context.check_hostname
        assert context.verify_mode == ssl.CERT_REQUIRED
