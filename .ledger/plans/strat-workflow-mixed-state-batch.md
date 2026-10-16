# Mixed-state S1 batch: fresh work, recovery and repeat safety

Status: failed GLM run archived and independently verified; repairs are published and one
explicitly authorized Opus pass completed (markov-run-5d3327ed).
The user requested a batch limit of ten against
roughly 20–30 Jira issues containing RFEs and STRATs in mixed states. The
gating rules are available in the current Fullsend fork. The agreeing-verdict
fix is published as fbc335bedb4a4eb97265da89d36bc29009a41fde. Breadboard
a75c72b is pushed/synced. Run markov-run-eaf92e4d launched at 23:16:30Z on
2026-10-15; the live seed completed and model job 231702-8b0253 was submitted.
Live pre-inference guard and actual process verification confirm all expected
resume points, nine acquired keys and GLM routing; no source changes at launch.
[GLM execution](../tasks/done/s1-mixed-state-glm.md).
[Repair and Opus task](../tasks/done/s1-mixed-state-repair-opus.md).

## First mixed-run findings

The host acquired the expected nine RFEs. All nine reviews were recorded,
seven strategies refined/pushed and four new STRATs created. The finish checker
found controls/deferred work and existing effects preserved, with run-owned
claims released and the foreign claim intact. It skipped the live repeat after
the failed invocation; do not count this as a passed repeat experiment.

The first native Workflow failed after 106m02s because review-only imports
were not marked Refined. Import instructions set Draft, whereas final business
validation requires Refined/Reviewed even when the host selects review-only.
The local reimport test used Refined and therefore missed this boundary.
[Bug](../bugs/fixed/strat-review-only-import-status-contract.md).

The primary agent stayed active and attempted a repair. The transcript shows
frontmatter.py changing the two task statuses to Refined at 01:12:57Z, followed
by a second Workflow invocation at 01:13:10Z. That invocation also failed,
because review composition hashes the whole task file, including status.
Freshness's separate semantic strategy hash excludes status; checking only that
hash did not establish that the existing reviews remained valid. Reverting
only the status in memory restores both original recorded review-input hashes.
No archived file was changed. One host launch does not limit the primary agent
to one native Workflow invocation or guarantee exit after native failure.
The first Workflow consumed 106m02s, followed by roughly 14m39s of parent
diagnosis/repair before the stop. This repair sequence changed artifacts;
no pipeline-source edits are shown in the primary's post-failure tool calls.

The user requested stopping; SIGTERM at 01:18:49Z ended Claude with exit 143.
All nine owned locks released successfully; native transcripts and logs were
saved without deleting the pod. Markov then failed before its independent
checker could start: the rich seed report was 306,233 bytes, passed as one
argument. [Benchmark bug](../bugs/fixed/strat-mixed-seed-exceeds-exec-argument-limit.md).
The final GLM capture is independently verified with receipts published:
17,077 files / 23.30 GB. No repair or fresh model job was launched in response
to the stop request; the subsequent user instruction authorizes repair and Opus.

## Repair before the Opus pass

record-create restores Refined for Draft review-only imports only when their
canonical strategy matches host-verified earlier push proof. It runs before
scoring/review snapshots and refuses promotion after a review has begun.
The batch push helper excludes these imports even though they now carry
Refined; their previous push remains reused. Completion validation and both
hash contracts stay strict. The real-emulator regression covers Draft import,
status restoration, no duplicate push, composed review and final completion.

The runner streams the rich seed report through stdin; a real offline Markov
executor check sends 350 KB and exercises the checker input contract. Legacy
direct JSON arguments remain accepted for small manual calls.

A failed business receipt prevents automatic Skill/Workflow relaunch in that
prepared run. The new mixed Opus tier also supervises native runtime status:
the first failed strat-pipeline journal terminates the primary process group,
then the normal shell validator, lock cleanup and capture run. Successful
Workflow completion keeps the ordinary CLI exit path. This process supervisor
is a benchmark-wrapper control, not a new claim about Fullsend runner behavior.
Local fake-process checks cover failure termination, ordinary success, CLI
failure, timeout and stale journals without inference. Earlier tiers keep their
existing source pins and monitor settings.

## Source of truth

Read the tested fork's config/pipeline-settings.yaml, scripts/list-rfe-ids.py,
scripts/jira_utils.py, .fullsend/shared/prepare_run.py,
scripts/strat_freshness.py and the three strategy Skills. Preserve the existing
S1 workflow and its batch cap of ten. The new Opus tier pins f5691f7, including the review-only restoration and
push exclusion. The earlier GLM tier retains fbc335b. Historical pins remain unchanged.

The existing seed_scenario.py creates new RFEs only. Its all-new batch checker
also assumes every seed RFE produces a new STRAT and a final review. Extend
seeding/checking explicitly for mixed state rather than reuse those assumptions.

## Proposed fixture inventory

Draft inventory: 29 initial issues, 18 RFEs and 11 linked STRATs. Work subjects
must stay distinct enough to avoid content deduplication. Reuse full synthetic
RFE templates and valid strategy bodies/frontmatter, not empty title-only seeds.

| RFE cases | Existing STRATs | State | Expected behavior |
| ---: | ---: | --- | --- |
| 4 | 0 | Eligible, no STRAT | Create, refine, push, score, review |
| 2 | 2 | Open Draft/Refinement, not auto-refined | Import existing STRAT, refine/push/review; no clone |
| 2 | 2 | Auto-refined, pushed, no review, valid prior provenance | Import and review; preserve refinement and published strategy |
| 2 | 2 | Auto-refined without reusable proof, including human-cleared gate | Refine/push/review again; do not trust the label alone |
| 1 | 1 | rubric-pass | Leave unchanged |
| 1 | 1 | needs-attention | Leave unchanged; a human gate is not permission to resume |
| 1 | 1 | human-sign-off only | Leave unchanged; test the late preparation gate explicitly |
| 1 | 1 | In Progress STRAT | Leave unchanged |
| 1 | 1 | Closed STRAT, no open replacement | Leave unchanged; do not clone a replacement |
| 1 | 0 | Missing quality approval | Exclude |
| 1 | 0 | Missing release scope/target version | Exclude |
| 1 | 0 | Processing plus foreign owner | Exclude; preserve the foreign claim |

These are ten potentially actionable RFEs plus eight controls, not a promise
that discovery and acquisition will both return ten. Record exact counts and
ordering from preparation before authorizing a model run.

## Gates verified in code

Discovery requires RHAIRFE, an allowed release label OR allowed Target Version,
and at least one quality label (rfe-creator-autofix-rubric-pass or tech-reviewed).
RFE Closed/Resolved/Draft and processing labels are excluded. Linked STRAT
rubric-pass/needs-attention/processing labels and In Progress/Review/Release
Pending/Closed/Resolved statuses are filtered before slicing the batch.
Exactly one open ungated replacement STRAT can make a previously processed
RFE eligible again; ambiguous multiple open clones must not become duplicates.

Preparation additionally skips human-sign-off, needs-attention and rubric-pass
STRATs, and refuses foreign/unowned/conflicting claims. An eligible STRAT
without auto-refined resumes at refine. Auto-refined plus a prior pushed mark
does not suffice for review-only: the stored freshness contract, source and
trusted helper identity, architecture, RFE inputs, live published strategy and
human inputs must agree. Missing/stale proof requires refinement again.

Current batch nuance: human-sign-off is a preparation gate but is absent from
discovery's STRAT skip_labels. A human-sign-off-only case may consume one of
the ten discovery slots and be skipped afterward. Include that outcome in the
preflight evidence; do not silently change key ordering, batch size or workflow
gates to disguise an underfilled batch. The execution deliberately records ten
candidates, nine acquired and one deferred. The local real-emulator preparation
confirms this outcome; the live guard must match before inference starts.

## Fixture preparation without inference

Create linked RFE/STRAT pairs, statuses, descriptions, labels and provenance
from a declarative manifest. Build review-only fixtures through the real
preparation/refinement-recording/push/progress helpers, using authored refined
content and the exact final candidate/context. This follows the existing
test_verified_later_resume_reuses_push_only_while_current integration test.
Do not fabricate a pushed boolean or replay old provenance across changed code.

The seed report must distinguish the raw eligible pool, ordered batch candidates,
expected acquired keys, preparation skips, resume points, existing STRAT mapping
and expected new work. BATCH_EXPECTED_KEYS asserts the ordered discovery list,
not the acquired subset. Dry-run/preparation checks must establish these facts
before any model is launched.

## Acceptance and idempotence checks

Compare before/after Jira snapshots per ticket and side effect. Expect new
clones only for fresh RFEs; preserve existing STRAT identities and links. Require
refinement only where planned, unchanged published strategy hashes for valid
review-only cases, one numeric review publication per newly completed strategy,
correct verdict labels and all required role/provenance files. Completion counts
must follow the manifest's work set, not the total number of STRATs in Jira.

Ignored controls must keep their descriptions, status, labels, links, comments
and attachments unchanged. All run-owned claims must release on exit; the
foreign control's processing/owner labels must remain. Use saved API/native
traces to check omitted stages and repeated clone/comment/attachment operations.

After the mixed run, perform discovery/preparation again against unchanged Jira,
without reseeding/reset. Completed work must be excluded, the human gate must
still skip and the single deferred RFE must remain available. Release the repeat
preparation's claim without invoking Claude; compare Jira before/after to reject
duplicate effects. This checks ordinary repeat safety without a second model
invocation, not global queue exhaustion. It does not establish crash safety for every possible
failure boundary; existing helper recovery tests remain separate evidence.

Use one GLM iteration for implementation testing under the standing rule;
Haiku/Opus needs separate approval. Preserve Tier 1 and all-new scenarios.
Archive and independently verify every run, including failures, under
var/run-data before any later reset. Preserve previous benchmark results.

## Implemented scenario

The new s1-mixed-glm tier uses fbc335b, one iteration, batch limit ten, agent
cap ten and native capture. The two review-only RFEs are seeded first; the
actual pinned pre-script, state recorder and push helpers produce their earlier
run and release its claims before the remaining issues are created. Authored
fixtures include the normal staff-input template and Jira-round-trip Markdown.
The seed report saves full rich-text snapshots through Jira v3.

Real local-emulator checks confirm candidates 1, 10, 13, 2, 3, 4, 5, 6, 7, 8;
RFE 13 is human-signed-off and skipped. Nine acquired RFEs split into four
fresh, three refinement and two review-only cases. RFE 9 is deferred. No cap or
source gate is changed to hide that underfill. A pre-inference guard rejects any
different discovery, acquisition, resume or reusable-proof set in the live job.

The finish checker preserves controls/deferred tickets and existing effects,
counts fresh clones, requires one final review/attachment per acquired strategy,
checks review-only content and omitted refine/push marks, and verifies ownership
cleanup. Successful jobs then prepare the remaining queue once with no Claude:
only the deferred RFE may be acquired, and release must leave Jira unchanged.

Validation: 89 offline benchmark tests pass, one optional integration skipped;
the separate local-emulator suite passes eight tests, including actual
preparation, push, review-only reimport and repeat cleanup. No inference used.

## Repair validation, 2026-10-16

Candidate f5691f7 is pushed to the Fullsend fork. Full component suite:
1,041 passed, six skipped; focused recovery suite 57 passed. Benchmark suite:
96 tests, OK with one optional integration skipped; that real local Jira suite
passes all nine separately against the committed candidate. Ruff, shell syntax
and diff checks pass. No model calls were used in these regressions. The
s1-mixed-opus tier authorizes exactly one Opus 4.6 pass after these checks.

The fixed mixed Opus pass launched at 2026-10-16T13:49:39Z as
markov-run-5d3327ed, Breadboard a2aec3c, candidate f5691f7. One iteration,
cap ten and concurrency ten, expected nine acquired. Archive root:
var/run-data/strat-workflow-hardening/fullsend-vertex-opus-mixed-state-c10-20261016.
Detached archive observer PID 1194342; no automatic replacement run. This
launch record preceded the terminal findings below. See the repair task for
live verification and final evidence.

## Opus terminal findings

Pipeline succeeded in 45m14s job time (41m09.550s native Workflow). All nine
acquired tickets completed: four fresh, three refine, two review-only. The
restored review-only status passed without late metadata changes or duplicate
pushes. Seven approve, two revise. All controls, prior effects, owned-lock
release and the zero-model repeat passed. Deferred RFE 9 remains available;
human-signed-off RFE 13 remains skipped.

The separate pinned benchmark remains failed solely on reviewer_outputs_returned:
three formatting false negatives among 36 reports. Independent API return,
provenance-hash and composed-review inspection verifies all 36 were delivered
and preserved. Numbered findings and Mostly sound recur; repeated consistent
Testability fields expose another checker assumption. Read-only diagnostic
replays isolate all three. Preserve the historical result; fix with offline
positive/negative report replays before any further paid test.

Final archive independently verified, receipts published: 11,940 files /
22,344,722,063 bytes, complete/final with no source errors. No replacement run.
[Audit](../notes/s1-mixed-state-opus-20261016.md).

## Cross-ticket follow-up

No contamination detected in the Opus scope/identity/copying inspection. All
36 reports identify only their assigned ticket; 511 reviewer scope audit events
show no cross-ticket reads attempted or allowed. The 37 denials concern the
correct ticket under the wrong local/ path. Nine processed subjects are unique.
The apparent duplicates come from seed construction: eight excluded/skipped
controls reuse subjects from the actionable/deferred pool. These are baseline
fixture duplicates, not new clones created by agents, and all controls stayed
unchanged. Use unique control subjects in a future fixture for clarity.
[Detailed evidence](../notes/s1-mixed-state-opus-20261016.md).

## PR 85 follow-up qualification, 2026-10-16

Deeper review of the same successful mixed Opus run confirms all nine reviewers
worked around the known scorer-path defect by staging files inside the repo.
All nine scorers lacked Bash for their required recovery preflight. Strace also
shows the refinement StructuredOutput guard and final completion guard killed
by Claude after about ten seconds, with execution continuing. Host completion
validation still passed. Operational completion therefore does not establish
that every guard ran or that only benchmark-parser defects remain. A complex
Markdown round-trip probe also confirms a review-only fingerprint coverage gap.
These are open defects/qualification gaps; no new model run or source repair.
[Review disposition and exact evidence](../notes/strat-creator-pr85-review-triage.md).
