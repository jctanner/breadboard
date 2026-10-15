# Mixed-state S1 batch: fresh work, recovery and repeat safety

Status: implementation and offline validation. The user requested a batch limit of ten against
roughly 20–30 Jira issues containing RFEs and STRATs in mixed states. The
gating rules are available in the current Fullsend fork. The agreeing-verdict
fix is published as fbc335bedb4a4eb97265da89d36bc29009a41fde. No mixed-state
model run has been launched yet. [Execution task](../tasks/current/s1-mixed-state-glm.md).

## Source of truth

Read the tested fork's config/pipeline-settings.yaml, scripts/list-rfe-ids.py,
scripts/jira_utils.py, .fullsend/shared/prepare_run.py,
scripts/strat_freshness.py and the three strategy Skills. Preserve the existing
S1 workflow and its batch cap of ten. The new tier pins the published
agreeing-recommendation fix. Historical pins remain unchanged.

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
