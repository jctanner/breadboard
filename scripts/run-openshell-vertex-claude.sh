#!/usr/bin/env bash
# Attach the stack's Vertex policy and GCP credentials to a direct OpenShell
# sandbox, then launch Claude Code through OpenShell's interactive exec API.
#
# Usage: scripts/run-openshell-vertex-claude.sh [sandbox-name] [model]
# Defaults: direct-agent-demo claude-haiku-4-5
# Reads ANTHROPIC_VERTEX_PROJECT_ID and CLOUD_ML_REGION from "$PWD/.env".

set -euo pipefail

NAMESPACE="${OPENSHELL_NAMESPACE:-ai-pipeline}"
RUNNER="deploy/github-actions-runner"
SANDBOX_NAME="${1:-direct-agent-demo}"
MODEL="${2:-claude-haiku-4-5}"
ENV_FILE="${PWD}/.env"
GCP_CREDENTIALS="/var/run/secrets/gcp/credentials.json"
SANDBOX_CREDENTIALS="/tmp/breadboard-gcp-credentials.json"

usage() {
  echo "Usage: $0 [sandbox-name] [model]" >&2
}

if [[ ! "${SANDBOX_NAME}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ || ! "${MODEL}" =~ ^[A-Za-z0-9][A-Za-z0-9._/-]*$ ]]; then
  usage
  exit 2
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "ERROR: kubectl is required" >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: ${ENV_FILE} is missing; run this script from the project root" >&2
  exit 1
fi

# This is the project's trusted shell-style .env file. Only the two Vertex
# settings below are passed to the sandbox; credential material stays in the
# Kubernetes-mounted GCP key file.
# shellcheck disable=SC1090
source "${ENV_FILE}"

if [[ -z "${ANTHROPIC_VERTEX_PROJECT_ID:-}" || -z "${CLOUD_ML_REGION:-}" ]]; then
  echo "ERROR: .env must set ANTHROPIC_VERTEX_PROJECT_ID and CLOUD_ML_REGION" >&2
  exit 1
fi
if [[ ! "${ANTHROPIC_VERTEX_PROJECT_ID}" =~ ^[A-Za-z0-9-]+$ || ! "${CLOUD_ML_REGION}" =~ ^[A-Za-z0-9-]+$ ]]; then
  echo "ERROR: Vertex project ID and region must contain only letters, digits, and hyphens" >&2
  exit 1
fi

kubectl exec -n "${NAMESPACE}" "${RUNNER}" -- sh -lc '
  test -s /var/run/secrets/gcp/credentials.json || {
    echo "ERROR: runner has no mounted GCP credentials at /var/run/secrets/gcp/credentials.json" >&2
    exit 1
  }
'

echo "Checking OpenShell sandbox ${SANDBOX_NAME}"
sandbox_info="$(kubectl exec -n "${NAMESPACE}" "${RUNNER}" -- \
  openshell sandbox get "${SANDBOX_NAME}" 2>&1)" || {
  if [[ "${sandbox_info}" == *"sandbox not found"* ]]; then
    echo "Sandbox not found; creating it detached"
    kubectl exec -n "${NAMESPACE}" "${RUNNER}" -- \
      openshell sandbox create --name "${SANDBOX_NAME}" --detach -- sleep infinity
  else
    printf '%s\n' "${sandbox_info}" >&2
    exit 1
  fi
}

attached_providers="$(kubectl exec -n "${NAMESPACE}" "${RUNNER}" -- \
  openshell sandbox provider list "${SANDBOX_NAME}")"
if [[ "${attached_providers}" != *vertex-ai* ]]; then
  echo "Attaching the stack's vertex-ai policy provider"
  kubectl exec -n "${NAMESPACE}" "${RUNNER}" -- \
    openshell sandbox provider attach "${SANDBOX_NAME}" vertex-ai
fi

echo "Copying the runner-mounted GCP credential file into the sandbox"
kubectl exec -n "${NAMESPACE}" "${RUNNER}" -- sh -c '
  set -eu
  sandbox_name=$1
  staged_file="$(mktemp /tmp/openshell-gcp-credentials.XXXXXX)"
  trap '\''rm -f "$staged_file"'\'' EXIT
  # Kubernetes Secret mounts expose files as symlinks. Dereference the link so
  # OpenShell uploads the credential contents, not a dangling ..data symlink.
  cp -L /var/run/secrets/gcp/credentials.json "$staged_file"
  openshell sandbox upload "$sandbox_name" "$staged_file" /tmp/breadboard-gcp-credentials.json
' sh "${SANDBOX_NAME}"

if ! kubectl exec -n "${NAMESPACE}" "${RUNNER}" -- \
  openshell sandbox exec --name "${SANDBOX_NAME}" -- \
  sh -c 'test -s "$1" && test ! -L "$1"' sh "${SANDBOX_CREDENTIALS}"; then
  echo "ERROR: OpenShell credential upload did not create a regular, nonempty file in the sandbox" >&2
  exit 1
fi

echo "Launching Claude Code with Vertex AI. Exit Claude Code to return here."
echo "The GCP credential copy remains in the sandbox until it is deleted."
printf 'When finished, remove it with:\n  kubectl exec -n %s %s -- openshell sandbox delete %s\n' \
  "${NAMESPACE}" "${RUNNER}" "${SANDBOX_NAME}"

remote_command="exec openshell sandbox exec --name '${SANDBOX_NAME}' --tty --env CLAUDE_CODE_USE_VERTEX=1 --env ANTHROPIC_VERTEX_PROJECT_ID=${ANTHROPIC_VERTEX_PROJECT_ID} --env CLOUD_ML_REGION=${CLOUD_ML_REGION} --env GOOGLE_APPLICATION_CREDENTIALS=${SANDBOX_CREDENTIALS} -- claude --model '${MODEL}'"

kubectl exec -it -n "${NAMESPACE}" "${RUNNER}" -- \
  sh -lc "${remote_command}"
