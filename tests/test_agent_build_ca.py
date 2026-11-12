"""Agent builds must validate public CA input before invoking the engine."""
import os
from pathlib import Path
import shutil
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def public_ca(tmp_path_factory):
    if not shutil.which("openssl"):
        pytest.skip("OpenSSL required")
    root = tmp_path_factory.mktemp("agent-ca")
    cert = root / "ca.crt"
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
        "-keyout", str(root / "key.pem"), "-out", str(cert),
        "-subj", "/CN=Agent build test", "-days", "1",
    ], check=True, capture_output=True)
    subprocess.run(["openssl", "x509", "-in", str(cert), "-addtrust", "serverAuth",
                    "-trustout", "-out", str(root / "trusted-ca.pem")],
                   check=True, capture_output=True)
    return cert


@pytest.mark.parametrize("script", ["05-build-images.sh", "05b-build-agent.sh"])
@pytest.mark.parametrize("ca_state", ["unavailable", "empty", "invalid", "valid", "appended_key", "prepended_key", "bundle", "trusted_bundle", "legacy_bundle", "corrupt", "trusted_only", "legacy_only"])
@pytest.mark.parametrize("relative_root", [False, True])
def test_agent_build_requires_valid_ca(tmp_path, public_ca, script, ca_state, relative_root):
    project = tmp_path / "project"
    dockerfile = project / "deploy/pipeline-agent/Dockerfile"
    dockerfile.parent.mkdir(parents=True)
    dockerfile.touch()
    commands = tmp_path / "commands"
    commands.mkdir()
    marker = tmp_path / "engine-called"
    captured = tmp_path / "captured-ca.crt"
    stubs = {
        "docker": '#!/bin/sh\ntouch "$ENGINE_MARKER"\ncp internal-ca.crt "$CA_CAPTURE"\nexit 77\n',
        # The grouped builder should reuse the completed dashboard only.
        "sudo": '#!/bin/sh\necho docker.io/library/pipeline-dashboard:latest\n',
        "kubectl": '''#!/bin/sh
case "$CA_STATE" in
 unavailable) exit 4 ;;
 empty) exit 0 ;;
 invalid) echo not-a-certificate ;;
 valid) cat "$PUBLIC_CA" ;;
 appended_key) cat "$PUBLIC_CA" "${PUBLIC_CA%/*}/key.pem" ;;
 prepended_key) cat "${PUBLIC_CA%/*}/key.pem" "$PUBLIC_CA" ;;
 bundle) cat "$PUBLIC_CA" "$PUBLIC_CA" ;;
 trusted_bundle) cat "${PUBLIC_CA%/*}/trusted-ca.pem" "$PUBLIC_CA" ;;
 corrupt) echo '-----BEGIN CERTIFICATE-----'; echo MAA=; echo '-----END CERTIFICATE-----' ;;
 trusted_only) cat "${PUBLIC_CA%/*}/trusted-ca.pem" ;;
 legacy_only) sed 's/BEGIN CERTIFICATE/BEGIN X509 CERTIFICATE/; s/END CERTIFICATE/END X509 CERTIFICATE/' "$PUBLIC_CA" ;;
 legacy_bundle) sed 's/BEGIN CERTIFICATE/BEGIN X509 CERTIFICATE/; s/END CERTIFICATE/END X509 CERTIFICATE/' "$PUBLIC_CA"; cat "$PUBLIC_CA" ;;
esac
''',
    }
    for name, body in stubs.items():
        path = commands / name
        path.write_text(body)
        path.chmod(0o755)
    result = subprocess.run(
        ["bash", str(ROOT / "deploy/scripts" / script)],
        env={**os.environ, "PATH": f"{commands}:{os.environ['PATH']}",
             "PROJECT_ROOT": "project" if relative_root else str(project), "FORCE_REBUILD": "0",
             "CA_STATE": ca_state, "PUBLIC_CA": str(public_ca),
             "ENGINE_MARKER": str(marker), "CA_CAPTURE": str(captured)},
        cwd=tmp_path, capture_output=True, text=True, timeout=10,
    )
    if ca_state in {"valid", "appended_key", "prepended_key"}:
        assert marker.exists(), result.stdout + result.stderr
        assert result.returncode == 77
        assert captured.read_text() == public_ca.read_text()
        assert "PRIVATE KEY" not in captured.read_text()
    else:
        assert result.returncode != 0
        expected_error = {
            "unavailable": "Could not read internal-ca-cert",
            "empty": "internal-ca-cert is empty",
            "corrupt": "not a valid X509 certificate",
        }.get(ca_state, "must contain exactly one certificate")
        assert expected_error in result.stderr
        assert not marker.exists(), result.stdout + result.stderr
    assert not (project / "internal-ca.crt").exists()
