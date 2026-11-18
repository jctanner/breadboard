#!/bin/bash
# The rfe-autofixer setup steps that matter to the gateway, then agentic-ci's gateway.start()
# with a timeout long enough to tell "slow" from "broken". Prints the gateway log.
set -u
# As strat-creator's with-fullsend-gateway.sh: keep the gateway off its in-cluster (Kubernetes) bootstrap.
unset KUBERNETES_SERVICE_HOST KUBERNETES_SERVICE_PORT KUBERNETES_PORT
: > /etc/subuid
: > /etc/subgid
printf '[storage]\ndriver = "vfs"\n' > /etc/containers/storage.conf
echo "SMOKE agentic-ci: $(python3 -m pip show agentic-ci 2>/dev/null | sed -n 2p)"
echo "SMOKE openshell: $(openshell --version) / $(openshell-gateway --version)"
echo "SMOKE supervisor env: ${OPENSHELL_SUPERVISOR_IMAGE:-unset}"
echo "SMOKE uid: $(id -u) XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-unset}"
python3 - <<'PY'
import glob, os, subprocess, time
from agentic_ci.backends.openshell import gateway
print("SMOKE gateway module:", gateway.__file__)
t0 = time.time()
try:
    gateway.start()
    print(f"SMOKE gateway healthy after {time.time()-t0:.0f}s")
    ok = True
except Exception as exc:
    print(f"SMOKE gateway start failed after {time.time()-t0:.0f}s: {exc}")
    ok = False
st = os.path.expanduser("~/.local/state/openshell")
for f in sorted(glob.glob(st + "/gateway-*.log")):
    print("----- gateway log", f)
    print(open(f).read()[-6000:])
cfg = glob.glob(os.path.expanduser("~/.config/openshell/*.toml")) + glob.glob(os.path.expanduser("~/.config/openshell/**/*.toml"), recursive=True)
for f in cfg:
    print("----- config", f); print(open(f).read())
print("----- openshell status"); print(subprocess.run(["openshell", "status"], capture_output=True, text=True).stdout[-1500:])
print("----- ps"); print(subprocess.run(["sh", "-c", "ps -eo pid,args | grep -E 'openshell|podman' | grep -v grep"], capture_output=True, text=True).stdout)
if ok:
    gateway.stop()
print("SMOKE_PASS" if ok else "SMOKE_FAIL")
PY
