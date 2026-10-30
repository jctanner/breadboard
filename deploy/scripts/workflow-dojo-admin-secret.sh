#!/usr/bin/env bash
# Create Workflow Dojo's bootstrap login Secret (admin/admin) if it is missing.
# The dojo only uses it to create the admin account when that account doesn't
# exist yet, so a password changed on the dojo's Account page sticks across
# restarts. Delete the dojo's state volume to start over.
set -euo pipefail

NAMESPACE=ai-pipeline
if ! kubectl get secret workflow-dojo-admin -n "${NAMESPACE}" >/dev/null 2>&1; then
  kubectl create secret generic workflow-dojo-admin -n "${NAMESPACE}" \
    --from-literal=username=admin --from-literal=password=admin
fi
