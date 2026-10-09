#!/usr/bin/env bash
# Deploy Model Relay to k3s.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
NAMESPACE=ai-pipeline

echo "==> Deploying Model Relay..."

# Local development default; override with MODEL_RELAY_ADMIN_KEY. The secret
# is created once and kept across redeploys.
ADMIN_KEY="${MODEL_RELAY_ADMIN_KEY:-admin}"
if ! kubectl get secret model-relay-admin -n "${NAMESPACE}" >/dev/null 2>&1; then
  echo "  Creating admin key secret..."
  kubectl create secret generic model-relay-admin -n "${NAMESPACE}" \
    --from-literal=admin-api-key="${ADMIN_KEY}"
fi

kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/02-certificates.yaml"
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/29-model-relay.yaml"
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/08-ingress-https.yaml"

echo "  Waiting for Model Relay..."
kubectl wait --for=condition=Available --timeout=180s deployment/model-relay -n "${NAMESPACE}" || true

echo "==> Model Relay deployed"
echo ""
echo "Access Model Relay:"
echo "  - Admin console: https://relay.local/admin/"
echo "  - Inference:     https://relay-api.local"
echo "  - Internal:      http://model-relay.ai-pipeline.svc.cluster.local:8080"
echo ""
echo "Admin key:"
echo "  kubectl get secret model-relay-admin -n ${NAMESPACE} -o jsonpath='{.data.admin-api-key}' | base64 -d"
