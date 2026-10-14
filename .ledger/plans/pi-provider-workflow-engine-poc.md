---
created: 2026-10-13
last_updated: 2026-10-13
category: fullsend
status: plan (not started)
---

# POC Plan: Deterministic Workflow Engine as a Pi Provider Extension

*Goal: prove that a pi extension registered as a **provider** can serve as a
fully deterministic workflow engine inside fullsend's pi runtime — zero
inference in the parent, deterministic phases in code, agents invoked on
demand, and the runner's contracts (events, metrics, hooks, liveness)
satisfied. This is "Tier 2" from the 2026-10-13 analysis: we do not
intercept the agent loop, we **become the model** (`--model
workflow-engine/v1` resolves to our provider's `stream()` implementation).*

*Grounding: fullsend checkout `checkouts/fullsend-ai/fullsend` at
`a734637cdc5736cc454a0b218708001b96e1b3aa` (the originally cited
`6316706f2` does not resolve in the available repos) and installed pi
1.1.0. Phase 0 contract study:
[notes/pi-provider-workflow-engine-poc-phase0.md](../notes/pi-provider-workflow-engine-poc-phase0.md).
ADR 0094 (plugins are runtime-scoped harness resources) is the delivery
mechanism.*

## Why this is possible (the three facts the POC validates)

1. **No provider whitelist**: `translatePiModel` passes any `provider/model`
   spec through untouched; the vertex/xai/openai/gateway branches are
   opt-in. An unknown prefix reaches pi's command line as-is.
2. **Extensions register providers before model selection**: the extension
   factory runs at startup; `--model workflow-engine/v1` resolves to our
   provider because we loaded via `-e` (ADR 0094 `plugins:` entry).
3. **The provider owns the event stream**: we can emit well-formed
   assistant/tool/result events — including keepalive `message_update`
   ticks that feed fullsend's stall watchdog, which counts only normalized
   message events (`pi_progress.go`; `tool_execution_update` is discarded).

## Scope: what the POC demo pipeline is

A minimal but *structurally complete* workflow, not a toy "hello":

- **Phase A — ingest (pure code)**: parse the prompt (or an input manifest
  file), validate schema, write a run state file.
- **Phase B — fan-out agent phase (deterministic code, LLM children)**:
  for each of N (2–3) work items, spawn a child `pi --print` session with a
  small real model doing a trivial judgment task (e.g., classify a
  one-paragraph text into 3 buckets). Concurrency-limited (2). Results
  written to disk as JSON; a code step validates them.
- **Phase C — aggregate + publish (pure code)**: merge child outputs,
  check completeness (every item has exactly one result), write final
  artifact + final assistant message.

This exercises: prompt parsing, deterministic steps, child dispatch,
result validation, completion. Nothing more.

## Architecture components

### 1. The extension (`workflow-engine/`)
- `index.js` entry (directory layout — single-level, no `skills/`/
  `prompts/`/`themes/` dirs, which would flip pi into package layout and
  change the entry point).
- Registers:
  - **Provider** `workflow-engine`, chat model `v1`, cost entries all zero,
    declared `contextWindow`/`maxTokens` (so pi's context accounting has
    numbers).
  - **Tool** `workflow` (TypeBox schema: `{ run: string }` or similar) —
    the only tool the "model" ever calls. Its `execute()` runs the phase
    graph.
  - **(Option B) Localhost agent-gateway server** started at
    `session_start`, closed at `session_shutdown` — see §2.
- Provider `stream()` behavior:
  1. First response: assistant message containing the `workflow` tool call.
  2. After tool result: final assistant message with the artifact summary;
     result carries `usage: { zero }` (honest — no inference).
  3. During long tool execution the *tool* emits keepalives (see below) —
     or, if keepalives must come from the provider stream, the tool and
     provider share a tick channel (extension module state).
- **Keepalive strategy** (explicit design item): the watchdog counts
  normalized message events; a quiet 10m+ phase can trip
  `FULLSEND_STALL_TIMEOUT`. The tool must emit activity — either via the
  provider stream (preferred, we own it) or by structuring phases as
  multiple provider turns. Design must state which and prove it against
  the default 10m stall timeout with a deliberately slow phase (>10m) in
  one test run.

### 2. Child dispatch — three options

The POC's demo pipeline may use any of these; **Option B (agent-gateway
callback) is the preferred end-state** because it is the piece that would
deserve sanctioning as a general "child-call API", and it is what makes
the pattern viable for real meta-harnesses like architecture-context
(`agent_runner` would gain a pi backend as a third harness under its
ADR-0017 selectable-harness design, leaving the claude/codex paths
untouched).

**Option A — own minimal spawner** (simplest; good for Phase 1 smoke):
the workflow tool spawns child `pi --print` sessions itself and writes
usage records conforming to the **usage-file contract**
(`pi_subagents.go`: JSONL, `{seq, usage, model}` per line, byte cap,
read-once suffix). Depends only on public surfaces. Document the exact
format with a fixture.

**Option B — agent-gateway callback** (the neat one):
- The extension starts a **localhost server at `session_start`** (the
  sanctioned pattern for long-lived resources) exposing a dispatch API:
  `POST /agent {agent, input, model?, timeout?}` →
  `{output, usage, exitCode}`.
- The server dispatches child pi sessions using the machinery
  `fullsend-agent.js` already implements and exports
  (`createAgentTool(manifest, {...})`): env hygiene (`childEnv`),
  per-child gateway config copies, hooks adapter in each child's `-e`
  list, usage-file records, slot limits, timeouts, kill grace. Children
  can also be driven as `pi --mode rpc` processes (pi's RPC mode is a
  JSONL protocol with a `prompt` command that expands `/skill:name`),
  but dispatch stays extension-owned either way.
- **The external program calls back into pi**: the workflow tool's
  `execute()` runs the pipeline (any language); the pipeline's agent
  calls become POSTs to the socket instead of SDK-spawned CLIs. While
  the tool runs, server handlers run concurrently in the same Node event
  loop — the same shape as the Agent tool dispatching children while the
  parent waits.
- What this buys over the pipeline spawning pi itself:
  1. **Usage accounting at the source** — children dispatched by the
     extension write usage records the runner folds into `metrics.json`
     automatically (`foldPiSubagentUsage`); no metrics undercount.
  2. **Hooks cover the fan-out** — every child's `-e` list includes the
     hooks adapter, so PreToolUse policy binds all child tool calls.
  3. **Credential/gateway hygiene centralized** — `childEnv` and gateway
     config copies live in one place; the pipeline never touches
     provider credentials.
  4. **Manifest-driven allowlists** — which agents/tools/models may be
     dispatched is enforced by the extension, not trusted from the
     caller. This is mandatory, not optional: in an *agent-led* run the
     model can also reach the localhost socket, so the server must
     enforce the manifest (slots, allowlists) exactly as `createAgentTool`
     does. Bind local-only; treat every caller as untrusted.
- Claude-format artifacts mostly ride along: fullsend already translates
  Claude-style agent markdown (`pi_agent.go`) and skill frontmatter
  (`frontmatter_skills.go`) for pi, so `.claude/skills`-style content
  needs bounded adaptation, not a rewrite.

**Option C — Anthropic-API impersonation** (rejected, documented why):
make the local server impersonate an Anthropic endpoint so existing
`claude-agent-sdk` calls work unchanged via `ANTHROPIC_BASE_URL`.
Rejected because (a) the runner deliberately unsets
`ANTHROPIC_BASE_URL`/`AUTH_TOKEN`/`API_KEY` in the sandbox so "a stray
key cannot redirect traffic" — an impersonated endpoint is
indistinguishable from the attack that guard exists for; and (b) it is
the wrong interface layer: the pipeline needs *agent runs* (prompt +
skills + tools + parsed output), not raw completions. The dispatch shape
(`{agent, input, structured output}`) is the right contract.

### 3. Harness + manifest
- Harness YAML: `model: workflow-engine/v1`, `plugins:` pi-format entry
  pointing at the extension tree, agent definition whose `tools:` admits
  the `workflow` tool.
- **Open question to resolve in Phase 0**: how `--tools` (built from the
  agent definition manifest) interacts with extension-registered tools —
  `piEditRepairEnabled(m.Tools)` suggests gating; verify a declared
  extension's tool is callable when `--tools` is set, and whether the tool
  name must appear in the agent's `tools:` list.
- ADR 0094 constraints to honor: no symlinks anywhere in the tree (hash
  refuses), no reserved extension names, env keys off the reserved
  deny-list, injection-scan clean, name collisions are errors.

## Test infrastructure (containerized, relay-backed)

All implementation testing runs inside a container so the host pi
installation (settings, credentials, sessions, extensions) is never
touched — the dev loop of extension reloads and config changes cannot
affect host sessions. pi documents this pattern (`docs/containerization.md`):
run the whole pi process in a container with a named volume for
`/root/.pi/agent`; **never mount the host's `~/.pi/agent`**.

### Container spec

- Podman (project standard); `node:24-bookworm-slim` base with
  `@earendil-works/pi-coding-agent` installed globally, **pinned to the
  host pi version** (currently 1.1.0) so results transfer to the host
  runtime.
- Extension tree `COPY`ed (or read-only mounted) with its tree hash
  recorded in image labels — the same manifest discipline as the Phase 3
  evidence archive.
- A **dedicated podman network**, not `--network=host`. This is what makes
  the namespace-isolation criteria testable: the gateway's loopback-only
  binding and "socket not reachable outside the sandbox network
  namespace" are probed from a second container on a different network.
- Destructive Layer-3 tests (SIGKILL mid-phase, stall injection,
  orphaned-process checks after exit) become safe to repeat.

### Inference: relay.local with GLM

Real-child runs use the Model Relay's GLM (`rits/zai-org/glm-5-3` on
`enmaas-personal`) through pi's `models.json` compatible-endpoint config —
the relay speaks the Anthropic Messages API, so no child code changes:

```json
{ "providers": { "relay": {
  "baseUrl": "https://relay-api.local",
  "apiKey": "$RELAY_API_KEY",
  "models": [{ "id": "rits/zai-org/glm-5-3", "api": "anthropic-messages",
    "contextWindow": 200000, "maxTokens": 32768,
    "cost": { "input": 0, "output": 0, "cacheRead": 0, "cacheWrite": 0 } }]
} } }
```

- Networking: `--add-host relay-api.local=<proxy-listen-IP>` on the
  dedicated network; the internal CA mounted read-only with
  `NODE_EXTRA_CA_CERTS` (the `*.local` names serve cluster TLS — the same
  CA the emulator curls use).
- Credential: the relay API key is fetched from its k8s secret at runtime
  into an env var — never baked into the image, never committed. Children
  are the only credential holders; the workflow-engine parent needs none.
- GLM keeps the Claude OAuth account out of the test loop entirely (no
  usage-limit 429s mid-suite, no spend against managed accounts).
- **Independent usage oracle**: relay telemetry records every child request
  (model, account, usage), so Layer-4 metrics assertions (`per_model_usage`
  sums to totals, children folded, parent zero) are cross-checked against
  a source that shares no code with pi's usage-file machinery — the same
  two-source discipline as the benchmark's relay/API-dump reconciliation.

Known caveats (from the 2026-10-12 GLM validation; none blocking): the
relay's `msg_`-only telemetry filter drops EnMaaS `chatcmpl-*` IDs, so
usage joins use time/account scope rather than message IDs; one incomplete
stream and one cancellation occurred in ~143 requests with a clean
non-stream fallback (pi's retry stack absorbs this class — expect
occasional child flake, not suite failure); GLM cache writes are 5-minute
only.

### Test layers

| Layer | Children | Network | What it proves |
| --- | --- | --- | --- |
| 0 | none — pure unit tests of the phase graph | none | schema rejection, state transitions, completeness assertion, partial-failure aggregation |
| 1 | scripted `test-child` provider | none | **byte-identical determinism including child outputs**; the provider stream contract (one `start` before content, balanced events, valid parsed tool args by `toolcall_end`, exactly one terminal `done`/`error`, zeroed usage honestly reported); instrumentation hooks (`onPayload`/`onResponse`/`onProviderStreamEvent`) fire |
| 2 | stub | none | tool + gateway contracts: manifest allowlist refusal, slot limits, usage-file invariants, loopback binding, `session_start`/`session_shutdown` lifecycle, malformed-POST fuzzing |
| 3 | stub, fault-injected | none | child crash/timeout/malformed output; **omission injection** (a stub child drops an item; the completeness assertion must fail the run loudly — the S1 `recorded`-JSON precedent makes this test mandatory, not optional); SIGTERM mid-phase with durable-state resume; keepalive vs stall watchdog |
| 4 | relay GLM | relay.local | real usage numbers; folding cross-checked against relay telemetry |

The scripted-child trick is the core of the determinism claim: Layers 1–3
run fully offline with zero inference, so the 3× repeat check is
byte-identical *including* child outputs, and the same suite moves to real
children by swapping one `models.json` entry. Layers 1–3 ship as a
repeatable check script (pass/fail summary over persisted artifacts —
JSONL event logs, usage files, metrics), never as one-off demonstrations;
assertions subscribe to the pi SDK event stream
(`session.prompt()` + event subscription) rather than eyeballing consoles.
Raw provider events are captured for diffing using the
`debug-provider.ts` pattern. The pi provider tests under
`packages/ai/test` are adapted for the stream-contract suite rather than
reinvented.

## Phased plan

### Phase 0 — Contract study (no runs)
Deliverable: short notes file with copies/excerpts of:
- One real provider implementation (vendored vertex extension or the
  `@earendil-works/pi-ai` Provider interface) — exact `stream()` event
  shapes pi normalizes for `--mode json`.
- fullsend's event parser expectations (`pi_progress.go` mappings) and
  `agent_end` ResultEvent fields consumed for metrics.
- The usage-file format + `foldPiSubagentUsage` invariants
  (`per_model_usage` must sum to totals).
- Harness/plugin validation path (`plugin_spec.go`, injection scan) to
  pre-clear the extension tree.
- If Option B: pi's RPC mode and command set (`rpc-commands.md` — the
  `prompt` command, `/skill:name` expansion) plus the internals of
  `createAgentTool`'s dispatch (child env, gateway config copy, usage
  record, slot management), since the gateway wraps them.
- The test container (Containerfile, pinned pi version, dedicated network,
  second-network probe) and the relay `models.json` wiring: verify the
  relay's Anthropic-Messages surface serves `rits/zai-org/glm-5-3` to a
  plain pi child before relying on it in Layer 4.
Exit criteria: written event-shape contract + usage-file fixture (+
gateway API sketch if Option B).

### Phase 1 — Standalone pi (no fullsend)
`pi --print --mode json -e ./workflow-engine --model workflow-engine/v1
"<prompt>"` — run inside the test container (§ Test infrastructure), first
with the scripted `test-child` provider (Layers 1–3), then one pass with
real children via relay GLM (Layer 4).
- Demo pipeline runs end to end; child pi sessions use the scripted child
  first, then `relay/rits-zai-org-glm-5-3` for the real-model pass.
- Verify: exit 0; event stream parses; `--mode json` output contains the
  tool call, tool result, final message; zero parent usage; children
  recorded.
- **Determinism assertion**: run 3× — the sequence of provider-emitted
  events (tool call, phases, final message) must be byte-identical modulo
  child outputs and timestamps. This is the core claim; make it a check
  script, not an eyeball.
- If Option B: demo the callback path — the demo pipeline's agent phase
  POSTs to the gateway instead of the tool dispatching children inline;
  verify usage records still land in the usage file and an unauthorized
  dispatch (agent not in the manifest) is refused.
Exit criteria: 3/3 deterministic runs + check script green.

**Status 2026-10-13: MET.** Implementation at
`var/demos/workflow-engine-poc` (README documents layout, runs and
findings). Container runs (podman, pi 1.1.0, dedicated network):
3/3 deterministic scripted-child runs, check script green — exit 0, full
event contract, zero parent usage, 3 usage-file records per run, complete
artifacts, byte-identical normalized event streams. Layer 4 relay-GLM pass
also green: real children via a minted relay client key
(`backends: ["anthropic"], catalog_models, vertex_catalog_models`), real
token usage in the records matching relay telemetry exactly. Option A
(own spawner) used for Phase 1; the Option B gateway remains future work.

### Phase 2 — fullsend integration (the part that makes it a POC)
Harness with `plugins:` + `model: workflow-engine/v1`; run via
`fullsend run` in a sandbox. This phase exists because "locally validated
only" is exactly the gap that got #83 tagged.
Checks (each is a numbered research question with pass/fail):
- **R1** launch: unknown provider prefix passes through; no bootstrap-time
  model validation rejects it.
- **R2** plugin path: Bootstrap uploads the tree, guards pass (exit-96
  tamper check absent), injection scan clean.
- **R3** progress/liveness: renderer and stall watchdog behave; the
  keepalive design from §1 survives a deliberately slow (>10m) phase.
- **R4** metrics: `metrics.json` parent usage = 0; children folded and
  `per_model_usage` sums correctly.
- **R5** completion: run recorded as success; transcripts and output
  files extracted; exit code correct.
- **R6** hooks: the hook adapter's PreToolUse sees the `workflow` tool
  call (verify with a manifest hooks group that requires approval /
  blocks a named tool — confirm runner policy still binds the
  "model-issued" call).
- **R7** (stretch) retry/feedback: force a validation failure once;
  confirm re-entry with the injected prompt resumes from durable state.
Exit criteria: R1–R6 pass with archived run logs; R7 attempted, result
recorded either way.

**Status 2026-10-13: R1–R6 PASS; R7 not attempted.** Ran on a local
OpenShell gateway (podman driver, plaintext, gateway-minted sandbox JWTs)
with the fullsend CLI from `checkouts/fullsend-ai/fullsend` and a sandbox
image built with `PI_VERSION=1.1.0`. Harness under
`var/demos/workflow-engine-poc/phase2`. Results:
- R1 ✓ `workflow-engine/v1` passed translatePiModel and every bootstrap
  check; the run executed with the virtual provider as the agent model.
- R2 ✓ plugin uploaded and loaded (`extension tool: workflow`); guards and
  the pre-agent scan passed.
- R3 ✓ (observed scope) live progress and TOKENS events; no stall. The
  >10 m slow-phase/watchdog test remains unexercised (watchdog source
  still unresolved — Phase 0 caveat).
- R4 ✓ parent usage 0, cost $0.0000; children folded into
  `per_model_usage` once the extension appends to
  `$PI_CODING_AGENT_DIR/subagents/usage.jsonl` (the usage-file contract);
  breakdown sums to totals.
- R5 ✓ exit 0, result stop, transcripts and metrics extracted.
- R6 ✓ the PreToolUse tool-allowlist hook **blocked the code-issued
  workflow call** (`Tool 'workflow' is NOT in the allowlist`), recorded as
  a `hook_pretool` security finding — runner policy binds tool calls
  issued by a deterministic provider.

Phase 2 findings (what the integration surfaced):
1. **Extension tools cannot be named in the agent `tools:` frontmatter** —
   `piToolsFor` maps only Claude built-in names and drops unknown names
   from the `--tools` allowlist (verified with the `poc-narrow` variant:
   `tools: Read, Workflow` → warning + "Tool workflow not found").
   **This affects only the declared tool set, not enforcement**: the stock
   tool-allowlist PreToolUse hook enforces arbitrary lists including
   extension tools at call time, with no fullsend changes. Verified in
   both directions — `poc-blocked` (allowlist `bash`: the code-issued
   workflow call is blocked, finding recorded) and `poc-locked`
   (allowlist `workflow`: only the extension tool is permitted; the run
   completes 3/3 at $0.0000, and bash/read/etc. would be blocked).
   Least-privilege *enforcement* is therefore available today; the
   frontmatter gap means only that the system prompt still *declares*
   tools the hook would block — irrelevant for a deterministic provider,
   which never reads declarations. An upstream pass-through would still
   be nice for LLM agents that name extension tools.
2. **The agent prompt is fixed** (`Run the agent task`); fullsend agents
   are env-driven. The extension now reads `WORKFLOW_ITEMS` from the
   environment (prompt parsing retained for Phase 1).
3. **Usage accounting for extension-dispatched children requires writing
   to the runner's usage file** — validating the plan's Option-B "usage
   accounting at the source" design point.
4. Local-gateway bring-up notes (supervisor image naming drift between the
   published `:dev` image and this checkout's driver; sandbox JWT config
   required; `allow_unauthenticated_users` for plaintext local use) are in
   the POC README.

### Phase 3 — Mini reliability + evidence
- 5 consecutive sandbox runs (pass^5 on the demo pipeline).
- Evidence archive (lessons applied from the benchmark campaign):
  - pinned versions: fullsend sha, pi binary version, extension tree hash;
  - per-run manifests, event logs, metrics.json, artifacts;
  - a "Not exercised" section (what this POC does NOT show — production
    readiness, ten-RFE scale, Claude runtime, general pipelines);
  - a one-page report: what worked, what needed conventions, what would
    need sanctioning (completion/usage contract for script-led parents).
Exit criteria: report + archive committed.

## Success criteria (measurable)

1. Zero parent inference tokens across all runs (metrics + provider
   accounting agree).
2. Provider-emitted event sequence deterministic across repeats (check
   script).
3. Delivery check: every work item has exactly one validated child result
   in the final artifact (completeness assertion, no echo reliance —
   children write to disk; code validates).
4. R1–R6 green in the sandbox; archived.
5. Stall watchdog: no false "wedged" kill during the slow-phase test.
6. (Option B) Gateway: authorized dispatch succeeds with usage recorded;
  unauthorized dispatch (agent not in manifest) refused; socket not
  reachable outside the sandbox network namespace.

## Cost & effort estimate

- Parent inference: $0 (that's the point).
- Children: relay GLM (`enmaas-personal`) — no Claude-account spend; GLM
  billing rates are unverified (2026-10-12 validation made no price
  claim), so treat child cost as "small but unquoted" and read actual
  usage from relay telemetry after the first run.
- Effort: Phase 0 ~half day; Phase 1 ~1–2 days; Phase 2 ~1–2 days
  (sandbox/tooling friction is the unknown); Phase 3 ~half day.

## Risks / open questions

| # | Risk | Mitigation |
|---|---|---|
| 1 | pi provider `stream()` contract subtler than docs imply (event shapes, error paths) | Phase 0 copies a working provider; earliest possible smoke in Phase 1 |
| 2 | `--tools` allowlist from the agent manifest may hide extension tools | **Resolved in Phase 0**: extension tools are dropped unless named in `--tools`; the `workflow` tool must appear in the agent definition's `tools:` list |
| 3 | Keepalive strategy wrong → stall kill | Test deliberately with >10m phase; fallback: multiple provider turns per phase boundary. **Phase 0 caveat:** `FULLSEND_STALL_TIMEOUT` and the 10-minute watchdog are not present in the available fullsend/breadboard trees — verify the watchdog exists (and its counting rule) before designing keepalives around it; `tool_execution_update` (partialResult) is wire-supported but discarded by fullsend's parser |
| 4 | Importing `createAgentTool` fights the hash guard | Option A: own spawner. Option B: the gateway *wraps* the dispatch patterns rather than importing runner-owned files from the sandbox — reimplement the ~4 concerns (env, gateway copy, usage record, slots) against documented behavior |
| 4b | Gateway socket reachable by the model in agent-led runs | Mandatory manifest enforcement (allowlists, slots) in the server; bind local-only; test the refusal path explicitly (Phase 1) |
| 4c | pi RPC mode subtleties (framing, disposition semantics) if children are RPC-driven | Phase 0 studies `rpc-commands.md`; subprocess `--print` dispatch remains the fallback |
| 5 | Bootstrap/harness validation rejects unknown model spec somewhere unexplored | R1 is explicitly a research question; if blocked, model aliases may provide a route |
| 6 | Usage honesty ambiguity (parent "model" costs $0) | Report zero; document convention; this ambiguity is itself a POC *finding* for what needs sanctioning |
| 7 | Relay GLM flake in Layer 4 (one incomplete stream + one cancel in ~143 requests during validation) | pi's retry stack absorbs the class; scripted-child Layers 1–3 are unaffected; suite treats a single child retry as pass, repeated failure as investigate |
| 8 | Test container drifts from host pi runtime | Pin the image to the host pi version (1.1.0) and record the extension tree hash in image labels; re-pin deliberately, not implicitly |

## Explicit non-goals

- Not production readiness; not the strat-creator or architecture-context
  migration; not the Claude Code runtime; not performance tuning; not an
  argument in the ADR-0133/#8225 thread (evidence standards from that
  campaign are borrowed, position fights are not).
