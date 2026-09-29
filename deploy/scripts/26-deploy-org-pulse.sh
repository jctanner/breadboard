#!/usr/bin/env bash
# Deploy Org Pulse (AI Engineering flavour, demo mode) to k3s.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"

echo "==> Deploying Org Pulse..."
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/02-certificates.yaml"
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/28-org-pulse.yaml"
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/08-ingress-https.yaml"

echo "  Waiting for MongoDB, the backend and the frontend..."
for deployment in org-pulse-mongodb org-pulse-backend org-pulse-frontend; do
  kubectl wait --for=condition=Available --timeout=180s "deployment/${deployment}" -n ai-pipeline || true
done

echo "==> Org Pulse deployed"
echo ""
echo "Access Org Pulse:"
echo "  - Via Ingress: https://orgpulse.local"
echo "  - Internal:    http://org-pulse-frontend.ai-pipeline.svc.cluster.local:8080"
echo "  - API:         http://org-pulse-backend.ai-pipeline.svc.cluster.local:3001/api"
echo ""
echo "Org Pulse runs in demo mode: fixture data, no Jira, GitHub or roster"
echo "credentials, refresh disabled. See docs/org-pulse.md."
