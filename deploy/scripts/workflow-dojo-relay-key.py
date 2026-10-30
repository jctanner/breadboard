#!/usr/bin/env python3
"""Provision Workflow Dojo's Model Relay API key as a Kubernetes Secret.

Idempotent. An existing Secret is kept while its key still authenticates
(and, for a key this script issued, has more than a week before expiry);
otherwise this integration's previous credentials are revoked and a new MaaS
key is issued with catalog access.

--stdin stores a key you created yourself (for example in the relay console)
after checking that it authenticates; that key is then kept on later runs.
--rotate forces a newly issued key. Keys stay in memory and reach kubectl on
stdin, never in process arguments or output.
"""

from __future__ import annotations

import argparse
import base64
import http.client
import json
import socket
import ssl
import subprocess
import sys
import time
from urllib.parse import urlencode

NAMESPACE = "ai-pipeline"
SECRET = "workflow-dojo-relay"
PROJECT = "vertex-shim-local"
CLIENT_ID = "workflow-dojo"
ADMIN_HOST = "relay.local"
API_HOST = "relay-api.local"
MIN_REMAINING_MS = 7 * 24 * 3600 * 1000
GRANTS = {
    "client_id": CLIENT_ID,
    "models": [],
    "backends": ["anthropic"],
    "catalog_models": True,
    "vertex_catalog_models": False,
    "mock_adc": False,
    "exchange_only": False,
}


def kubectl_json(*args: str) -> dict | None:
    result = subprocess.run(["kubectl", "-n", NAMESPACE, *args, "-o", "json"], capture_output=True, text=True)
    if result.returncode != 0:
        if "NotFound" in result.stderr:
            return None
        raise RuntimeError(f"kubectl {' '.join(args)} failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


def secret_value(name: str, key: str) -> str | None:
    secret = kubectl_json("get", "secret", name)
    data = (secret or {}).get("data", {})
    return base64.b64decode(data[key]).decode().strip() if key in data else None


def store_secret(data: dict[str, str]) -> None:
    """Replace the Secret's contents (kubectl apply on stdin; values never in argv)."""
    manifest = {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {"name": SECRET, "namespace": NAMESPACE, "labels": {"app": "workflow-dojo"}},
        "type": "Opaque",
        "stringData": data,
    }
    subprocess.run(["kubectl", "-n", NAMESPACE, "delete", "secret", SECRET, "--ignore-not-found"],
                   check=True, capture_output=True)
    applied = subprocess.run(["kubectl", "apply", "-f", "-"], input=json.dumps(manifest), capture_output=True, text=True)
    if applied.returncode != 0:
        raise RuntimeError(f"Could not store the key in Secret {SECRET}: {applied.stderr.strip()}")


class PinnedHTTPS(http.client.HTTPSConnection):
    """Connect to relay.local's address while verifying another virtual host.

    Some hosts only map relay.local in /etc/hosts; relay-api.local is served by
    the same proxy and certificate.
    """

    def __init__(self, host: str, address: str, context: ssl.SSLContext) -> None:
        super().__init__(host, 443, context=context, timeout=30)
        self._address = address

    def connect(self) -> None:
        sock = socket.create_connection((self._address, 443), self.timeout)
        self.sock = self._context.wrap_socket(sock, server_hostname=self.host)


def request(context, address, host, method, path, headers, body=None):
    conn = PinnedHTTPS(host, address, context)
    try:
        payload = None if body is None else json.dumps(body).encode()
        conn.request(method, path, body=payload, headers={**headers, "Content-Type": "application/json"})
        response = conn.getresponse()
        text = response.read().decode() or "null"
        return response.status, json.loads(text) if text.strip()[:1] in "[{n" else text
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rotate", action="store_true", help="issue a new key even if the current one works")
    parser.add_argument("--stdin", action="store_true", help="store the API key read from stdin instead of issuing one")
    options = parser.parse_args()

    ca = secret_value("model-relay-tls", "ca.crt")
    if not ca:
        raise SystemExit("Secret model-relay-tls has no ca.crt")
    context = ssl.create_default_context(cadata=ca)
    address = socket.gethostbyname(ADMIN_HOST)

    def authenticates(key: str) -> int:
        status, _ = request(context, address, API_HOST, "GET", "/v1/models", {"x-api-key": key})
        return status

    if options.stdin:
        supplied = sys.stdin.readline().strip()
        status = authenticates(supplied) if supplied else 0
        if status != 200:
            raise SystemExit(f"The supplied key does not authenticate against relay-api.local (status {status})")
        store_secret({"api-key": supplied, "source": "supplied"})
        print(json.dumps({"secret": SECRET, "action": "stored supplied key"}))
        return 0

    current_key = secret_value(SECRET, "api-key")
    current_id = secret_value(SECRET, "key-id")
    if current_key and not current_id and not options.rotate:
        status = authenticates(current_key)
        if status == 200:
            print(json.dumps({"secret": SECRET, "action": "kept supplied key"}))
            return 0
        print(f"Stored supplied key no longer authenticates (status {status}); issuing a new one", file=sys.stderr)

    admin_key = secret_value("model-relay-admin", "admin-api-key")
    if not admin_key:
        raise SystemExit("Secret model-relay-admin is missing; deploy Model Relay first (make host-deploy-relay)")
    admin = {"Authorization": f"Bearer {admin_key}"}
    base = f"/api/private/v1/projects/{PROJECT}/credentials"

    def admin_call(method, path, body=None):
        status, data = request(context, address, ADMIN_HOST, method, path, admin, body)
        if status >= 300:
            raise RuntimeError(f"relay admin {method} {path} -> {status}")
        return data

    listing = admin_call("GET", f"{base}?{urlencode({'limit': 500})}")
    rows = listing.get("items", []) if isinstance(listing, dict) else listing
    ours = [r for r in rows if r.get("client_id") == CLIENT_ID]

    if current_key and current_id and not options.rotate:
        row = next((r for r in ours if r.get("key_id") == current_id), None)
        expires = (row or {}).get("expires_at_ms") or (row or {}).get("expiresAt")
        fresh = row is not None and (not isinstance(expires, (int, float)) or expires - time.time() * 1000 > MIN_REMAINING_MS)
        status = authenticates(current_key)
        if fresh and status == 200:
            print(json.dumps({"secret": SECRET, "key_id": current_id, "action": "kept"}))
            return 0
        print(f"Existing key unusable (models status {status}, credential {'found' if row else 'missing'}); replacing",
              file=sys.stderr)

    for row in ours:
        admin_call("DELETE", f"{base}/{row['key_id']}")
    issued = admin_call("POST", base, {**GRANTS, "token_type": "maas", "name": "Workflow Dojo", "expiresIn": "90d"})
    try:
        store_secret({"api-key": issued["api_key"], "key-id": issued["key_id"], "source": "issued"})
    except RuntimeError:
        admin_call("DELETE", f"{base}/{issued['key_id']}")
        raise
    print(json.dumps({"secret": SECRET, "key_id": issued["key_id"], "action": "issued",
                      "revoked": [r["key_id"] for r in ours], "expires": issued.get("expiresAt")}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
