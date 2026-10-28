#!/usr/bin/env bash
# Clone source repositories used to build locally deployed platform components.

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
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
  "fullsend-ai/fullsend|git@github.com:fullsend-ai/fullsend.git|a734637cdc5736cc454a0b218708001b96e1b3aa"
  "fullsend-ai/agents|git@github.com:fullsend-ai/agents.git|6ffe9c77"
  "org-pulse-core|git@github.com:red-hat-data-services/org-pulse-core.git"
  "rhai-org-pulse|git@github.com:red-hat-data-services/rhai-org-pulse.git"
)

mkdir -p "${CHECKOUTS_DIR}"

for repo in "${repos[@]}"; do
  name="$(echo "${repo}" | cut -d'|' -f1)"
  url="$(echo "${repo}" | cut -d'|' -f2)"
  ref="$(echo "${repo}" | cut -s -d'|' -f3)"
  destination="${CHECKOUTS_DIR}/${name}"

  if [ -d "${destination}/.git" ]; then
    echo "==> ${name} already exists; keeping current checkout"
    if [ -n "${ref}" ]; then
      git -C "${destination}" checkout --detach "${ref}" >/dev/null 2>&1 || true
    fi
    continue
  fi

  if [ -e "${destination}" ]; then
    echo "ERROR: ${destination} exists but is not a Git checkout" >&2
    exit 1
  fi

  echo "==> Cloning ${name} into ${destination}"
  git clone "${url}" "${destination}"
  if [ -n "${ref}" ]; then
    git -C "${destination}" checkout --detach "${ref}"
  fi
done

echo "Component repositories are available in ${CHECKOUTS_DIR}"
