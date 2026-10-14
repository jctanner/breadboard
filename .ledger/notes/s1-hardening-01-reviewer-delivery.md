# S1 repair 1: reviewer delivery

2026-10-13. [Plan](../plans/strat-workflow-s1-hardening.md).

## Candidate

Local emulator repository `opendatahub-io/strat-creator`, branch
`eval/s1-hardening`, commit `c49b43c4eeccefc69ea402539430406e1877909e`.
Base `eval/pr-83` remains `1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43`.

The four reviewer Skills select `strat-reviewer`. That agent explicitly offers
Read, Grep and Glob and returns the assessment as prose. Its tools exclude
StructuredOutput. Plugin registration and Fullsend vendoring include the new
definition; the receiving Workflow status schema is unchanged.

## Offline/native checks

The component suite passed: 835 tests, 7 opt-in tests skipped. The updated
Fullsend host integration check verifies the exact reviewer definition reaches
the consumer repository. Shell/Python checks and diff checks passed.

One native 2.1.296 handoff control copied the actual candidate agent definition,
pinned even its mock model requests/aliases to GLM, and offered the original
schema to the receiver. The effective reviewer tools were exactly Read/Grep/Glob,
with no schema tool. Assessment, dissent and target markers reached the receiver
through the Skill result; the parent retained its outer schema and the Workflow
completed. Six stub requests, one execution, zero provider calls. Working captures
are under ignored `tmp/s1-hardening-01/mock-delivery` pending archival.

## Single GLM scenario

One direct Breadboard job submitted at 2026-10-13T22:52:26Z:
`script-run-all-glm-5-3-1013-225226-784455`.
Source is the candidate commit above. MLflow experiment:
`strat-workflow-hardening/01-reviewer-delivery/glm`.

The exact primary/helper/alias model is `rits/zai-org/glm-5-3`, medium effort,
with strace and raw API capture enabled. The focused test calls the real four
Skills once under the same outer review-status schema. Inputs are small authored
strategy/RFE/architecture files, rather than historical internal/customer data.
No Jira issue is created/reset or updated; no scoring, strategy generation or
publication is requested. No whole-job retry or premium-model test is authorized.

Host collector is waiting for terminal status, then collecting and verifying
available system evidence under
`var/run-data/strat-workflow-hardening/01-reviewer-delivery/<job>/<capture>`.
Direct-job archival support records actual dashboard provenance without inventing
a Markov run; the reset guard also recognizes the hardening experiment labels.
The eleven archive tests pass. Fullsend sandbox integration and full pipeline
qualification remain separate from this focused boundary test.

## Final GLM result

Completed at **2026-10-13T23:02:23Z**, about **9 minutes 57 seconds** after job
creation. Claude Code is **2.1.296**; CLI exit zero. The persisted native Workflow
is completed with `{"key":"RHAISTRAT-9001","recommendation":"revise",
"needs_attention":true}`. Its outer status schema worked. Binary SHA-256:
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`, matching
the pinned binary used in the diagnosis and stub control.

The independent delivery verifier passed with no errors:

| Role | Launches | Assessment characters in receiving request | Delivered |
| --- | ---: | ---: | --- |
| Feasibility | 1 | 7,771 | Yes |
| Testability | 1 | 8,325 | Yes |
| Scope | 1 | 5,076 | Yes |
| Architecture | 1 | 4,814 | Yes |

All 21 captured specialist requests offered exactly Read, Grep and Glob. None
offered StructuredOutput. All **50 request/response pairs** used the exact hosted
GLM request ID. The four assessments are present in the receiving model's actual
Skill results; this does not rely on model claims or recovery from transcripts.
There was one live scenario execution, no repeated role launch, and no Haiku or
Opus inference. This is a focused repair check, not a full pipeline or batch run.

Reported provider usage: 91,906 input tokens, 645,632 cache-read input tokens,
zero reported cache-creation tokens and 41,842 output tokens. The combined
reported categories total 779,380 tokens. GLM pricing/category semantics are not
verified here; no dollar estimate or Claude client fallback price is used.

## Final archives

The live capture independently verifies with `complete=true`, `final=true`,
`errors=[]`; its final checksum-backed receipt is published. Root:

`var/run-data/strat-workflow-hardening/01-reviewer-delivery/script-run-all-glm-5-3-1013-225226-784455/20261013T230234593031Z/`

It contains **16 sources, 553 files and 1,224,099,833 bytes**, including 101
browsable API files, 348 strace files, native transcripts/state/journal, the exact
candidate source archive and delivery verification, MLflow/Jira/Observatory
snapshots, readable Jira export, service logs and relay telemetry. Shared-service
snapshots cover the collection interval; they are not one atomic system snapshot.

The stub control and launch metadata have a separate verified private capture:
`var/run-data/strat-workflow-hardening/01-reviewer-delivery/native-control/20261013T231239368875Z/`.
Earlier captures were not overwritten. Credentials were not committed or printed.

## Status and limits

Item 1's focused repair is complete on the local hardening branch. This verifies
the project/vendored Skill configuration and the actual result boundary on the
tested binary. Fullsend sandbox execution, namespaced interactive-plugin use,
full pipeline operation, batch target isolation, final incorporation and content
accuracy still need their own checks. Historical branches remain unchanged.
The reset guard's new experiment matching passes offline; deploying that guard
into a newly imported Markov source is separate from the host collector used here.

The component's 835 tests passed (7 opt-in tests skipped). Breadboard benchmark
checks passed: 31 tests, including archive and delivery checks, with six unrelated
Markov-binding tests skipped. No additional model scenario is implied by those
offline tests. Next priority: item 2, per-strategy reviewer scope.
