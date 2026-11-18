#!/usr/bin/env python3
"""CC-75: let the Jira client trust an extra CA through STRAT_EXTRA_CA_FILE (mirror branch only).

Kind: upstream-proposal (strat-creator: STRAT_EXTRA_CA_FILE lets the Jira client trust a private CA; SSL_CERT_FILE is reserved in Fullsend env.sandbox)

Fullsend 0.55.0 drops SSL_CERT_FILE from a harness's env.sandbox ("reserved:
runner infrastructure or security deny-list"), so the sandboxed Python Jira
client cannot be pointed at the emulator CA that way. scripts/jira_utils.py
builds the one TLS context every Jira call uses (fetch_issue.py imports it);
load an additional CA file from the non-reserved STRAT_EXTRA_CA_FILE when set.
Unset (the public default), behaviour is unchanged.
Usage: 0005-jira-extra-ca.py <tree>
"""
import sys
from pathlib import Path

path = Path(sys.argv[1]) / "scripts/jira_utils.py"
text = path.read_text()
OLD = """ssl_ctx = ssl.create_default_context()
try:
    import certifi
    ssl_ctx.load_verify_locations(certifi.where())
except (ImportError, OSError):
    pass
"""
NEW = OLD + """# CC-75 emulator mirror: an extra trusted CA (e.g. a local Jira emulator's).
if os.environ.get("STRAT_EXTRA_CA_FILE"):
    ssl_ctx.load_verify_locations(os.environ["STRAT_EXTRA_CA_FILE"])
"""
if text.count(OLD) != 1:
    raise SystemExit(f"{path}: expected one ssl_ctx block")
path.write_text(text.replace(OLD, NEW))
print("strat-creator 0005-jira-extra-ca: applied")
