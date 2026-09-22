#!/usr/bin/env bash
# Run the conformance triage scenario end to end and leave an evidence folder.
#
# This is the conformance path, not a legacy compatibility test: it files a
# real issue on the forge, waits for the real Fullsend workflow to route and
# dispatch it, and then asserts on what the run actually produced rather than
# on whether it reported success. Several runs during this work concluded
# "success" while doing nothing useful - uploading an empty artifact, or
# writing a result the agent never reached - so the assertions below check
# artefacts and identities, and the run conclusion is only one of them.
#
# Everything it collects is written under var/conformance/<run-id>/ so a
# failure can be handed to someone else without chat history.
#
# The triage action the agent chooses is deliberately NOT asserted. It depends
# on what else is open in the repository - an issue resembling an open one is
# correctly triaged as a duplicate - and every action exercises the same path:
# sandbox, agent, schema validation, post-script, forge write. Asserting the
# action would make this check fail for a correct result.
#
# For the same reason the issue it files is closed when the run finishes, so
# repeated runs neither accumulate open issues nor turn into a chain of
# duplicates of each other.
#
# Usage: 24-run-conformance-triage.sh [--keep-issue]
#   --keep-issue   leave the filed issue open for inspection

set -euo pipefail

KEEP_ISSUE=0
for arg in "$@"; do
  case "${arg}" in
    --keep-issue) KEEP_ISSUE=1 ;;
    *) echo "unknown argument: ${arg}" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"

FORGE="${CONFORMANCE_FORGE:-https://github.local}"
REPO="${CONFORMANCE_REPO:-fullsend-dev/triage-target}"
TOKEN="${GITHUB_EMULATOR_TOKEN:-ghp_admin_default_token}"
API="${FORGE}/api/v3/repos/${REPO}"
AUTH="Authorization: token ${TOKEN}"
# The workflow that is the conformance path. Selecting on the event alone is
# not enough: the legacy m8 fixture fires on the same issues event and is
# cancelled every time, and picking it up has cost real time more than once.
WORKFLOW_NAME="${CONFORMANCE_WORKFLOW:-fullsend}"
# The identity the post-script must write as. If this ever reverts to the run
# actor, credential scoping has regressed the way it did in G39.
EXPECT_AUTHOR="${CONFORMANCE_BOT:-fullsend-triage[bot]}"
TIMEOUT_SECONDS="${CONFORMANCE_TIMEOUT:-900}"

fail() { echo "CONFORMANCE FAIL: $*" >&2; exit 1; }
note() { echo "==> $*"; }

command -v python3 >/dev/null || fail "python3 is required"
command -v curl >/dev/null || fail "curl is required"

api() { curl -sk -H "${AUTH}" "$@"; }

# --- Precondition: the gateway serves the profiles we think it does --------
# A provider profile is the sandbox's network and binary policy. The gateway
# served a 26-day-old copy of one while every run reported importing it,
# because Fullsend's ImportProfile discarded a refused delete and cached
# success (G42, fixed upstream by patch 0010). The symptom was an agent denied
# access its own policy file granted, and it cost a day to find.
#
# So this is checked before anything else runs: the installed profile must
# match the mirrored source the run will be composed against. Skipped when
# openshell is not reachable, since a conformance run against a stack without
# a gateway fails later and more clearly.
if kubectl get deploy/github-actions-runner -n ai-pipeline >/dev/null 2>&1; then
  note "Checking installed provider profiles against the mirrored source"
  for PROFILE in fullsend-vertex-ai fullsend-github-ro; do
    INSTALLED="$(kubectl exec -n ai-pipeline deploy/github-actions-runner -- \
      openshell provider profile export "${PROFILE}" 2>/dev/null || true)"
    SOURCE="$(api "${FORGE}/fullsend-ai/agents/raw/main/profiles/${PROFILE}.yaml" 2>/dev/null || true)"
    if [ -z "${INSTALLED}" ] || [ -z "${SOURCE}" ]; then
      note "  ${PROFILE}: could not compare (skipping)"
      continue
    fi
    printf '%s' "${INSTALLED}" > /tmp/.conf-installed.yaml
    printf '%s' "${SOURCE}" > /tmp/.conf-source.yaml
    python3 - "${PROFILE}" /tmp/.conf-installed.yaml /tmp/.conf-source.yaml <<'PY' || fail "provider profile ${PROFILE} is stale; see above"
import sys, yaml
name, installed_path, source_path = sys.argv[1:4]
def shape(path):
    d = yaml.safe_load(open(path)) or {}
    eps = sorted(
        (e.get("host"), e.get("port"), e.get("protocol"), e.get("access"), e.get("path"))
        for e in (d.get("endpoints") or [])
    )
    return eps, sorted(d.get("binaries") or [])
gi, bi = shape(installed_path)
gs, bs = shape(source_path)
if gi == gs and bi == bs:
    print(f"  {name}: matches source")
    sys.exit(0)
print(f"  {name}: DOES NOT MATCH the mirrored source", file=sys.stderr)
for label, inst, src in (("endpoints", gi, gs), ("binaries", bi, bs)):
    missing = [x for x in src if x not in inst]
    extra = [x for x in inst if x not in src]
    if missing:
        print(f"    {label} missing from the gateway: {missing}", file=sys.stderr)
    if extra:
        print(f"    {label} only on the gateway:      {extra}", file=sys.stderr)
print("    Reconcile it in place (delete is refused while a sandbox references it):",
      file=sys.stderr)
print(f"      openshell provider profile export {name} > /tmp/{name}.yaml", file=sys.stderr)
print(f"      # copy resource_version from that export into the source file, then",
      file=sys.stderr)
print(f"      openshell provider profile update --file <source> {name}", file=sys.stderr)
sys.exit(1)
PY
  done
fi

# --- File the issue -------------------------------------------------------
# The timestamp makes each issue identifiable, not substantively novel: two
# runs file the same complaint, and the second is correctly triaged as a
# duplicate of the first. That is why the issue is closed at the end and why
# the action is not asserted.
STAMP="$(date -u +%Y%m%d-%H%M%S)"
TITLE="Conformance check ${STAMP}: undocumented behaviour in the repository root"
read -r -d '' BODY <<EOF || true
Filed automatically by deploy/scripts/24-run-conformance-triage.sh at ${STAMP}.

**Steps to reproduce**
1. List the repository root and note which files are not mentioned in any of
   \`README.md\`, \`CONTRIBUTING.md\`, \`SUPPORT.md\` or \`MAINTAINERS.md\`.
2. Try to determine from the documentation alone whether each one may be
   modified or removed.

**Expected**
Every file at the root is either explained in the documentation or removed.

**Actual**
Some are neither, so a contributor cannot tell what is load-bearing.

**Impact**
Anyone tidying the repository risks deleting something a test depends on, and
an agent working in it has the same problem.
EOF

note "Filing an issue on ${REPO}"
ISSUE="$(python3 - "$API" "$TOKEN" "$TITLE" "$BODY" <<'PY'
import json, ssl, sys, urllib.request
api, token, title, body = sys.argv[1:5]
req = urllib.request.Request(
    api + "/issues",
    data=json.dumps({"title": title, "body": body}).encode(),
    headers={"Authorization": "token " + token, "Content-Type": "application/json"},
)
ctx = ssl.create_default_context(); ctx.check_hostname = False; ctx.verify_mode = ssl.CERT_NONE
print(json.load(urllib.request.urlopen(req, context=ctx))["number"])
PY
)" || fail "could not file the issue"
[ -n "${ISSUE}" ] || fail "could not file the issue"
note "Issue #${ISSUE}"

# --- Wait for the run -----------------------------------------------------
note "Waiting for the ${WORKFLOW_NAME} workflow (timeout ${TIMEOUT_SECONDS}s)"
RUN_ID=""; CONCLUSION=""
DEADLINE=$(( $(date +%s) + TIMEOUT_SECONDS ))
while [ "$(date +%s)" -lt "${DEADLINE}" ]; do
  if [ -z "${RUN_ID}" ]; then
    RUN_ID="$(api "${API}/actions/runs?per_page=10" | python3 -c '
import sys, json
name = sys.argv[1]
for r in json.load(sys.stdin).get("workflow_runs", []):
    if r.get("event") == "issues" and r.get("name") == name:
        print(r["id"]); break
' "${WORKFLOW_NAME}" 2>/dev/null || true)"
  fi
  if [ -n "${RUN_ID}" ]; then
    read -r STATUS CONCLUSION <<<"$(api "${API}/actions/runs/${RUN_ID}" | python3 -c '
import sys, json
d = json.load(sys.stdin)
print(d.get("status"), d.get("conclusion"))' 2>/dev/null || echo "unknown None")"
    [ "${STATUS}" = "completed" ] && break
  fi
  sleep 15
done
[ -n "${RUN_ID}" ] || fail "no ${WORKFLOW_NAME} run appeared for issue #${ISSUE}"
[ "${STATUS:-}" = "completed" ] || fail "run ${RUN_ID} did not finish within ${TIMEOUT_SECONDS}s"
note "Run ${RUN_ID} finished: ${CONCLUSION}"

# --- Collect evidence -----------------------------------------------------
# Collected before the assertions, so a failing run still leaves a folder.
EVIDENCE="${PROJECT_ROOT}/var/conformance/run-${RUN_ID}"
mkdir -p "${EVIDENCE}"
note "Collecting evidence to ${EVIDENCE#${PROJECT_ROOT}/}"

JOB_ID="$(api "${API}/actions/runs/${RUN_ID}/jobs" | python3 -c '
import sys, json
for j in json.load(sys.stdin).get("jobs", []):
    if j.get("name") == "Triage":
        print(j["id"]); break' 2>/dev/null || true)"
[ -n "${JOB_ID}" ] && api "${API}/actions/jobs/${JOB_ID}/logs" > "${EVIDENCE}/triage-job.log" || true
api "${API}/issues/${ISSUE}" > "${EVIDENCE}/issue.json"
api "${API}/issues/${ISSUE}/comments" > "${EVIDENCE}/issue-comments.json"
api "${API}/actions/runs/${RUN_ID}" > "${EVIDENCE}/run.json"
api "${API}/actions/runs/${RUN_ID}/artifacts" > "${EVIDENCE}/artifacts.json"

ARTIFACT_ID="$(python3 -c '
import json, sys
d = json.load(open(sys.argv[1]))
print(d["artifacts"][0]["id"] if d.get("total_count") else "")' "${EVIDENCE}/artifacts.json")"
if [ -n "${ARTIFACT_ID}" ]; then
  api "${API}/actions/artifacts/${ARTIFACT_ID}/zip" > "${EVIDENCE}/evidence.zip"
  api "${API}/actions/artifacts/${ARTIFACT_ID}" > "${EVIDENCE}/artifact-index.json"
fi

# Revisions, so a failure can be tied to the source that produced it.
python3 - "${PROJECT_ROOT}" "${EVIDENCE}" "${RUN_ID}" "${JOB_ID}" "${ISSUE}" "${CONCLUSION}" <<'PY'
import json, subprocess, sys, pathlib
root, evidence, run_id, job_id, issue, conclusion = sys.argv[1:7]
def rev(p):
    try:
        return subprocess.run(["git", "-C", str(pathlib.Path(root) / p), "rev-parse", "HEAD"],
                              capture_output=True, text=True, check=True).stdout.strip()
    except Exception:
        return None
summary = {
    "run_id": run_id, "job_id": job_id or None, "issue": int(issue),
    "conclusion": conclusion,
    "revisions": {
        "breadboard": rev("."),
        "fullsend": rev("checkouts/fullsend-ai/fullsend"),
        "agents": rev("checkouts/fullsend-ai/agents"),
        "openshell": rev("checkouts/openshell"),
        "github-emulator": rev("checkouts/github-emulator"),
    },
}
pathlib.Path(evidence, "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
PY

# --- Close the issue ------------------------------------------------------
# Before the assertions, so a failing run does not leave one open either. The
# issue is preserved in issue.json and issue-comments.json.
if [ "${KEEP_ISSUE}" -eq 0 ]; then
  curl -sk -o /dev/null -X PATCH -H "${AUTH}" -H "Content-Type: application/json" \
    -d '{"state":"closed"}' "${API}/issues/${ISSUE}" || true
  note "Closed issue #${ISSUE} (evidence retained)"
fi

# --- Assertions -----------------------------------------------------------
# Each of these failed silently at least once during this work.
note "Checking what the run actually produced"
python3 - "${EVIDENCE}" "${CONCLUSION}" "${EXPECT_AUTHOR}" <<'PY'
import json, sys, pathlib
evidence, conclusion, expect_author = sys.argv[1:4]
E = pathlib.Path(evidence)
problems = []

if conclusion != "success":
    problems.append(f"run conclusion is {conclusion!r}, not 'success'")

arts = json.loads((E / "artifacts.json").read_text())
if not arts.get("total_count"):
    problems.append("no artifact was uploaded, so the run left no evidence of itself")
elif not (E / "evidence.zip").exists() or (E / "evidence.zip").stat().st_size == 0:
    problems.append("the artifact could not be downloaded")

issue = json.loads((E / "issue.json").read_text())
if not issue.get("labels"):
    problems.append("the agent applied no label to the issue")

comments = json.loads((E / "issue-comments.json").read_text())
authors = [c["user"]["login"] for c in comments]
if len(comments) < 2:
    problems.append(f"expected a status comment and a triage comment, found {len(comments)}")
wrong = [a for a in authors if a != expect_author]
if wrong:
    # G39: the post-script wrote as the run actor because an ambient admin
    # token outranked the minted one. Nothing in the log said so.
    problems.append(f"comments written by {sorted(set(wrong))}, expected only {expect_author!r}")

log = E / "triage-job.log"
if log.exists():
    text = log.read_text(errors="replace")
    if "policy_denied" in text:
        problems.append("the sandbox policy denied a request the agent needed")
    if "Agent exited with code 0" not in text:
        problems.append("the agent did not exit 0")

print(f"  conclusion      {conclusion}")
print(f"  artifact        {arts.get('total_count', 0)} ({(E / 'evidence.zip').stat().st_size if (E / 'evidence.zip').exists() else 0} bytes)")
print(f"  labels          {[l['name'] for l in issue.get('labels', [])]}")
print(f"  comment authors {sorted(set(authors))}")

if problems:
    print("\nCONFORMANCE FAIL:", file=sys.stderr)
    for p in problems:
        print(f"  - {p}", file=sys.stderr)
    sys.exit(1)
PY

note "Conformance triage passed. Evidence: ${EVIDENCE#${PROJECT_ROOT}/}"
