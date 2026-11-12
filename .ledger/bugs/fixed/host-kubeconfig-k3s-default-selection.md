# K3s kubectl ignored the copied user config

The operator reproduced a successful host-kubeconfig copy followed by permission
denied on the protected server config. K3s's kubectl symlink selects its server
file when KUBECONFIG is unset. Install the user file0600 in directory0700, back up
differing operator data0600, refuse root invocation and configure an idempotent
Bash fallback preserving explicit contexts. Print the export required in an
already-running shell. Source server permissions remain untouched.

Actual fresh Bash on the test host runs kubectl get nodes without sudo; server
config remains0600/root and the user config0600/operator. Offline tests cover
selection, explicit contexts, modes, backup/idempotence, root refusal and failed
source comparison preserving the old config. Non-Bash setup is explicitly manual.
