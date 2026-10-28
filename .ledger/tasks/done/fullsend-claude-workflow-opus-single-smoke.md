# Task: Single-RFE Opus smoke through Fullsend and OpenShell

## Goal

Run one new synthetic RFE through GitLab CI on `feat/fullsend-claude-workflow`,
using the released native Fullsend launcher and hardened Claude Workflow.
The user authorized one paid smoke on 2026-10-18; no automatic paid retry.

## Acceptance criteria

- [x] Seed one distinct eligible RFE without resetting existing Jira data.
- [x] Submit the authorized smoke with Opus 4.6, high effort, cap ten; retain
      the initial bootstrap failure separately and allow no paid retry.
- [x] Verify the pinned candidate, actual model route and native Workflow launch.
- [x] Inspect strategy/review delivery, completion receipt and host validation.
- [x] Inspect publication, owned-lock release and sandbox cleanup.
- [x] Archive evidence privately, including real API dumps and syscall traces,
      and independently verify its manifest. Preserve failure evidence too.

## Pins and prior qualification

- GitLab project 7, initial qualified adapter head `7b93d35a3bc718f45ec96b4e8d77461fb81dfc81`.
- Candidate `6ed858b2294a29457153a90f187a801022c21e8b` (PR 85).
- Fullsend 0.47.1, Claude Code 2.1.296, OpenShell 0.0.112-rhaiv.0.
- Opus-only relay client, managed Vertex account; no upstream key in sandbox.
- Model-free preflight 2095/job 4059 passed and its archive verifies.
- [Setup and preflight](../done/fullsend-claude-workflow-relay-copy.md).

## Status

Done. Successful pipeline **2100**, strategy job **4068**, dashboard trigger
**4069**, on adapter SHA `fdc770c1dcec61b2153cbd6901e1db7947a78bc9`.
Ticket **RHAIRFE-19** requests workbench PVC expansion with quota, RBAC and
storage-class readiness checks. Existing 18 RFEs were preserved; the new
summary and scope differ from each of them. Exact launch variables and the
pre-run Jira inventory are saved in the private launch receipt, to be archived.

The initial guard found old pending September demo pipelines, none running.
The narrowed guard confirmed no active pipeline on the copied branch before
the single submission; those historical pending entries were left unchanged.

### Pre-inference adapter failure

Pipeline **2096/job 4060** ran 01:34:38–01:38:26 UTC (3m48s), but native
Fullsend rejected `--debug api,hooks` before creating any sandbox or running
host preparation. Owned-lock release and gateway/capture cleanup passed.
The relay archive has **zero requests**. The flag now uses `--debug=api,hooks`;
all **16 model-free checks** pass, including a real released-CLI parser test.
See [bug and fix](../../bugs/fixed/fullsend-workflow-debug-optional-flag.md).

Final failed-launch archive verifies:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2096/20261019T014133.547497Z`.
The prior capture at `20261019T014003.674624Z` is explicitly incomplete because
an optional whole historical results-repository fetch hit HTTP 502. The final
capture retains its head plus the actual run artifacts instead. Both captures
are preserved. The corrected launch reuses the same ticket and settings; this
is a continuation after zero inference, not an automatic paid retry.

### Context preparation and evidence retention

Pipeline **2097/job 4062** failed in the host pre-script on broken sparse
architecture aliases, before sandbox/model execution. The RFE was locked once
and released successfully. Archived relay request list is empty. The artifact
redactor then dropped its local folders on trusted-clone symlinks, so the
available-evidence capture verifies hashes but has a known native-artifact gap.
See [reproduction and fixes](../../bugs/fixed/fullsend-workflow-sparse-context-and-artifact-links.md).

The copied adapter now uses the same context pin/subset as the benchmarks,
records links without following them, and refuses a complete-archive claim
when required artifacts are absent. All **18 model-free checks** pass; the
unchanged freshness guard accepts the real 1,844-document pinned snapshot and
rejects the broken sparse-checkout negative control. No source Workflow edit,
new RFE, inference call, or paid retry was needed for either bootstrap fix.

### Context pin and certificate ordering

Pipeline **2098** reuses RHAIRFE-19 after a live check that processing/owner
labels were released. Explicit primary/subagent settings remain Opus 4.6 /
high / cap ten. Candidate pin is unchanged. Context pin is the benchmark's
`7d61f097a9220aeb1280837b66b532177ec558b6`.

The snapshot fetch in 2098 stopped on the runner's inherited local-only CA
before a lock, gateway or model started. Export the existing combined
public/local CA before bootstrap. The shell ordering regression passes;
**19 model-free tests** pass. [Fix](../../bugs/fixed/fullsend-workflow-context-ca-order.md).
The 2098 archive is complete and independently verified:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2098/20261019T015557.703731Z`.

A new 2097 capture explicitly records the native-artifact gap and correctly
fails completeness verification:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2097/20261019T015556.613703Z`.
This preserves the earlier capture without silently changing its manifest.

### Actual smoke continuation

**2099/4066** submitted at approximately 01:58 UTC with the same RFE and all
explicit model settings. The pinned snapshot fetched successfully at 01:58:41;
gateway/sandbox image preparation passed. No paid inference retry.

2099 reached native Claude, but OpenShell refused the compiled `claude.exe`
identity, which was absent from the relay profile. The native result is
`ERR_PROXY_TUNNEL`, one agent run, **zero tokens / $0**; relay has zero requests.
Missing business output was correctly rejected and host publication skipped.
The owned RFE claim was released. Command exit 1, capture exit 0, cleanup exit 0.

Its complete archive and separate verification pass:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2099/20261019T020654.319358Z`.
Manifest: **2,791 files / 266,600,681 bytes**, including **11 raw API capture
files** and **139 syscall trace files**, native sessions and OpenShell policy
denials. [Exact executable fix](../../bugs/fixed/fullsend-workflow-native-claude-proxy-policy.md)
adds only that observed path, with no network or credential-policy relaxation.
All **19 model-free checks** pass. The native SDK made transport retries even
though Fullsend's validation loop was limited to one iteration; these are
different retry layers, and none of these attempts reached inference.

**2100/4068** continues with the same ticket, model settings, source and context
pins. Previous zero-usage result and unlocked ownership were checked before
submission. No paid run has been repeated.

Read-only completion/archive observer PID **1342264** is attached. It waits
for the root pipeline and any downstream dashboard build, captures evidence
under `var/run-data/fullsend-claude-workflow`, then runs a separate checksum
verification. It cannot launch or retry model work. Private status output:
`/tmp/fullsend-workflow-opus-smoke-observer-2100-result.json`;
progress log `/tmp/fullsend-workflow-opus-smoke-observer-2100.log`.
Launch receipt `/tmp/fullsend-workflow-opus-single-native-actual.json` is
included in automatic archival.

### Live qualification, 02:14 UTC

2100/4068 is running. Native Claude started at **02:13:58 UTC** and invoked
the **Workflow tool at 02:14:05**; it reported the Workflow running at 02:14:26.
Source remains the pinned candidate; all five original GitLab branch heads
were unchanged at publication. No strat-creator source edits were made.

The first relay request `97d0d0b7-135d-49ef-a265-03d30082f3ae` completed with
HTTP 200. Requested and resolved model both equal **claude-opus-4-6**, project
**vertex-shim-local**, upstream profile **vertex-strat-evals**, run ID
**gitlab-job-4068**. The next request was also HTTP 200. Real evidence counts
at the first live inspection: four API files / 203,487 bytes and 153 strace
files / 49,163,615 bytes. These are provisional counts, not a final inventory.

Business completion/reviewer delivery/publication and final lock/gateway
cleanup still require terminal analysis. The observer will retain the final
data and independently verify it. No further paid run is authorized by this
task.

### Terminal result

**PASS.** Strategy job 4068 ran **02:09:38–02:35:43 UTC (26m05s)** on
2026-10-19. Native Claude ran once; the Workflow completed create, refine,
push and review for RHAIRFE-19 → **RHAISTRAT-16**, recommendation **approve**.
All four role report files are present: feasibility, testability, scope and
architecture. The completion contract is `strat-business-validation-v1`,
`check_exit: 0`, receipt `7fc6da1ecf8a46dc8d2edd10d7553115`, no errors or skips.
Fullsend's host validation passes against run record, progress, artifacts and
scores. Post-script publishes the report bundle successfully to results main,
now `383dce3bdaf3722c8c42a1e98717757fa5b12308`. Downstream dashboard pipeline
**2101** also succeeds. The owned RFE claim is released. Fullsend, capture,
gateway cleanup and lock-release exits are all zero.

Final private archive:
`var/run-data/fullsend-claude-workflow/gitlab-pipeline-2100/20261019T023624.716768Z`.
**5,535 files / 910,118,102 bytes**, including **218 API capture files**,
native transcripts, syscall traces, both pipeline results, exact CI/candidate
source, Jira/shared-service state and relay lifecycle events. Archive collection
and a separate verification process both exit zero. The observer finishes at
02:37:02 UTC. Native CLI reports $7.0745; that is not an invoice reconciliation.

### Changes to carry into strat-creator

The successful smoke used the unchanged `6ed858b` feature branch with local
deployment adaptations. Two general fixes should be carried into that branch:
safe default architecture fetching that avoids broken sparse aliases, and
host-only dependency preflight while retaining qualified Claude checks inside
the sandbox. Relay endpoints/profiles, CA setup, launcher flags and evidence
collection remain deployment configuration. No feature-branch edits or new
model run were performed while answering this follow-up.
