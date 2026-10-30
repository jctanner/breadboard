#!/usr/bin/env bash
# Deploy Workflow Dojo (optional; not part of deploy-all.sh).
# Requires Model Relay. Provisions the dojo's relay API key Secret first.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
NAMESPACE=ai-pipeline

echo "==> Deploying Workflow Dojo..."
python3 "${PROJECT_ROOT}/deploy/scripts/workflow-dojo-relay-key.py"
bash "${PROJECT_ROOT}/deploy/scripts/workflow-dojo-admin-secret.sh"
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/31-workflow-dojo.yaml"
kubectl rollout restart deployment/workflow-dojo -n "${NAMESPACE}"
kubectl rollout status deployment/workflow-dojo -n "${NAMESPACE}" --timeout=180s

echo "==> Workflow Dojo deployed"
echo "  - UI:       https://dojo.local (needs dojo.local in /etc/hosts and the ingress-proxy route)"
echo "  - Login:    admin / admin by default; change it on the Account page"
echo "  - Internal: http://workflow-dojo.${NAMESPACE}.svc.cluster.local:8080"
