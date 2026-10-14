# Claude Code 2.1.296: schema tools and missing forked Skill results

Priority 1 of the [production-gap handoff](../../../.ledger/notes/claude-workflow-production-gaps-handoff.md).
The unmodified pinned Linux binary matches SHA-256
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.

## Finding

The missing specialist handoff has a deterministic reproducer. A schema-bearing
receiving agent's forked Skill inherits its StructuredOutput tool and the same
schema. When the specialist ends by calling that tool, the forked Skill's return
selects the last assistant record's text, which is empty, and substitutes
`Skill execution completed`. The specialist's structured fields and earlier
assessment/dissent text do not enter the receiving model through that result.

This also reproduces with ordinary CLI `--json-schema`, without Workflow.
Workflow scheduling and parallelism are therefore not necessary causes. The
boundary is a mismatch between schema-oriented termination and a text-oriented
forked Skill return. The model chooses the tool-ending response, influenced by
the inherited tool description; prose-ending controls deliver the report even
when the StructuredOutput tool remains available.

Twenty deterministic matrix controls vary ordinary CLI versus Workflow, outer schema
absent/present, direct versus forked completion, and result form. They run only
against a local API stub, with authored skill/target/assessment/dissent markers.
The [verified controls](claude-code-2.1.296-workflow-handoff-controls.json) retain
actual receiving requests and persisted workflow outcomes.
An additional control verifies an explicit specialist tool whitelist workaround.

| Context / specialist ending | Ordinary CLI | Workflow |
| --- | --- | --- |
| No outer schema; fork returns prose | Assessment, dissent and target delivered | Same |
| Outer schema; fork returns prose | All three markers delivered | Same |
| Outer schema; fork calls StructuredOutput only | Completion acknowledgement; no marker delivery | Same |
| Outer schema; one wire response has prose then StructuredOutput | Completion acknowledgement; prose lost from Skill return | Same |
| Outer schema; earlier prose/Read, then StructuredOutput | Completion acknowledgement; earlier prose lost | Same |
| Direct structured completion, without Skill fork | Valid structured result | Valid structured result |
| Direct prose only, with outer schema | CLI success without structured_output in this control | Workflow agent fails after missing-output nudge |

The last row is a separate validation boundary: checking CLI exit/subtype alone
does not establish schema-constrained output. An external caller must verify the
actual structured result it expects. A successful Workflow can likewise contain
business-level missing reports if the receiving agent supplies a valid outer
status object after the acknowledgement-only specialist results.

## Exact code path

[Nine exact symbols](claude-code-2.1.296-workflow-handoff-symbols.json) give byte
ranges/hashes in the extracted `.bun` payload. The complete source remains
ignored; these are original descriptive reconstructions.

```text
Workflow schema agent:
    construct validated StructuredOutput tool from schema
    include that tool in available tools
    run SA with requiresStructuredOutput = true
    collect structured_output attachment as this agent's result

forked Skill preparation (YKt):
    expand the skill prompt with its arguments
    derive available tools from the receiving agent's tools and skill rules
    create a fresh skill conversation and file-read state

forked Skill execution (Re in the SkillTool module):
    run SA with those available tools
    do not pass a requiresStructuredOutput override
    collect child events in W
    result = artifact-provenance note + XKt(W, "Skill execution completed")

XKt:
    select last assistant record using Cy
    extract/join text from that record
    return extracted text, or the completion fallback if empty
```

`Re` is `[134621902,134626110)`, `Fe` (Skill dispatch) is
`[134627392,134630887)`, `YKt` is `[129014187,129017174)` and `XKt` is
`[129017501,129017604)`. Workflow `kr`/`vr` and generic `SA` establish the
schema tool installation and per-run options. `SA` sets
`requiresStructuredOutput` from the explicit argument, rather than automatically
preserving the parent's requirement. Therefore **tool/schema inheritance is
confirmed; inheritance of a mandatory termination flag is not the cause**.

The decisive captures also record effective StructuredOutput instructions:
the inherited tool description says to use it for the final response. The
specialist's user prompt is the expanded authored Skill, including its correct
target. The controls do not depend on a model following that instruction; the
stub supplies each ending deliberately to isolate result handling.

In the streaming mixed-response control, the persisted child transcript has a
text assistant record followed by a tool-only assistant record. The selector
uses the latter, even though one API response carried both blocks. The same
wire-ending pattern appears in the affected real Opus calls. Earlier text
remaining on disk or in host events is distinct from text delivered to the
receiving model.

## What this explains in the real runs

The [archive provenance report](claude-code-2.1.296-workflow-review-provenance.md)
joins all twelve S1 Opus calls through captured task-start prompts, API pair
indexes and unique tool IDs. All ten acknowledgement-only specialists finish
with StructuredOutput; the two delivered testability reports finish with text.
The specialists have the same outer review/status schema available. S2 Opus
specialists have no StructuredOutput tool in the inspected requests and all
twelve return prose. S1 GLM reproduces the tool-ending acknowledgement, but its
review agent explicitly recovers report text from saved transcripts afterward.

The real expanded specialist prompts contain the supplied per-strategy key.
Whole-batch scope drift therefore cannot be attributed to those arguments being
silently absent. The wording directs the model to review only the supplied key
while also offering directory-wide inputs; enforcing target scope remains a
separate integration/model-behavior concern.

## Supported remedies and limits

- A Skill can select a custom `agent:` whose explicit `tools:` whitelist excludes
  StructuredOutput. The additional control uses a Read-only specialist: its
  request offers only Read, its assessment/dissent/target return through Skill,
  and the receiving Workflow agent retains and successfully uses its outer
  StructuredOutput schema. A real specialist needs its own required tools in
  that whitelist and still needs output/scope validation. This fixture is a
  supported configuration workaround, not a deployed strategy fix.
- A direct schema agent returning the actual specialist assessment object avoids
  this nested text projection; positive direct controls validate that route.
- A prose-ending specialist delivers through the current Skill boundary. Merely
  requesting prose is not a hard guarantee while an inherited tool instructs a
  structured ending; the capture must validate what actually arrived.
- Explicit persistence/reading of the assessment can recover it. S1 GLM provides
  archive evidence for this route, with completeness limits. Ad hoc inspection
  of private transcript layout is a fragile production adapter.
- A caller can validate role, target, assessment and dissent before composition
  and reject/retry acknowledgement-only results. Nonempty status/error strings
  are insufficient, as the existing benchmark-gate bug already demonstrates.

No target-binary patch, strategy implementation change, deployment or paid run
was performed. This evidence narrows the production concern to an observable
result-contract boundary shared by CLI and Workflow. It does not establish that
native Workflow scheduling is defective or that shell orchestration fixes the
same nested Skill contract automatically. Recovery, cancellation, budgets and
retry advice will be assessed separately in the remaining production controls.

## Reproduction

Subsequent [S1 hardening controls](claude-code-2.1.296-workflow-hardening-controls.md)
verify the configured-agent remedy in the actual repair and exercise reviewer
scope and refinement receipts. Their separate GLM validation follows this
original mock-only investigation.

```bash
python3 scripts/claude_binary_analysis/run_workflow_handoff_experiments.py \
  tmp/claude-code-binary-analysis/2.1.296/input/claude \
  tmp/claude-code-binary-analysis/2.1.296/traces/handoff-reproduce-new \
  --route workflow --schema --completion fork --mode structured
```

Use a new directory each time. Changing `--mode prose` gives a positive delivery
control; `--route cli --schema` reproduces outside Workflow. The
[runner](../run_workflow_handoff_experiments.py),
[mock response helper](../mock_api_support.py) and
[verifier](../verify_workflow_handoff_controls.py) retain fixture Git/tree hashes,
runner/helper snapshots, actual offered schemas, scoped instructions, child
messages, Skill results and persisted outcomes. Mock token values are not real
usage. Compaction, remote Skill execution and other binary versions are outside
this matrix.
