# S1 reviewer Skill forks complete without returning their prose

## Evidence

Known tier 1 finding reproduced in the 2026-10-11 tier 2 S1 Haiku batch,
Markov `markov-run-02336f23`, S1 pin `1bd7f17`. Final archive:
`var/run-data/strat-workflow/markov-run-02336f23/20261011T143354300275Z/`.
Job `script-run-workflow-all-claude-haiku-5-5-1011-134802-315418`.
Its browsable `artifacts/eval-result.json` joins reviewer calls and parent
tool results: **14 of 16 reviewer Skill launches** return only
`Skill execution completed`, with zero reviewer-result characters.
Each of RHAISTRAT-1 and RHAISTRAT-3 has three roles returning no text on
both attempts, plus one role whose first attempt returns no text.
Only feasibility for RHAISTRAT-1 and scope for RHAISTRAT-3 return prose.
RHAISTRAT-2 receives no dedicated review due to the separate refine return
mismatch. API dumps and final review files preserve these missing returns.

## Impact and limits

Repeated reviewer work consumes requests/time while its output is unavailable
to the parent review agent. Final reviews use numeric scorer results and
explicitly note missing prose. The tier 2 reviewer-output gate fails even
for the two strategies with recorded reviews. Both have revise 4/8 scores;
revise verdicts themselves are valid outcomes and do not cause job failure.
This run confirms the return failure; the underlying Claude Code Skill/fork
behavior remains a separate implementation diagnosis. Do not attribute it
to relay loss: captured relay health has zero dropped requests/events and
zero storage errors.

## Status

Open; reproduced from prior tier 1 investigations. No S1/S2 change or rerun.

## 2026-10-11 Opus batch reproduction

`markov-run-7845a7f1` finished after 71.8 minutes with completed S1 job,
three APPROVE reviews and all other checks passing. The reviewer-return
gate still fails: 11/12 Skill results are empty completion markers; the
remaining RHAISTRAT-3 architecture result is a connection-error string.
The detector incorrectly labels that error as a returned review because
it is nonempty. No substantive specialist review is demonstrated by these
tool-result bodies. Final review documents do contain prose, so inspection
of alternative recovery paths is still needed before claiming the parent
had no access to specialist work. Final verified archive:
`var/run-data/strat-workflow/markov-run-7845a7f1/20261011T162230677725Z/`;
see S1 `artifacts/eval-result.json`, `artifacts/workflow/stream.jsonl` and
`artifacts/repo-artifacts/strat-reviews/`. No design change or rerun.

## 2026-10-11 reproduction after relay repair

`markov-run-c5ba3904`, job
`script-run-workflow-all-claude-opus-4-6-1011-170435-3f61ed`, completed
with all runner exits zero and three APPROVE verdicts. Relay has zero
request failures and seven complete streams beyond 120 s. Nevertheless
**10 of 12** specialist Skill calls still return only completion markers.
Only testability calls launched for RHAISTRAT-1 and RHAISTRAT-2 return
prose (15036 and 11317 characters), each covering all three strategies.
No specialist retry is recorded by the gate. The sole failed benchmark
check remains reviewer_outputs_returned. This separates the persistent
return failure from the repaired relay timeout. Scope drift has its own
bug; the underlying missing-return implementation remains to diagnose.
Verified final archive:
`var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z/`.

## GLM reproduction (single-RFE S1, 2026-10-11)

During authorized GLM run `markov-run-23df27ac`, job
`script-run-workflow-all-glm-5-3-1011-224849-152aa2`, all four reviewer
Skill results are acknowledgement-only: feasibility/testability 100 characters,
scope 94, architecture 101, ending `Skill execution completed`. At about 37
minutes the requests contain nine deduplicated StructuredOutput calls. No API
errors and every model request uses the exact GLM ID. This reproduces the
return-loss mechanism with another provider/model; transport compatibility does
not repair PR #83's reviewer contract. Final outcome/archive remains pending.

GLM run is now final: single-RFE smoke PASS / APPROVE 6/8, 40.4 minutes,
11 StructuredOutput calls overall. All four specialist schemas say approve;
feasibility also sets needs_attention=true, while the final review helper returns
false. None of these structured leaf fields or assessments arrive through the
Skill acknowledgements; do not infer an intentional flag override alone.
The manual reviewer-return gate fails despite smoke pass. Complete verified
archive: var/run-data/strat-workflow/markov-run-23df27ac/20261011T232950539833Z/.
S2 GLM returns four substantive reports and has zero StructuredOutput calls.

## 2026-10-12: Binary diagnosis and alternate-delivery audit

Pinned2.1.296 mock controls reproduce the loss with both Workflow schema agents
and ordinary CLI --json-schema. The Skill fork inherits StructuredOutput/schema
and its final-response instruction, then selects last-assistant text rather
than the structured attachment or earlier assessment. Twenty matrix cases
establish tool-ending acknowledgements versus prose-ending delivery. A custom
Skill agent whose explicit tools exclude StructuredOutput delivers prose while
the receiver keeps its outer schema; this is a verified configuration workaround,
not a deployed fix. [Diagnosis](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-specialist-handoff.md).

Correction to interpreting the GLM return gate: four expected returns are still
missing, but the receiver explicitly recovers earlier prose by reading native
transcripts through Bash/Read. Three selected bodies arrive in full and
substantial architecture text arrives with a completeness limit. Some S1 Opus
published sections have earlier scorer provenance. Thus expected handoff loss
does not prove all findings were unavailable or the final prose fabricated.
The issue remains open; no pipeline or target binary was modified.
