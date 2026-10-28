# Judge saved refined strategies: Opus 4.6 versus 5.5

User requested a content comparison after the scope-checker repair, 2026-10-18.
Compare the two existing mixed-state runs, not new generations:
`markov-run-bfc0b766` and `markov-run-296d9e2e`.

- [x] Match eight produced/refined strategies by source RFE, verify shared inputs
      and identify two unchanged review-only controls.
- [x] Prepare A/B documents without model names, pipeline scores or role reviews.
      Freeze the rubric before reading the pairs.
- [x] Judge every pair against its RFE and retained architecture evidence.
      Distinguish four fresh-create/refine cases from four same-draft refinements.
- [x] Record evidence, limitations, per-case judgments and a readable conclusion.
      Preserve all original archives and verdicts.

Rubric: score each criterion 0, 1 or 2 (ten possible points): requirement
coverage/scope; technical grounding and consistent decisions; implementable
design detail; observable acceptance tests; operational and failure behavior.
0 means missing or materially wrong; 1 means useful but an important gap
remains; 2 means sufficiently specific and coherent for a strategy, with no
material gap identified from the supplied evidence. Unsettled implementation
details alone are not defects when bounded and assigned to a discovery step.
Length and confident phrasing do not earn points. A blocking contradiction can
override a simple numerical total in the pairwise preference.

This is one assistant content review with model labels masked during scoring.
It is not a new blinded human study, calibrated multi-judge experiment or
estimate of either model's average quality. No separate provider judge or
pipeline calls are required for this pass. Review-only controls are not
additional generations or independent trials.

## Result

Completed: one assistant pass, preferences/criterion ratings frozen before
unmasking, then selected post-freeze reference/reviewer checks. 5.5 preferred
in all eight pairs (four fresh, four same-draft refinements), with substantive
remaining gaps preserved. Two unchanged controls receive lower pipeline scores
under 5.5, showing reviewer behavior/variation contributes to the approval
difference. No policy changes, new generations or external judge calls.

[Readable assessment](../../notes/strat-content-opus46-vs55-20261018.md).
Private evidence is separate from both original archives at
`var/run-data/strat-workflow-hardening/content-judge-opus46-vs55-20261018/`.
Complete/final manifest: 708 listed files / 15,429,495 bytes. All checksums
verify, original 16 candidate/4 control-source hashes remain unchanged, both
321-file reference sets match, frozen judgment/mapping hashes still match.
Manifest SHA-256: `e3fc58e37ff5bbb4c739b2c1406a39e4b29564869a5bad3bffe59e19493580ad`.
Preparation/verification/archive scripts compile and `git diff --check` passes.
Additional provider calls/cost: 0 / $0; conversation model usage is not metered
by this benchmark and is excluded. No agent-eval-harness run was performed.
