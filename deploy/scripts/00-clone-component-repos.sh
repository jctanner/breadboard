#!/usr/bin/env bash
# Clone source repositories used to build locally deployed platform components.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
CHECKOUTS_DIR="${PROJECT_ROOT}/checkouts"

repos=(
  "github-emulator|git@github.com:jctanner/github-emulator.git"
  "gitlab-emulator|git@github.com:jctanner/gitlab-emulator.git"
  "jira-emulator|git@github.com:jctanner/jira-emulator.git"
  "markov|git@github.com:vokramd/markov.git"
  "markovd|git@github.com:vokramd/markovd.git"
  "observatory|git@github.com:opendatahub-io/observatory.git"
  "model-relay|git@github.com:jctanner/model-relay.git"
  "hooksink|git@github.com:jctanner/hooksink.git"
  "fullsend-ai/fullsend|git@github.com:fullsend-ai/fullsend.git"
  "fullsend-ai/agents|git@github.com:fullsend-ai/agents.git"
  "org-pulse-core|git@github.com:red-hat-data-services/org-pulse-core.git"
  "rhai-org-pulse|git@github.com:red-hat-data-services/rhai-org-pulse.git"
  "workflow-dojo|git@github.com:jctanner/claude-workflow-dojo.git"
)

mkdir -p "${CHECKOUTS_DIR}"

for repo in "${repos[@]}"; do
  name="$(echo "${repo}" | cut -d'|' -f1)"
  url="$(echo "${repo}" | cut -d'|' -f2)"
  destination="${CHECKOUTS_DIR}/${name}"

  if [ -d "${destination}/.git" ]; then
    echo "==> ${name} already exists; keeping current checkout"
    continue
  fi

  if [ -e "${destination}" ]; then
    echo "ERROR: ${destination} exists but is not a Git checkout" >&2
    exit 1
  fi

  echo "==> Cloning ${name} into ${destination}"
  git clone "${url}" "${destination}"
done

echo "Component repositories are available in ${CHECKOUTS_DIR}"
