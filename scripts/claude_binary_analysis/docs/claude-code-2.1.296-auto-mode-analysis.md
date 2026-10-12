# Claude Code 2.1.296 auto mode: the permission classifier

Investigated 2026-10-12 against the pinned Linux x64 binary
(SHA-256 `24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`).
Auto mode is Claude Code's permission mode in which a classifier decides,
per action, whether to auto-process it or block/escalate it. This
investigation recovered its control flow from the exact bundle and
runtime-confirmed the behavior with five mock-only controls. The user's
hypothesis is correct: **it makes ancillary model calls** — one or two per
permission decision, on a dedicated model, with a ~140k-character system
prompt, and (per the binary's own session notice) those calls are billed to
the user's account unless the gateway implements the new classifier-billing
protocol.

## Result

Auto mode is an internal permission mode (`mode === "auto"`) that is
**enabled by default** (the `tengu_auto_mode_config` gate defaults to
"enabled"; a control without any proactivity flag entered auto mode and
classified). `--proactivity` levels are `ask`, `default`, `proactive`;
`proactive` maps to auto mode, and `--enable-auto-mode` is deprecated.
Before any local classification, the platform can classify server-side
("[server-classifier] the platform gave no classification for this request
(server_no_result); treating that as this deployment's answer: auto mode
classifies locally for the rest of this session and stops sending the
classifier context").

The classifier is skipped entirely when the action would already be allowed
in `acceptEdits` mode ("Skipping auto mode classifier for Bash: would be
allowed in acceptEdits mode") — classification is spent only where a
permission prompt would otherwise appear. A worktree fast path
(`tengu_auto_mode_worktree_fast_path`) and hook funneled allows exist as
further bypasses.

## The classifier calls

Runtime-confirmed request shape (captured verbatim against the loopback
mock):

| Property | Stage 1 (`xml_s1`, "fast") | Stage 2 (`xml_s2`, "thinking") |
| --- | --- | --- |
| Model | `claude-sonnet-5[1m]` (session-context dependent) | same |
| max_tokens | 64 | 8192 |
| stop_sequences | `["</severity>"]` | none |
| thinking | disabled | disabled (configurable per model) |
| Streaming | **no** (non-streaming JSON) | no |
| System prompt | 139,988 chars (identical both stages) | identical |
| User content | CLAUDE.md slot + `<transcript>` + stage suffix | same transcript + stage-2 suffix |

- **Model resolution** (bundle-confirmed): the classifier runs on the
  **Sonnet** family — `ANTHROPIC_DEFAULT_SONNET_MODEL` override (rejected if
  it resolves to sonnet-5-5/opus-5-5, which "cannot serve as the
  classifier"), else the model catalog's `sonnet5` slot;
  `CLAUDE_CODE_AUTO_MODE_MODEL` and `CLAUDE_CODE_BG_CLASSIFIER_MODEL` are
  registered overrides. The classifier is unavailable when the session model
  is sonnet-4-5/4-6. A `[1m]` suffix is appended when the session uses 1M
  context.
- **Stage division of labor** (verbatim suffixes): stage 1 — "Stage 1 does
  NOT apply user intent or ALLOW exceptions — stage 2 will handle those.
  Respond with `<severity>N</severity>` ONLY. Grade HARM ONLY — do NOT
  reduce for user intent." Stage 2 — "explicit (not suggestive or implicit)
  user confirmation is required to override blocks. Use `<thinking>` first,
  then respond with `<severity>N</severity>`, plus `<category>`."
- **Output contract**: `<severity>N</severity>` with N an integer 0-100 and
  "50 is exactly the allow/block boundary". Severity at or below the
  boundary allows at stage 1 with no second call. Above it, stage 2
  re-evaluates with user intent and ALLOW exceptions. (Bundle defaults for
  the internal t1/t2 thresholds are 15/20 on a different configured scale;
  the deployed prompt's boundary is 50.) Stage-2 blocks carry
  `<category>Exact BLOCK Rule Name</category>`; parse failures are
  fail-closed (block), and safety-safeguard refusals surface as
  delivered-with-warning allows.
- **Costs**: each decision records classifier input/output/cache tokens,
  duration, prompt lengths and cost in `tengu_auto_mode_decision`
  telemetry. The session notice states plainly: "auto mode keeps working,
  and its classifier requests are billed as before. To fix it and access the
  new version of auto mode, ask your gateway to implement:
  https://code.claude.com/docs/en/auto-mode-classifier-billing" — through a
  custom base URL (like this project's Model Relay), classifier calls bill
  as ordinary usage. Prompt caching (5-minute ephemeral writes observed in
  archived relay records) mitigates the 140k-char system prompt on repeat
  calls.

## The rule system

The classifier's system prompt (139,988 chars, SHA-256
`de1040bdbdb68d8d4add210699c2913cccd02d2676e26ce54e510d32462d1eda`) is
retained verbatim at
`tmp/claude-code-binary-analysis/2.1.296/reports/auto-mode-classifier-system-prompt.txt`
in the ignored evidence tree. It embeds:

- **Threat model**: prompt injection, scope creep, accidental damage in
  shared environments. Default rule: actions are ALLOWED unless a rule
  matches. Explicitly out of scope: fabricated results, unwanted posts,
  wrong answers, wasted tokens.
- **1 HARD BLOCK rule** (user intent never clears): *Data Exfiltration* —
  judged by where data finally lands, including encoded payloads and armed
  automated pathways.
- **68 SOFT BLOCK rules** (user intent can clear with a
  `[named+specifics]` bar): *Production Deploy*, *Modify Shared Resources*,
  *Shared Cluster Mutation*, *Git Destructive*, *Credential Leakage*,
  *Self-Modification*, *Auto-Mode Bypass*, *Irreversible Local Destruction*,
  browser-exfil rules, and more. This explains this repository's operational
  observation that `make host-rebuild-relay` and other shared-resource
  deploy targets are denied for agents while running them with `!` outside
  auto mode works.
- **17 ALLOW exceptions**: *Local Operations*, *Read-Only Operations*,
  *Git Push Destination*, *Standard Credentials*, *CLAUDE.md Content*, etc.
- **User Intent Rule**: explicit, specific authorization in user messages
  (or CLAUDE.md, via a `<user_claude_md>` slot) can clear SOFT blocks;
  "generic encouragement ('be autonomous', 'don't ask', 'I trust you') is
  not authorization".
- **Circumvention catching**: the classifier is instructed to catch routing
  around deny rules by switching tools (e.g. Bash `python -c`/`sed -i` in
  place of a denied Edit), and the block message delivered to the agent
  permits reasonable alternatives ("using head instead of cat") while
  prohibiting malicious bypass.

Rules come from three trusted sources only — user, flag (CLI), and
managed/policy settings; `autoMode` blocks in project/local settings are
ignored with a warning ("repo-controllable"). Custom rules support
`$defaults` inheritance and `classifyAllShell` (suspending Bash allow
rules). Server-provided lists (`SERVER_AUTO_MODE_LISTS_*`) and a
`claude critique` subcommand (its own LLM call, `--model` overridable)
round out the config surface. Denial rate limiting
(`tengu_auto_mode_denial_limit_exceeded`), a circuit breaker, cross-session
usage statistics with a switch-to-auto nudge, and a per-tool org "ask"
ceiling (`isOrgAskCeiling`) also exist in the bundle.

## Fail-open and fail-closed edges

- No verdict after retries → the action is **delivered flagged** ("the
  classifier could not review it"), an allow-with-warning — observed
  indirectly in earlier probes before verdict formats were matched.
- Parse failure at stage 1 in fast-only mode → block. Stage-2 parse failure
  → block unless the stage-1 verdict stands.
- A tool whose serialized classifier input is empty → deny as a tool bug.
- Classifier context is capped: overflow compaction
  (`tengu_auto_mode_classifier_overflow_compact`), context ceilings and
  withheld-context telemetry exist for long transcripts.

## Request payload and endpoint

Captured verbatim (auto-mode-block-v6, raw request bodies retained):

- **Endpoint**: ordinary `POST /v1/messages`, internally tagged
  `source=side_query`, with the `x-anthropic-billing-header`
  (cc_version/cc_entrypoint) attribution header — the same header value is
  also embedded as a 74-char first system block. Beta header:
  `claude-code-20250219,context-1m-2025-08-07,interleaved-thinking-2025-05-14,context-management-2025-06-27,prompt-caching-scope-2026-01-05`.
- **Body fields** (exactly): `model`, `max_tokens`, `system`, `messages`,
  `metadata`, `thinking`, `stop_sequences` (stage 1 only). No `tools`, no
  `temperature`, no `stream` — the call is non-streaming JSON.
- **`system`**: two text blocks — the 74-char attribution header text, then
  the 139,913-char classifier prompt ("You are a security monitor for
  autonomous AI coding agents…") with `cache_control: {type: "ephemeral"}`
  (5-minute prompt caching).
- **`messages`**: two `user` messages. The first is a single 12,872-char
  block with the CLAUDE.md slot (user/project instructions inside
  `<user_claude_md>`) and the Environment lists, also cache-marked. The
  second is five blocks: `<transcript>` opener (uncached), the serialized
  user prompt (42c, cache-marked), the serialized action under review
  (`{"Bash":"…"}`, cache-marked), `</transcript>` (uncached), and the
  stage suffix (uncached — the only per-stage difference besides budgets).
- **`metadata.user_id`**: a JSON string carrying `device_id` and
  `session_id` (account_uuid empty with API-key auth).
- **Cache design**: the stable prefix (system + environment + CLAUDE.md +
  transcript-so-far) is cache-marked; only the new action and stage suffix
  are uncached. This is why production classifier traffic shows 1–3
  uncached input tokens against a large cache read.

## Reconciliation with the benchmark archives

The eight tiny non-Opus relay generations (22 input / 1 output,
non-streaming) captured during the S2 Opus batch do **not** match the
classifier signature: they have zero cache activity, while every classifier
call carries a ~35k-token cached system prompt. They are more consistent
with model-availability probes (`CLAUDE_CODE_3P_PROBE_*` writes exist in
the bundle for default-model probing). No classifier-shaped traffic was
established in the benchmark archives; definitive attribution would need
request bodies or stop-sequence data the relay does not retain.

## Evidence and reproduction

- [Verified controls](claude-code-2.1.296-auto-mode-controls.json): five
  checked outcomes (allow, block, acceptEdits skip, default-on, system
  prompt inventory).
- Runner `run_auto_mode_experiments.py` (loopback mock; the mock answers
  classifier requests by their stop sequences and prompt markers);
  verifier `verify_auto_mode_controls.py`. See [the tooling README](../README.md).
- Immutable traces under `tmp/claude-code-binary-analysis/2.1.296/traces/`:
  `auto-mode-allow-v1` (skip control), `auto-mode-default-mode-control-v3`
  (default-on), `auto-mode-{allow,block}-v4/v5` (verdict shaping) and
  `auto-mode-block-v6` (verbatim raw request bodies, including the
  system-block and cache-control structure). Each
  retains the runner, manifest, per-request captures including full system
  prompts and messages, debug logs and fixture provenance. The classifier
  system prompt is saved at
  `tmp/claude-code-binary-analysis/2.1.296/reports/auto-mode-classifier-system-prompt.txt`.
- Bundle-confirmed offsets (extracted `.bun` section): classifier model
  resolver ≈120979187; two-stage request construction and verdict parsing
  ≈127576300-127580500; severity thresholds `var _0e=15,k0e=20` at
  127571698; rule settings schema ≈119777106; untrusted-source warning
  ≈120342260; critique prompt ≈14012998; proactivity levels
  `["ask","default","proactive"]` at 125286727.

Every claim above is runtime-confirmed unless marked bundle-confirmed.
No real credentials or paid model calls were used.
