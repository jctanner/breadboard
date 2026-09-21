#!/usr/bin/env bash
# Run the deterministic Fullsend/OpenShell direct-token smoke (formerly "M4")
# and retain its Job logs. This is a named legacy compatibility test, not the
# conformance path - see .ledger/plans/fullsend-integration-conformance-plan.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
MANIFEST="${PROJECT_ROOT}/deploy/k8s/25-fullsend-direct-token-smoke.yaml"
ARTIFACTS_DIR="${PROJECT_ROOT}/deploy/fullsend/legacy/artifacts/direct-token-smoke"

kubectl -n ai-pipeline delete job fullsend-direct-token-smoke --ignore-not-found --wait=true
kubectl -n ai-pipeline delete pods -l job-name=fullsend-direct-token-smoke --ignore-not-found --wait=true
kubectl apply -f "${MANIFEST}"
for _ in $(seq 1 120); do
  POD="$(kubectl -n ai-pipeline get pods -l job-name=fullsend-direct-token-smoke -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  if [ -n "${POD}" ] && kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- test -f /artifacts/.fullsend-done >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
if [ -z "${POD:-}" ] || ! kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- test -f /artifacts/.fullsend-done >/dev/null 2>&1; then
  echo "Fullsend direct-token smoke did not produce completion marker" >&2
  kubectl -n ai-pipeline get pods -l job-name=fullsend-direct-token-smoke -o wide >&2 || true
  exit 1
fi
kubectl -n ai-pipeline logs "${POD}"
mkdir -p "${ARTIFACTS_DIR}"
kubectl -n ai-pipeline cp "${POD}:/artifacts" "${ARTIFACTS_DIR}" \
  --container=artifact-holder --retries=2
STATUS="$(kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- cat /artifacts/.fullsend-status)"
kubectl -n ai-pipeline delete job fullsend-direct-token-smoke --ignore-not-found
if [ "${STATUS}" != "0" ]; then
  echo "Fullsend exited with status ${STATUS}" >&2
  exit 1
fi
echo "Direct-token smoke artifacts copied to ${ARTIFACTS_DIR}"
