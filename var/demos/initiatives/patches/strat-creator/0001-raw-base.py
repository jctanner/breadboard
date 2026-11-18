#!/usr/bin/env python3
"""CC-75 emulator transformation for strat-creator (mirror branch only).

Kind: upstream-proposal (strat-creator: STRAT_CREATOR_RAW_BASE for GitHub Enterprise or mirrors; public GitHub stays the default)

.fullsend/ci/fullsend-config.py hard-codes public GitHub: STRAT_CREATOR_REPO must
be https://github.com/<org>/strat-creator.git and agent sources are rewritten to
raw.githubusercontent.com. Add an opt-in STRAT_CREATOR_RAW_BASE for a same-host
GitHub Enterprise-style raw endpoint (<host>/<org>/strat-creator/raw), used by
the breadboard GitHub emulator. Without the variable, behaviour is unchanged.
Usage: 0001-raw-base.py <tree>
"""
import sys
from pathlib import Path

path = Path(sys.argv[1]) / ".fullsend/ci/fullsend-config.py"
text = path.read_text()


def replace_once(old, new):
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence, found {count}: {old[:70]!r}")
    text = text.replace(old, new)


HELPER = '''

def raw_prefix(repository, env):
    """Raw-content prefix of the strat-creator repository.

    Public GitHub by default. STRAT_CREATOR_RAW_BASE (opt-in; GitHub Enterprise
    or an emulator) names <host>/<org>/strat-creator/raw for a same-host
    STRAT_CREATOR_REPO of https://<host>/<org>/strat-creator.git.
    """
    raw = env.get("STRAT_CREATOR_RAW_BASE", "").rstrip("/")
    if raw:
        match = re.fullmatch(r"(https://[A-Za-z0-9.-]+(?::[0-9]+)?)/([A-Za-z0-9_.-]+)/strat-creator[.]git", repository)
        if not match or raw != f"{match.group(1)}/{match.group(2)}/strat-creator/raw":
            raise ValueError("STRAT_CREATOR_RAW_BASE must be <host>/<org>/strat-creator/raw of STRAT_CREATOR_REPO")
        return raw
    if not re.fullmatch(r"https://github[.]com/[A-Za-z0-9_.-]+/strat-creator[.]git", repository):
        raise ValueError("STRAT_CREATOR_REPO must name a public GitHub strat-creator repository")
    return repository.removesuffix(".git").replace("https://github.com/", "https://raw.githubusercontent.com/")
'''
replace_once("\n\ndef verify_consumer(", HELPER + "\n\ndef verify_consumer(")
replace_once(
    '''    if not re.fullmatch(r"https://github[.]com/[A-Za-z0-9_.-]+/strat-creator[.]git", repository):
        raise ValueError("STRAT_CREATOR_REPO must name a public GitHub strat-creator repository")
    prefix = repository.removesuffix(".git").replace("https://github.com/", "https://raw.githubusercontent.com/")
''',
    "    prefix = raw_prefix(repository, env)\n",
)
replace_once(
    '''        prefix = record["repository"].removesuffix(".git").replace("https://github.com/", "https://raw.githubusercontent.com/")
''',
    '''        prefix = raw_prefix(record["repository"], env)
''',
)
path.write_text(text)
print("strat-creator 0001-raw-base: applied")
