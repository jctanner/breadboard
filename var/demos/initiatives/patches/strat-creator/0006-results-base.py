#!/usr/bin/env python3
"""CC-75: an opt-in Git base for the results repository (mirror branch only).

Kind: upstream-proposal (strat-creator: STRAT_RESULTS_GIT_BASE instead of the hard-coded gitlab.com results remote)

.fullsend/ci/run-fullsend.sh hard-codes the results remote as
https://gitlab.com/$RESULTS_REPO.git. On the breadboard mirror a live run must
publish to the GitLab emulator instead, so read the base from
STRAT_RESULTS_GIT_BASE (an https origin, no path or credentials). Unset (the
public default), behaviour is unchanged.
Usage: 0006-results-base.py <tree>
"""
import sys
from pathlib import Path

path = Path(sys.argv[1]) / ".fullsend/ci/run-fullsend.sh"
text = path.read_text()
OLD = '  export RESULTS_REPO_URL="https://gitlab.com/$RESULTS_REPO.git"\n'
NEW = '''  # CC-75 emulator mirror: STRAT_RESULTS_GIT_BASE names another GitLab (e.g. an emulator).
  results_base="${STRAT_RESULTS_GIT_BASE:-https://gitlab.com}"
  [[ "$results_base" =~ ^https://[A-Za-z0-9.-]+(:[0-9]+)?$ ]] || { echo 'STRAT_RESULTS_GIT_BASE must be an https origin' >&2; exit 2; }
  export RESULTS_REPO_URL="$results_base/$RESULTS_REPO.git"
'''
if text.count(OLD) != 1:
    raise SystemExit(f"{path}: expected one RESULTS_REPO_URL export")
path.write_text(text.replace(OLD, NEW))
print("strat-creator 0006-results-base: applied")
