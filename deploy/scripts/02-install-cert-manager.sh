#!/bin/bash
# Install cert-manager for certificate management

set -euo pipefail

CERT_MANAGER_VERSION="v1.14.4"

echo "==> Installing cert-manager ${CERT_MANAGER_VERSION}..."

# Install cert-manager CRDs and deployment
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/${CERT_MANAGER_VERSION}/cert-manager.yaml

echo "==> Waiting for cert-manager to be ready..."
kubectl wait --for=condition=Available --timeout=300s \
  -n cert-manager deployment/cert-manager
kubectl wait --for=condition=Available --timeout=300s \
  -n cert-manager deployment/cert-manager-webhook
kubectl wait --for=condition=Available --timeout=300s \
  -n cert-manager deployment/cert-manager-cainjector

echo "==> Enabling NameConstraints feature gate on cert-manager..."
for deploy in cert-manager cert-manager-webhook; do
  if ! kubectl get deployment "${deploy}" -n cert-manager -o jsonpath='{.spec.template.spec.containers[0].args}' | grep -q "NameConstraints=true"; then
    kubectl patch deployment "${deploy}" -n cert-manager --type=json \
      -p='[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--feature-gates=NameConstraints=true"}]'
  fi
done
kubectl rollout status deployment/cert-manager -n cert-manager --timeout=120s
kubectl rollout status deployment/cert-manager-webhook -n cert-manager --timeout=120s

echo "==> cert-manager installation complete!"
echo ""
kubectl get pods -n cert-manager
echo ""
echo "==> Next: Apply certificate infrastructure from deploy/k8s/"
