#!/usr/bin/env bash
# Install the user config and select it for K3s's bundled kubectl in Bash.
set -euo pipefail

[ "$(id -u)" -ne 0 ] || { echo "Run as the operator user, not root or sudo make" >&2; exit 1; }

config_dir="${HOME}/.kube"
config_file="${config_dir}/config"
# Optional source override supports isolated fixture tests.
source_file="${K3S_KUBECONFIG_SOURCE:-/etc/rancher/k3s/k3s.yaml}"
install -d -m 0700 "${config_dir}"
if [ -e "${config_file}" ]; then
  compare_status=0
  sudo cmp -s "${source_file}" "${config_file}" || compare_status=$?
  if [ "${compare_status}" -eq 1 ]; then
    backup_file=$(mktemp "${config_dir}/config.backup.XXXXXXXX")
    install -m 0600 "${config_file}" "${backup_file}"
    printf 'Existing user config backed up to %s\n' "${backup_file}"
  elif [ "${compare_status}" -ne 0 ]; then
    echo "Could not compare kubeconfigs; existing user config was preserved" >&2
    exit 1
  fi
fi
sudo install -m 0600 -o "$(id -u)" -g "$(id -g)" "${source_file}" "${config_file}"

marker='# Breadboard user kubeconfig (preserve an explicit KUBECONFIG)'
if ! grep -Fqx -- "${marker}" "${HOME}/.bashrc" 2>/dev/null; then
  cat >> "${HOME}/.bashrc" <<'EOF'

# Breadboard user kubeconfig (preserve an explicit KUBECONFIG)
if [ -z "${KUBECONFIG:-}" ] && [ -r "${HOME}/.kube/config" ]; then
  export KUBECONFIG="${HOME}/.kube/config"
fi
EOF
fi
printf '%s\n' 'User kubeconfig installed with mode 0600.' \
  'New Bash shells select it when KUBECONFIG is unset.' \
  'For the current shell, run: export KUBECONFIG="$HOME/.kube/config"'
