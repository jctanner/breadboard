# S1 rejects a completed refine after a malformed structured return

## Evidence

2026-10-11 tier 2 S1 Haiku batch, Markov `markov-run-02336f23`, S1 pin
`1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43`. Final archive:
`var/run-data/strat-workflow/markov-run-02336f23/20261011T143354300275Z/`.
Job `script-run-workflow-all-claude-haiku-5-5-1011-134802-315418`.

At 13:52:27 UTC the refine helper's Bash result confirms RHAISTRAT-2 is
`Refined`, `refine_count: 1`, and prints `{"recorded": "RHAISTRAT-2"}`.
At 13:52:28.226 UTC its StructuredOutput call instead returns
`{"recorded": "{\"recorded\": \"RHAISTRAT-2\"}"}`. Exact API evidence:
`jobs/<job>/api-dumps/c77fdced-41d7-443f-911f-68e9fb368dab.request.json`
and `2b29c154-5388-4a29-a44e-83dae2e05515.response.json`.
Stream line 49 also records this returned value for agent
`ab209a8d2e29fdb95`, label `refine RHAISTRAT-2`.

## Cause and impact

RECORDED schema accepts any string. The nested JSON string therefore passes
schema validation, but the Workflow's `r.recorded === toRefine[i].strat`
comparison rejects it. Its in-memory refined set omits RHAISTRAT-2 even
though persisted progress records completion. Scoring/review select only
the in-memory ready strategies; RHAISTRAT-2 is excluded. The push script
still pushes all three refined files. Final assembly reports
`refine: RHAISTRAT-2 returned no result; review: RHAISTRAT-2 not recorded`,
and the host validation fails with exit 1.

## Expected

Require a valid strategy key at the structured-return boundary and handle
invalid helper returns explicitly. A successfully persisted refine should
not silently diverge from the Workflow's readiness state. Any recovery
must verify persisted state and the target key rather than accepting
arbitrary nested JSON. Evaluate the intended repair before altering S1.

## Status

Open for the original benchmark pin, which remains unchanged. Detailed
historical evidence is in the evaluation plan.

2026-10-14: focused repair verified on local `eval/s1-hardening`, candidate
`30cf8506d5dbf5b9149971a799e1f3bf5700b7ab`. Assigned-key receipt schemas
reject nested JSON/wrong targets. Completion marks validate saved artifacts;
a fresh disk checkpoint reconciles readiness independently of agent receipts,
and plugin hooks reject invented checkpoint results. Native controls exercise
the original malformed-output class, missing completion and wrong targets
with zero provider calls. One GLM two-ticket fixture recovers an injected
legacy receipt without repeating work; full system/job archive verifies.
This is not an unchanged historical-model rerun or Fullsend/full-batch
qualification. [Repair and evidence](../../notes/s1-hardening-03-refine-receipts.md).
