# Fullsend strategy CI

Publishes `feat/fullsend-strategy-poc` in
`redhat/rhel-ai/agentic-ci/strat-pipeline`; native `main` and its four job
contracts remain available for comparison and rollback. The normal pipeline supports
manual `single-rfe` and manual/scheduled `batch-discover`. Native single-RFE has no resource group; issue
locking is handled by the entrypoint. Native batch resource groups are untouched.

## Publish

Supply `GITLAB_ADMIN_USER`, `GITLAB_ADMIN_PASSWORD`, and `GITLAB_CA_FILE`
through the environment, then run:

```sh
python3 var/demos/fullsend-entrypoint-poc/strategy-ci/publish.py --enable-runner
```

The script uses the existing project and runner registration, installs the M5
bot's Basic credentials from `ai-pipeline/fullsend-strategy-jira`, and publishes
without running CI. It preserves results/GCP/Org Pulse inputs and native main.
`--enable-runner` requires exactly one maintained `glemu-k8s-runner`; it adds
privilege and independent emptyDirs to each job pod, then restarts its manager.
It never mounts the host Podman socket or storage. Destroying a job pod removes
its gateway, sandbox processes, and storage. M7 must make this capability
persistent in deployment/reset automation and validate convergence.

## Required inputs before playing single-rfe

- `RFE_KEY=RHAIRFE-1` as a pipeline variable.
- `VERTEX_CREDENTIALS_JSON`: existing Breadboard Vertex credential JSON,
  provisioned as a masked variable from `ai-pipeline/gcp-credentials`.
  Authorized-user ADC is explicitly approved by the user for this POC.
- `ANTHROPIC_VERTEX_PROJECT_ID`: that credential's permitted Vertex project.
- `RESULTS_PUSH_TOKEN`: masked GitLab results repository credential.
- `ORG_PULSE_API_TOKEN`: masked publication credential.
- `FULLSEND_GITLAB_ANALYST_TOKEN`: the Fullsend triage-role forge credential,
  if required by the selected feature build.

The fork revision is pinned in CI and checked on every job. Source metadata,
Fullsend binary revision/checksum, image versions, logs, and run outputs are
retained for 30 days. Credential files and the target checkout are excluded.
The same target checkout supplies the harness, skills, and target repository;
no source emulator or upstream main substitution is allowed.

Create a pipeline on the POC branch and play `single-rfe` after build success.
The downstream dashboard trigger runs only after successful strategy completion.
Org Pulse's native helper is non-blocking; acceptance additionally requires a
separate read of the published feature, not merely pipeline success.

## Acceptance evidence

The real run is recorded in the M6 ledger task: pipeline 2037/job 3955,
RHAIRFE-1 → RHAISTRAT-1, result run 20261006-165222.
The user approved the existing Breadboard Vertex credentials, superseding
the dedicated-service-account requirement. Trusted local-service access, real phase execution, result publication,
timeout/cancellation and hard-pod removal have been verified; the final
fresh-pod recovery check is recorded in the ledger. The updated fork uses opaque local-service tunnels with certificate and
hostname verification in clients; public GitHub retains HTTP inspection.

## Diagnostics

Milestone diagnostics live on `feat/fullsend-runner-validation`, outside the
normal pipeline. Use runner-validation/publish.py --diagnostic model-smoke,
--diagnostic sandbox-connectivity, or --diagnostic lifecycle-check --lifecycle
cancel|timeout|hard-kill. Preserve the existing job-owned cancellation and
partial-work recovery rules; see the completed M6 ledger evidence.

## Artifact handling

An inherited EXIT sanitizer and the CI after-script redact exact managed credential values from output and
native Claude transcripts before upload. A synthetic fixture in the read-only
gate verifies this path. If redaction fails, generated artifact directories
are removed to prevent uploading sensitive content. Do not upload the target
checkout, private credential file, Podman storage or gateway database.

The real strategy review recommended **revise** (5/8) and set
`strat-creator-needs-attention`. Keep that review outcome and process it
through the normal human workflow; repeating an already processed seed is
not equivalent to the initial acceptance run. M7 covers durable deployment,
reset convergence and the remaining single-runner platform regression.

M7 additionally verified sanitization on a deliberate failure (2044/3975,
synthetic credential only). The EXIT sanitizer preserves the original nonzero
status; it is needed because the emulator skips its appended after_script
after a script error. `--enable-runner` now delegates to the authoritative
deployment script instead of modifying live runner configuration separately.

## Exact model gate before M8

The strategy harness and CI caller pin `claude-opus-4-6` with effort high.
The wrapper pins the opus alias and all subagent selection to that model;
ambient Fullsend model/fallback overrides are cleared. General Fullsend
defaults and historical M6 evidence remain unchanged (M6 used 4.8).

`publish.py` without run options republishes CI without starting strategy work.
`../runner-validation/publish.py --diagnostic model-smoke` selects only the feature build and a one-turn
Vertex smoke in the normal OpenShell CI image. It derives a smoke harness
from the pinned strategy harness and launches the generated `fullsend-claude`
helper with tools disabled. It does not reset Jira, process RHAIRFE-1, create
strategy artifacts or publish results. Existing credentials, hooks, image pins,
EXIT redaction and job-owned gateway cleanup are preserved.

Verify actual stream/provider model metadata and nonzero token usage before
closing the gate; an echoed CLI flag alone is insufficient. A failed or
unavailable 4.6 request must not fall back to the moving opus alias.

Verified in pipeline **2047**, model-smoke job **3981**: assistant response and
result canonicalModel report `claude-opus-4-6`, provider `vertex`, one turn
with nonzero usage. Claude Code v2.1.260; pinned strategy source `68614f6`.
Artifacts contain no managed credential matches; cleanup exit 0 with no
containers or job network remaining. Full evidence and the corrected initial
smoke invocation are recorded in the completed pre-M8 ledger task.

## M8 batch invocation

Publish only (no pipeline): `publish.py`. Create an explicitly selected manual
single-RFE pipeline: `publish.py --rfe RHAIRFE-N`. Create a discovery pipeline:

```sh
python3 var/demos/fullsend-entrypoint-poc/strategy-ci/publish.py \
  --batch-discover --batch-size 2 --batch-offset 0 \
  --expected-keys 'RHAIRFE-A RHAIRFE-B'
```

Play `batch-discover` after the feature build passes. Use actual issue keys.
The expected bound is optional in regular usage; when provided it aborts before
locking if discovery changed. Native pipeline-settings JQL/filtering runs before
size/offset slicing. Batch jobs serialize with resource_group strat-batch and
keep the native five-hour budget. No recurring schedule is installed here.
`batch-selected` is the approved name for the deferred curated-list variant.

Normal jobs are build, selected strategy job and its matching dashboard bridge;
no diagnostics or missing-job needs occur. Schedule source selects discovery
only when RFE_KEY is blank. Results dashboard rules support either strategy
job; the emulator's eager bridge still needs a fresh build after publication.

Before recovering a failed batch inspect partial Jira effects, linked strategies,
retained artifacts and recorded locks. Cleanup releases only owned locks;
do not reset Jira, drop review gates, or automatically replay partial work.

## M8 acceptance and Org Pulse recovery

Source efcf946, pipeline 2053/job 3993: RHAIRFE-2/3 → RHAISTRAT-2/3,
actual Opus 4.6, both reviews approve 8/8, run 20261006-223446. Results,
sanitation, owned locks and gateway cleanup passed. Fresh dashboard 2055/3996
contains both strategies and run data. These fixtures are now processed.

If ingest reports success but per-feature Org Pulse GETs return 404 after a
Jira reset/key reuse, inspect canonical review data and stale flags first.
The existing admin POST /api/admin/refresh/handler with
`{"handlerId":"releases:jira-sync"}` reconciles recreated keys and bypasses
cadence. Use existing admin secret handling; do not print internal secrets,
edit data files manually, reset Jira, or repeat strategy/model work. The
underlying ingest-trigger/cadence bug is tracked in the ledger; M8 verified
this recovery and both per-feature reads without claiming a durable fix.

### CI progress logging

Current caller pins strat-creator `7244097` and Fullsend `bdedebeaf`.
Shell entrypoint stdout is forwarded live and retained in the iteration artifact.
Claude completed-message output is rendered even without partial-message events;
partial streams avoid duplicate completed responses. Tool summaries are compact,
with complete tool details available in transcript artifacts. Live stdout/stderr
pass through credential masking before reaching the runner. Historical job logs
are unchanged. Regression checks cover long lines, credentials, completed and
partial responses, and the completion marker. Existing job 3993 transcripts
replayed into 97,108 bytes of readable output.
