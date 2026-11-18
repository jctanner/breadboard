#!/usr/bin/env python3
"""CC-75: register the verified local harness copies when STRAT_CREATOR_RAW_BASE is set.

Kind: emulator-gap (Fullsend 0.55.0 fetches harnesses only from github.com/raw.githubusercontent.com and refuses internal hosts; a configurable allowlist in Fullsend would retire this)

Fullsend 0.55.0 fetches URL agent sources only from github.com and
raw.githubusercontent.com, and refuses hosts that resolve to internal
addresses (internal/fetch/fetch.go DefaultPolicy), so it cannot fetch a
harness from an in-cluster emulator. It does accept a relative local path
inside the --fullsend-dir (internal/harness/registry.go
containedRegisteredPath). materialize_runtime already copies .fullsend from the
verified checkout of STRAT_CREATOR_REF into that directory, so in emulator mode
register <name>/<name>.yaml instead of a raw URL. Same commit, same bytes;
without STRAT_CREATOR_RAW_BASE the public URL behaviour is unchanged.
Usage: 0002-local-harness.py <tree>
"""
import sys
from pathlib import Path

path = Path(sys.argv[1]) / ".fullsend/ci/fullsend-config.py"
text = path.read_text()
OLD = '''            entry["source"] = f"{prefix}/{record['commit']}/.fullsend/{name}/{name}.yaml#sha256={digest}"
'''
NEW = '''            if env.get("STRAT_CREATOR_RAW_BASE"):
                # Emulator mode (CC-75): Fullsend refuses internal hosts, so use the
                # verified local copy of the same commit (copied above).
                entry["source"] = f"{name}/{name}.yaml"
            else:
                entry["source"] = f"{prefix}/{record['commit']}/.fullsend/{name}/{name}.yaml#sha256={digest}"
'''
if text.count(OLD) != 1:
    raise SystemExit(f"{path}: expected one materialize_runtime source line")
path.write_text(text.replace(OLD, NEW))
print("strat-creator 0002-local-harness: applied")
