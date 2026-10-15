# Hardened S1 schemas use top-level oneOf rejected by Anthropic

## Summary

Observed 2026-10-14 in the authorized conditional Opus batch on candidate
`0e7e752702727076818001d3a29208532b40dbab`. GLM completed the same candidate,
but Anthropic rejects the schema before the review step can make a model call.
GLM-only controls did not establish Anthropic schema compatibility.

## Reproduction

Markov `markov-run-687db37c`, job
`script-run-workflow-all-claude-opus-4-6-1014-231007-d5c565`, native
Workflow `wf_03ee11ea-2e4`, Claude Code 2.1.296.

The native progress for `review RHAISTRAT-2` and `review RHAISTRAT-1` at
23:29:37–23:29:38 UTC records:

```text
API Error: 400 tools.9.custom.input_schema: input_schema does not support
oneOf, allOf, or anyOf at the top level
```

Both steps end in 335–342 ms with zero reported tokens and zero tool calls.
The native journal records two failed agents. Successful-response API dumps
contain no corresponding error bodies, so their error count alone misses this
failure. At 23:30 UTC all three strategies had been refined and pushed; the
third scorer was still active. No reviews had been recorded complete.

## Cause and expected behavior

`workflows/strat-pipeline.js` uses top-level `oneOf` in `VERDICT` to relate
recommendation to needs_attention. It also uses top-level `oneOf` in both the
`RESULT` schema and the final inline result schema to relate action/check_exit.
These tool input schemas are not accepted by the tested Anthropic endpoint.
The Workflow should use provider-supported schema syntax while retaining its
deterministic consistency and saved-completion checks.

## Repair

Use plain object schemas with supported property types/enums. Enforce the
cross-field relationships in deterministic validation, retaining the existing
receipt and numeric-decision checks. Keep bundled Workflow copies identical.
Validate request schema compatibility before another paid batch; a fresh paid
Opus retry requires authorization beyond the single attempt already launched.

Fixed on `eval/s1-hardening` at `f3508786a1e2200731b25dfeda7e01ef772d32ce`.
Both schemas are plain objects; explicit JavaScript verdict consistency and
failed-step checks retain rejection after removing the unsupported unions.
The existing final action/check_exit and saved-completion verification remain.
No new hook, helper or agent call. Full suite: 1,005 passed, seven skipped.
A native Claude 2.1.296 loopback control verifies the actual final request
schema, wrong-hash refusal and valid completion, with zero provider calls.
No live Anthropic rerun has qualified this revision yet. The original failed
Opus job and its source/baseline edits remain preserved as evidence.

[Repair and evidence](../../tasks/done/s1-hardening-anthropic-schema-compatibility.md).
[Batch task](../../tasks/done/s1-hardening-three-rfe-glm-opus.md).
