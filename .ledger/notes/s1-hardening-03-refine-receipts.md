# S1 repair 3: refinement receipts and persisted readiness

2026-10-14 UTC. [Plan](../plans/strat-workflow-s1-hardening.md).

## Contract

The original RECORDED schema accepted arbitrary strings. A serialized JSON
object passed its string field but failed exact-key comparison, excluding
completed work from review. The repair does not parse nested JSON as proof.

Per-target refine schemas permit only the assigned key or explicit none.
Marking completion verifies current-run ownership, valid identity/source/Jira
metadata, Refined/Reviewed status and nonempty strategy content. Saved marks
are timestamps; arbitrary JSON strings are not completion records.

The Workflow reconciles all refinement targets with a fresh refine-status
helper before push/review, using saved marks plus current valid artifacts.
Malformed/missing/wrong-target handoffs recover when persisted work verifies;
a valid-looking handoff without recorded completion cannot advance. The
initial read filters invalid saved readiness too, avoiding unnecessary work
when a valid mark/artifact already exists.

Plugin StructuredOutput hooks verify the initial refined set and full
reconciliation object against actual current-run disk state. The model can
launch commands/carry JSON but cannot override the readiness calculation.
This addresses this receipt boundary; replay freshness and final business
outcome policy remain separate hardening items.

## Validation plan

- Offline state/control-flow cases: valid; completed with malformed/missing/
  wrong-target receipt; plausible receipt without completion; wrong run;
  missing/invalid/wrong-source artifact; refused invalid mark; no duplicate
  refinement of verified work.
- One native loopback scenario, zero provider calls, with actual candidate
  scripts/hooks/refine-stage code. Force malformed structured receipt and an
  invented readiness snapshot; verify rejection and persisted-state recovery.
- One focused GLM fixture scenario if needed for actual JSON carrying through
  the new boundary. Use authored proposals, no Jira writes, one execution and
  full private archival. Do not regenerate or judge full production strategies.

## Status

Candidate `30cf8506d5dbf5b9149971a799e1f3bf5700b7ab` is committed and published
only to local `eval/s1-hardening`. Historical pins remain unchanged.

The component full suite passed 886 tests, with seven opt-in live checks
skipped. Focused state/Workflow checks passed 69 tests. The archive verifier's
four controls reject CLI success without saved completion, repeated fixture
work, and omission of the injected fault. Changed Python files pass Ruff;
documentation/source diffs pass `git diff --check`.

Native control v3 uses Claude Code 2.1.296, binary SHA-256
`24972e3bc859fab2b46ed4c1e51f7d6130f06d3bd550811a114640de3370d0de`,
actual candidate helpers/hooks/refine-stage code, and a forked fixture Skill.
Twenty-six loopback requests, zero provider calls: two targets with verified
work become ready; two without completion fail refinement. Nested JSON and
wrong-ticket StructuredOutput calls fail the assigned-key schema. An invented
all-ready checkpoint is denied before the corrected disk snapshot passes.

All local attempts are retained in private
`var/run-data/strat-workflow-hardening/03-refine-receipts/controls/20261014T022830740858Z/`
with 698 checksummed files. V1's original verifier mistook native `status` for
`state`; the original and corrected verification are both preserved. V2 used
an inline fixture; v3 matches the production Skill's fork boundary.

One GLM diagnostic completed:
`script-run-all-glm-5-3-1014-022559-ec9a80`. It uses two distinct authored
proposal fixtures and medium effort for every agent. It injects the old nested
receipt after a successful agent return to exercise recovery; the native
control separately tests malformed output at the real schema boundary. No
Jira writes, resets, strategy regeneration or content judging are involved.
Independent verification of the captured job evidence passes: 32 request /
response pairs, all exact hosted GLM; both target-bound receipt schemas seen;
one refine Skill, one fixture action and one completion mark per target. Both
files are Refined with `refine_count: 1`; the current-run progress has both
marks. Two hook events verify the initial state and fresh completion snapshot.
The native Workflow result records the injected nested receipt, both ready
keys and no failures. CLI exit 0 agrees with native completion and persisted
readiness. Job duration was 3m24s (02:25:59–02:29:23 UTC).

Reported API usage is 80,645 input, 374,784 cache-read input, zero cache
creation and 14,774 output tokens: 470,203 across those categories. This is
the focused fixture diagnostic, including its launch/completion discussion,
not a full-pipeline cost estimate. No provider dollar figure is asserted;
Claude's reported cost basis for the hosted model is unknown.

Final full-system archive independently verifies with no errors: 16 sources,
448 files, 1,201,141,918 bytes. This includes 64 API dump files (32 pairs),
288 strace files, native transcripts/state, candidate source, Kubernetes
resources/logs, Jira/MLflow/Observatory snapshots, architecture context, shared
dashboard state, service logs and relay telemetry. The verified final archive
receipt is published to the dashboard's archival guard. Archive:

`var/run-data/strat-workflow-hardening/03-refine-receipts/script-run-all-glm-5-3-1014-022559-ec9a80/20261014T022947632132Z/`

Launch metadata, independent verification and verifier source are retained
separately, without modifying the completed job archive:
`var/run-data/strat-workflow-hardening/03-refine-receipts/verification/20261014T023532118127Z/`.

## Qualification limits

Item 3's focused repair is complete. The checkpoint adds one agent per
refinement batch; its command launch still goes through a model, but the
StructuredOutput hook checks the returned readiness against disk. A missing
or invalid checkpoint holds targets back rather than accepting their receipts.
Recovery requires both a current-run saved mark and a valid matching artifact;
a refined file alone does not settle an interrupted mark or repeated side
effect. That recovery policy remains item 7.

These cases do not qualify generated strategy quality, ten-ticket batches,
Fullsend/OpenShell execution, stale-input replay, final review composition or
business outcome policy. Historical benchmark branches remain affected and
unchanged. Items 4–9 remain pending, including the separately recorded
revise/needs_attention disagreement.
