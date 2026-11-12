#!/usr/bin/env python3
"""Lima 2+ operations with argv boundaries and a repository-only host mount."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def run(*args, **kwargs):
    return subprocess.run(['limactl', *map(str, args)], check=True, **kwargs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['up', 'halt', 'shell', 'status', 'install-k3s', 'deploy-all', 'kubeconfig', 'configure-dns', 'validate', 'delete'])
    args = parser.parse_args()
    instance = os.getenv('LIMA_INSTANCE', 'breadboard')
    if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]*', instance):
        parser.error('LIMA_INSTANCE must be an instance name, not flags or a path')
    if any(c in str(ROOT) for c in ',:\n'):
        parser.error('Lima mount paths cannot contain commas, colons or newlines')
    domain = os.getenv('BREADBOARD_DOMAIN', 'local')
    # Validate before creating or starting a VM.
    subprocess.run(['python3', str(ROOT / 'deploy/scripts/render_domain_manifest.py'), '/dev/null', domain], check=True, stdout=subprocess.DEVNULL)

    def shell(*command, **kwargs):
        return run('shell', '--workdir', '/', instance, '--', *command, **kwargs)

    if args.action == 'up':
        instances = run('list', '-q', capture_output=True, text=True).stdout.splitlines()
        if instance not in instances:
            run('start', '--name=' + instance, '--tty=false', '--mount-only', str(ROOT) + ':w', os.getenv('LIMA_CONFIG', str(ROOT / 'deploy/lima/breadboard-vm.yaml')))
        else:
            status = json.loads(run('list', '--json', instance, capture_output=True, text=True).stdout)
            if status['status'] != 'Running':
                run('start', '--tty=false', instance)
        # Existing VMs must have the same explicit mount; no automatic home mount.
        shell('test', '-f', str(ROOT / 'Makefile'))
        shell('sudo', 'ln', '-sfn', str(ROOT), '/breadboard')
        shell('sudo', 'ln', '-sfn', str(ROOT), '/vagrant')
    elif args.action == 'halt':
        run('stop', instance)
    elif args.action == 'shell':
        shell()
    elif args.action == 'status':
        run('list', instance)
    elif args.action == 'delete':
        if input(f'Delete Lima VM {instance}? Type yes: ') != 'yes':
            parser.exit(1, 'Cancelled\n')
        run('delete', '-f', instance)
    elif args.action == 'kubeconfig':
        directory = Path.home() / '.kube'
        directory.mkdir(mode=0o700, exist_ok=True)
        descriptor, name = tempfile.mkstemp(prefix='breadboard-lima.', dir=directory)
        try:
            with os.fdopen(descriptor, 'wb') as handle:
                shell('sudo', 'cat', '/etc/rancher/k3s/k3s.yaml', stdout=handle)
            os.replace(name, directory / 'breadboard-lima.yaml')
        finally:
            Path(name).unlink(missing_ok=True)
    else:
        scripts = {'install-k3s': '01-install-k3s-host.sh', 'deploy-all': 'deploy-all.sh', 'configure-dns': '29-configure-tailscale-dns.sh', 'validate': 'validate-lima.sh'}
        shell('sudo', 'env', f'PROJECT_ROOT={ROOT}', f'BREADBOARD_DOMAIN={domain}', 'bash', str(ROOT / 'deploy/scripts' / scripts[args.action]))


if __name__ == '__main__':
    main()
