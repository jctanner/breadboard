# Phase 0 contract study: pi provider workflow-engine POC

Written 2026-10-13 for [pi-provider-workflow-engine-poc](../plans/pi-provider-workflow-engine-poc.md).
Read-only study; no runs. Sources are quoted with file and version so Phase 1
can re-verify each claim mechanically.

**Grounding correction:** the plan cites fullsend checkout `6316706f2`; that
object does not resolve in the available repos. The study was done against
`checkouts/fullsend-ai/fullsend` at `a734637cdc5736cc454a0b218708001b96e1b3aa`
(merge of #7383). The installed pi is **1.1.0**
(`~/.pi/agent/install/releases/1.1.0`, `pi --version` → 1.1.0). Re-pin the
plan's grounding to these values.

## 1. pi provider/stream contract (what `workflow-engine/v1` must emit)

### Event protocol (pi-ai `AssistantMessageEvent`, dist/types.d.ts, 1.1.0)

```typescript
{ type: "start"; partial: AssistantMessage }
| { type: "text_start" | "text_delta" | "text_end"; contentIndex; delta?; content?; partial }
| { type: "thinking_start" | "thinking_delta" | "thinking_end"; contentIndex; delta?; content?; partial }
| { type: "toolcall_start" | "toolcall_delta"; contentIndex; delta?; partial }
| { type: "toolcall_end"; contentIndex; toolCall: ToolCall; partial }
| { type: "done"; reason: "stop"|"length"|"toolUse"|"deferred"; message: AssistantMessage }
| { type: "error"; reason: "aborted"|"error"; error: AssistantMessage }
```

Rules (docs/custom-provider.md, "Implement custom streaming"):
- emit one `start` before content events; updates and `done` never before it;
- a stream may terminate directly with `error` when setup fails before `start`;
- **exactly one terminal `done` or `error`**;
- tool-call arguments must contain valid parsed input by `toolcall_end`;
- cancellation converts to an `aborted` result with `errorMessage`;
- successful messages need accurate input/output/cache/total-token and cost
  values (our provider reports zeros — honestly);
- honor instrumentation hooks (`options.onPayload`, `options.onResponse`,
  `options.onProviderStreamEvent`) or the provider behaves differently from
  built-ins (testable with a wrapping observer extension).

`Provider` implements `stream(model, context, options)` /
`streamSimple(...)` returning this event stream (`ProviderStreams`,
types.d.ts:204-212). `TranscriptContext` carries messages; system prompts and
tool declarations live in transcript system messages — read them with
`getCurrentSystemPrompt` / `getCurrentTools`, not `context.systemPrompt`.
Extensions register providers via `pi.registerProvider()` **in the (possibly
async) factory, before startup model selection** — validating plan fact 2.

Model declaration needs: id, name, input capabilities, `cost`
({input, output, cacheRead, cacheWrite} — zeros), `contextWindow`,
`maxTokens`, reasoning support (docs/custom-provider.md "Supply and refresh
models").

### `--mode json` wire format (docs/json.md, 1.1.0) vs fullsend's parser

fullsend's parser (below) was written against pi 0.84.2 and re-checked at
0.85.0; the 1.1.0 format is **compatible** with what it reads, with
additions it ignores:

- Session header `{type:"session", version:3, id, timestamp, cwd}` — no model.
- `message_update` is delta-only; `message_end.message` is authoritative.
  Nested `assistantMessageEvent` types: `start`, `text_*`, `thinking_*`,
  `toolcall_*`, `done`, `error`.
- `tool_execution_start {toolCallId, toolName, args}`;
  `tool_execution_update {…, partialResult}`; `tool_execution_end
  {toolCallId, toolName, result, isError, durationMs}` (durationMs new).
- `agent_end {messages, willRetry}`; `agent_settled {aborted}` (aborted new);
  `auto_retry_start/end`; compaction events now carry `reason`/`result`;
  queue events (`queue_update`, `entry_appended`, `session_info_changed`,
  `thinking_level_changed`).
- `tool_execution_update` exists on the wire — a tool can push partial
  results. fullsend discards it (see §2), but pi's own loop sees it.

## 2. fullsend's event-parser expectations (pi_progress.go)

Mappings (normalized AgentEvent ← pi event):

| pi event | fullsend AgentEvent |
| --- | --- |
| `message_update` → `text_delta`/`thinking_delta` | TextEvent / ThinkingEvent |
| `message_end` (assistant) | InitEvent{Model} on first, TokensEvent, ErrorEvent if stopReason error/aborted |
| `tool_execution_start` | ToolUseEvent summary from args (held until end) |
| `tool_execution_end` | ToolUseEvent (+result text on isError) |
| `auto_retry_start` | RetryEvent |
| `agent_end`/`agent_settled`/`compaction_*` | result-state machine |
| `turn_start/end`, `tool_execution_update`, `queue_update`, `auto_retry_end` | **no mapping — discarded** |

Facts that shape the provider design:

- **InitEvent.Model comes from the first assistant message's `model` field** —
  our provider's assistant messages will name `workflow-engine/v1`, so the
  runner's init shows it.
- StopReason union: `pending|stop|length|toolUse|error|aborted|deferred`;
  only `error`/`aborted` are errors; `length` deliberately is not.
- **`--mode json` exits 0 on model error** — error detection is from the
  stream, not the exit code. The parser fails closed on streams with no
  recognized terminal event.
- `agent_end.willRetry=false` is *not* terminal (compaction retry, queued
  follow-ups can continue); `agent_settled` is the end-of-prompt marker; the
  ResultEvent is emitted once at EOF.
- Extension-tool progress summaries take the **first string-valued arg among
  `path, file, pattern, query, command`** — name the `workflow` tool's
  argument accordingly (e.g. `run` is invisible; `query` or `command` shows).
- Metrics consumed from ResultEvent: NumTurns, TotalCostUSD, IsError,
  ErrorMessage, Subtype, Input/Output/Reasoning/CacheWrite/CacheRead tokens.

**Stall watchdog — open item.** `FULLSEND_STALL_TIMEOUT` and the 10-minute
watchdog do **not** exist in the fullsend checkout or the breadboard deploy
tree; only the "tool_execution_update is discarded" half of the plan's claim
is verified (unmapped list above). Resolve in Phase 2 empirically (R3) or
find the platform-side source. Keepalive options either way: tool
`partialResult` events (wire-supported), or `agent_before_settle`
continuation turns (see §6).

## 3. Usage-file contract (pi_subagents.go)

Line shape written by the extension (one JSON object per child):

```json
{"seq": 1, "model": "relay/rits-zai-org-glm-5-3",
 "usage": {"input": 120, "output": 80, "cacheRead": 0, "cacheWrite": 0, "cost": 0.001}}
```

- **`seq` AND `usage` are both required** (two-pass probe); a line missing
  either is skipped and counted, never folded. `model` optional; empty →
  `unknown` bucket. Extra fields (description, stopReason, durationMs)
  ignored by the runner.
- File capped at **1 MiB** (~4k records) on read; read is **rename-then-
  print** to `<file>.read` — fold is idempotent per iteration (a retry
  cannot double-count).
- Values clamped at zero (an agent-writable file must not be able to
  subtract from audited totals); NaN/Inf costs clamped.
- Fold invariants: the **parent entry is added on every fold** (dispatching
  or not) under the parent model spec; `per_model_usage` must sum to the
  run totals over exactly five fields — input, output, cache-creation,
  cache-read, cost. Reasoning tokens are run-level only (not in the
  breakdown).
- The runner reads the file via an in-sandbox shell command after the
  iteration; a missing file is the ordinary no-children case.

## 4. Harness/plugin validation (plugin_spec.go, pluginformat)

- `plugins:` entry: string path, or `{path, env, pi: {args}}`. `npm:`/
  `git:`/`ssh:` sources rejected (no network fetch at startup). No path
  traversal; basename must match `[a-zA-Z0-9_-]+`; duplicate paths and
  duplicate basenames are errors (sandbox upload replaces wholesale).
- Format detection requires **exactly one runtime** to claim the directory:
  pi loads `index.js/index.ts/index.mjs/index.cjs` or `package.json`
  `"pi.extensions"`/`"main"` from it; a Claude plugin is a `plugin.json`
  bundle. A directory neither runtime loads fails validation up front.
- Reserved sandbox names (rename required):
  `fullsend-hooks`, `fullsend-agent`, `fullsend-edit-repair`,
  `anthropic-vertex`, `xai-vertex`. (`workflow-engine` is safe.)
- **Plugin env deny-list** (keys must match `^[A-Z_][A-Z0-9_]*$`):
  - exact: PATH, HOME, TMPDIR, ENV, BASH_ENV, SHELL, IFS, CDPATH,
    PROMPT_COMMAND, HOSTALIASES, OPENSSL_CONF, SSLKEYLOGFILE,
    REQUESTS_CA_BUNDLE, CURL_CA_BUNDLE, JAVA_TOOL_OPTIONS, RUBYOPT, PERL5OPT,
    GOPROXY, GOFLAGS, CLOUD_ML_REGION;
  - prefixes: `LD_`, `DYLD_`, `PYTHON`, `NODE_`, `SSL_`, `JITI_`, `PI_`,
    `FULLSEND_`, `TIRITH_`, `GOOGLE_`, `GCLOUD_`, `CLOUDSDK_`, `GIT_`,
    `ANTHROPIC_`, `XAI_`, `OPENAI_`, `AZURE_`, `AWS_`;
  - suffixes: `_PROXY`, `_API_KEY`, `_TOKEN`; and any `_SECRET` substring.
  **Design consequence:** the relay credential env var cannot be
  `RELAY_API_KEY` — use e.g. `WORKFLOW_RELAY_KEY` (also avoids `PI_*`/
  `FULLSEND_*`). Env values must not contain newlines/NUL.
- `pi.args` accepts only flags the extension registered
  (`pi.registerFlag`); pi's own options are rejected.
- Injection scan (LLMGuard): ML prompt-injection scanner ships only in the
  runner image; sole call site is `fullsend scan input` (not the plugin
  path). The plugin tree additionally passes `pluginformat.Detect` +
  tree checks (no symlinks; regular files).
- Exit-code guards to expect in-sandbox: 94 (agent extension tampered),
  95 (manifest tampered), 97 (hooks extension missing), 98 (config-dir
  tampered). Extension preflight hashes the host tree and re-verifies the
  sandbox copy before every dispatch.

## 5. Option B internals (fullsend-agent.js, and Risk 2 resolved)

`createAgentTool(manifest, {spawn, log, now, env, killGraceMs,
manifestPath, manifestSum})`:

- Concurrency: `maxConcurrent` from the manifest (default
  `DEFAULT_MAX_CONCURRENT`); waiters queue behind slots. Timeout:
  `timeoutSeconds` → ms. Stop sequence: **SIGTERM, escalate to SIGKILL after
  `killGraceMs` (default 3000 ms)**; children are *not* detached (a killed
  parent must not leave children spending tokens).
- `childArgs`: `--print --mode json --no-approve --no-extensions
  --no-prompt-templates --no-themes --session-dir <sessionsDir>/<prefix>-<seq>`,
  `-e` per manifest extension (hooks adapter in every child's `-e` list),
  `--tools <joined>` (or `--no-builtin-tools` when the allowlist is empty),
  `--model <spec>`, `--thinking <level>`, `--append-system-prompt
  CHILD_SYSTEM_NOTE` (replaces the parent's orchestrator persona).
- `childEnv(base, modelSpec)`: per-provider hygiene — anthropic-vertex
  children get ANTHROPIC_API_KEY/AUTH_TOKEN/BASE_URL/VERTEX_BASE_URL
  deleted and GOOGLE_CLOUD_PROJECT pinned; xai-vertex children get
  XAI_API_KEY deleted. A relay/GLM child needs no scrub rules (no built-in
  provider matches), but the same pattern applies if one ever does.
- Usage records appended per child (§3 shape) via `recordUsage`;
  integrity re-check before every dispatch (manifest sum + per-extension
  sha256 digests; "changed since load; refusing to dispatch").
- **Risk 2 resolved:** `--tools` is a comma-separated allowlist of tool
  names/patterns; extension tools are dropped unless named (measured by
  fullsend at 0.85.0, confirmed by `pi --help` at 1.1.0: "Only +name/-name
  entries add to or remove from the defaults"). **The `workflow` tool must
  appear in the agent definition's `tools:` list**, which the runner turns
  into `--tools`. Bare `--tools workflow,bash,read,edit,write` enables
  exactly those.
- pi RPC mode (docs/rpc-commands.md): bidirectional JSONL;
  `{"type":"prompt","message":…}` (with `streamingBehavior:"steer"` to
  queue during streaming); `/skill:name` expansion in prompts;
  `get_state` for session id. Usable for extension-driven children;
  `--print` subprocess dispatch remains the fallback.

## 6. Extension API surfaces used (docs/extensions.md, 1.1.0)

- Factory: sync or async; pi waits for it before startup (providers
  available to model selection). **Do not start sockets/watchers/timers in
  the factory** — start long-lived resources at `session_start`, close them
  from an idempotent `session_shutdown`. (Directly sanctions the Option B
  gateway lifecycle.)
- `pi.registerTool()` with `exposure` (default `direct` = declared to the
  model and callable); `annotations` (readOnlyHint/destructiveHint/…) are
  what permission extensions read — relevant to R6.
- Events: `tool_call` can mutate input or **block** execution (hooks bind
  tool calls regardless of who issued them — R6's premise);
  `provider_stream_event` fires per parsed provider event (the
  `debug-provider.ts` capture pattern); `message_end` can replace a
  finalized message; **`agent_before_settle` is the final actionable
  boundary** — it can append entries and request one continuation, which is
  the provider-turn-per-phase keepalive fallback; `agent_settled` is
  notification-only.
- Tool calls from one assistant message run in parallel; use `ctx.signal`
  for nested work owned by an active turn.

## 7. Plan-fact verification summary

| Plan fact | Status |
| --- | --- |
| 1. No provider whitelist — `provider/id` passes `translatePiModel` untouched | ✅ verified (pi_run.go:174-199: `if strings.Contains(model, "/") { return model }`; provider prefixes case-insensitive; bare ids get the default provider prefix) |
| 2. Extensions register providers before model selection | ✅ verified (async factory awaited before startup; registerProvider in factory) |
| 3. Provider owns the event stream incl. keepalives feeding a stall watchdog | ⚠️ **partial**: the provider-owns-the-stream half is verified; the watchdog (`FULLSEND_STALL_TIMEOUT`, 10 m default) is **not found** in either available tree — treat R3's premise as unverified until Phase 2 or a platform source is found |

## 8. Relay/GLM wiring (Phase 1 verification item)

models.json entry per the plan (§ Test infrastructure). Phase 0 additions:
the credential env name must dodge the plugin env deny-list
(`WORKFLOW_RELAY_KEY`, not `RELAY_API_KEY`); GLM model spec on the wire is
`rits/zai-org/glm-5-3` (validated 2026-10-12 through the relay's
Anthropic-Messages surface). The live "relay serves GLM to a plain pi
child" check is a run — deferred to the start of Phase 1 per this phase's
no-runs rule.

## Exit criteria assessment

- Written event-shape contract: §1 (provider events + json wire format). ✅
- Usage-file fixture: §3 (record shape, invariants, example line). ✅
- Gateway API sketch (Option B): the dispatch surface to wrap is §5
  (createAgentTool contract); the plan's `POST /agent {agent, input,
  model?, timeout?}` → `{output, usage, exitCode}` maps onto it directly. ✅
- Open items carried to Phase 1/2: stall-watchdog source; grounding sha
  re-pin; live relay-GLM child check; `pi.run` event-subscription harness
  (SDK `session.prompt()`).
