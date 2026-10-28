#!/bin/bash
# Deploy the Go reverse proxy (ingress controller)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${SCRIPT_DIR}/../.."

echo "==> Deploying Go Reverse Proxy (Ingress Controller)..."

# Use docker or podman
if command -v docker &> /dev/null; then
  CONTAINER_CMD="docker"
elif command -v podman &> /dev/null; then
  CONTAINER_CMD="podman"
else
  echo "ERROR: Neither docker nor podman found"
  exit 1
fi

# Build the proxy image
cd "${PROJECT_ROOT}/deploy/golang-reverse-proxy"
echo "  Building container image..."
${CONTAINER_CMD} build -t ingress-proxy:latest . -q

# Import to k3s (remove old image first so containerd doesn't skip the import)
echo "  Importing image to k3s..."
sudo k3s ctr images rm docker.io/library/ingress-proxy:latest localhost/ingress-proxy:latest 2>/dev/null || true
${CONTAINER_CMD} save ingress-proxy:latest | sudo k3s ctr images import - > /dev/null
sudo k3s ctr images tag localhost/ingress-proxy:latest docker.io/library/ingress-proxy:latest 2>/dev/null || true

# Deploy to cluster
echo "  Deploying to Kubernetes..."
"${SCRIPT_DIR}/apply-domain-manifests.sh" deployment.yaml

# Restart pods to pick up the new image
echo "  Restarting pods..."
kubectl rollout restart deployment/ingress-proxy -n ai-pipeline

# Wait for deployment
echo "  Waiting for ingress-proxy to be ready..."
kubectl rollout status deployment/ingress-proxy -n ai-pipeline --timeout=120s || true

# Wait for certificate
echo "  Waiting for TLS certificate..."
for i in {1..30}; do
    STATUS=$(kubectl get certificate -n ai-pipeline ingress-proxy-tls -o jsonpath='{.status.conditions[?(@.type=="Ready")].status}' 2>/dev/null || echo "")
    if [ "$STATUS" = "True" ]; then
        echo "  ✓ Certificate ready"
        break
    fi
    sleep 2
done

# Get LoadBalancer IP
LB_IP=$(kubectl get svc -n ai-pipeline ingress-proxy -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "pending")

DOMAIN="${BREADBOARD_DOMAIN:-local}"

# Ensure /etc/hosts has entries for all local services so scripts inside the VM/host resolve them
HOSTS_LINE="127.0.0.1 dashboard.local fullsend.local github.local gitlab.local jira.local markovd.local observatory.local orgpulse.local relay.local relay-api.local hooksink.local hooksink-admin.local mlflow.local"
if [ "${DOMAIN}" != "local" ]; then
  HOSTS_LINE="${HOSTS_LINE} dashboard.${DOMAIN} fullsend.${DOMAIN} github.${DOMAIN} gitlab.${DOMAIN} jira.${DOMAIN} markovd.${DOMAIN} observatory.${DOMAIN} orgpulse.${DOMAIN} relay.${DOMAIN} relay-api.${DOMAIN} hooksink.${DOMAIN} hooksink-admin.${DOMAIN} mlflow.${DOMAIN}"
fi

MARKER="# Breadboard services"
if grep -q "${MARKER}" /etc/hosts 2>/dev/null; then
  sed -i "s/^.*${MARKER}.*$/${HOSTS_LINE} ${MARKER}/" /etc/hosts 2>/dev/null || true
elif [ -w /etc/hosts ]; then
  echo "${HOSTS_LINE} ${MARKER}" >> /etc/hosts
fi

echo "==> Ingress proxy deployed successfully"
echo ""
echo "LoadBalancer IP: ${LB_IP}"
echo ""
echo "Access services via:"
echo "  - GitHub:    http://${LB_IP} -H 'Host: github.${DOMAIN}'"
echo "  - GitLab:    http://${LB_IP} -H 'Host: gitlab.${DOMAIN}'"
echo "  - Jira:      http://${LB_IP} -H 'Host: jira.${DOMAIN}'"
echo "  - Dashboard: http://${LB_IP} -H 'Host: dashboard.${DOMAIN}'"
echo "  - Fullsend:  http://${LB_IP} -H 'Host: fullsend.${DOMAIN}'"
echo "  - MLflow:    http://${LB_IP} -H 'Host: mlflow.${DOMAIN}'"
echo "  - Org Pulse: http://${LB_IP} -H 'Host: orgpulse.${DOMAIN}'"
echo "  - Relay:     http://${LB_IP} -H 'Host: relay.${DOMAIN}'"
echo "  - Webhooks:  http://${LB_IP} -H 'Host: hooksink.${DOMAIN}'"
echo "  - Webhooks admin: http://${LB_IP} -H 'Host: hooksink-admin.${DOMAIN}'"
echo ""
