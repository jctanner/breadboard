#!/usr/bin/env bash
# Deploy the webhook sink to k3s.
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-/vagrant}"
NAMESPACE=ai-pipeline

echo "==> Deploying webhook sink..."

# Created once and kept across redeploys. The admin key defaults to "admin"
# for local development, as Model Relay's does; the default sender and
# consumer tokens are random. Override with HOOKSINK_ADMIN_KEY,
# HOOKSINK_DEFAULT_SENDER_TOKEN and HOOKSINK_DEFAULT_CONSUMER_TOKEN.
random_value() {
  LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 40
}
if ! kubectl get secret hooksink-tokens -n "${NAMESPACE}" >/dev/null 2>&1; then
  echo "  Creating token secret..."
  kubectl create secret generic hooksink-tokens -n "${NAMESPACE}" \
    --from-literal=admin-key="${HOOKSINK_ADMIN_KEY:-admin}" \
    --from-literal=default-sender-token="${HOOKSINK_DEFAULT_SENDER_TOKEN:-whs_$(random_value)}" \
    --from-literal=default-consumer-token="${HOOKSINK_DEFAULT_CONSUMER_TOKEN:-whc_$(random_value)}"
fi
kubectl apply -f "${PROJECT_ROOT}/deploy/k8s/31-hooksink.yaml"

echo "  Waiting for webhook sink..."
kubectl wait --for=condition=Available --timeout=120s deployment/hooksink -n "${NAMESPACE}" || true

echo "==> Webhook sink deployed"
echo ""
echo "Access the webhook sink:"
echo "  - Console:  https://hooksink-admin.local/admin/"
echo "  - Host:     https://hooksink.local/events"
echo "  - Senders:  http://hooksink.${NAMESPACE}.svc.cluster.local/hooks/<channel>"
echo "  - Consumer: http://hooksink.${NAMESPACE}.svc.cluster.local/events?after=<seq>&wait=30"
echo ""
echo "Admin key and default tokens:"
echo "  make host-hooksink-tokens"
