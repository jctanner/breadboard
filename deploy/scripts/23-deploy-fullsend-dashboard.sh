#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
"${SCRIPT_DIR}/apply-domain-manifests.sh" "${PROJECT_ROOT}/deploy/k8s/26-fullsend-dashboard.yaml"
kubectl rollout restart deployment/fullsend-dashboard -n ai-pipeline
kubectl rollout status deployment/fullsend-dashboard -n ai-pipeline --timeout=180s
