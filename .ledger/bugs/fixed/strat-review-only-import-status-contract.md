# Review-only import conflicts with final artifact-status validation

Observed in mixed-state GLM run markov-run-eaf92e4d, candidate fbc335b,
Claude Code 2.1.296. Status: fixed locally and published as strat-creator f5691f7; paid Opus validation pending.

The host verified real earlier push provenance and selected RFE 1/2 for review
only. All nine strategies eventually had recorded reviews. The first Workflow
failed at 2026-10-16T01:04:10.704Z with two business errors: RHAISTRAT-1 and
RHAISTRAT-2 "strategy is not refined". Native duration: 6,362,443 ms.

The strategy-create Skill's existing-STRAT import explicitly sets status=Draft.
Review-only recovery correctly skips refinement/push, but
scripts/strat_pipeline_outcome.py:133 requires Refined or Reviewed for every
artifact before its subsequent review-only exemption for saved refine/push
marks. This is a contract mismatch between import and completion validation;
the observed failure alone does not establish weaker GLM reasoning.

The primary transcript confirms the attempted repair. At 01:12:57.369Z it
called scripts/frontmatter.py set for both task files with status=Refined.
At 01:13:10.300Z it invoked Workflow by name again. This second native Workflow
(wf_6d35d18f-851, three agents, 138,865 ms) failed at 01:15:36.774Z with
"Review provenance/input identity disagrees". The parent inspected freshness's
semantic strategy hash, which excludes status, but missed review composition's
separate hash over the complete task file. Its metadata repair invalidated the
saved reviews. It continued investigating until the user's stop at 01:18:49Z.

Independent offline confirmation against both retained task files: their current
SHA-256 differs from their review manifest's input hash. Replacing only
status: Refined with status: Draft in memory restores the exact recorded hash
for each. No archived file was edited. This establishes the status-only cause,
not merely a correlation. Observed mutations were task artifacts; the primary
transcript shows no Edit/Write of pipeline source in this repair sequence.

The local fixture test checked provenance and reimport with status=Refined;
it did not reproduce the Skill's status=Draft import or final completion gate.
Extend that integration test to cover the real import/status contract before
another paid run. Preserve numeric-only approval, genuine pushed proof and
immutable review inputs when choosing the repair.

Evidence: native journals, repo-tmp progress, repo-artifacts task files and
workflow/output/agent-result.json in the stopped job's retained artifacts.
Primary session: e39871f8-51fe-44b3-815d-3afd21349eeb.jsonl.
Archive root: var/run-data/strat-workflow-hardening/fullsend-glm-mixed-state-c10-20261015.

## Repair and verification

record-create restores Refined only for a Draft import with matching trusted
prior push proof, before any review snapshot. It refuses changes once review
has begun. The batch push helper explicitly excludes these review-only imports.
A failed completion receipt also blocks Skill/Workflow relaunch. Full component
suite: 1,041 passed, six skipped. The real local Jira regression passes import,
no duplicate push, review composition and final completion. Opus is authorized
for one mixed-state pass; its outcome is not yet known.
