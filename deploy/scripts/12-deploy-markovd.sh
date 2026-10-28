#!/bin/bash
# Deploy markovd (workflow dashboard + PostgreSQL) to k3s

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"

echo "==> Deploying markovd..."

cd "${PROJECT_ROOT}/deploy/k8s"

echo "--- Ensuring namespace and cert infrastructure ---"
kubectl apply -f 00-namespace.yaml
kubectl apply -f 01-ca-issuer.yaml

echo "--- Applying markovd resources ---"
"${SCRIPT_DIR}/apply-domain-manifests.sh" 15-markovd.yaml
"${SCRIPT_DIR}/apply-domain-manifests.sh" 08-ingress-https.yaml

echo "--- Waiting for certificate ---"
kubectl wait --for=condition=ready certificate/markovd-tls -n ai-pipeline --timeout=120s || {
  echo "WARNING: Certificate not ready after 120s"
  kubectl describe certificate markovd-tls -n ai-pipeline
}

echo "--- Waiting for PostgreSQL ---"
kubectl wait --for=condition=Available --timeout=120s \
  deployment/markovd-postgres -n ai-pipeline || true

echo "--- Waiting for markovd ---"
kubectl wait --for=condition=Available --timeout=120s \
  deployment/markovd -n ai-pipeline || true

echo ""
echo "==> markovd deployed successfully"
echo ""
DOMAIN="${BREADBOARD_DOMAIN:-local}"
echo "Access markovd:"
echo "  - Internal: http://markovd.ai-pipeline.svc.cluster.local:8080"
echo "  - Via Ingress: https://markovd.ai-pipeline.svc.cluster.local"
echo "  - Via Edge: https://markovd.${DOMAIN}"
echo ""
echo "Check status:"
echo "  kubectl get pods -n ai-pipeline -l app=markovd"
echo "  kubectl get pods -n ai-pipeline -l app=markovd-postgres"
echo ""
