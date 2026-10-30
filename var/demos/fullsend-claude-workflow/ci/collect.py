#!/usr/bin/env python3
"""Retain downloaded symlinks as data without letting artifact tools follow them."""
import json
import os
import sys
from pathlib import Path


def record_links(root):
    if root.is_symlink():
        raise ValueError('Refusing artifact root symlink')
    inventory = root / 'symlink-inventory.json'
    records = []
    for here, directories, files in os.walk(root, followlinks=False):
        for name in sorted(directories + files):
            path = Path(here) / name
            if path.is_symlink():
                records.append({'path': str(path.relative_to(root)), 'target': os.readlink(path)})
                path.unlink()  # Only a downloaded link, never its target.
                if name in directories:
                    directories.remove(name)
    previous = json.loads(inventory.read_text()) if inventory.exists() else []
    if not isinstance(previous, list):
        raise ValueError('Invalid symlink inventory')
    inventory.write_text(json.dumps(previous + records, indent=2) + '\n')
    return records


if __name__ == '__main__':
    record_links(Path(sys.argv[1]))
