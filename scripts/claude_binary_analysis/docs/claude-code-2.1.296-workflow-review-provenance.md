# Native Workflow specialist returns: real-run review provenance

Priority 2 of the [production-gap handoff](../../../.ledger/notes/claude-workflow-production-gaps-handoff.md).
Archives are read-only. No benchmark or provider run was launched.

## Findings

The S1 Opus expected Skill handoff loses ten assessments, but this does not make
every published section provenance-free. Its receiving review agent has scorer
reports and strategy inputs. For strategy 1, three published sections closely
reuse scorer material read **before** the specialists launched. The delivered
testability report supplies a fourth section with strong textual fidelity.

S1 GLM demonstrates a different route: the receiving agent explicitly reads
the completed specialists' native JSONL transcripts, extracts earlier assistant
text into `/tmp/reviewer-prose.txt`, and reads that file. Three selected
assessment bodies arrive in full through these tool results; substantial
architecture prose also arrives, but the complete selected body is not observed
as one returned input. Thus all four acknowledgement-only Skill returns have
an observed recovery route, with an architecture completeness limit.

S2 Opus delivers all twelve expected specialist reports and S2 GLM all four.
In these requests, their specialist forks do not have StructuredOutput tools.
All substantive Opus reports still assess the whole batch, despite correct
per-strategy keys in the expanded prompts. Delivery, scope, incorporation and
factual accuracy remain different properties.

## Sources and method

The compact records contain original request/response filenames, timestamps,
generation message IDs, tool IDs, selected text hashes, effective schemas,
target lines, alternate input candidates, published paths and source hashes:

- [S1 Opus: twelve calls](claude-code-2.1.296-workflow-s1-opus-provenance.json),
  `markov-run-c5ba3904`, capture `20261011T175615927646Z`.
- [S2 Opus: twelve calls](claude-code-2.1.296-workflow-s2-opus-provenance.json),
  `markov-run-79d3241a`, capture `20261012T021947729737Z`.
- [S1 GLM: four calls](claude-code-2.1.296-workflow-s1-glm-provenance.json),
  `markov-run-23df27ac`, capture `20261011T232950539833Z`.
- [S2 GLM: four calls](claude-code-2.1.296-workflow-s2-glm-provenance.json),
  `markov-run-428f237a`, capture `20261012T002415035434Z`.

Each API index explicitly pairs request and response filenames with a message
ID; the auditor follows those pairings. S1's task-start events associate exact
expanded skill prompts and fork IDs with launch tool IDs. Child requests are
joined by those prompts, continuing across compaction through unique tool
result IDs or exact captured compact summaries. This recovered strategy 2's
architecture completion after its original prompt disappeared from history.

Other captures lack the same task-start stream in the browsable artifacts;
their initial child joins use role, expanded target and launch/return interval,
then unique tool IDs. These joins have less direct launch identity evidence.
All receiving results themselves are joined by the exact Skill tool ID. No
GLM-to-relay message join is claimed.

Chronology uses API index timestamps. Extracted file mtimes are not used. The
original tar inventory records only the collected artifact/API/strace roots;
it does not establish that every native home-directory transcript or journal
was archived. The GLM receiving tool outputs themselves preserve the observed
transcript recovery, so that conclusion does not depend on an uncaptured
transcript being accessible to this investigation.

For final incorporation, the auditor compares distinct twelve-word fragments
of each selected assessment and each published role section against **incoming
user/tool-result text**, excluding the receiving agent's own assistant output.
This identifies transmission and textual reuse, not semantic truth or perfect
review fidelity. Missing lexical overlap can be a legitimate summary. Candidate
overlaps from common strategy facts do not establish access to a whole report.
Selected assessment means the latest substantive assistant text block, not all
reasoning or every intermediate statement.

## Per-call S1 Opus provenance

Every row has an observed specialist assessment and a completed published role
section. “Not observed” refers to delivery of that specialist assessment through
the expected result or another captured input; it does not mean the section has
no other sources. Full identities and source file hashes are in the JSON record.

| Target | Role | Skill tool ID | Specialist ending | Assessment delivery | Final incorporation/source evidence |
| --- | --- | --- | --- | --- | --- |
| 1 | feasibility | `toolu_01YGFVw3JpzqHHTMDFVDMooe` | prose + StructuredOutput | Not observed | Strategy-1 scorer Read precedes launch; 96.9% of published section fragments present in that input |
| 1 | testability | `toolu_01ABTudEnL5Nxiw6PXc5mC7z` | prose | Delivered | 95.8% of final section fragments present in its Skill return; specific missing tests and revise dissent retained |
| 1 | scope | `toolu_0132HWzzXrMTMuoLc4g6U73A` | prose + StructuredOutput | Not observed | Earlier scorer input covers 89.3% of published section fragments |
| 1 | architecture | `toolu_01UnA5iLQG3DF5GM6bsuu3uy` | prose + StructuredOutput | Not observed | Earlier scorer input covers 90.4% of published section fragments |
| 2 | feasibility | `toolu_01AMgcJVQMsAEJQ9hZJvp9QU` | prose + StructuredOutput | Not observed | Scorer/strategy inputs observed; little verbatim overlap, semantic attribution unresolved |
| 2 | testability | `toolu_01AZUwcraruBrM2chyJ5UcPw` | prose | Delivered | Final section exists; little verbatim overlap, semantic fidelity requires further review |
| 2 | scope | `toolu_013yeNcq331MxyhKidj8P4sj` | prose + StructuredOutput | Not observed | Scorer/strategy inputs observed; semantic attribution unresolved |
| 2 | architecture | `toolu_01Xgum13daJtGTkvBV9iB2mE` | prose + StructuredOutput | Not observed | Completion joined across compaction; scorer inputs observed, semantic attribution unresolved |
| 3 | feasibility | `toolu_018xnSY7eY8eyVfw3G1MZNsx` | prose + StructuredOutput | Not observed | Other review/strategy inputs observed; semantic attribution unresolved |
| 3 | testability | `toolu_01JV43n5Nykuk76sy4ySnYYb` | prose + StructuredOutput | Not observed | Final testability dissent exists, but its source cannot be attributed to the missing specialist body |
| 3 | scope | `toolu_01EQD3e7WrXBRbrXSHAEW5zV` | prose + StructuredOutput | Not observed | Section exists; no full alternate specialist delivery observed |
| 3 | architecture | `toolu_018LzYL9UyWQ1RFKqNyinYrw` | prose + StructuredOutput | Not observed | Scorer report accessed later in review work; semantic attribution unresolved |

All ten tool-ending calls return only the acknowledgement through Skill. The
same effective review/status schema is present in their forks and receiving
agents. The two text-ending calls deliver substantive bodies. This archive
pattern matches the [twenty-control reproduction](claude-code-2.1.296-workflow-specialist-handoff.md).

## Affected specialist and positive control examined in detail

**Strategy 1 feasibility:** the specialist's response raises a routing ambiguity:
the notebooks BFF manages Workspace/WorkspaceKind, so legacy Notebook annotation
writes need a clarified core-BFF/legacy route. It also discusses shared controller
utilities, cross-team risk and Event TTL. The final feasibility section agrees
on approval but says there are no feasibility concerns and omits that explicit
routing clarification.

The receiving agent already read `/tmp/strat-assess/RHAISTRAT-1/RHAISTRAT-1.result.md`
through `toolu_01KFAXhXCfoYYAJ2S8uC118c`. The corresponding API response is
`6ccce7ac-b98b-4154-94c2-2221c9743f27.response.json`, timestamp
`17:24:00.786Z`; the specialist launch is `17:24:34.888Z`. The original scorer
generation `13dec14d-2dc5-4260-bee3-b034dbdf6f05.response.json` is captured at
`17:23:09.897Z` in the same job. The published section's effort breakdown,
dependency list and mitigation language closely follow that scorer input.
These are **within-run earlier scorer records**, not evidence of resurrecting
an old run's review. A later reread of the newly published strategy-1 review is
also present and must not be mistaken for pre-composition specialist delivery.

This supports an inference of scorer-based backfill while the distinct
specialist assessment was not observed in receiving inputs. It does not support
labeling the published prose fabricated, or claiming that every shared factual
concern was unavailable to the review agent.

**Strategy 1 testability:** the specialist report is delivered through
`toolu_01ABTudEnL5Nxiw6PXc5mC7z`. It identifies missing UI verification,
per-namespace limit enforcement, Event audit tests, Notebook/Workspace parity
and a direct non-exemption culling test. The final section preserves these
specific concerns and its revise recommendation, with minor formatting and
wording changes. This is a positive incorporation control. The overall final
approve verdict is not evidence of unanimous specialist approval.

The remaining rows document sources and uncertainty individually. A complete
independent semantic/factual review of every sentence is not established by
fragment matching, artifact cardinality or final model verdicts.

## S1 GLM: explicit recovery after missing expected returns

All four specialists use StructuredOutput and their Skill results carry
acknowledgements. The receiving review agent then locates native files under
the run's `.claude/projects/.../subagents/` directory and identifies the role of
each agent. At `23:25:10.006Z` it issues a Bash tool command that scans the four
JSONL files for the last nonempty assistant text block and writes the collected
role reports to `/tmp/reviewer-prose.txt`.

That command is in `b1fc1fed-04ce-4114-b83c-af7686eab6d9.response.json`, paired
with `8de8afec-35a4-4e2d-820b-fa877221cac5.request.json`. Its output arrives in
the receiving model request `6e700ce6-2dda-466e-9c74-46bdbfaee476.request.json`.
The subsequent Read of the collection uses `chatcmpl-tool-97e322c7fd75dda3`,
recorded in `48c91a38-199e-4270-8896-e953df8785a2.response.json`; its content is
present in `1ce42405-6b98-4dfd-9dd0-f5da6daed4b7.request.json`.

| Role | Expected Skill return | Alternate delivery observed | Published section evidence |
| --- | --- | --- | --- |
| feasibility | Acknowledgement | Full selected prose in transcript-extraction Bash output | Final section fragments fully present in that input |
| testability | Acknowledgement | Full selected prose in Read of the recovery file | Final section fragments fully present in that input |
| scope | Acknowledgement | Full selected prose in Read of the recovery file | Final section fragments fully present in that input |
| architecture | Acknowledgement | Substantial prose in the recovery Read; full selected body not observed | 94.5% of final section fragments present in the recovery input |

The architecture completeness limitation and the missing structured fields
remain material. Recovering earlier text does not itself recover every field of
the specialist's StructuredOutput input. In particular, the final aggregate
attention flag cannot be attributed to an intentional override merely because
it differs from a specialist's structured flag.

This is a demonstrated alternate model-visible delivery path, not merely host
storage. It is also an ad hoc model-authored recovery action tied to private
transcript paths, not a guaranteed Skill return API or a durable integration
contract. It shows why the original gate outcome and actual provenance should
both be retained when evaluating the run.

## Implication for production advice

The expected nested return boundary is faulty for these tool endings, and
target-scope validation is still missing. Native Workflow's scheduling does not
explain either by itself. S1 GLM can recover text explicitly; some S1 Opus
sections have alternate scorer provenance. S2 delivers its expected prose but
shares the scope problem. These findings weaken any blanket claim that S1
publishes invented reviews or that an external shell automatically solves the
harness result mismatch.

An integration should persist and validate each role's target, assessment and
dissent before composition, record which source supplied each final section,
and check aggregate disagreements explicitly. Direct schema assessment calls
or validated persisted report files provide an inspectable contract. Native
Workflow can coordinate those calls; an external runner can coordinate them
too. Recovery/cancellation/limits/retries still need their own evidence before
choosing the durable production execution boundary.

## Verification

The [read-only auditor](../audit_workflow_review_provenance.py) and
[archive verifier](../verify_workflow_review_provenance.py) check thirty-two
calls, effective schema inheritance, exact return IDs, source hashes and
published section presence. Full compact records retain separate delivery and
incorporation fields. They deliberately leave semantic fidelity unresolved
where the evidence is insufficient. No archive, benchmark pin, live service,
pipeline implementation or published issue was modified.
