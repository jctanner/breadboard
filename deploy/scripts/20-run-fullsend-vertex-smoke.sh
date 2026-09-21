#!/usr/bin/env bash
# Run the focused Fullsend/Claude/Vertex smoke (formerly "M5") using the
# proven direct-token-smoke Job shape. This is a named legacy compatibility
# test, not the conformance path - see
# .ledger/plans/fullsend-integration-conformance-plan.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
SOURCE_MANIFEST="${PROJECT_ROOT}/deploy/k8s/25-fullsend-direct-token-smoke.yaml"
ARTIFACTS_DIR="${PROJECT_ROOT}/deploy/fullsend/legacy/artifacts/vertex-smoke"
MANIFEST="$(mktemp)"
trap 'rm -f "${MANIFEST}"' EXIT

sed \
  -e 's/fullsend-direct-token-smoke/fullsend-vertex-smoke/g' \
  -e 's/direct-token-smoke/vertex-smoke/g' \
  -e 's/runtime: dummy/runtime: claude/g' \
  -e 's/name: triage/name: claude/g' \
  -e 's/fullsend run triage/fullsend run claude/g' \
  -e 's/breadboard\.dev\/fixture: direct-token-smoke/breadboard.dev\/fixture: vertex-smoke/' \
  "${SOURCE_MANIFEST}" > "${MANIFEST}"

awk '
/^[[:space:]]+GITHUB_API_URL: http:\/\/github\.local\/api\/v3$/ {
  print
  print "        CLAUDE_CODE_USE_VERTEX: ${CLAUDE_CODE_USE_VERTEX}"
  print "        CLOUD_ML_REGION: ${CLOUD_ML_REGION}"
  print "        ANTHROPIC_VERTEX_PROJECT_ID: ${ANTHROPIC_VERTEX_PROJECT_ID}"
  print "        GOOGLE_APPLICATION_CREDENTIALS: /sandbox/workspace/gcp-credentials.json"
  next
}
/^    env:$/ {
  print "    host_files:"
  print "      - src: /var/run/secrets/gcp/credentials.json"
  print "        dest: /sandbox/workspace/gcp-credentials.json"
  print "        optional: true"
}
{ print }
' "${MANIFEST}" > "${MANIFEST}.tmp"
mv "${MANIFEST}.tmp" "${MANIFEST}"

kubectl -n ai-pipeline delete job fullsend-vertex-smoke --ignore-not-found --wait=true
kubectl -n ai-pipeline delete pods -l job-name=fullsend-vertex-smoke --ignore-not-found --wait=true
kubectl apply -f "${MANIFEST}"

POD=""
for _ in $(seq 1 600); do
  POD="$(kubectl -n ai-pipeline get pods -l job-name=fullsend-vertex-smoke -o jsonpath='{.items[0].metadata.name}' 2>/dev/null || true)"
  if [ -n "${POD}" ] && kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- test -f /artifacts/.fullsend-done >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

if [ -z "${POD}" ] || ! kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- test -f /artifacts/.fullsend-done >/dev/null 2>&1; then
  echo "Fullsend Vertex smoke did not produce completion marker" >&2
  kubectl -n ai-pipeline get pods -l job-name=fullsend-vertex-smoke -o wide >&2 || true
  exit 1
fi

kubectl -n ai-pipeline logs "${POD}"
mkdir -p "${ARTIFACTS_DIR}"
kubectl -n ai-pipeline cp "${POD}:/artifacts" "${ARTIFACTS_DIR}" --container=artifact-holder --retries=2
STATUS="$(kubectl -n ai-pipeline exec "${POD}" -c artifact-holder -- cat /artifacts/.fullsend-status)"
kubectl -n ai-pipeline delete job fullsend-vertex-smoke --ignore-not-found

if [ "${STATUS}" != "0" ]; then
  echo "Fullsend Vertex smoke exited with status ${STATUS}" >&2
  exit 1
fi

echo "Vertex smoke artifacts copied to ${ARTIFACTS_DIR}"
