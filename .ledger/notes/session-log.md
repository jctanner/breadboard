
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
