# Existing SME revision flow

The existing design supports repeated human-guided revisions, including
resubmitting an already CI-approved strategy. An SME description edit alone
does not reopen or enqueue it. The intended human resubmission step removes
the current CI verdict label. Calling all SME reprocessing a missing feature
was too broad; automatic edit-triggered reprocessing is a separate behavior.

## Sources inspected

| Source | Identity | Relevant material |
| --- | --- | --- |
| Supplied GitLab strat-pipeline checkout | Local main `fd36b15` | `.gitlab-ci.yml`, README, Claude wrapper and post-processing scripts |
| Current upstream strat-creator main | Fetched `fullsend/main`, `b3961721822d709034c346d642b533fd9573fcb3` | Human review guide; pull, push, refine, review and create skills; import, locking and publication helpers |
| S1 feature branch | Clean `6ed858b2294a29457153a90f187a801022c21e8b` | Native preparation, deterministic import, freshness checks and unchanged human skills |
| Existing SME-loop demo | `var/demos/strat-dashboard-sme-loop-test/` | Main and continuation workflows, README, workflow contract tests |

Upstream main was exported to `/tmp/strat-sme-main-b396172` for isolated
inspection and model-free tests. The active feature checkout was not changed.
The GitLab identity above describes the supplied local checkout, not a claim
that its private remote was refreshed.

## The designed human loop

The authoritative description is the current-main
[human review guide](https://github.com/fullsend-ai/strat-creator/blob/b3961721822d709034c346d642b533fd9573fcb3/docs/human-review-guide.md).

1. CI publishes a strategy with `strat-creator-rubric-pass` or
   `strat-creator-needs-attention`.
2. `/strategy-pull RHAISTRAT-N` imports its current Jira description, the
   linked RFE and comments, and the previous review into `local/`. Large
   strategies are reassembled from the generated-content attachment while
   retaining the live description's SME section.
3. The human edits `## Staff Engineer / SME Input` in the strategy artifact.
   This section belongs to the **RHAISTRAT strategy**, not its source RHAIRFE.
4. `/strategy-refine RHAISTRAT-N` regenerates the affected generated sections;
   `/strategy-review RHAISTRAT-N` reviews that new output. SME guidance has
   priority over overlays and generated architecture context. The Business
   Need and SME sections must remain unchanged by refinement.
5. `/strategy-push RHAISTRAT-N` publishes the strategy and SME section and
   removes the current `needs-attention` or `rubric-pass` label.
6. A later eligible CI batch imports the existing strategy, refines with its
   updated SME input and reviews it again. Once approved, the human can pull
   and use `/strategy-signoff`.

Pull stamps `workflow: local`. Both refinement and review explicitly bypass
pipeline label gates in local mode and perform no Jira writes. That is how a
human can iterate while the strategy still carries its previous CI verdict.
Push is the separate publication/resubmission step. Human sign-off remains a
separate final gate; resubmission does not silently clear it.

The guide explicitly permits `/strategy-push` on previously approved
strategies after substantial SME changes. The implementation is described in
[strategy-push](https://github.com/fullsend-ai/strat-creator/blob/b3961721822d709034c346d642b533fd9573fcb3/.claude/skills/strategy-push/SKILL.md).
It is an agent-invoked skill containing separate content-push and label-removal
commands, not an atomic Jira edit or a background description watcher.

If someone edits the designated SME section directly in Jira, a subsequent
pull/import can read it. The edit itself does not perform the resubmission
step. A still-approved or needs-attention strategy remains excluded from
ordinary scheduled selection until deliberately reopened. Other selection
criteria and source-RFE ownership checks still apply after reopening.

## GitLab orchestration has two distinct paths

The scheduled batch discovers eligible RFEs with `list-rfe-ids.py
--jql-default`, locks them, creates/imports strategies, refines, deterministically
pushes refined files, reviews, and publishes result data. The default discovery
excludes RFEs whose linked strategy retains a blocking review label.

The separate manual `reprocess-strat` job takes `STRAT_KEY`, locks the linked
RFE with `lock-strat`, pulls the existing strategy into the artifact directory,
then runs refine, deterministic strategy push, review and post-processing.
It is not a normal batch-discovery pass.

Its guards require an auto-created strategy and a Cloners link and reject
`needs-attention` and human sign-off. They allow `rubric-pass`. Pull still
stamps `workflow: local`, even with `--local-dir .../artifacts`, so the existing
review label is not, by itself, a reason the subsequent skills must skip.
That local-mode exception matters when comparing this job with S1 resume.

There is also a static integration question on this older manual path:
local-mode review says it performs no Jira writes, while the outer job
explicitly publishes the strategy but has no equivalent explicit review-label
publisher. This audit establishes the source contract, not a newly observed
end-to-end failure of that job. Do not equate a manual job's existence with
proof of its final Jira review state on today's main.

## We already have a two-edit SME integration demo

[Demo and usage](../../var/demos/strat-dashboard-sme-loop-test/README.md).
The Markov workflow runs an initial create/refine/review, then two successive
SME edits followed by refinement and review. Expected `refine_count` is
**1, then 2, then 3**.

The reusable continuation supplies important actions itself:

- Authenticates as the SME user, posts a comment and edits only the Jira
  description's SME section using ADF.
- Explicitly removes both CI review verdict labels.
- Gives the refine agent an extra instruction to fetch the current Jira SME
  section and merge it into the existing local artifact before refinement.
- Asserts the expected count, preserved SME markers and Business Need, and a
  changed artifact. It also checks the description's existing headings survive.

Markovd still records a completed full run, **`markov-run-bb4af08c`**,
2026-07-31 11:57:26–12:53:20 UTC. The initial count assertion, both continuation
calls, both label-clearing steps and both later count assertions completed.
The inspected record has 53 steps. No new run was launched for this audit.

This is evidence for a deliberately reopened, explicitly synchronized SME
loop. It does not establish automatic discovery after a description edit,
execution through Fullsend/OpenShell, or semantic compliance with every SME
directive. The assertions check markers and whole-artifact changes, not a
separate content-quality judgment. The demo references the historical
`feature/dashboard-sme-and-loop-metrics` fork, not today's main or S1.

## S1 retains the human flow; its new runtime needs its own SME qualification

Compared with current upstream main, S1 leaves the human review guide and
pull, push and refinement skill definitions unchanged. For an eligible later
run, strategy-create's existing-strategy path uses the deterministic import
helper to fetch the current Jira strategy and SME input. Its pipeline import
uses pipeline metadata rather than inheriting local-mode gate bypasses.

Freshness checks protect the prepared run's input snapshot. A change during
that run stops stale publication or reuse. A new eligible run captures a new
baseline, imports the new SME input and refines again when the previous push
is no longer reusable. Freshness is not a permanent ban on revising a ticket.

There are two important coverage distinctions:

- The ten-ticket mixed-state benchmark seeded a previously human-cleared
  state. It did not enact an SME edit, resubmit, rediscover and revise sequence.
  The native Fullsend smoke processed one fresh RFE and also did not do so.
- S1 `strat-resume` still skips a strategy carrying `rubric-pass`, unlike the
  older manual GitLab `reprocess-strat` path above. The documented human
  push/resubmit flow removes that verdict first and remains available. If
  direct approved-ticket manual reprocessing is required as a separate entry
  point, preserve or explicitly decide that parity; do not silently treat
  resume and reprocess as interchangeable.

The next SME qualification should reuse this existing contract on the current
candidate/runtime: initial reviewed strategy, genuine new SME directive,
deliberate resubmission, later-job import and refinement, new review, preserved
human input, and a subsequent no-op without further changes. That is a
qualification gap, not evidence that a new edit watcher is required. No paid
test or source change is authorized by this audit alone.

## Model-free verification

All **36 checks passed**; Jira helper tests use isolated emulator instances.

| Checks | Result |
| --- | --- |
| Current-main pull/SME round trips, two-cycle preservation, frontmatter and manual locking guards | 17 passed |
| Existing SME demo workflow contract | 5 passed |
| S1 live-source changes, later-job stale-push rejection and complex strategy reimport | 11 passed |
| Temporary current-main probes: description-only edit retains both types of gate; explicit reopen changes eligibility; pull imports live SME and selects local mode | 3 passed |

The temporary probes live only in the exported `/tmp` tree. Existing current-main
tests and S1 tests ran against their respective source identities. No model
calls, shared Jira reset, new job, feature modification or push occurred.
