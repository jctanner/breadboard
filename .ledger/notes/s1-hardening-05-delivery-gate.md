# S1 repair 5: assessment delivery gate

2026-10-14. [Plan](../plans/strat-workflow-s1-hardening.md).

## Repair

This item repairs Breadboard's benchmark checker. S1's source remains on
`eval/s1-hardening` at `7cfcadaa51b752792011c106e1a2aa27b7c65529`.
Numeric scores remain the sole production approval gate. No model run,
deployment, reset or Jira write is needed to test this deterministic checker.

`check_run.py::reviewer_returns` now uses the shared `role-assessment-v1`
contract in `review_assessment.py`. It requires a real receiving user tool
result matched to a single-target forked Skill launch, an identifiable assigned
strategy section, a completed judgment for the requested role, one completed
recommendation, and explanatory role content. It rejects completion markers,
progress/error returns, empty reports, heading/verdict-only text, unfilled
templates, role/target substitutions and conflicting versions of one tool ID.
Repeated identical conversation histories are still counted once.

There is no whole-report character threshold. An explanatory clause has a
transparent minimum of six words; supporting fields or a Findings/Rationale
section can supply it. This is a mechanical content contract, not a semantic
guarantee that those words are substantive or technically correct. The tests
include short valid reports, grounded no-concern conclusions, legacy formatting,
and genuine findings about connection errors. Quoted API placeholders inside
an actual review do not turn it into an unfilled report template.

An intentional architecture skip is recorded as `skipped`, never as a delivered
assessment. It fails the benchmark's four-assessment coverage requirement; it
does not change the production numeric policy or its existing skip behavior.
Delivery identifies the requested section. Other strategy headings are recorded
through `exclusive_report_target`, separately from delivery. A whole-batch review
can contain a real assigned assessment and still fail the separate scope check.
Final incorporation and technical accuracy remain separate checks too.

The focused delivery and scope verifiers share this content contract. The
manifest-driven binary-analysis checker continues to verify complete declared
reference reports or authored fragments independently.

## Historical replay

`replay_delivery_gate.py` reads archived API channels and the expected strategy
inventory from the original evaluation. Focused diagnostics without an evaluation
require explicit independently known keys; launches never define completeness.
It saves the original gate, original overall pass/fail and a separate recomputed
gate with pair-level reasons and input hashes. It refuses to write inside the
original capture or overwrite an existing result. Outputs have private file
permissions. Historical evaluation records and archives are unchanged.

| Saved case | Original returned pairs | Recomputed assessments | Expected |
| --- | ---: | ---: | ---: |
| S1 Opus batch with stream error, `markov-run-7845a7f1` | 1 | 0 | 12 |
| S2 Opus batch stopped by quota, `markov-run-6bcb3c32` | 8 | 7 | 12 |
| Completed S1 Opus batch, `markov-run-c5ba3904` | 2 | 2 | 12 |
| Completed S2 Opus batch, `markov-run-79d3241a` | 12 | 12 | 12 |
| Focused GLM delivery repair, `script-run-all-glm-5-3-1013-225226-784455` | Not recorded by this benchmark gate | 4 | 4 |
| Focused GLM scope repair, `script-run-all-glm-5-3-1014-004354-220e59` | Not recorded by this benchmark gate | 12 | 12 |

The two known false positives now fail: S1's architecture error for RHAISTRAT-3
and S2's architecture progress message for RHAISTRAT-1. The overall historical
benchmark outcomes do not change. The aborted scope launcher is also retained
in the draft inspection inventory; it delivered no reports and is not a successful
review scenario. None of these replays constitute new model trials.

Full normalized reference checks independently reproduce 2/12 for the completed
S1 Opus batch and 12/12 for completed S2. The stronger focused delivery/scope
verifiers also pass against their original GLM captures. This verifies the new
checker against actual returned text, not only authored unit fixtures.

## Validation and evidence

Benchmark suite: **62 passed, six unchanged optional Markov orchestration tests
skipped** (68 total). Independent reference-checker suite: **nine passed**.
Python compilation and diff checks pass. New fixtures cover non-assessments,
role/target attribution, intentional skips, separate scope reporting, receiving
channel identity, conflicting histories and immutable replay behavior.

The six original captures are fully checksum-verified before replay, and their
manifest hashes remain unchanged afterward. The new private evidence capture
retains exact checker/test sources, replay commands/results, original archive
verification logs, independent reference checks and test output. Its final
location is:

`var/run-data/strat-workflow-hardening/05-delivery-gate/controls/20261014T144916473604Z/`

All **53 files, 1,890,673 bytes** verify against its final manifest. Manifest
SHA-256: `155af417a0dca65192f6195c04d13eeb234cbcfbf2ee01eac0c5ccf53588f031`.

Provider calls: **0**. Additional inference tokens: **0**. No new strace, API
calls, service logs or MLflow run were created; the replays reference the original
complete system archives. No Claude binary change or new binary behavior is
claimed. The first evidence-runner attempt selected the seed job instead of the
design job and stopped before a replay; its log is retained. The corrected
runner selects the job carrying the archived evaluation. A second draft selected
the earlier aborted scope launcher based on CLI exit zero; it failed the expected
12-report assertion. The final runner uses the exact successful fixture job ID.
Those runner errors and draft results are retained, not counted as model trials.

## Status and limits

Item 5's deterministic checker repair is implemented in Breadboard's working
tree. Future deployed benchmark runs need to pin the updated Breadboard source;
this task does not publish unrelated root changes or alter historical pins.
This is a delivery/format check, not content judging, final incorporation proof
or a statistical reliability result. Item 6 remains pending.
