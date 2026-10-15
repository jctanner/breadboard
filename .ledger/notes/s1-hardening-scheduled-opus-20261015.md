# Scheduled S1 Opus batch, October 15

Schedule #6 fired once at 00:30 America/New_York (04:30 UTC), creating
`markov-run-dd4a838118bd23d18c693b01`. The model job was
`script-run-workflow-all-claude-opus-4-6-1015-043012-dff80e`.

| Measurement | Observed result |
| --- | --- |
| Model job | 00:30:12 to 01:06:40 New York; 36m28s |
| Markov orchestration | 04:30:00.890 to 05:06:48.213 UTC; 36m47s |
| Native Workflow | 34m19.336s, one execution |
| Sources | Breadboard 5ed4a28494bcbb0d3fed31cbe985bca16fc49cc0; strat-creator f3508786a1e2200731b25dfeda7e01ef772d32ce |
| Outer agent cap | Five |
| Business result | Three strategies completed, one review each, all locks released |
| Recorded scores / verdicts | 8/8 approve, 8/8 approve, 6/8 approve |
| Provider calls | 284 captured Opus requests and responses, no API errors or 429s |
| Tokens | 335 uncached input; 1,457,842 cache creation; 8,898,359 cache reads; 156,562 output |
| Total usage | 10,513,098 tokens; 50,903 thinking tokens already included in output |
| API-equivalent cost | $17.48 using the report's $5/$6.25/$0.50/$25 per-million Opus rates; not an OAuth invoice |
| Pinned benchmark | FAIL on reviewer_outputs_returned only; nine other checks pass |
| Independent handoff audit | All 12 actual parent returns match the saved reports; all 12 preserved verbatim in published reviews |

## Why the benchmark is red

RHAISTRAT-3's architecture report starts its judgment with “Mostly sound, with
two architectural concerns requiring clarification.” The pinned role-assessment
checker accepts judgments starting with “sound”, “concerns identified” or
“conflicts with platform”. It therefore rejects this 7,179-character report.

This is not an empty Skill return. The actual receiving tool_result contains
the full report, its file hash matches provenance, its producer transcript
contains the same text, and the final review includes it verbatim. The checker
records content_chars=7179 but result_chars=0 because it uses zero to represent
an assessment it rejected. That field alone must not be interpreted as missing
transport data. The recorded benchmark verdict remains unchanged.

[Tracked checker/producer vocabulary mismatch](../bugs/open/strat-review-gate-mostly-sound-false-negative.md).
A future fix should decide between canonical producer wording and explicitly
supported qualified judgments, preserving negative tests for unfinished output.
No paid rerun is needed to reproduce this case.

## What independently verifies

The saved completion result, run summary, receipt and every receipt input hash
agree. Exactly one native Workflow completed with the expected receipt, its
stored JavaScript matches the pinned source, and its final result is recorded
in the actual started/completed final agent's journal.

For each of the 12 reports, the audit checks role/key identity, exclusive target
heading, producer transcript, receiving Skill result, provenance hash and
verbatim inclusion in the published review. These checks establish delivery,
scope at the report-heading level and preservation. They do not independently
grade technical accuracy, or prove that every discussed component is relevant.
Approval follows the user-selected numeric-score policy; individual specialist
recommendations can disagree with the aggregate decision.

This is one three-ticket run with a changed source and cap, not an isolated
measurement of the concurrency setting or a population failure-rate estimate.

## Archive recovery

The overnight collector captured job evidence, API dumps, strace, native traces
and the other services, but the full retained dashboard snapshot exceeded its
fixed 600-second stream timeout. That capture is marked incomplete, and the
observer correctly stopped without publishing a reset-authorizing receipt.
The dashboard retains approximately 29 GiB of data.

The host collector now uses fast lossless gzip and a configurable 30-minute
default per-stream timeout. Compression is wrapped outside tarfile to support
the MLflow Python 3.10 and Observatory Python 3.11 runtimes. Sixteen archive
tests pass, including binary/inventory preservation, older-runtime compatibility
and timeout selection; the full suite reports 72 tests, seven skipped.

Recovery created a separate final capture, reusing checksum-verified successful
sources and retrying only the two service snapshots after the Python fix.
Its manifest records source intervals and recovery provenance. Both earlier
incomplete captures remain unchanged. Shared-service snapshots are collected
later in the morning, not at job completion. No model rerun or reset occurred.

Final capture: `markov-run-dd4a838118bd23d18c693b01/20261015T111127302464Z/`
under the evidence root below. Independent verification passes: complete/final,
errors=[], 3,599 files, 8,998,503,549 bytes, with the final checksum-backed receipt
published. API dumps, strace, native traces, logs and service snapshots are
present. Manifest SHA-256:
`242eb02ef58cc0a28e20b4aaa37d7dad6d48c07e11cc8936ce114be038e2a3d5`.
The completion/report audit was also repeated against this final capture.

Private evidence root:
`var/run-data/strat-workflow-hardening/opus-scheduled-20261015-0030/`.
The launch-context/post-run-audit.json file records the independent checks and
exact report hashes; archive-recovery.log records the collection retry.
