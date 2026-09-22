#!/usr/bin/env bash
# Seed the repeatable GitHub App/OIDC/action fixture after the emulators are
# ready. This is the default seeded fixture (formerly "M8"); it is a named
# compatibility test, not the per-repo conformance path - see decisions 1 and
# 5 in .ledger/plans/fullsend-integration-conformance-plan.md. Work package 2
# will replace what this script installs with the real per-repo scaffold.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
export PYTHONPATH="${PROJECT_ROOT}/deploy/fullsend/seed"

# The per-repo shim calls a reusable workflow in fullsend-ai/fullsend, so
# that repository has to exist in the emulator before any dispatch can
# resolve (gap A1).
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-upstream-fullsend.py"
# Non-admin actors, so the authorization gate can be exercised in both
# directions rather than only ever admitting the repository owner.
# The CLI resolves its agent definitions from fullsend-ai/agents at run time,
# so that repository has to exist here too or the run reaches the internet.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-upstream-agents.py"
# ...and the repository has to allow fetching from it.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-config-allowlist.py"
# The dummy runtime runs a scripted scenario instead of a model, and hard-fails
# without it. This is what the conformance run actually asserts.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-behaviour-script.py"
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-conformance-actors.py" > /dev/null
# The agent action installs the CLI from the workspace, a release, or a source
# build, in that order. Seeding the first stops every run falling through to the
# third and compiling the CLI it already has.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-vendored-binary.py"
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-github-app.py"
# The trust-boundary check breakpoint B4 asks for, plus the private repository
# it probes against.
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/seed-trust-check.py"
python3 "${PROJECT_ROOT}/deploy/fullsend/seed/mirror-fullsend-workflows.py"
