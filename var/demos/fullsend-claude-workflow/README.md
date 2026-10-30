# Claude Workflow through Fullsend and OpenShell

This fixture copies GitLab.local `strat-pipeline` branch
`feat/fullsend-agent-led-poc` at `89c879b` into
`feat/fullsend-claude-workflow`. The two successful POC branches and main
are preserved. No custom Fullsend entrypoint is used.

The job checks out PR 85's tested `feat/s1-workflow-hardening` source at
`6ed858b2294a29457153a90f187a801022c21e8b`. Its native `strat-single` or
`strat-batch` agent launches `strat-pipeline:strat-pipeline`. Workflow code,
prompts, plugin hooks, host preparation, validation, publication and owned
lock cleanup come from that pin.

The architecture snapshot uses the benchmark's exact commit
`7d61f097a9220aeb1280837b66b532177ec558b6`: release `rhoai-3.6-ea.2` plus
overlays. The adapter builds this subset before preparation and retains its
source receipt. This avoids broken sibling aliases in the default cone sparse
checkout while preserving the candidate's strict freshness checks.

The default is **claude-opus-4-6, high effort, concurrency ten** for the
primary agent, subagents and model aliases. The user selected Opus for this
exercise. There is one validation iteration and no automatic paid retry.
Changing defaults does not itself authorize a strategy run.

## Runtime and secrets

Released Fullsend 0.47.1 is verified against its published tarball checksum.
A job-local derived image installs the qualified Claude Code 2.1.296 and
the candidate’s locked Python helper dependencies on the pinned sandbox
base, then adds the public local CA. Source and image identities are retained
in job artifacts. A trusted observer in the job-owned container engine attaches
strace to agent processes; it preserves OpenShell's process restrictions.
Attachment is sampled, so initial syscalls before attachment can be missed.

Inference uses `https://relay-api.local/v1/messages`. The relay project
`vertex-shim-local` selects its configured upstream account; clients receive
no upstream Google or EnMaaS credential. A relay-issued, Opus-only client key
is stored in the masked `MODEL_RELAY_API_KEY` GitLab variable, scoped to the
`fullsend-claude-workflow` environment. `provision.py` reads the existing
relay administration Secret in memory, and never prints a secret value.
The key expires after 90 days; rotate it through the relay before expiry.

OpenShell holds the relay key and Jira token as provider credentials. The
agent receives placeholders. Profiles allow only exact local endpoint hosts
and the required HTTP methods/paths. Direct model endpoints and relay
administration are excluded. Results and Org Pulse credentials stay on the
runner. Existing shared project variables and old branch configuration remain.

## Setup and model-free checks

Run from Breadboard, supplying the current local CA path. Emulator admin
authentication can be supplied through `GITLAB_ADMIN_USER` and
`GITLAB_ADMIN_PASSWORD`; the local synthetic defaults are admin/admin.

```sh
export GITLAB_CA_FILE=/path/to/current-local-ca.crt
uv run --with httpx python var/demos/fullsend-claude-workflow/provision.py
uv run --with httpx python var/demos/fullsend-claude-workflow/publish.py --publish
uv run --with httpx python var/demos/fullsend-claude-workflow/publish.py --preflight
```

Publication creates no pipeline. The preflight starts only
`workflow-preflight`: real OpenShell provider registration, sandbox creation,
Claude version/dependency checks, authorized model discovery, Jira identity
GET and blocked-host checks. It does not invoke a model, acquire tickets or
change Jira records. Pushes and unsolicited scheduled runs are disabled.

```sh
WORKFLOW_TEST_FULLSEND=/path/to/verified/fullsend uv run --offline --no-project \
  --with pytest --with pyyaml --with httpx python -m pytest -q \
  var/demos/fullsend-claude-workflow/test_ci.py
```

After a passing preflight, an explicitly authorized single-ticket smoke uses
the new branch with `STRATEGY_MODE=strat-single` and `RFE_KEY=RHAIRFE-N`.
A later authorized batch uses `STRATEGY_MODE=strat-batch`, `BATCH_SIZE`,
`BATCH_OFFSET` and optional exact `BATCH_EXPECTED_KEYS`. The original host
pre-script discovers, selects and claims tickets. The Workflow consumes its
prepared input. Both modes share the original batch resource lock.

## Evidence

Always-retained job artifacts contain source/runtime pins, generated harness
configuration (host variable references only), native Fullsend output,
validation results, host run records, sandbox workspace and Claude sessions,
raw API bodies, syscall traces and gateway/capture/cleanup logs. The sandbox
is retained only until collection, then job-owned containers and gateway
state are destroyed. Live output and uploaded artifacts are redacted.

Raw API capture still needs confirmation during the first inference smoke;
model-free preflight cannot produce API response bodies. Preserve failures
as failures. Archive every diagnostic and strategy run privately under
`var/run-data`; never publish raw run artifacts in the results repository.

For a terminal pipeline, save and independently verify its evidence:

```sh
uv run --with httpx python var/demos/fullsend-claude-workflow/archive.py --pipeline PIPELINE_ID
uv run --with httpx python var/demos/fullsend-claude-workflow/archive.py --verify /path/to/capture
```

The collector saves GitLab artifacts and traces, readable Jira state, online
SQLite backups for Jira/MLflow/Observatory/GitLab, service logs and paginated
relay request events. Each capture has its own manifest and checksums.
It also saves dashboard trigger metadata and downstream job evidence, the
capture-time results branch head, and any receipts supplied with `--context`.
Wait for downstream builds before final collection. Missing required native
artifacts make the capture incomplete. Symlinks are retained as metadata,
without following targets, across both host and downloaded evidence.

Implementation decisions and acceptance evidence are recorded in
[the ledger task](../../../.ledger/tasks/done/fullsend-claude-workflow-relay-copy.md).

Model-free acceptance: GitLab pipeline 2095/job 4059 passed on branch head
`7b93d35a`, including Opus discovery, secret placeholders, strict TLS,
blocked direct endpoints, actual syscall capture and cleanup. Its 115-file
private archive verifies. That setup sent zero inference requests and made no
Jira mutations; actual Workflow execution is qualified separately below.

The first authorized smoke seeded only RHAIRFE-19. Bootstrap attempts
2096/4060 and 2097/4062 stopped before inference; the latter released its
owned claim but lost local artifacts to the original redactor. Available
traces and shared-service data are retained with that gap documented. After
18 model-free checks, the adapter corrections were published at `f7567865`.
2098 exposed CA export ordering, corrected before the pinned-context fetch.
2099 reached native Claude but its compiled `claude.exe` identity was excluded
from the relay executable policy: zero tokens, no relay requests, clean claim
release and capture. Its complete native archive verifies (11 API files and
139 syscall traces). Add the exact observed executable path to the relay
profile. All 19 model-free checks pass; corrected adapter `fdc770c1` is running
as 2100/4068 with the same ticket. It invoked the native Workflow at 02:14:05
UTC on 2026-10-19. First Opus 4.6 requests returned HTTP 200 through
`vertex-shim-local` / `vertex-strat-evals`; real API and syscall capture are
active. The job then **passed in 26m05s**: RHAIRFE-19 → RHAISTRAT-16, approve,
all four role reports and native business validation, report publication,
downstream dashboard 2101 and owned-lock/gateway cleanup. Its complete private
archive and separate checksum verification pass (5,535 files / 910.12 MB).
No paid retry was needed. Two portable source fixes remain: safe default context
fetching and host preflight placement; local integration settings stay here.
See [the integration smoke task](../../../.ledger/tasks/done/fullsend-claude-workflow-opus-single-smoke.md)
for current status and final evidence.
