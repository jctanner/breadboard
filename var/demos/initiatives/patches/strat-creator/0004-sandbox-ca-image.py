#!/usr/bin/env python3
"""CC-75: add the emulator CA to the per-job sandbox image (mirror branch only).

Kind: environment (the emulators' private CA baked into the per-job sandbox image)

The corsair recipe (var/demos/fullsend-claude-workflow/ci/Containerfile) put the
public roots plus the local CA at /etc/ssl/certs/ca-certificates.crt in a derived
sandbox image, so OpenShell's TLS-terminating provider endpoints can verify the
relay ingress and the Jira emulator. strat-creator's job-owned gateway wrapper
builds the sandbox image from .fullsend/ci; when CC75_SANDBOX_CA (built by
strat-pipeline patch 0001) names a readable bundle, build from a private copy of
that context with the bundle added. The verified .fullsend checkout is untouched.
Usage: 0004-sandbox-ca-image.py <tree>
"""
import sys
from pathlib import Path

path = Path(sys.argv[1]) / ".fullsend/ci/with-fullsend-gateway.sh"
text = path.read_text()
OLD = '''podman --url "unix://$SOCKET" build --quiet --pull=never \\
  --build-arg "BASE_IMAGE=$FULLSEND_BASE_IMAGE" --tag "$FULLSEND_SANDBOX_IMAGE" \\
  --file "${BASH_SOURCE[0]%/*}/fullsend-sandbox.Containerfile" \\
  "${BASH_SOURCE[0]%/*}" >"$FULLSEND_OUTPUT_DIR/sandbox-build.log" 2>&1
'''
NEW = '''BUILD_CTX="${BASH_SOURCE[0]%/*}"
if [[ -n "${CC75_SANDBOX_CA:-}" && -r "$CC75_SANDBOX_CA" ]]; then
  # CC-75 emulator mirror: public roots plus the local emulator CA in the image.
  BUILD_CTX="$STRAT_PRIVATE_DIR/gateway/sandbox-context"
  mkdir -p "$BUILD_CTX"
  cp "${BASH_SOURCE[0]%/*}/fullsend-sandbox.Containerfile" "$BUILD_CTX/"
  cp "$CC75_SANDBOX_CA" "$BUILD_CTX/ca-bundle.pem"
  printf '\\nUSER root\\nCOPY ca-bundle.pem /etc/ssl/certs/ca-certificates.crt\\n' >>"$BUILD_CTX/fullsend-sandbox.Containerfile"
fi
podman --url "unix://$SOCKET" build --quiet --pull=never \\
  --build-arg "BASE_IMAGE=$FULLSEND_BASE_IMAGE" --tag "$FULLSEND_SANDBOX_IMAGE" \\
  --file "$BUILD_CTX/fullsend-sandbox.Containerfile" \\
  "$BUILD_CTX" >"$FULLSEND_OUTPUT_DIR/sandbox-build.log" 2>&1
'''
if text.count(OLD) != 1:
    raise SystemExit(f"{path}: expected one sandbox build command")
path.write_text(text.replace(OLD, NEW))
print("strat-creator 0004-sandbox-ca-image: applied")
