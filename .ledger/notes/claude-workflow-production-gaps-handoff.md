# Handoff prompt: Claude Workflow production gaps

Investigate the remaining production-relevant gaps in Claude Code's native
Workflow system. Start with the missing specialist handoffs and the provenance
of published review findings, then investigate recovery, cancellation, limits
and retries. Produce evidence that can strengthen or change our recommendation
between native Claude Workflows and externally orchestrated agent calls.

This is an investigation, not a request to fix or deploy the strategy pipeline.
Do not assume native Workflows are intrinsically unreliable or that bash is
intrinsically correct. Identify the exact failing boundary and distinguish
engine defects, integration mistakes, configuration effects and model behavior.

## Workspace and initial reading

Work from `/home/jtanner/workspace/github/jctanner.redhat/breadboard`.
Read repository instructions and `.ledger/agentic_work_ledger.md`. Component
checkouts are separate repositories; read their local instructions before edits.
Preserve unrelated changes, including work being done by other agents.

Read these existing sources before extending the investigation:

- `scripts/claude_binary_analysis/README.md` and its `docs/README.md` index.
- `scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-analysis.md`,
  its pseudocode, binary manifest, claim ledger, correspondences and controls.
- `scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-skill-isolation-analysis.md`.
- `scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-information-sharing.md`.
- Any newer skill-variable/result-handling reports in the documentation index.
- `.ledger/plans/strat-workflow-eval-plan.md`, especially the bottom sections
  comparing completed Opus runs, scheduling, handoffs and production advice.
- `.ledger/bugs/open/strat-workflow-reviewer-output-loss.md`,
  `strat-workflow-specialist-review-scope.md` and
  `strat-workflow-review-return-gate-accepts-status.md`.

Use the pinned, unmodified 2.1.296 binary from the existing immutable workspace
under `tmp/claude-code-binary-analysis/2.1.296/`. Verify its identity against the
manifest: SHA-256
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.
Do not silently replace it with whichever release is currently installed.
The payload has multiple ES modules; follow import/export bindings beyond the
old printable-index heuristic. Use the existing parser/carving/hash tooling.

## What we already know

Workflow runs deterministic JavaScript in a restricted VM inside Claude's
process. The parent gets an asynchronous launch receipt; eventual results are
persisted and notified. `parallel()` and `pipeline()` provide overlapping work.
An ordinary `agent()` returns final assistant text; a schema agent requires a
StructuredOutput result. Rejected parallel branches can become `null` while the
outer workflow completes. A journal supports cached-prefix replay.

Sixteen mock workflow controls cover these basics. Cross-process restoration,
cancellation races and several limit/retry branches remain untested. The
examined local workflow token budget initializes to `null`; the initial VM
timeout is not a total workflow deadline. Do not extrapolate either observation
to all CLI/SDK budget or timeout controls.

Separate investigations already proved shared skill availability metadata and
some file-change/reporting channels. Child output visible to the host or SDK is
not automatically content delivered to the receiving model. Avoid duplicating
those investigations; use their findings to test specific missing boundaries.

## Real-run evidence

All paths below are relative to the Breadboard root. Archives are immutable
evidence: read them without modifying files or manifests. `var/run-data` is a
symlink to `/data/breadboard`; do not reset live services to reconstruct a run.

| Run | Final capture | Design job |
| --- | --- | --- |
| S1 Opus, relay repaired | `var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z/` | `script-run-workflow-all-claude-opus-4-6-1011-170435-3f61ed` |
| S2 Opus, completed repeat | `var/run-data/strat-workflow/markov-run-79d3241a/20261012T021947729737Z/` | `script-strategy-entrypoint-all-claude-opus-4-1012-005035-b81781` |
| S1 GLM, single RFE | `var/run-data/strat-workflow/markov-run-23df27ac/20261011T232950539833Z/` | `script-run-workflow-all-glm-5-3-1011-224849-152aa2` |
| S2 GLM, single RFE | `var/run-data/strat-workflow/markov-run-428f237a/20261012T002415035434Z/` | `script-strategy-entrypoint-all-glm-5-3-1011-233753-27ed46` |

Within each capture, inspect `jobs/<job>/api-dumps/index.jsonl`, request/response
bodies, artifacts, original `files.tar.gz`, strace, logs and relay records.
S1 artifacts include `workflow/stream.jsonl` and published review files. Read
the manifests/inventories to locate additional captured state rather than
assuming every native journal or transcript is available.

Use API index pairings and message IDs for exact joins. Request/response
filenames differ. Extracted file mtimes reflect extraction time; use original
tar metadata, indexes or relay timestamps for chronology. S1/S2 Opus generation
IDs join exactly to relay records. EnMaaS GLM IDs were not retained by relay's
`msg_` filter; its job indexes still retain IDs. Do not claim exact GLM relay
joins where the evidence cannot support them.

S1's original design pin is `1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43`;
S2's is `0287b838d2bc59a2569cf2dd971aad7ad2d76dad`. Preserve both.

S1 Opus completed in 51.2 minutes with no transport errors, but ten of twelve
specialist Skill results were completion acknowledgements; only two returned
substantive assessments. S2 Opus completed in 88.7 minutes with all twelve
substantive returns and no transport errors. Both published three approved
reviews. All substantive returns in this pair assessed the whole batch despite
per-strategy targets. S1 GLM similarly returned four acknowledgements while S2
GLM returned four substantive assessments. These observations do not by
themselves diagnose the cause or establish factual strategy accuracy.

## Priority 1: reproduce the missing specialist handoff

Trace the complete chain: Workflow `agent()` options/context -> nested Skill
fork -> specialist conversation/attachment -> result selection and serialization
-> tool result -> receiving review agent's actual model request.

Establish whether schema/tool context propagates into the Skill fork, whether
that changes termination or result selection, and where prose or structured
fields disappear. Schema inheritance is a hypothesis, not an established cause.
Inspect argument expansion/target selection too, incorporating any completed
skill-variable investigation rather than assuming a propagation defect.

Build a small deterministic mock matrix that varies one factor at a time:
ordinary CLI versus Workflow agent; parent schema absent versus present;
direct completion versus a `context: fork` Skill. Probe specialist prose only,
structured output only, and prose followed by structured output as appropriate.
Use distinctive assessment, dissent and target markers. Include positive and
negative controls, and capture the effective child tools/schema/instructions.

For every case, show whether each marker occurs in the child's model messages,
final text/attachment, returned Skill result and receiving agent's next request.
Keep host-visible events separate from model-visible findings. Report the
minimal reproducer and any supported integration workaround; do not deploy it.

## Priority 2: establish final-review provenance in the real archives

For S1's missing returns, identify alternate access routes: explicit file reads,
tool outputs, messages, changed-file attachments or harness-provided records.
Determine whether the receiving review agent obtained the specialist findings
before composing the published sections. Host storage alone is not delivery.

Start with one affected specialist and one positive returned-result control;
then assess all twelve Opus specialist calls if evidence permits. Include GLM
as corroboration when useful. Compare distinctive concerns, recommendations
and dissent with the final documents; allow legitimate summarization.

Produce a per-call provenance table with strategy/role/tool ID, child assessment
source, expected result, alternate delivery evidence and final incorporation.
Separate "delivered", "delivered via another route", "not observed" and
"unresolved because evidence is missing". Do not label prose fabricated merely
because its expected tool result was empty. Distinguish within-run earlier
reviews from artifacts retained from previous runs when examining prior context.

Finish these first two priorities and write their findings before the broader
controls below. The result may change our production recommendation.

## Remaining production controls

3. **Crash recovery and side effects.** Restart in a fresh process using saved
   session state. Kill only fixture-owned processes at controlled boundaries:
   during an agent, after a harmless file/counter side effect but before result
   journaling, and after journaling. Record which calls reuse cache or rerun,
   whether side effects duplicate, and behavior with a truncated journal or
   competing resumptions. Do not assume replay provides exactly-once writes.
4. **Cancellation and deadlines.** Exercise queued/running agents, a delayed
   mock stream and a harmless long-lived child command. Verify what survives
   stop, skip, retry, SIGTERM and the print background-wait ceiling. Look for
   late writes/notifications and released concurrency slots. Separate logical
   cancellation from actual termination; bound every probe with a supervisor.
5. **Budget and concurrency enforcement.** Trace CLI `--max-budget-usd` into
   Workflow and nested Skill execution, contrasting it with local
   `tokenBudget.total=null`. Check accounting and behavior at exhaustion for
   queued and running work, retries and cached calls. Vary the supported
   concurrency override and exercise nested work. Mock usage proves accounting
   behavior, not real prices, quota allowance or provider enforcement.
6. **Retries and incomplete streams.** Inject mock 429/Retry-After, transient
   5xx, a broken stream and a stall. Identify retry scope, counters, backoff,
   final status/null behavior and which prior messages/tools survive. Use a
   harmless counter tool to detect repeated side effects. Do not spend real
   quota to induce a failure; bounded retry exhaustion is part of the control.
7. **Replay with changed shared state.** Keep prompt/options identical while
   changing fixture files, discovered skills or instructions; observe cache
   reuse and stale results. Exercise concurrent completions with reversed
   ordering to establish what determines the chained journal keys. Distinguish
   a documented caller responsibility from an engine defect.

## Evidence, boundaries and deliverables

- Use the unmodified pinned release and loopback mock API with fresh fixture
  repositories/configuration. No paid inference, real credentials, live Jira
  writes, benchmark launches, deployment changes or upstream publication.
- Modify authored tools/fixtures when needed; do not execute extracted modules
  or patch the target binary to manufacture a result. Use bounded failure
  injection and clean up only processes/resources owned by each fixture.
- Put generated binaries, module carves and runtime evidence in new immutable
  directories under ignored `tmp/claude-code-binary-analysis/2.1.296/`. Preserve
  failures as evidence; do not overwrite them with passing reruns.
- Label conclusions as runtime-confirmed, exact-bundle/static, archive-observed
  or inferred. Record exact module/function byte ranges and hashes, fixture and
  runner provenance, commands, request counts and persisted outcomes.
- Maintain reports and compact claims/controls under
  `scripts/claude_binary_analysis/docs/`, updating its index. Keep work tasks,
  bugs and progress in `.ledger/`; append benchmark implications at the bottom
  of `.ledger/plans/strat-workflow-eval-plan.md`, not the old handoff document.
- Add executable verifiers for new runtime claims. Run relevant tooling checks,
  claim/path/hash validation and `git diff --check`. CLI exit zero alone is not
  sufficient verification. Do not commit raw evidence, secrets or unrelated work.
- Summarize what is an engine defect, an avoidable integration issue, expected
  behavior or still unverified. Explain whether the findings change production
  advice, including remedies and their limits. A negative or unresolved result
  with precise evidence is acceptable; invented certainty is not.

Complete the investigation within these boundaries. If a particular test is
blocked by missing evidence or unavailable controls, record that limitation
and continue with the independent priorities.
