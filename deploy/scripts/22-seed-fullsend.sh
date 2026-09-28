#!/usr/bin/env bash
# Seed the repeatable GitHub App/OIDC/action fixture after the emulators are
# ready. This is the default seeded fixture (formerly "M8"); it is a named
# compatibility test, not the per-repo conformance path - see decisions 1 and
# 5 in .ledger/plans/fullsend-integration-conformance-plan.md.
#
# The per-repo scaffold now exists alongside it: the conformance path runs the
# mirrored reusable-dispatch.yml with FULLSEND_PER_REPO_INSTALL=true, and this
# fixture is the named compatibility test beside it rather than a placeholder
# for it. Note its m8-role-events.yml fires on the same issues events and is
# cancelled every time, which makes run selection ambiguous; see the open
# work-package-2 item about keeping legacy fixtures out of the path.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
export PYTHONPATH="${PROJECT_ROOT}/deploy/fullsend/seed"

# The per-repo shim calls a reusable workflow in fullsend-ai/fullsend, so
# that repository has to exist in the emulator before any dispatch can
# resolve (gap A1).
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-upstream-fullsend.py"
# The reusable dispatch's harness job installs the CLI from a release whose
# tag points at the workflow's own commit; that is the common path on real
# GitHub and the only one that completes here. Every time, because a mirror
# commit moves the head the tag has to sit on.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-fullsend-release.py"
# Non-admin actors, so the authorization gate can be exercised in both
# directions rather than only ever admitting the repository owner.
# The CLI resolves its agent definitions from fullsend-ai/agents at run time,
# so that repository has to exist here too or the run reaches the internet.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-upstream-agents.py"
# ...and the CLI allows fetching from it on its own: patch 0013 derives the
# forge's prefixes into the default allowlist, at scaffold time and at run time.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-triage-auto-code-off.py"
# The dummy runtime runs a scripted scenario instead of a model, and hard-fails
# without it. This is what the conformance run actually asserts.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-behaviour-script.py"
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-conformance-actors.py" > /dev/null
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-github-app.py"
# The App the dashboard onboards repositories with: its key goes to a Secret
# the dashboard mounts, and each onboarding mints a one-hour installation
# token scoped to the one repository (conformance plan, work package 7).
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-onboarding-app.py"
# The trust-boundary check breakpoint B4 asks for, plus the private repository
# it probes against.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-trust-check.py"
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/mirror-fullsend-workflows.py"
