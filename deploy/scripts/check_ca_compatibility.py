#!/usr/bin/env python3
"""Refuse implicit CA migration before deployment mutates an existing install."""
import ipaddress
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

from render_domain_manifest import transform_manifest


def permitted_names(manifest: str):
    dns_block = manifest.split('      dnsDomains:\n', 1)[1].split('      ipRanges:', 1)[0]
    ip_block = manifest.split('      ipRanges:\n', 1)[1].split('---', 1)[0]
    entries = lambda block: [line.strip().removeprefix('- ').strip('"') for line in block.splitlines() if line.strip().startswith('- ')]
    return set(entries(dns_block)), {ipaddress.ip_network(value) for value in entries(ip_block)}


def compatible(extension: str, expected_dns: set, expected_ips: set) -> bool:
    if 'Name Constraints: critical' not in extension or 'Excluded:' in extension:
        return False
    dns = set(re.findall(r'DNS:([^\s,]+)', extension))
    ips = {ipaddress.ip_network(value) for value in re.findall(r'IP:([^\s,]+)', extension)}
    return dns == expected_dns and ips == expected_ips


def main():
    root = Path(__file__).resolve().parents[2]
    manifest = transform_manifest((root / 'deploy/k8s/01-ca-issuer.yaml').read_text(), os.getenv('BREADBOARD_DOMAIN', 'local'))
    expected_dns, expected_ips = permitted_names(manifest)
    crd = subprocess.run(['kubectl', 'get', 'crd', 'certificates.cert-manager.io', '--ignore-not-found', '-o', 'name'], check=True, capture_output=True, text=True)
    if not crd.stdout.strip():
        return  # cert-manager is not installed yet on a fresh cluster.
    result = subprocess.run(['kubectl', 'get', 'certificate', 'internal-ca', '-n', 'ai-pipeline', '--ignore-not-found', '-o', 'json'], check=True, capture_output=True, text=True)
    if not result.stdout.strip():
        return  # Fresh managed installation: no root Certificate exists.
    existing = json.loads(result.stdout)['spec'].get('nameConstraints', {})
    permitted = existing.get('permitted', {})
    if (not existing.get('critical') or set(permitted.get('dnsDomains', [])) != expected_dns
            or {ipaddress.ip_network(value) for value in permitted.get('ipRanges', [])} != expected_ips):
        sys.exit('Existing CA specification differs from requested constraints. Refusing automatic CA migration; follow deploy/lima/README.md.')
    # Read only the public ConfigMap; no Secret/key access is needed for preflight.
    certificate = subprocess.run(['kubectl', 'get', 'configmap', 'internal-ca-cert', '-n', 'ai-pipeline', '-o', 'jsonpath={.data.ca\\.crt}'], check=True, capture_output=True).stdout
    with tempfile.TemporaryDirectory(prefix='breadboard-ca-check-') as directory:
        path = Path(directory) / 'ca.crt'
        path.write_bytes(certificate)
        extension = subprocess.run(['openssl', 'x509', '-in', str(path), '-noout', '-ext', 'nameConstraints'], check=True, capture_output=True, text=True).stdout
    if not compatible(extension, expected_dns, expected_ips):
        sys.exit('Existing CA constraints differ from the requested domain/manifest. Refusing automatic CA migration before applying changes. Use a disposable install or perform the explicit CA/leaf/image/client-trust migration in deploy/lima/README.md, then retry.')


if __name__ == '__main__':
    main()
