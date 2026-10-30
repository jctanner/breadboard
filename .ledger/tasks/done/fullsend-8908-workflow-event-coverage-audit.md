# Audit Fullsend #8908 display coverage beyond the captured happy path

Owner asked whether every Workflow display event was covered after the local
fix. The initial patch is not exhaustive. Audit on 2026-10-29 inspected the
installed native Claude 2.1.312 binary's embedded JS/schema (read-only), the
staged Fullsend parser/renderer, and prior archived 2.1.296 evidence. No model
was invoked and no component code was changed during this follow-up audit.

## Confirmed local patch gaps

- `task_updated.patch.status` schema includes pending and paused; the patch's
  state mapper ignores both. Paused workflows exist in the runtime.
- `patch.description` is emitted independently of status; the patch ignores
  description-only updates and does not merge lifecycle metadata.
- `task_progress.last_tool_name` and its bounded progress `summary` are emitted;
  the patch only consumes description and nested Workflow agent tool metadata.
  Progress summary is distinct from the potentially full task_notification
  result summary, which should remain excluded from display by default.
- Agent records include blocked/error/cached metadata; the patch renders
  generic failed/completed without these distinctions or safe failure detail.
- Broader stream display messages such as task_summary, background_tasks_changed,
  informational, hooks and rate-limit events are not exhaustively handled by
  this patch. Membership snapshots are not proof of execution or completion.

## Producer limits

Embedded function `jFn` excludes workflow_log entries; the Workflow onSdkEmit
callback filters both the incoming batch and stored workflowProgress through
it. Thus internal Workflow log messages are absent from the task progress
wire snapshot in this inspected runtime. Fullsend cannot render records not
emitted to it. Declared workflow_phase records still do not prove execution.

## Evidence and limits

Binary: `/home/jtanner/.local/share/claude/versions/2.1.312`.
Parser: checkout branch fix/8908-claude-workflow-progress,
internal/runtime/claude_task_progress.go and claude_progress.go.
Raw bounded extraction: `/tmp/fullsend-8908-event-audit-runtime.txt` (partial
embedded code, useful alongside fresh targeted binary extraction).
Official Agent SDK docs fetch exceeded the web tool's content limit; no
third-party reference was used to establish runtime behavior.

The archived replay proves the original observed run displays progress. It
does not prove all Workflow event/state/error/pause/recovery variants. Future
Claude versions cannot be covered by a claim of all possible events.

- [x] Audit captured-run scope against current runtime emitter/schema.
- [x] Extend parser and display tests for confirmed wire-level gaps.
- [x] Document explicit emitted/displayed/ignored/unavailable event matrix.

## Broader implementation authorized and completed locally

Owner requested the broader useful event coverage in this same feature branch.
The component patch now includes pending/paused states, partial description
and error merges with explicit clearing, run identity inheritance, suppressed
late nonterminal snapshots, ambient start suppression, top-level task tool
and progress-summary fields, worker-restart cause, and blocked/cached/error
agent metadata. The sanitized retained display state is bounded; raw IDs are
hashed for cache keys. New starts can reset an identity.

An explicit display decoder also covers hook lifecycle/outcome/exit metadata,
mid-turn summaries (including null clears and older summary shape), background
non-ambient membership count, permission-denial identity/reason, compaction
and requesting status, session state, salient informational/text notifications,
and rate-limit warning/rejection/reset/recovery. Transcript-only info,
hook output, permission tool-result bodies, task completion summary/results,
prompts, static phase inventories, unknown/malformed kinds/states, and raw
usage counters remain excluded. Unknown raw events are still captured.

`docs/cli/run.md` includes an event matrix and producer/version/cache limits;
`docs/runtimes/claude.md` links it. These are version-bounded compatibility
claims, not a guarantee about every future Claude event.

Validation:

- Expanded focused parser/renderer race tests pass, including final separate
  error/status patches and explicit error clearing (1.675s final run).
- Complete runtime race suite passes (85.196s, 93.3% package statements).
- New display decoders/renderer functions are 100% covered; task decoder
  97.9%; shared parser 93.5% and renderer dispatch 100% in full runtime run.
- Actual CLI iterationEventHandler path race tests pass (1.084s): runner and
  provider credential literals redacted, no model content or tool spans added.
- Original verified archive replay passes: 325 task/agent events produce 56
  display lines after improved deduplication, all expected phase names and
  completion still visible. Raw archive is untouched; harness/output stay /tmp.
- Final staged make lint passes (Go vet, secret checks, Markdown links).
- git diff checks pass. All other main-module packages pass race tests (exit 0),
  excluding the previously documented full CLI timeout; the focused CLI
  checks above cover the changed display consumer. No suite ceiling raised.

Artifacts: `/tmp/fullsend-8908-expanded-{runtime,final-focused,cli,lint,replay,
other-packages}.log`, runtime and final-focused .cover profiles in /tmp.
No model calls, commit, push, PR, deployment, or upstream issue edits.

Local broader implementation complete. Thirteen intended files are staged on
fix/8908-claude-workflow-progress. No commit or publication requested yet.
The original full CLI run timeout is still an explicitly recorded validation
limit; it is not reported as a passing full repository suite. The nested
mintcore module previously passed its separate GitHub-tagged race run; it
was not changed or re-run for this runtime-only expansion.
