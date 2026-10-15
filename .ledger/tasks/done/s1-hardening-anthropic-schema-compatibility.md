# Anthropic-compatible Workflow output schemas

Status: done. Implemented and pushed on `eval/s1-hardening` at
`f3508786a1e2200731b25dfeda7e01ef772d32ce`, based on `0e7e752`.

Priority requested 2026-10-14: fix this first after the current Opus job ends
and its evidence is archived. Leave the active run unchanged by the operator.

Replace unsupported top-level oneOf in the canonical/bundled Workflow schemas
with supported object properties/enums. Preserve cross-field consistency through
small deterministic checks in the existing Workflow and receipt validators.
No new standalone hook/script or extra agent call should be necessary.

Acceptance: plain provider-compatible tool schema shapes; inconsistent verdict
and action/check_exit pairs still fail; saved numeric/completion verification
remains intact; bundled copies match; relevant controls and required component
suite pass. Include a schema compatibility check before another paid batch.

No additional paid Opus batch is authorized by this repair plan. Existing GLM
single-case testing rules remain; prefer zero-provider controls where sufficient.
The current agent's edits are diagnostic evidence, not an accepted source patch.

## Implementation and verification

Both Workflow copies now send plain object schemas. JavaScript checks that
approve implies needs_attention=false and revise/reject imply true, using exact
boolean comparisons. Existing final checks require completed/check_exit=0 and
a valid current-run receipt. A recorded step failure now prevents a claimed
successful final receipt from completing the Workflow. Numeric scoring and the
saved-artifact/completion validators are unchanged. No hook, helper script or
additional agent call was added.

New tests reproduce eight failures before the patch. The focused schema/control
flow/composition/outcome suite then passes 88 tests; full `make test` passes
1,005 tests with seven skipped in 266.30 seconds. Ruff, bundled-copy parity,
diff checks and staged credential-pattern scan pass. Remote branch SHA was
independently read back after pushing.

One Claude Code 2.1.296 control uses only an authored loopback API. Completion,
native state/journal and reporting agree; the existing hook rejects a fabricated
receipt hash, and reporting recovery preserves completed work. All 93 tool
schemas across six captured requests have object roots without top-level
oneOf/allOf/anyOf, including three StructuredOutput schemas. Provider calls and
inference spend are zero. Capture:
`var/run-data/strat-workflow-hardening/schema-compatibility/20261014/native-completion/`.

Live Anthropic acceptance and another three-RFE batch have not been tested on
this revision. Existing benchmark pins and finalized archives remain unchanged.
Primary-agent source/baseline protection, scorer-path recovery and specialist
format/delivery issues remain separate work. No paid batch was relaunched.

[Fixed schema bug](../../bugs/fixed/strat-workflow-anthropic-top-level-union-schema.md).
[Batch task](s1-hardening-three-rfe-glm-opus.md).
