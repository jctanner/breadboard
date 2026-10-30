#!/usr/bin/env python3
"""Observe agent syscalls from the trusted CI operator, outside its seccomp filter.

Uses only the job-owned Podman engine. Leaves OpenShell's process restrictions
in place. Attachment is sampled; initial syscalls before attachment can be missed.
"""
import os
import signal
import subprocess
import sys
import time

REMOTE = r'''
import json, os, pwd, signal, subprocess, time
from pathlib import Path
root = Path('/sandbox/workspace/evidence/strace')
root.mkdir(parents=True, exist_ok=True)
account = pwd.getpwnam('sandbox')
uid = account.pw_uid
# The observer can run before Fullsend/SSH creates the workspace. Leave the
# workspace itself writable by its intended sandbox owner, not the operator.
os.chown(root.parents[1], uid, account.pw_gid)
api = root.parent / 'api-dumps'
api.mkdir(exist_ok=True)
os.chown(api, uid, account.pw_gid)
seen, active = set(), []
try:
    while not Path('/tmp/workflow-observer.stop').exists():
        for p in Path('/proc').iterdir():
            if not p.name.isdecimal() or p.name in seen:
                continue
            try:
                status = dict(line.split(':', 1) for line in (p / 'status').read_text().splitlines() if ':' in line)
                if int(status['Uid'].split()[0]) != uid or int(status['TracerPid']) != 0:
                    continue
                seen.add(p.name)
                log = (root / ('attach-' + p.name + '.log')).open('wb')
                proc = subprocess.Popen(['strace', '-fftt', '-s', '1024', '-o', str(root / ('trace-' + p.name)),
                                         '-p', p.name], stdin=subprocess.DEVNULL, stdout=log, stderr=log)
                active.append((proc, log))
                print(json.dumps({'attached_pid': int(p.name), 'mode': 'external-operator'}), flush=True)
            except (OSError, ValueError, KeyError):
                pass
        time.sleep(0.1)
finally:
    for proc, log in active:
        if proc.poll() is None:
            proc.send_signal(signal.SIGINT)
    for proc, log in active:
        try: proc.wait(timeout=5)
        except subprocess.TimeoutExpired: proc.kill(); proc.wait()
        log.close()
'''


def main():
    base = ['podman', '--url', sys.argv[1]]
    stopping = False
    children = {}

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    while not stopping:
        found = subprocess.run(base + ['ps', '--filter', 'label=openshell.managed=true', '--format', '{{.ID}}'],
                               capture_output=True, text=True, timeout=10, check=True)
        for identity in found.stdout.split():
            if identity not in children:
                children[identity] = subprocess.Popen(base + ['exec', '--privileged', '--user', '0', identity,
                                                               'python3', '-u', '-c', REMOTE])
        time.sleep(0.25)
    failures = []
    for identity, proc in children.items():
        subprocess.run(base + ['exec', '--user', '0', identity, 'touch', '/tmp/workflow-observer.stop'], timeout=10)
        try:
            result = proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            proc.terminate()
            result = proc.wait(timeout=5)
        if result:
            failures.append(identity)
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
