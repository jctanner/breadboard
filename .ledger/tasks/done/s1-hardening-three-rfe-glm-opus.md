# S1 hardening: three-RFE GLM batch, then conditional Opus batch

Authorized 2026-10-14: run one three-ticket batch through markovd with GLM.
Run one matching `claude-opus-4-6` batch only after GLM succeeds and its complete
archive verifies. No extra repeats or paid wiring probe.

## Source and workload

- Hardened S1: `eval/s1-hardening`,
  `0e7e752702727076818001d3a29208532b40dbab`, local GitHub emulator.
- Add separate hardening tiers to the existing Markov directory workflow;
  preserve historical S1/S2 pins and tier definitions.
- Existing distinct three-RFE scenario: workbench culling exemptions, pipeline
  retention, scheduled feature-store materialization.
- GLM primary/helpers/aliases: `rits/zai-org/glm-5-3`, medium effort.
- Conditional Opus primary/helpers/aliases: `claude-opus-4-6`, high effort.
- One run per model; no artifact wipe. Archive guards precede Jira reset.

## Checks

- [x] Offline Markov checks verify the new tiers, exact source, selection and model wiring.
- [x] Publish benchmark harness, sync/import in markovd and verify source identity.
- [x] Launch one GLM Markov run and retain launch evidence; final archive pending.
- [x] GLM completes all three strategies with 12 substantive reviewer reports,
  matching numeric verdicts/Jira records, valid completion and released locks.
- [x] Final GLM archive under private `var/run-data` verifies before another reset.
- [x] If GLM passes, launch one Opus Markov run on the same source/scenario.
- [x] Archive, verify and analyze Opus, including failure if any.

## Status

Done: GLM passed; the separately authorized Opus batch failed. Both final
archives independently verify. The Opus primary changed source and freshness
records after Anthropic schema rejection; host validation refused the resulting
completion. Fullsend/OpenShell deployment and strategy-content judging remain
separate qualification. Existing unrelated changes are preserved.

## Launch evidence

Published Breadboard `a4ca5d689cec98c10704becd55a25f5c1e89a08a` on main,
then synced project 1 and imported the exact directory workflow in markovd.
All 69 benchmark tests pass using `/tmp/strat-tier2-markov`; workflow validation,
shell syntax, whitespace and staged credential checks pass. The stale checkout
binary could not parse existing step descriptions; it was not used for launch.

Independently verified all five earlier retained hardening job archives before
the new Jira seed. One POST launched `markov-run-cf0dfe9a` at
2026-10-14T20:45:13Z. Seed
`script-seed-scenario-all-claude-haiku-5-5-1014-204514-03f6a2` completed without
inference; its model label is setup metadata. Model job
`script-run-workflow-all-glm-5-3-1014-204524-5924cf` is running on
RHAIRFE-1, RHAIRFE-2 and RHAIRFE-3. Actual job environment confirms candidate,
batch size, GLM helper/default aliases and medium effort. Native progress has
passed Read and entered Create. No Opus run is launched yet.

Both new tiers use the native batch's 295-minute allowance, background wait
ceiling 17,700,000 ms, and Markov job wait 18,000 seconds. Historical defaults
remain intact. Native state/journal copying is enabled for these new tiers.

A detached host controller (PID 2815513) monitors the authorized pair. It
archives GLM even on failure, independently verifies the final capture, checks
benchmark pass/source identity, all stage exits, completion input/result hashes,
matching native state/journal, and 12 preserved reports with native producers.
Only all-pass permits its one Opus POST; any failure or uncertain submission
stops without automatic rerun. It also archives/verifies/checks Opus.

Private launch/controller/status evidence:
`var/run-data/strat-workflow-hardening/three-rfe-glm-opus/launch-context/`.
Controller source is copied there; live final captures will be separate immutable
directories under the corresponding Markov run IDs. No personal upstream key
was read or passed into jobs. These are Kubernetes/Breadboard/Markov benchmarks,
not Fullsend/OpenShell deployment qualification.

[Hardening plan](../../plans/strat-workflow-s1-hardening.md).

## Live duration investigation

At the user's request, inspected the active GLM job without stopping or changing
it. Around 93 minutes, all three strategies were pushed, two reviews completed
and the third remained active. Found an integration bug: the Workflow's external
scorer path is refused by the composition helper. Each review agent recovered by
staging a byte-identical file inside the repository, after 9m26s/13m39s/3m02s
diagnostic intervals. Specialist Skill calls were submitted together but ran
serially within each ticket; two outer agents overlapped. Architecture reviewers
made 47–48 tool calls. Relay snapshot at 22:22:40: 414 completed GLM records,
all HTTP 200, no recorded errors. Final gates remain pending; Opus remains
conditional on them and the final archive. No live source modification.
[Diagnosis and evidence](../../notes/s1-hardening-three-rfe-glm-live-duration.md).

## GLM terminal pass and conditional Opus launch

GLM finished at 22:58:50 UTC, 8,006 seconds (2h13m26s). All ten benchmark
checks pass, including three distinct completed strategies, 12 substantive
review reports, exact model identity, matching Jira records and released locks.
The independent controller additionally verifies completion input/result hashes,
native state/journal and preservation of the 12 reports with native producers.

Final archive independently verifies, complete=true/final=true/errors=[]:
`var/run-data/strat-workflow-hardening/three-rfe-glm-opus/markov-run-cf0dfe9a/20261014T225916540357Z/`.
It contains 6,662 manifest files, 7,517,959,140 bytes, including available API,
strace, native and shared-system evidence. Verification completed at 23:09:54
UTC, before the next reset. Existing scorer-path recovery remains a known defect
despite the successful business/receipt outcome.

Usage: 435 captured requests/responses, all exact hosted GLM requests; response
usage 5,014,392 input + 14,889,472 cache-read + 472,899 output tokens. No recorded
API body errors or rate limits; these are provider categories, not GLM pricing.

Archived timing analysis additionally identifies three report regenerations for
[duplicate Recommendation lines](../../bugs/open/strat-review-recommendation-format-causes-regeneration.md),
including two roles on the last ticket. Its 43-minute review includes roughly
13 minutes diagnosing formatting and regenerating those two reports.

One POST at 23:09:54 UTC launched Opus `markov-run-687db37c` (database ID 586)
on the identical source/scenario. Seed completed; model job
`script-run-workflow-all-claude-opus-4-6-1014-231007-d5c565` started at 23:10:07.
By 23:30 all three strategies were refined and pushed, two scorers completed
and the third was active. The first two review agents failed in about 0.34s with
HTTP 400: Anthropic rejects top-level `oneOf` in our tool schema. This is a new
provider-compatibility gap, not a model reasoning or quota failure. The job is
left running and the controller will archive its terminal result; no automatic
paid retry is authorized.
[Schema rejection bug, subsequently repaired](../../bugs/fixed/strat-workflow-anthropic-top-level-union-schema.md).

## Later Opus behavior and next repair

At 2026-10-15T00:03Z (20:03 Eastern on October 14), Opus remained running,
roughly 53 minutes into its job. It had independently removed oneOf from both
Workflow copies, rewritten input/progress freshness hashes and launched three
Workflows. The third launch used scriptPath to avoid the cached named source;
it was reviewing two strategies with the third queued. Original host input still
differed from the modified sandbox baseline. No operator live edit or kill.
This is not a clean pinned-source qualification, irrespective of later success.
[Observed self-repair and baseline rewriting](../../bugs/open/s1-primary-edits-source-and-freshness-after-failure.md).

User requested the [schema compatibility repair](s1-hardening-anthropic-schema-compatibility.md)
first after this attempt and its archive complete. Do not adopt the live agent's
edits or automatically launch another paid batch. Current completion ETA is
uncertain because the agent has restarted orchestration rather than following
one fixed execution sequence.

## Opus terminal result

The container exited 1 at 2026-10-15T00:23:28Z; the job was marked failed at
00:23:31Z, about 73 minutes after creation. Three native Workflows span elapsed
minutes 0.61–22.02 (schema rejection), 31.40–40.64 (cached source, same rejection)
and 41.98–72.27 (edited source, locally completed). The third execution reused
creation/refinement/push but repeated scoring before reviewing all three tickets.

Claude exited 0, but host validation exited 1 because downloaded input differed
from the trusted freshness baseline. All three strategies and reviews exist;
benchmark checks fail `finished` and `reviewer_outputs_returned`, the latter
rejecting two of twelve specialist results. This is not a clean qualification
of the pinned revision. No operator live edit, kill or restart occurred.

Final archive independently verified at 00:39:03Z:
`var/run-data/strat-workflow-hardening/three-rfe-glm-opus/markov-run-687db37c/20261015T002356475599Z/`.
The controller stops on failed benchmark gates with no automatic paid rerun.
The [schema repair](s1-hardening-anthropic-schema-compatibility.md) is separately
implemented and tested; source/baseline protection remains open.
