# Workflow comparison: reproduction and delivery-check evidence

Evidence date: 2026-10-12. This is a controlled mock reproduction and read-only
replay of existing benchmark data. No paid strategy run, deployment, reset or
baseline modification was performed.

## R2: current installed release

The installed executable reports Claude Code 2.1.296 and matches the original
binary SHA-256 `24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`.
This is a new run on the same release, not evidence about newer releases.

The `workflow/schema/fork/earlier-prose` control supplies an authored assessment,
dissent and target, then a neutral Read, then a StructuredOutput ending. The
specialist has the parent's schema available. Its native transcript preserves
the earlier report; the receiving Skill tool result is only
`Skill execution completed`, with none of the authored report markers.
The outer Workflow completes and the CLI exits zero; the mocked receiver's
result explicitly records that assessment and dissent were not delivered.

Seven mock API requests were captured. This confirms the projection behavior
for the prescribed ending, not how often a real model chooses that ending.
The exact skill, schema, mock response blocks, packaged receiving result,
native transcript, journal and terminal state are retained.

## R3: manifest-driven delivery assertion

[check_specialist_delivery.py](../check_specialist_delivery.py) accepts an input
manifest of expected strategy/role/tool-ID pairs. Each pair declares either a
hashed reference report or required authored fragments. It checks only the
receiving result channel; it does not use transcript recovery to fill a missing
result. The paired-API adapter joins actual Skill launch IDs to tool results in
user messages. Repeated histories are deduplicated.

For these archive replays, hashed reference reports are the complete selected
specialist assessment bodies identified by the existing provenance audit. Their
hashes are checked against `assessment_sha256` before creating the manifest.
The expected pair set is independently checked against the three strategy keys
in archived evaluation records and the four required roles; observed launches
alone do not define completeness.
The check requires the full normalized reference text inside the actual return,
not merely nonempty text, a status string or a mention of the role.

| Archived design | Required reports | Complete normalized reports in expected returns | Checker exit |
| --- | --- | --- | --- |
| Native Workflow, repaired Opus batch | 12 | 2 | 1: failed contract |
| Scripted Pipeline, completed Opus batch | 12 | 12 | 0: passed contract |
| R2 authored mock fixture | 1 | 0 | 1: failed contract |

An error result, conflicting result versions, wrong launch identity, missing
report text, unexpected result ID or missing expected pair fails. Empty manifests,
empty assertions, duplicate expected identities and changed reference-file hashes
are rejected as invalid inputs. System reminders cannot satisfy report assertions.
Nine focused tests cover those boundaries and paired-file extraction.

Text normalization follows the archive auditor: lowercase ASCII word/path tokens
joined with spaces. This tolerates formatting changes; it does not establish
byte-for-byte fidelity. Nor does a report's arrival establish correct target
scope, final incorporation, factual accuracy, or future reliability. Authored
fragments check only those fragments; the full-report mode used for this pair
has the stronger declared contract. All referenced reports are selected final
assessment text, not the complete intermediate conversation.

## Reproduction commands

The archived manifests and reports contain private benchmark text and remain
outside git. From the Breadboard root, the replay command is:

```bash
python3 scripts/claude_binary_analysis/check_specialist_delivery.py \
  var/run-data/claude-workflow-hardening/20261012-r2-r3/r3/r3-s1-opus/manifest.json \
  --api-dir var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z/jobs/script-run-workflow-all-claude-opus-4-6-1011-170435-3f61ed/api-dumps
```

The corresponding Scripted Pipeline manifest is `r3/r3-s2-opus/manifest.json`; its
source job is identified in the evidence JSON. Exit 1 is the expected observed
delivery failure, not a verifier malfunction. For authored controls, supply
`--channels` with an `observations` array of strategy, role, tool_use_id, content
and is_error, instead of `--api-dir`.

## Archive and provenance

[Compact evidence record](claude-code-2.1.296-benchmark-hardening-evidence.json)
links the original API indexes and audit records, the generated manifests and
checker outputs, the current-version invocation and transcript, and their hashes.
The private final archive is
`var/run-data/claude-workflow-hardening/20261012-r2-r3/`: 92 files, 934,213 bytes,
with every file independently checked against `manifest.json`. It mirrors the
mock control and the private reference/check inputs, including the manifest
generator. Original benchmark archives are unchanged.

R1 is [pre-registered](../../../.ledger/plans/strat-workflow-matched-concurrency-retest.md)
but has not run. It proposes a fresh sequential Native Workflow/Scripted Pipeline
pair on common pinned infrastructure. Neither matched-concurrency cost nor
parallel-execution safety is established by R2/R3.

## Follow-up: benchmark gate repair

On 2026-10-14, S1 hardening item 5 replaced Breadboard's nonempty-return detector
with a shared completed-assessment contract. It checks the requested section,
role judgment, recommendation and explanatory content in the receiving channel.
Errors, progress and completion markers fail; skips and exclusive scope are
recorded separately. This is checker work, with no new Claude binary invocation.

Read-only replay preserves original gate/pass values. It rejects both known
false positives and accepts the real GLM repair reports (4/4 and 12/12).
Completed Opus replays remain 2/12 for S1 and 12/12 for S2, matching the unchanged
full-reference checker above. These counts still do not grade accuracy, final
incorporation or exclusive scope.
[Contract, tests and checksum-verified private evidence](../../../.ledger/notes/s1-hardening-05-delivery-gate.md).
