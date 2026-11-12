#!/usr/bin/env python3
"""Copy a pinned image's public policy and migrate OpenShell 0.1 TLS spelling."""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import uuid
import subprocess
import tempfile
import tarfile

import yaml


def migrate_policy(raw: str) -> str:
    # Use syntax marks rather than a YAML 1.1 load/dump round trip: unrelated
    # scalar spelling (on/off, octal-looking strings, etc.) must stay untouched.
    if any(isinstance(token, (yaml.tokens.AnchorToken, yaml.tokens.AliasToken, yaml.tokens.TagToken))
           for token in yaml.scan(raw)):
        raise ValueError('Policy anchors/aliases/tags require an explicit migration')

    def mapping(node):
        if not isinstance(node, yaml.MappingNode):
            raise ValueError('Expected a policy mapping')
        result = {}
        for key, value in node.value:
            if not isinstance(key, yaml.ScalarNode) or key.value in result:
                raise ValueError('Expected unique scalar policy keys')
            result[key.value] = value
        return result

    policy = mapping(yaml.compose(raw))
    version = policy.get('version')
    if not isinstance(version, yaml.ScalarNode) or version.value != '1':
        raise ValueError('Expected a version 1 sandbox policy')
    replacements = []
    for rule in mapping(policy['network_policies']).values() if 'network_policies' in policy else []:
        endpoints = mapping(rule).get('endpoints')
        if endpoints is None:
            continue
        if not isinstance(endpoints, yaml.SequenceNode):
            raise ValueError('Expected a sequence of network endpoints')
        for endpoint in endpoints.value:
            tls = mapping(endpoint).get('tls')
            if isinstance(tls, yaml.ScalarNode) and tls.value == 'terminate':
                if tls.tag != 'tag:yaml.org,2002:str' or tls.style not in (None, '\x27', '\x22'):
                    raise ValueError('Unsupported TLS scalar requires an explicit migration')
                # Empty is the same Unspecified/Auto value as an omitted field
                # in OpenShell 0.1.4; preserve every other byte, including keys.
                replacements.append((tls.start_mark.index, tls.end_mark.index))
    for start, end in sorted(replacements, reverse=True):
        raw = raw[:start] + '""' + raw[end:]
    yaml.compose(raw)  # Refuse an invalid splice before producing a build input.
    return raw


def prepare_policy(image: str, output: Path, engine: list[str]) -> None:
    if not engine or image.startswith('-'):
        raise ValueError('Expected a container engine and image reference')
    name = 'breadboard-policy-' + uuid.uuid4().hex
    try:
        container = subprocess.check_output(
            [*engine, 'create', '--name', name, '--entrypoint', '/bin/true', image], text=True,
        ).strip()
        if not re.fullmatch(r'[a-f0-9]{12,64}', container):
            raise ValueError('Container engine returned an invalid container ID')
        # Stream cp's archive into a caller-owned file. This works with sudo
        # engines regardless of image UID/mode, and never materializes image
        # symlinks on the host filesystem.
        with tempfile.TemporaryFile() as archive:
            subprocess.run([*engine, 'cp', f'{container}:/etc/openshell/policy.yaml', '-'],
                           stdout=archive, check=True)
            if archive.tell() > 2_097_152:
                raise ValueError('Image policy archive exceeds the size limit')
            archive.seek(0)
            with tarfile.open(fileobj=archive, mode='r:') as bundle:
                members = bundle.getmembers()
                if len(members) != 1 or not members[0].isfile():
                    raise ValueError('Image policy must be a regular file, not a symlink')
                if members[0].size > 1_048_576:
                    raise ValueError('Image policy exceeds the OpenShell size limit')
                stream = bundle.extractfile(members[0])
                assert stream is not None
                with stream:
                    migrated = migrate_policy(stream.read().decode('utf-8'))
            output.write_text(migrated, encoding='utf-8')
            output.chmod(0o644)  # Public policy must be readable by the runtime UID.

    finally:
        cleanup = subprocess.run([*engine, 'rm', '-v', name],
                                 stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        if cleanup.returncode:
            print(f'Warning: could not remove temporary policy container {name}', file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('image')
    parser.add_argument('output', type=Path)
    parser.add_argument('engine', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    prepare_policy(args.image, args.output, args.engine)


if __name__ == '__main__':
    main()
