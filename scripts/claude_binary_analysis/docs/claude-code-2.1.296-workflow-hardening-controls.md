# Claude Code 2.1.296: runtime controls for the S1 repairs

Verified 2026-10-13–14 against the unmodified Linux binary, SHA-256
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.
These controls exercise the actual executable, Skills and hooks with a local
API stub. They follow the [specialist handoff investigation](claude-code-2.1.296-workflow-specialist-handoff.md).

The question was whether the repairs work through Claude's real tool and
completion boundaries. A unit test that supplies an agent result cannot
establish effective tool inheritance, schema rejection, hook execution or
delivery through a forked Skill. The stub supplies deliberate bad answers;
Claude still executes the actual tools, scripts and return handling. Native
controls use fresh configuration directories and no provider credentials or
provider calls. Separate GLM checks test the configured path with a real model.

## 1. Reviewer delivery: verify the configured remedy

The earlier investigation found that a forked Skill could inherit its caller's
StructuredOutput tool. A tool-ending specialist loses its assessment at the
text-only Skill return, even when the assessment remains in its transcript.

A native control loaded the actual candidate `strat-reviewer` definition with
an explicit Read/Grep/Glob whitelist. The specialist's request offered those
three tools, excluded StructuredOutput, and delivered assessment, dissent and
target markers through its Skill result. The caller retained its outer schema
and completed correctly: six loopback requests, zero provider calls.

This confirms the previously identified workaround in the actual repair
configuration; it is not a newly discovered Claude return mechanism. The
subsequent single GLM check delivered all four real reviewer reports.
[Candidate, captures and limits](../../../.ledger/notes/s1-hardening-01-reviewer-delivery.md).

## 2. Reviewer scope: bind hooks to the actual child

The scope control ran twelve forked reviewers across three distinct tickets.
The stub deliberately requested foreign-file reads, broad searches and
wrong-ticket completions. Actual plugin hooks blocked 36 forbidden tool calls
and 12 wrong completions, then allowed the corrected inputs and delivered all
12 corrected reports. The initial verified scenario used 45 loopback request
pairs and made zero provider calls.

One new runtime observation mattered: the child assignment transcript can be
unavailable when its first tool hook runs. The early guard blocked some valid
first reads because it treated this timing gap as a missing assignment. The
repair waits up to two seconds for that agent's assignment, then denies access
if it is still unavailable. Two seconds is our adapter policy, not a guaranteed
Claude flush deadline. Assignment binding uses the hook's agent identity and
that child's initial prompt, rather than a shared current-ticket variable.

Final native qualification also tested frozen source RFEs in strat-originals
with no rfe-tasks directory. The one completed GLM scope scenario delivered
12/12 reports; its live denials were alternate-path and broad-search probes,
not observed foreign-ticket reads. Frozen-source parity was checked separately
without another paid run. A diagnostic launcher failure also established that
this invocation needs a repeated `--plugin-dir` flag for each plugin.
[Source revisions, attempted controls and exact evidence](../../../.ledger/notes/s1-hardening-02-reviewer-scope.md).

## 3. Refinement receipts: separate shape from saved completion

The historical malformed receipt was an application contract failure: the
schema allowed any string, including serialized JSON, while the Workflow
required an exact ticket key. Completed work was consequently omitted from
the ready set. A target-bound enum closes that schema gap; saved-state
reconciliation handles a missing or unusable return.

The final native control used the actual candidate refinement stage, a
forked fixture Skill, real completion helpers and plugin hooks:

| Deliberate input | Observed result |
| --- | --- |
| Completed target, correct receipt | Target ready |
| Completed target, nested-JSON receipt | StructuredOutput schema rejects it; the stub returns `none`; saved completion still makes the target ready |
| Uncompleted target, correctly shaped receipt | Receipt passes its schema; our saved-state check holds the target back |
| Uncompleted target, another ticket's receipt | StructuredOutput schema rejects it; corrected `none` still leaves the target unready |
| Invented checkpoint claiming all four ready | PreToolUse hook rejects StructuredOutput; the corrected disk snapshot is accepted |

The malformed receipts produce tool errors in the next API request, including
`Output does not match required schema`. A schema-valid but invented checkpoint
instead produces a hook error. Thus both schema enforcement and command hooks
operate at a Workflow step agent's structured completion boundary, before
its result is accepted. The stub supplied the corrections; this does not
establish that a real model will always recover from those errors.

Final result: two completed targets ready, two uncompleted targets failed
refinement, 26 loopback requests, three checkpoint audit events and zero
provider calls. Claude enforces the schema and hook decisions. Our Python
helper supplies the business rule: both a current-run completion mark and a
valid matching strategy file are required.

The single GLM check used two authored fixture actions. It injected the legacy
nested receipt after one valid agent return, testing Workflow reconciliation;
the native control above separately tests rejection at the actual schema
boundary. Both targets became ready with one Skill/action/mark each. All 32
captured request pairs used `rits/zai-org/glm-5-3`. The fixture does not generate
or judge production strategies. [Repair and archived evidence](../../../.ledger/notes/s1-hardening-03-refine-receipts.md).

## 4. Composition: capture the delivered Skill result

A native hook probe established that PostToolUse for Skill exposes the actual
delivered report in `tool_response.result`, with `success`, `status: forked`,
`commandName` and child `agentId`. The event also carries the caller agent,
tool invocation ID and supplied Skill/arguments. The probe captured 12 such
events, using 45 loopback requests and zero provider calls.

The repaired composer uses these receipts directly. It does not recover report
bodies from child transcripts. A Bash PostToolUse receipt binds its begin
session to the actual caller; Skill receipts then fill the four role slots for
that target and session. The final control also tests a begin JSON receipt
mixed with ordinary shell output. Hooks observe tool-response data rather
than model descriptions of what a reviewer supposedly said.

Final native control: 37 request pairs, zero provider calls, eight reports
preserved across two targets. An independent verifier joins each final role
section to its receiving API tool result and the named child's final message.
Both deliberately supplied revise/needs_attention=false outputs fail the
actual Workflow StructuredOutput schema; corrected outputs complete.

The user's decision is **numeric scores as the sole approval gate**. One
target remains approve/false at 8/8 while retaining two revise recommendations;
the other remains revise/true at 4/8 while retaining specialist approvals.
The composer lists those differences without rewriting the reports. The
numeric rule agrees with the original rubric for all 81 score combinations.

One subsequent GLM scenario on local candidate `7cfcada` runs the real
strategy-review orchestrator with authored scorer/reviewer fixtures. All 8/8
reports match their delivered results and child responses; both persisted
numeric decisions match the native Workflow result. It uses 62 API pairs,
all exact hosted GLM, and completes in 6m02s. It does not test independent
strategy content quality or full generation/publication.

Earlier attempts exposed two diagnostic errors: missing fixture reviewer
directories, then a missing STRAT constant in the generated Workflow. The
latter returned CLI success while the Workflow failed, reinforcing the need
to check native state. Neither is a new Claude bug. Both attempts, the plain
and mixed-output controls and their captures are retained privately.
[Repair, policy and archival evidence](../../../.ledger/notes/s1-hardening-04-review-composition.md).

## Reproduction and retained evidence

Use the corresponding pinned candidate checkout and a new output directory:

```bash
python3 scripts/claude_binary_analysis/run_reviewer_scope_control.py \
  tmp/claude-code-binary-analysis/2.1.296/input/claude \
  /path/to/strat-creator-at-4102e7a /tmp/new-scope-control --frozen-rfe

python3 scripts/claude_binary_analysis/run_refine_receipt_control.py \
  tmp/claude-code-binary-analysis/2.1.296/input/claude \
  /path/to/strat-creator-at-30cf850 /tmp/new-refine-control

python3 scripts/claude_binary_analysis/run_review_composition_control.py \
  tmp/claude-code-binary-analysis/2.1.296/input/claude \
  /path/to/strat-creator-at-7cfcada /tmp/new-composition-control --mixed-begin-log
```

The [scope runner](../run_reviewer_scope_control.py) and
[refinement runner](../run_refine_receipt_control.py), and
[composition runner](../run_review_composition_control.py) retain binary/runner
hashes, committed fixture provenance, requests/responses, native state and
verification results. The refinement control's first verifier read `state`
instead of native `status`; its original and corrected results are both
retained. That was a verifier error, not a Claude failure. Its final fixture
uses the production Skill's fork boundary.

Raw controls and each live job's API dumps, strace, transcripts and system
snapshots are privately archived under
`var/run-data/strat-workflow-hardening/`, with exact locations in the linked
repair records. No new binary source carving was needed for these controls.
Other Claude releases, Fullsend/OpenShell execution, full production batches,
strategy quality and statistical reliability remain unqualified here.
