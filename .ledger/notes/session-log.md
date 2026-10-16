
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

## 2026-10-15: failed dashboard job duration

Fixed the jobs/evals API fallback to current time for failed Kubernetes jobs.
Use terminal condition timestamps for stable duration in the lists and detail
modal; active retries keep running and unknown terminal times remain unknown.
Ten regression tests, Python/JavaScript checks and diff checks pass. Rebuilt
the dashboard and verified all four real failed job durations across automatic
browser refreshes, including matching detail duration. See the
[fixed bug](../bugs/fixed/dashboard-failed-job-duration.md).

## 2026-10-15: S1 hardening on the Fullsend fork

Created local feat/s1-workflow-hardening in
checkouts.tmp/jctanner-fullsend-ai/strat-creator, from origin/main b396172.
Merged exact fullsend-ai PR #83 head 6b78355 (eight original Wayne Sun commits),
retaining the newer release-3.8 config and type-descriptor additions. The only
merge conflict was Makefile; both lint/type validation and Workflow targets
remain. Replayed all twelve follow-ups through tested source f350878, without
conflicts. All 88 S1 follow-up paths match the historical source exactly.

Full make test: 1,005 passed, seven skipped; type descriptor validation, focused
review-score tests and full-branch diff checks pass. Tip 6a05210 is a one-line
inherited-whitespace cleanup. New branch clean and committed locally; original
S1 checkout/main unchanged. No model run, deployment, public PR or push.
Source mapping and validation are in the completed port task.

## 2026-10-15: Rewire Markov to Fullsend PR #85

Verified the fork branch and upstream PR #85 both at 6a05210. Both current S1
hardening tiers now clone the public fork at that exact commit. Seeding and
native execution share the source selection; seed/run/evaluation metadata
records it, with historical A/B source pins retained. All 72 offline benchmark
checks pass using a current Markov build. Cluster source fetch and a read-only
seed dry run pass. Published benchmark code as Breadboard 5493469 and synced
project 1; read back the existing workflow and verified its source commit and
candidate pins. No model run or reset. Other pending Breadboard changes remain
unstaged. See tasks/done/strat-workflow-fullsend-source.md.

## 2026-10-15: One-ticket S1 integration smoke on Vertex

Launched one authorized Markov run, markov-run-d7043ace, with a run-only
one-ticket batch configuration, new fork pin 6a05210 and claude-opus-4-6.
Offline execution verifies effective batch size one and the batch-discover
launcher. Four previous retained model archives independently verified first.
The seed completed and model job 171835-332613 is running. Actual Claude PID
142 verifies the correct source, model aliases, cap five and one locked RFE.
Vertex requests return HTTP 200 with google-service-account authentication.
Observer PID 4112002 will archive and verify terminal evidence; no paid retry.
Context: var/run-data/strat-workflow-hardening/fullsend-vertex-opus-one-rfe-20261015/.

## 2026-10-15: Fullsend/Vertex smoke results

Markov run d7043ace and model job 171835-332613 completed, 27m54s; native
Workflow 26m17s. One strategy approved 7/8, every stage exit zero. Audited the
completion receipt and input hashes, exact stored script, all four producer
transcripts, actual Skill receiving channels and verbatim published reports.
All agree. Primary launched one Workflow and read its result, with no rewrite.

All 108 API responses match Vertex relay message IDs: HTTP 200, complete usage,
no errors. API/relay totals agree at 3,743,001 tokens including cache. Eight
separate token-count calls also succeeded. Numeric-only approval preserves
testability's revise recommendation as configured.

Strict benchmark rejects feasibility formatting alone. The detailed numbered
findings are swallowed into unrecognized parser fields; adding a Findings
heading only in memory makes the report pass. Recorded a new checker bug and
updated the hardening plan. Historical FAIL and artifacts remain unchanged.
Collection has finished and published a receipt; the observer's independent
verification is pending at this update. No model work was repeated.

Final observer verification then passed with no problems: 1,612 files /
6,357,233,437 bytes, complete/final, errors=[], receipt published. API dumps,
strace and shared system evidence are included. Preserved audit scripts/results
and exact relay correlation in launch-context; moved the smoke task to done.

## 2026-10-15: One-ticket latency compared with three-ticket batch

Compared native phases and actual reviewer transcripts against the verified
overnight run. Job time falls 36m28s to 27m54s while tokens fall 10.51M to 3.74M.
Three-ticket refinement/scoring/review overlap, so elapsed duration does not
scale with ticket count. Found another bottleneck: all four reviewer Skills are
requested in one API response but run serially within each ticket. The one-ticket
reviewer interval takes 8m49s; longest reviewer 2m50s. Recorded timings and a
performance bug; exact runtime serialization cause remains unverified. No
model inference or source changes were needed for the diagnosis.

## 2026-10-15: Confirm Skill serialization in Claude's dispatcher

Exact 2.1.296 binary inspection resolves the reviewer serialization cause:
generic tools default isConcurrencySafe=false, Skill does not override it, and
both streaming/nonstreaming dispatch paths serialize unsafe calls. Added a
credential-free native loopback control. Four Skills from one Workflow caller
reach concurrency one; one Skill from each of four callers reaches concurrency
four. Both return all four Skills and exit zero, with no real provider calls.
Saved a maintained binary-analysis report and compact source/control hashes;
updated the performance bug, timing note and hardening plan. The pipeline
implementation and historical benchmark results remain unchanged.

## 2026-10-15: Confirm the same serialization before Workflows

Extended the isolated concurrency control with a real plain claude -p
slash-command route and Workflows disabled. The authored prompt is loaded,
four Skills return, maximum child concurrency is one, exit zero; no provider
calls. Checked the historical S2 Opus launch/first/last response hashes: each
ticket's four Skills are requested in one response and child responses occur
in role order. Updated the maintained binary report, compact evidence, shared
performance bug and hardening plan. Preserved exact runners for prior controls.

## 2026-10-15: Defer reviewer concurrency optimization

The user put reviewer concurrency on the backburner given approximately six
minutes of ideal single-ticket savings. Recorded the decision in the hardening
plan, open performance finding and index. Full ten-ticket simultaneous review
would require 40 reviewer workers; implementation also needs multi-caller
capture/receipt validation and explicit partial-failure/recovery handling.
Existing pipeline dispatch stays in place. Evidence is retained, with no
concurrency implementation or qualification run planned until revisited.

## 2026-10-15: Prepare ten-ticket S1 with concurrency ten

Updated both current S1 hardening tiers to batch-ten-new-rfes, batch size ten,
Workflow cap ten and one iteration. Added three complete fictional RFE templates
for training checkpoint recovery, storage connection credential rotation and
evaluation report export; combined with seven existing distinct capabilities.
Reviewer dispatch stays unchanged and deferred. Historical smaller tests remain.

All 75 benchmark tests pass with actual offline Markov execution, including the
ten-key environment/source wiring, missing-tenth rejection and forty-report
coverage checks. Markov validation and diff checks pass. Published only the seven
required benchmark files as 0359a9a after staged-file and credential-pattern
checks; unrelated pending changes remain unstaged.

Synced Markovd project 1, imported workflow 744 and verified all 64 files against
the pushed commit. Live read-only seed dry run confirms ten distinct eligible
planned RFEs. No model run, reset or live issue creation. Completed task records
the source pin and next GLM launch settings; terminal archival guards remain.

## 2026-10-15: Launch ten-ticket S1 GLM at concurrency ten

User authorized the prepared batch. Exact offline variables and all 64 imported
files verify source 0359a9a / candidate 6a05210. All five prior retained model
archives independently reverified before seeding; no active jobs/conflicting
schedules. GLM's enmaas-personal route and managed API-token readiness pass.

One POST launched markov-run-d72c2f57 at 19:10:43 UTC. Ten distinct RFEs seeded
and discovered; model job script-run-workflow-all-glm-5-3-1015-191057-721118 is
running. Observer PID 33397 will archive/independently verify terminal evidence
under var/run-data/strat-workflow-hardening/fullsend-glm-ten-rfe-c10-20261015/.
No automatic paid retry or Opus continuation. Actual process settings pending
startup inspection; all launch and preflight evidence retained privately.

Startup verification subsequently passed: clean 6a05210 source, ten acquired
RFEs, batch mode/size ten, cap ten, medium effort and GLM for primary, helpers
and all aliases. Relay confirms successful generation through enmaas-personal.
The model job is running and the detached observer remains attached.

## 2026-10-15: Accept repeated agreeing reviewer verdicts

User authorized ignoring duplicate Recommendation lines when the verdict agrees.
Updated both identical helper copies in the Fullsend strat-creator fork and the
independent Breadboard benchmark classifier. Original report bytes/hashes and
numeric-only gating remain intact. Missing, blank, malformed and conflicting
values remain failures; architecture-only skip remains enforced.

Validation: 47 focused composition tests; make test-unit 575 passed / five
skipped; make test 1,033 passed / seven skipped (265.78s); all 79 benchmark
tests pass with offline Markov execution. Ruff and both diff checks pass.
Both unchanged formerly blocked reports pass the plugin/host helpers and
benchmark classifier; all forty archived reports pass the live parser.
No inference, retry/resume, artifact edits or historical result changes.
Changes are local only; no commits/pushes or Markov source-pin update. Fix task
and bug moved to done/fixed; the independent numbered-findings issue stays open.

## 2026-10-15: Correct ten-ticket run to Opus

User explicitly selected “Stop GLM, archive, then run Opus.” Dashboard stop
deleted the GLM workload and Markov runner; Markovd's stale running status was
reconciled through its cancel endpoint. No model process signal was sent by
the guarded stop helper before those deletions. Replaced the read-only
observer with a deleted-job recovery collector. Shared workflow stream,
stderr, 95 API dump files and 678 syscall trace files survive. Pod-local native
transcripts/worktree and pod logs do not; archival records the gap explicitly.

Prepared an exact one-iteration Opus launch on the same ten-RFE scenario,
source/candidate and cap ten. Offline Markov execution passes without model
calls. Waiting for the stopped GLM archive to verify before resetting Jira or
launching Opus. No automatic model retry is authorized.

The GLM recovery capture completed and independently verified 894 files /
6,123,261,163 bytes, no capture-source errors, receipt published. It explicitly
discloses lost native/pod-local evidence. All five earlier retained model
archives were also independently checked before seeding the next run.

One POST launched Opus run markov-run-fbc62d49 at 19:38:50 UTC. Actual Claude
PID 145 verifies clean 6a05210 source, all ten acquired RFE keys, cap ten, high
effort and Opus primary/helpers/aliases. Initial telemetry: nine Opus streaming
calls, all HTTP 200 through vertex-strat-evals. Model job
script-run-workflow-all-claude-opus-4-6-1015-193904-1a3da4 is running. Observer
65418 will collect and independently verify terminal evidence, with no model
retry. Private evidence root: fullsend-vertex-opus-ten-rfe-c10-20261015 under
var/run-data/strat-workflow-hardening/.

## 2026-10-15: Diagnose and archive the ten-ticket Opus failure

markov-run-fbc62d49's model job exited 1 after 51m24s. Native Workflow failed
after 44m47s; outer CLI exited 0. All ten strategies created/refined/pushed and
scored, all forty reviewer reports delivered. The live capture parser rejected
two reports with repeated identical revise recommendation lines (RHAISTRAT-3
feasibility, RHAISTRAT-7 testability). Missing composition inputs prevented
publication and review recording for those two; eight final reviews completed.
Completion guards rejected partial work. Reproduced both failures offline and
confirmed removing only a duplicate identical line in memory makes each pass;
saved evidence and FAIL unchanged. Recorded a new bug and plan findings.

All ten claims released, confirmed by release record and Jira snapshot. Relay
has one 502; all role reports still returned and terminal failures identify the
parser. Three other feasibility reports trigger the existing external checker
false negative despite being captured/composed. No model retry or resume.

Final archive: fullsend-vertex-opus-ten-rfe-c10-20261015/markov-run-fbc62d49/
20261015T203122658615Z under var/run-data/strat-workflow-hardening. Independently
verified 10,935 files / 20,472,635,632 bytes, no capture-source errors, receipt
published. Includes native data, 1,898 API body files and 7,392 syscall traces.
Run task moved to done; audit saved as s1-fullsend-opus-ten-rfe-20261015.md.

## 2026-10-15: Design mixed-state S1 batch

Verified discovery, STRAT/RFE status and label gates, host resume selection and
freshness requirements in the current Fullsend fork. Draft scenario plan covers
fresh creation, import/refinement, verified review-only recovery, stale/missing
provenance fallback and ignored controls across roughly 20–30 Jira records.
The existing all-new seed/checker needs extension. Record discovery, acquired
and skipped sets separately: human-sign-off is currently gated after the batch
cap. Plan no-reset, no-model preparation replay to check ordinary repeat safety.
No fixture seed, Jira reset, paid run, commit/push or Markov sync performed.
Plan: plans/strat-workflow-mixed-state-batch.md.

## 2026-10-15: mixed-state S1 implementation and GLM launch

Published the agreeing-recommendation parser fix as strat-creator fbc335b.
Added the separate mixed-state tier, 29-issue manifest, genuine push provenance,
pre-inference guard, immutable-control/per-ticket checks and a model-free repeat
preparation. 89 offline benchmark tests pass; the separate real local-emulator
suite passes eight tests including recovery reimport. Ruff, shell syntax and
diff checks pass. Earlier retained archives and cancelled GLM evidence were
independently reverified before reset.

Breadboard a75c72b pushed and synced. One authorized GLM run launched:
markov-run-eaf92e4d, job script-run-workflow-all-glm-5-3-1015-231702-8b0253.
Live guard and primary process confirm candidate fbc335b, GLM 5.3/medium,
cap ten, ten discovered/nine acquired: four create, three refine, two review.
Human-signed-off RFE 13 skips after discovery cap; RFE 9 remains deferred.
Initial GLM requests succeed through enmaas-personal. Observer PID 330749
will archive and independently verify under
var/run-data/strat-workflow-hardening/fullsend-glm-mixed-state-c10-20261015.
No paid retry or Opus continuation. Completion and archival results pending.

## 2026-10-16: stopped mixed-state GLM after native failure

User requested stop. SIGTERM sent to the verified primary at 01:18:49Z,
without deleting the pod. Claude exit 143, host validation one, lock release
zero; all nine owned keys released. Job restart disabled. Native transcripts,
API dumps, syscall traces and run artifacts retained; automatic collector
started terminal archival at 01:20:37Z. Final verification pending.

First native Workflow failed after 106m02s on the two review-only task statuses.
The primary subsequently invoked a second native Workflow inside the same job;
that also failed. Last result reports a review input/provenance mismatch, and
the two saved task statuses at shutdown are Refined. Recorded the import versus
completion-status contract bug; transcript analysis is still needed for the
precise parent repair sequence. No new host job or Opus run was submitted.

The finish checker passed its Jira/control/clone/ownership checks but skipped
the live repeat after failure. Markov's independent check did not start: its
306,233-byte seed argument exceeded the exec argument limit. Both defects are
under bugs/open/ and the mixed-state plan records these findings. Original
failure is retained. Archive destination and observer remain in the execution task.

## 2026-10-16: mixed-state repair and one authorized Opus pass

Published strat-creator f5691f7: verified review-only imports restore Refined
before review hashes; duplicate push skipped; failed-receipt relaunch blocked.
Full suite 1,041 passed / six skipped. Published Breadboard a2aec3c: seed JSON
via stdin, native-failure monitor in new mixed Opus tier, skipped repeat remains
a failure. Benchmark suite 96 passed with one optional skipped, separate local
Jira suite nine passed, no inference. Prior captures independently verified.
Launched only markov-run-5d3327ed at 13:49:39Z, exact Opus 4.6, batch cap ten
and concurrency ten. Detached observer PID 1194342 retains terminal evidence
under var/run-data/strat-workflow-hardening/fullsend-vertex-opus-mixed-state-c10-20261016.
Live process verification passed: candidate clean, Opus/all aliases pinned,
high effort, cap ten, monitor enabled, nine expected resume points; successful
Vertex responses observed. Job script-run-workflow-all-claude-opus-4-6-1016-135017-13fd26.
Result pending; no replacement model job.

## 2026-10-16: mixed Opus result verified

markov-run-5d3327ed completed. Pipeline exit zero; model job 45m14s, native
Workflow 41m09.550s. All nine tickets and model-free repeat passed; seven
approve/two revise. All 36 role reports delivered, hash-matched and composed.
Pinned benchmark remains failed on three formatting false negatives; recorded
repeated-judgment bug and recurrences without changing stored results.
Final archive independently verified: 11,940 files / 22,344,722,063 bytes,
receipts published. Task moved done; plan and audit updated. No new model run.
