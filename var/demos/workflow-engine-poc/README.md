# workflow-engine POC (pi provider)

Phase 1 of the [pi provider workflow-engine POC]
(.ledger/plans/pi-provider-workflow-engine-poc.md): a deterministic workflow
engine registered as a **pi provider** (`workflow-engine/v1`, zero
inference) whose `workflow` tool runs a demo pipeline — ingest, fan-out
child `pi --print` sessions (concurrency 2), aggregate with a completeness
assertion. Children run on the scripted `test-child` provider (Layers 1–3,
fully offline, byte-deterministic) or on real GLM through the Model Relay
(Layer 4).

Contract study: [.ledger/notes/pi-provider-workflow-engine-poc-phase0.md]
(../../../.ledger/notes/pi-provider-workflow-engine-poc-phase0.md).

## Layout

| Path | Purpose |
| --- | --- |
| `workflow-engine/index.js` | The extension: provider + `workflow` tool (thin module dispatcher) |
| `workflow-engine/lib/host.js` | The `wf` API: `agent()` (schema-validated, journaled), `parallel()`, `pipeline()` |
| `workflow-engine/workflows/*.mjs` | Workflow modules — `demo.mjs` (classify) and `org-scan.mjs` (clone → fan-out scan, with cardinality cross-check and per-repo reality check) |
| `test-child/index.js` | Scripted child provider (`test-child/echo`), no inference |
| `relay-models.json` | Layer 4: relay provider for children (`$WORKFLOW_RELAY_KEY` interpolated at request time; key never written to disk) |
| `check.py` | Phase 1 check script: per-run contract assertions + cross-run determinism |
| `Containerfile` | Test container (pi pinned 1.1.0; extension tree copied; build with `--build-arg TREE_HASH=<sha>`) |
| `runs/` | Runtime evidence (gitignored) |

Adding a workflow is dropping a `.mjs` module in `workflows/` — the tool
dispatches `run-<name>` to `workflows/<name>.mjs`, input arrives via
`WORKFLOW_COMMAND` + `WORKFLOW_INPUT` (or `WORKFLOW_ITEMS`), and the module
authors against the `wf` API (`agent`/`parallel`/`pipeline`). No provider
or extension changes; `org-scan.mjs` was added this way and verified both
locally (3/3 repos scanned, 4 usage records, content-addressed journal)
and through fullsend (exit 0, parent $0.0000, 4 child requests folded,
telemetry reporting `gen_ai.system: workflow-engine` with zero tokens).

## Running

```bash
# Layers 1-3: scripted children, offline, 3x determinism (in container)
podman build --build-arg TREE_HASH=$(find workflow-engine test-child \
  relay-models.json -type f | sort | xargs sha256sum | sha256sum | cut -d' ' -f1) \
  -t workflow-engine-poc:v1 -f Containerfile .
podman network create pocnet   # once
podman run --rm --network pocnet -v "$PWD/runs:/workspace/runs:Z" \
  workflow-engine-poc:v1 \
  python3 /opt/poc/check.py --pi pi --ext /opt/poc/workflow-engine \
    --runs 3 --out /workspace/runs/container-check

# Layer 4: real children via relay GLM (cluster must be up)
WORKFLOW_RELAY_KEY=<minted relay client key> podman run --rm \
  --network pocnet --add-host relay-api.local:host-gateway \
  -v <relay-ca.crt>:/etc/relay-ca.crt:ro -e NODE_EXTRA_CA_CERTS=/etc/relay-ca.crt \
  -e WORKFLOW_CHILD_MODEL=relay/rits/zai-org/glm-5-3 \
  -e WORKFLOW_CHILD_MODELS_JSON=/opt/poc/relay-models.json \
  -e WORKFLOW_RELAY_KEY -v "$PWD/runs:/workspace/runs:Z" \
  workflow-engine-poc:v1 \
  python3 /opt/poc/check.py --pi pi --ext /opt/poc/workflow-engine \
    --runs 1 --out /workspace/runs/relay-check \
    --expect-child-model relay/rits/zai-org/glm-5-3
```

Host smoke (isolated from `~/.pi` via a scratch `HOME` per run) works the
same way: `python3 check.py --ext "$PWD/workflow-engine" --runs 3 --out
/tmp/poc-smoke`.

The relay client key is minted per-run from the admin API
(`POST /api/private/v1/projects/vertex-shim-local/credentials` with
`backends: ["anthropic"], catalog_models: true, vertex_catalog_models:
true`); it is passed only as an environment variable and never written into
the repo or the run directories.

## Verified (2026-10-13)

- 3/3 deterministic runs in the container (Layers 1–3): exit 0, the full
  event contract (tool-call turn, tool result, final message, agent_settled),
  zero parent usage, 3 usage-file records, complete artifact, and
  byte-identical normalized event streams across runs (timestamps, session
  ids and the per-run scratch directory masked).
- Layer 4 (relay GLM): pipeline completes with real children; usage records
  carry real token counts (e.g. 1442/77, 418/101 input/output with a cache
  read) that match the relay's own telemetry exactly — the independent
  usage-oracle cross-check from the plan.
- Determinism scope: child outputs are excluded by design for real-model
  runs (`--runs 1`); with scripted children the entire stream, including
  child-derived content, is byte-identical.

## Findings recorded during implementation

- The legacy provider registration requires `baseUrl` and `apiKey` even for
  a fully local provider — placeholders are honest here (no HTTP occurs).
- The stream contract enforces block types in `partial` snapshots: at
  `toolcall_start`, `partial.content[contentIndex]` must already be a
  tool-call block.
- Spawned child `pi --print` processes must get `stdio: ["ignore", ...]` —
  a piped stdin that never closes makes the child block forever.
- Children must not inherit `PI_*` environment variables.
- Podman bridge networks cannot reach the host's LAN IP for the `*.local`
  proxy; `--add-host relay-api.local:host-gateway` is the working wiring.
- pi resolves three-segment model specs (`relay/rits/zai-org/glm-5-3`)
  correctly; `models.json` `apiKey` supports `$ENV` interpolation.

## Phase 2: fullsend integration (local)

Ran `fullsend run --runtime pi` against a local OpenShell gateway with the
podman driver. Setup (all from the checkouts, nothing touching the K3s
cluster):

1. **Gateway**: `cargo build -p openshell-server --release
   --no-default-features --features in-tree-compute-drivers` and
   `cargo build -p openshell-sandbox --release` from `checkouts/openshell`;
   the supervisor goes in a scratch OCI image exposing `/openshell-sandbox`
   (the published `:dev` supervisor image renamed the binary — build from
   the checkout). Gateway config (`/tmp/openshell-gateway-config.toml`):

   ```toml
   [openshell.drivers.podman]
   supervisor_image = "localhost/openshell/supervisor:local"

   [openshell.gateway.gateway_jwt]   # required: mints per-sandbox tokens
   signing_key_path = "..."          # openssl genpkey -algorithm ed25519
   public_key_path = "..."
   kid_path = "..."

   [openshell.gateway.auth]          # local plaintext only
   allow_unauthenticated_users = true
   ```

   Start: `openshell-gateway --disable-tls --drivers podman
   --bind-address 127.0.0.1 --port 18080 --config <toml>`, then
   `openshell gateway add http://127.0.0.1:18080`.
2. **Sandbox image**: `podman build --build-arg PI_VERSION=1.1.0 -t
   fullsend-sandbox-poc:v1 -f images/sandbox/Containerfile images/sandbox/`
   from `checkouts/fullsend-ai/fullsend`.
3. **Harness**: `phase2/.fullsend/` (config.yaml, harness/poc.yaml with
   `model: workflow-engine/v1` + the plugin entry, agents/poc.md with **no
   `tools:` frontmatter** — see finding 1 below, the bundled plugin tree,
   policies/base.yaml) and `phase2/target-repo` as the target.
4. **Run**: `fullsend run poc --runtime pi --fullsend-dir .fullsend
   --target-repo target-repo` with the openshell CLI on PATH.
   `poc-blocked` is the R6 variant (tool-allowlist hook enabled,
   `FULLSEND_TOOL_ALLOWLIST=bash`).

Verified 2026-10-13 (R1–R6; details in the plan): end-to-end run with 3/3
items classified in-sandbox, parent tokens 0 / $0.0000, `per_model_usage`
folding parent + children (the extension appends to
`$PI_CODING_AGENT_DIR/subagents/usage.jsonl`), transcripts/metrics
extracted, and the PreToolUse hook blocking the code-issued `workflow`
call with a recorded security finding. R7 and the stall-watchdog test
remain unexercised.

### Phase 2 findings

1. Extension tools cannot be named in the agent `tools:` frontmatter
   (`piToolsFor` maps only Claude built-ins and drops unknown names from
   `--tools`); omitting `tools:` leaves extension tools active — the
   least-privilege path needs upstream work.
2. The agent prompt is fixed ("Run the agent task"); fullsend agents are
   env-driven — the extension reads `WORKFLOW_ITEMS`.
3. Extension-dispatched children fold into metrics only when the extension
   writes the runner's usage file (validates the plan's Option-B
   "usage accounting at the source").
