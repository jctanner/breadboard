
## 2026-10-13: Folded test infrastructure into the pi provider POC plan

Added a "Test infrastructure (containerized, relay-backed)" section to
.ledger/plans/pi-provider-workflow-engine-poc.md: podman container per pi's
documented pattern (named volume for /root/.pi/agent, host ~/.pi never
mounted, pi pinned to host version, dedicated network so namespace criteria
are testable); relay.local GLM via models.json compatible-endpoint config
with runtime-secret credentials; relay as an independent usage oracle; the
five-layer test matrix with the scripted test-child provider for offline
byte-determinism, the mandatory omission injection (S1 recorded-JSON
precedent), and known GLM/relay caveats. Wired into Phase 0/1, cost, and
two new risk rows.

## 2026-10-13: pi provider POC Phase 0 complete

Contract study against fullsend a734637c and pi 1.1.0, recorded in
.ledger/notes/pi-provider-workflow-engine-poc-phase0.md: full
AssistantMessageEvent protocol and provider musts; --mode json wire format
(1.1.0 compatible with fullsend's parser, additions ignored); parser
mappings and ResultEvent metrics fields; usage-file contract with fixture
and fold invariants; plugin validation rules including the env deny-list
(forbids *_API_KEY/_TOKEN/_SECRET/PI_*/FULLSEND_* — relay credential must
be named e.g. WORKFLOW_RELAY_KEY); Option B createAgentTool internals
(child args, childEnv, slots, SIGTERM grace, integrity re-checks); RPC
prompt command. Risk 2 resolved (extension tools must be named in --tools).
Two honesty flags: the stall watchdog (FULLSEND_STALL_TIMEOUT) is not in
either tree (plan fact 3 partial), and the plan's grounding sha does not
resolve (re-pinned). Plan and task updated; relay-GLM live check deferred
to Phase 1 start per the no-runs rule.

## 2026-10-13: pi provider POC Phase 1 complete

Implemented the workflow-engine extension (provider workflow-engine/v1 with
a deterministic two-turn streamSimple emitting the workflow tool call and
final message; the tool runs ingest -> fan-out (concurrency 2, child
pi --print sessions) -> aggregate with completeness assertion and usage-file
records), the scripted test-child provider, check.py (contract assertions +
cross-run determinism), and the podman container (pi 1.1.0, tree-hash label,
dedicated network). Fixed during bring-up: registration needs baseUrl/apiKey
placeholders; partial snapshots must carry correctly-typed content blocks at
toolcall_start; children need stdin ignored and PI_* stripped; podnet needs
--add-host relay-api.local:host-gateway; relay client keys need
backends ["anthropic"] plus both catalog flags. Results: 3/3 deterministic
container runs (byte-identical normalized streams) and a Layer 4 pass with
real GLM children through the relay — usage records match relay telemetry
token-for-token (independent usage oracle). No key material persisted
(verified); runs/ gitignored. Task filed done; plan exit criteria recorded.

## 2026-10-13: Model Relay full-filter telemetry

Implemented and deployed via make host-rebuild-relay. Overview totals are
independent of table pagination; raw snapshots and reporting rollups update
atomically. Fixed measured summary timeouts and increased the bounded event
buffer to preserve synchronized stream bursts. Final stress cases reached actual
32/128/256 streams on one CPU with 100,000 history rows; minute-crossing checks
also passed. 39,680 requests, 2,473 reporting reads, zero dropped requests/events
or storage errors. All 4,859 deployed requests, control state and credential files
were preserved. No paid calls. Evidence: notes/model-relay-telemetry-rollover.md
and checkouts/model-relay/.ledger/notes/telemetry-aggregates-stress-results.md.

## 2026-10-13: pi provider POC Phase 2 complete (R1–R6)

Stood up the local fullsend integration path: built openshell-gateway from
the checkout (podman driver, plaintext, Ed25519 sandbox-JWT signing
material, allow_unauthenticated_users for local use), built the fullsend
sandbox image with PI_VERSION=1.1.0, built the fullsend CLI, and created
the POC harness (config.yaml, harness, agent md, bundled plugin tree,
policy) under var/demos/workflow-engine-poc/phase2. Fixed along the way:
supervisor image naming drift (built a scratch supervisor image from the
checkout's openshell-sandbox binary — glibc-compatible with the sandbox
image), missing gateway JWT config (sandbox tokens), and the missing
test-child upload (bundled into the plugin tree). Results:
fullsend run --runtime pi with model workflow-engine/v1 completes
end-to-end — 3/3 items classified inside the sandbox, parent tokens 0 /
cost $0.0000, per_model_usage folds parent + children, transcripts and
metrics extracted, and the PreToolUse allowlist hook blocks the
code-issued workflow call with a recorded security finding (R6). R7 not
attempted; the stall watchdog remains unverified. Phase 1 check re-run on
the updated extension: 3/3 PASS. Findings recorded in the plan and POC
README; task filed done.

## 2026-10-13: Corrected the Phase 2 tool-allowlist finding severity

Clarified that the POC required zero fullsend changes: every R1-R6 result
ran on the unmodified checkout, and least-privilege enforcement including
extension tools is available stock via the tool-allowlist PreToolUse hook.
Demonstrated both directions: poc-blocked (allowlist bash — the code-issued
workflow call is blocked with a recorded finding) and a new poc-locked
variant (FULLSEND_TOOL_ALLOWLIST=workflow — only the extension tool is
permitted; the run completes 3/3 at $0.0000). The frontmatter translation
gap (poc-narrow: tools: Read, Workflow is dropped) affects only the
declared tool set, which a deterministic provider never reads. Plan
finding #1 updated accordingly; harness poc-narrow replaced by poc-locked
in the phase2 registry.

## 2026-10-13: Workflow-module abstraction (Claude-Workflows-shaped API)

Refactored the workflow-engine POC so the pipeline is a loadable module with
a Claude-Workflows-shaped authoring surface: workflows/demo.mjs exports
meta + default(wf, input) and uses wf.agent()/wf.parallel(); lib/host.js
implements the host — schema-validated agent results (TypeBox), a
content-addressed JSONL journal (inspectable replay instead of engine
magic), bounded-concurrency parallel/pipeline, and loud failures for
invalid/missing child output. The tool became a thin module dispatcher
(command run-demo -> workflows/demo.mjs). Phase 1 check re-passed 3/3
byte-identical on the new architecture; the fullsend Phase 2 run also
re-passed (3/3 in-sandbox, parent $0.0000, children folded). Differences
from Claude's Workflow API are deliberate: contracts validated at the
boundary, journaling on disk, full Node stdlib in workflow code, zero
inference in the parent.

## 2026-10-13: org-scan workflow — drop-in module proof

Added workflows/org-scan.mjs (the architecture-context shape: a clone agent
returns the checkout manifest, one scan agent per repo) with zero changes
to the provider or extension beyond the generalized input contract
(WORKFLOW_COMMAND/WORKFLOW_INPUT, {command, input} tool arguments,
run-id over command+input, artifact.summary as the workflow's own result
text). Carried the campaign guards into the module: the clone's
cardinality cross-check (list length must equal its reported repo_count)
and the per-repo reality check (each scan must name the repo it was
given). test-child learned CLONE/SCAN verbs (fixed an emit-closure scoping
bug found by the child error message). Verified: Phase 1 demo check 3/3
byte-identical on the new argument shape; org-scan locally (3/3 repos,
4 usage records, journal keyed by content hash); org-scan through
fullsend (exit 0, parent $0.0000, per_model_usage test-child/echo=4 +
workflow-engine/v1=1, OTel span gen_ai.system=workflow-engine with zero
tokens). README updated with the drop-in authoring story.

## 2026-10-13: Per-agent cwd in wf.agent()

Added opts.cwd to the workflow host (spawn option; falls back to the run
dir when the target does not exist) and org-scan now passes each scan
agent its checkout directory. Demonstrated locally: with checkouts
materialized, each child session's system message records
cwd=<workspace>/.context/org/<repo> while the clone agent stays in the run
dir. Demo check re-passed 3/3. Layer answers: pi SDK sessions take a
first-class cwd; pi's native Task/Agent tool has no cwd parameter
(children inherit the parent cwd); Claude Workflow agent() cannot have one
(VM has no processes) — its analog is isolation:worktree.

## 2026-10-13: Streaming child output to the primary

Wired pi's native partial-result channel: the workflow tool's execute()
now accepts pi's onUpdate callback and the host parses each child's
--mode json stdout line-by-line as it arrives, forwarding text deltas as
tool_execution_update events (partialResult {agent, delta}, truncated to
200 chars) on the parent's stream while still buffering for the
authoritative final parse. Verified: the parent stream gains one update
event per child delta (28 events vs 25), Phase 1 check re-passes 3/3
byte-identical (scripted children emit deterministic deltas). Caveat
carried from Phase 0: fullsend's parser discards tool_execution_update,
so these updates reach raw stream observers but not fullsend's renderer;
child stderr remains buffered for error reporting.

## 2026-10-13: S1 hardening plan and reviewer delivery repair

Recorded the nine-item plan in plans/strat-workflow-s1-hardening.md; GLM only,
one live scenario execution per revision, premium models only with approval
and necessity. Local eval/s1-hardening c49b43c preserves the benchmark pins
and configures all four review Skills with an explicit Read/Grep/Glob agent.
835 component tests pass (7 opt-in skipped); one native stub control delivers
assessment/dissent/target with the parent schema intact. One focused GLM job
completed in 9m57s: 4/4 assessments delivered, 50 captured GLM request/response
pairs, valid outer result, completed native workflow. Final private system/job
archive and separate native-control capture independently verify. No Jira reset
or write, no Haiku/Opus inference. Evidence: notes/s1-hardening-01-reviewer-delivery.md.
Item 1 focused repair is done; item 2 scope isolation is next.

## 2026-10-13: Skill invocation from wf.agent()

Answered and demonstrated: pi implements the Agent Skills spec (SKILL.md,
same format as Claude) but has NO model-invocable Skill tool — skills are
prompt-driven (advertised in the system prompt's skills section; the model
reads SKILL.md with the read tool when a task matches). The explicit form
is "/skill:name args", and it DOES expand in --print mode: the skill's
instructions are inlined into the child's user message with the args
appended. Discovery rules verified: user skills (<agent-dir>/skills/ =
$HOME/.pi/agent/skills) load unconditionally; project .pi/skills requires
project trust (untrusted dirs silently skip). Wired WORKFLOW_CHILD_SKILLS
into the host (copied into each child's scratch agent dir so no trust is
needed) and proved wf.agent("/skill:classifier classify alpha") end to
end via workflows/skill-probe.mjs — the child's received prompt is the
expanded skill text. Demo check re-passed 3/3.

## 2026-10-13: S1 hardening item 2

Completed assigned-ticket scope on local eval/s1-hardening (4102e7a). Mandatory
keys and plugin hooks restrict reviewer inputs and report targets. Corrected
GLM diagnostic on 107e7af: 12/12 reports across three tickets, 13m43s, 77 API
pairs, no foreign content markers; full private archive independently verifies.
Cancelled launcher-error attempt archived separately with deleted-pod limits.
Frozen Fullsend source layout additionally passes a native zero-provider control
and 868 component tests. No premium model, Jira write/reset or historical-pin
change. Outcome flag contradiction recorded for items 4/6. Item 3 is next.
[Evidence](s1-hardening-02-reviewer-scope.md).

## 2026-10-14: S1 hardening item 3

Completed refinement receipt repair on local eval/s1-hardening (30cf850).
Assigned-key schemas reject malformed/wrong returns; actual saved marks and
valid strategy files determine readiness through a freshly checked snapshot.
886 component tests pass; native forked-Skill fault control makes zero provider
calls. One GLM two-ticket fixture recovers an injected nested receipt, with
one Skill/action/mark each; 3m24s and 32 API pairs, all hosted GLM. Full private
archive verifies (16 sources, 448 files, including API dumps and strace).
No Jira write/reset, premium model or historical pin change. Items 4–9 pending.
[Evidence and qualification limits](s1-hardening-03-refine-receipts.md).


## 2026-10-14 — GitHub emulator aggregate PR diff downloads

Implemented and deployed UI/GitHub-style `.diff` URLs and PR API diff Accept
media types using `make host-rebuild-github`. Raw Git output preserves metadata;
permissions reuse the API gateway. Merge snapshots preserve post-merge diffs.
80 focused tests and both repositories' diff checks pass. Live strat-creator#2
returns identical 111,179-byte diffs for all four representations, covering
all 43 files. See [task evidence](../tasks/done/github-emulator-pr-diff.md).

## 2026-10-14: S1 hardening item 4

Completed review composition on local eval/s1-hardening (7cfcada). User chose
numeric scores as the sole approval gate. Actual delivered Skill reports are
captured with invocation identities/hashes and composed unchanged; scorer
text stays separate and dissent stays explicit. 906 component tests pass;
native controls exercise post-tool payloads, mixed shell output and false
attention flags with zero provider calls. One GLM real-orchestrator fixture:
8/8 authored reports preserved across two distinct targets, 6m02s, 62 API pairs.
Full archive independently verifies: 16 sources, 821 files, including 124 API
dumps and 508 strace files. No premium model, Jira write/reset or baseline-pin
change. Runtime findings also recorded in binary analysis docs. Items 5–9 pending.
[Evidence and limits](s1-hardening-04-review-composition.md).

## 2026-10-14: S1 hardening item 5, assessment delivery gate

Repaired Breadboard benchmark delivery checks with role-assessment-v1 and immutable
replay. Status/errors/acknowledgements and incomplete scaffolding fail; valid
assigned assessments pass; skips/scope/incorporation/accuracy remain distinct.
62 benchmark tests and 9 reference-checker tests pass, six optional Markov tests
skipped. Six fully verified original captures replay; both reported false
positives fail, real GLM repairs remain 4/4 and 12/12, completed Opus remains
S1 2/12 and S2 12/12. Original results unchanged. Zero model calls/tokens.
Private new evidence: 05-delivery-gate/controls/20261014T144916473604Z, 53 files,
1,890,673 bytes, independently checksum-verified. S1 source/numeric policy
unchanged; checker is in the root working tree. Item 5 done; item 6 pending.
See .ledger/notes/s1-hardening-05-delivery-gate.md for contract and limits.

## 2026-10-14: S1 hardening item 6, final outcome

Completed on local eval/s1-hardening at 4c32d21bb2687bda032e4e609ea68853f3fe24dc.
Deterministic business validation saves a hashed completion receipt, checked at
the final structured boundary and trusted host validation. Invalid/null outcomes
fail the Workflow; native state/journal observation separates CLI/reporting
failure from completed work. Reporting recovery restores the same receipt/output
without changing progress. Numeric scores remain the sole approval gate.
941 component tests pass, 7 opt-in tests skipped. Three zero-provider native
controls pass, including a failed Workflow with CLI zero and completed work with
reporting exit 1. One GLM final-step fixture completed in 57s, five API pairs,
one validation command, independently verified; no Jira writes/reset or reviewer
rerun. Complete live evidence and separate controls archives checksum-verify.
See .ledger/notes/s1-hardening-06-final-outcome.md for archive roots and limits.
No Fullsend entrypoint changes; actual Fullsend/OpenShell and whole-pipeline
qualification remain separate. Items 7–9 remain pending.

## 2026-10-14: S1 hardening item 7, publication recovery

Locally pushed `80a11ed` on eval/s1-hardening: durable mutation intent and
conservative Jira read-back, clone/link recovery, deterministic saved-review
publication, owner-bound cleanup and preserved preparation, sealed results and
one immutable run with repeatable summaries. Full suite 966 passed/seven skipped;
real process-death/lost-response controls, local concurrency and post-script
retries pass. Independent captured-HTTP replay verifies 12 parameter cases.
Zero provider calls/tokens, no deployed resets or historical pin changes.

Final control archive under var/run-data/strat-workflow-hardening/07-recovery
verifies: 7,072 files, 81,379,029 bytes, with all available local HTTP/strace,
fixture states, source revisions and test logs retained. Source credential scan
clean. Root changes remain uncommitted and unrelated work preserved.
Jira owner labels do not provide atomic distributed fencing; recorded that gap
separately. Native Workflow replay and Fullsend/full-batch qualification remain
separate; items 8–9 pending. See notes/s1-hardening-07-recovery.md.

## 2026-10-14: S1 hardening item 8, freshness

Locally pushed `0e7e752`: host source/context/input baseline, phase provenance,
strict same-run freshness before reuse/writes and verified later-job continuation.
Legacy/changed pushes require refinement. Actual plugin hook refuses native
replay; the passing control uses a real completed journal. 990 component tests
pass/seven skipped; three zero-provider native controls independently verify.
Earlier fixture failures retained. Zero inference or deployed reset; numeric
gate and historical benchmarks unchanged.

Private 08-freshness archive verifies: 17,723 files/182,139,499 bytes, all 21
authored API pairs, source, fixture state, native journals and logs. Strace was
not enabled and no live model/MLflow job was created. Root control runner and
records updated; root work remains uncommitted and unrelated changes preserved.
Item 9 is pending. See notes/s1-hardening-08-freshness.md for contract and limits.

## 2026-10-14: S1 hardening item 9 rejected

User rejected the budget/deadline proposal as not a bug. Fullsend's existing
per-iteration timeout surrounds either a Claude Workflow or ordinary agent
invocation; additional spending caps and pacing are application policy, not a
demonstrated Workflow-specific defect. Closed the task with an explicit rejected
resolution and updated the plan/index: eight focused repairs, one rejected
proposal, no pending repair in the original list. Existing native limit evidence
is unchanged; deployment/full-batch/content qualification and cross-host fencing
remain separate. No implementation, new model test, deployment or commit.

## 2026-10-14: hardened S1 GLM batch launched through markovd

User authorized one three-RFE GLM batch and one conditional Opus batch if GLM
succeeds. Added separate hardening tiers pinned to 0e7e752, preserving historical
tiers/pins, and native evidence capture. Published the benchmark helpers/gates
and harness as Breadboard a4ca5d6; 69 offline tests pass with the current Markov
binary, validation/syntax/credential checks pass. Synced/imported exact source
in markovd and independently verified five earlier job archives before seeding.

GLM run markov-run-cf0dfe9a started at 20:45:13 UTC; distinct three-RFE seed
completed and model job script-run-workflow-all-glm-5-3-1014-204524-5924cf is
running, GLM-only aliases/medium effort verified. Detached controller PID 2815513
will archive/verify/check completion, native receipts and 12 preserved reports
before its sole conditional Opus launch. Failures stop without paid reruns.
Private evidence lives under var/run-data/strat-workflow-hardening/three-rfe-glm-opus.
No Opus launch yet; final batch results pending. Unrelated changes preserved.

## 2026-10-14: read-only diagnosis of long GLM batch

User requested inspection without killing the job. At roughly 93 minutes all
three strategies were pushed; two reviews completed and the third remained
active. Found and recorded strat-workflow-scorer-path-outside-composition-scope:
external /tmp scorer output fails repository-only composition input validation.
GLM staged byte-identical inputs after 9m26s/13m39s/3m02s diagnostic intervals.
Observed two outer agents, serial specialists despite batched calls, overlay
reads and long successful output generation. One malformed scope report caused
a replacement specialist call. Live tracked source diff was empty.

Relay snapshot saved privately at diagnostics/20261014T222239233070Z: 414 GLM
records, all completed HTTP 200, no recorded errors; generation median 11.384s,
p95 113.333s. Job left running; no source, policy or conditional launch change.
See notes/s1-hardening-three-rfe-glm-live-duration.md. Final gates remain pending.

## 2026-10-14: GLM passed; conditional Opus exposes schema compatibility gap

GLM completed at 22:58:50 UTC in 8,006s. All ten benchmark checks and controller
checks pass: three strategies, 12 preserved reports, receipt/native journal,
matching Jira state and released locks. Final private archive independently
verified at 23:09:54: 6,662 files, 7,517,959,140 bytes, complete/final, no errors.
GLM usage 5,014,392 input + 14,889,472 cache-read + 472,899 output, 435 API pairs.

Controller launched the authorized Opus run markov-run-687db37c at 23:09:54,
model job script-run-workflow-all-claude-opus-4-6-1014-231007-d5c565. By 23:30,
three strategies pushed and scoring nearly complete, but two review agents
failed immediately with HTTP400 rejecting top-level oneOf tool input schemas.
Recorded strat-workflow-anthropic-top-level-union-schema; GLM acceptance did not
establish Anthropic compatibility. Job left running; terminal archive pending.
No live edits, kill or additional paid retry. Earlier GLM ETA was too optimistic.

## 2026-10-14 evening: Opus primary self-repair discovered

At 00:03–00:05 UTC October 15, Opus still ran. The benchmark primary, not the
operator, removed oneOf in both Workflow files, rewrote input/progress source
hashes and launched three Workflows. The last used scriptPath after a named
launch picked up cached original code. Two ticket reviews were active, another
queued. Host prepared input still differed from its modified sandbox copy.
Recorded s1-primary-edits-source-and-freshness-after-failure: this cannot count
as clean qualification of the original pin. Job remains untouched by operator;
archive/terminal validation pending. User requested schema fix first afterwards;
created pending repair task, with no new paid batch authorization. Reliable
completion ETA is unavailable while the primary continues self-repair/relaunch.

## 2026-10-14: archived GLM Gantt reconstruction

Reconstructed exact outer intervals from final native progress and specialist
transcripts. GLM job 133m26s, archival/verification about 11m. Third ticket
review started at minute 85 and took 42m35s. First four reports returned after
26m, but testability/scope were rejected for duplicate Recommendation lines;
about 7m diagnosis + 6m replacement reviews preceded 4m finalization. Recorded
the output-instruction/capture formatting gap. Updated the existing duration
note; no new inference, run mutation or archive modification.

## 2026-10-14: Workflow concurrency finding added to benchmark plan

Added consolidated insight 16 to strat-workflow-eval-plan.md: CPU-derived
default, explicit environment override, observed two-slot GLM scheduling and
separate serial specialist Skill behavior. Linked binary controls and native
timeline evidence. Future comparisons should pin/record concurrency; no live
configuration change or additional inference.

## 2026-10-14 evening: Opus terminal evidence and self-modification finding

Reconstructed the Opus Gantt from its finalized capture: three native Workflow
executions inside one approximately 73-minute job. The third completed after
primary-agent source and freshness edits; host validation rejected the changed
baseline, and benchmark delivery checks rejected two specialist results. Final
archive verification passed. Added consolidated benchmark insight 17 and updated
the hardening plan/bug: deterministic control flow does not enforce predictable
job failure when the surrounding agent can edit and relaunch its program.
External enforcement remains proposed; no repair, paid rerun or archive mutation.

## 2026-10-14 evening: Anthropic Workflow schema compatibility fixed

Committed/pushed f3508786a1e2200731b25dfeda7e01ef772d32ce to local
eval/s1-hardening; remote SHA read back. Removed unsupported top-level unions
from both Workflow copies, added exact verdict consistency checks and refusal
of a claimed completion after recorded failure. Numeric policy and existing
saved-completion verification remain intact; no new hook/script/agent call.

Eight new regression failures reproduced before repair; focused 88 pass and
full make test passes 1,005 with seven skipped (266.30s). Ruff, parity, diff and
staged credential scans pass. One native 2.1.296 loopback control passes with
zero provider calls, valid completion and wrong-hash refusal; 93 emitted tool
schemas across six authored requests have supported object roots. Evidence is
under var/run-data/strat-workflow-hardening/schema-compatibility/20261014/native-completion.

Moved schema task/bug to done/fixed and closed the completed batch task with
its Opus failure/verified archive. Updated index and findings. The Git push
needed the cluster's public CA and existing emulator development credential;
neither credential nor runtime capture was committed. No paid rerun, historical
pin update, live-source adoption or source/baseline protection fix.

## 2026-10-14 evening: next Opus concurrency set to five

Prepared s1-hardening-opus with component f350878 and explicit native Workflow
agent cap five. Markov job environment and run metadata carry the setting;
wrapper summary records it and empty settings leave other native defaults unset.
All 69 offline benchmark tests, current Markov validation, shell syntax and diff
checks pass. Three tickets may only supply three ready outer agents; Skill
scheduling is separate. Historical captures and other tier pins remain intact.
No paid run, Jira reset or deployed import; publication/sync accompanies the next
authorized launch. Recorded source/concurrency confound in the plan findings.

## 2026-10-14 evening: authorized Opus concurrency-five batch launched

Published/synced/imported Breadboard 5ed4a28494bcbb0d3fed31cbe985bca16fc49cc0.
Scoped staged credential/path checks passed; unrelated changes and this log
were excluded from the commit. Five previous model-job archives independently
verify before reseeding. One POST at 02:16:52 UTC October 15 launched
markov-run-f286ae61; model job script-run-workflow-all-claude-opus-4-6-1015-021705-c4354c.
Actual Claude process/checkout verifies Opus, high effort, source f350878 and
native cap five. Native Read has started. Controller PID 3178553 will archive
and independently verify terminal evidence under strat-workflow-hardening/
opus-concurrency5, then check completion, preserved reports and source/launch
integrity. No additional paid iteration; final result pending.

## 2026-10-14 evening: Opus concurrency-five run aborted by HTTP 429

Read-only diagnosis confirms model container exit 1 at 02:40:24 UTC October 15,
23m19s after creation. Native wf_06d4a5cf-be3 completed create/refine/push/score,
but all three reviews and the final result agent received upstream account
rate-limit 429s. No completed review or agent-result.json. Relay confirms
Anthropic/claude-oauth rate_limit_error with upstream IDs; inspected logs do not
establish the window/reset or concurrency causation. One Workflow launch and
no primary Edit/Write calls observed; schema rejection did not recur.
Recorded consolidated finding 19. Markov reports its failed design result and
the detached collector is active; final manifest verification pending. No retry.

## 2026-10-14 evening: Opus concurrency-five archive complete

Controller independently verified the final capture at 02:53:34 UTC October 15.
Manifest complete/final, errors=[], 2,898 files and 5,601,760,759 bytes. API dumps,
strace, native traces, logs and system snapshots are present; final receipt
published. Collection/verification took about 12m41s. Configuration verifies
f350878, cap five, one native Workflow and a script matching the pin. Controller
stopped on the expected benchmark failures after successful archival. Moved the
completed run task to done and updated index/findings. No paid retry.

## 2026-10-15: markovd schedules and authorized overnight Opus

Implemented backend and frontend one-time/cron scheduling in markovd on
feat/run-scheduling. Durable PostgreSQL claims, frozen definitions/inputs,
IANA zones, pause/resume/delete and conservative launch recovery. Go race suite,
64-worker claim test, isolated PostgreSQL recovery/payload tests, frontend
build/tests, deployed restart and browser checks pass without model calls.
Fixed the editor loading race found during verification.

User selected 00:30 America/New_York, October 15, with reset padding. Saved
schedule #6 at 04:30 UTC: one S1 three-RFE Opus pass, cap five, f350878 and
Breadboard 5ed4a28. Previous final captures reverified before queuing. Detached
archive observer PID 3302018 stores evidence under private
var/run-data/strat-workflow-hardening/opus-scheduled-20261015-0030; no paid retry.

## 2026-10-15 morning: scheduled Opus closure

Schedule #6 fired once; model job completed 04:30:12–05:06:40 UTC (36m28s).
All stage exits and final receipt/input hashes verify. Exactly one native
Workflow matches f350878. All 12 reports verify against actual Skill receiving
channels, producer transcripts, provenance hashes and final published reviews.
The pinned benchmark rejects one report's “Mostly sound” judgment; this is a
vocabulary mismatch, not handoff loss. Result remains unchanged; issue recorded.
284 Opus calls, no API errors/429s, 10.51M usage tokens, about $17.48 at the
report's standard API-equivalent rates. Independent content judging not run.

Overnight archival timed out on the 29 GiB retained dashboard source. Repaired
stream timeout/compression, including Python 3.10/3.11 compatibility, and recovered
a separate final capture with explicit source intervals. Both incomplete
captures remain unchanged. Final verification and live receipt readback pass:
3,599 files / 8,998,503,549 bytes; 569 browsable API dumps and 2,357 strace files.
No model rerun or reset. Sixteen archive tests pass; full suite 72 tests, seven
skipped. Task and archive bug moved to done/fixed; findings updated.
