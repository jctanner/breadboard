# Address waynesun09's PR8913 findings

Owner requested addressing these comments as requested:
- https://github.com/fullsend-ai/fullsend/pull/8913#discussion_r4418019549
  Stable Workflow index identity despite a late/omitted agentId.
- https://github.com/fullsend-ai/fullsend/pull/8913#discussion_r4418019560
  Explicit undocumented/private protocol labels for workflow_progress and
  task_summary in docs and decoder comments.

Base: clean fix/8908-claude-workflow-progress at 8e1fd4028.
Existing commit/push and read-only claude-opus-5-5 review authorization applies.
Broader event scope remains authorized; no scope splitting or review messages.

- [x] Reproduce queued(index only) -> start(agentId) -> done as one row.
- [x] Key by positive index, retaining sanitized ID as optional display
  metadata; use ID identity only when index is absent. Suppress ID-only
  progress duplication, preserve distinct indices/tasks/runs.
- [x] Mark private undocumented fields/messages and patch-release drift risk
  in user docs and the specified decoder comments.
- [x] Validate focused/full runtime race, CLI consumer, coverage, staged
  lint/vet/links and original archive replay.
- [x] Read-only Opus 5.5 review, repair any material findings.
- [x] Signed-off commit, push, remote/PR exact-head verification.

The queued/start test is a reduced model of the review's 2.1.312 producer
sequence, not a fabricated recorded 2.1.312 run. Original archive replay is
still 2.1.296; a new live producer qualification is not inferred or claimed.

## Fix and validation

Red regression reproduced two cached rows/two running lines and completion
lost the learned ID. Positive indices now key by task/run/index only; absent
indices retain hashed ID identity. Sanitized AgentID is retained on sparse
indexed updates. Canonical display fingerprints omit indexed ID attribution
so learning an ID alone updates cached metadata without another progress
line. Visible indexed rows use #index (known ID). Regression confirms one
running/one completion and one terminal row holding the learned ID.
Distinct task/run/index and fallback-ID scopes are covered, including an
ID-only row whose ID matches an indexed row's ID.

Docs and specified code comments label workflow_progress/workflow_agent and
system/task_summary as undocumented internal Claude Code extensions, absent
from a stable public SDK contract and changeable/removable in any patch
release. Version qualification is explicit: original 2.1.296 archive plus
2.1.312 embedded-schema evidence; no fabricated new recorded 2.1.312 fixture.
The optional new live recording has not been claimed or run.

Full runtime race PASS (84.787s, 93.3% package statements); CLI consumer race
PASS (1.077s); staged lint/vet/secret/links PASS; archive replay PASS (325
normalized events, 55 lines), now showing stable index + ID attribution.
Changed identity/format/render/merge functions 100%; task decoder 98.6%,
status decoder 93.2%. Artifacts /tmp/fullsend-8913-wayne-{red,focused,runtime,
cli,lint,replay}.log and .cover profiles.

Read-only claude-opus-5-5 review completed in 76.97s, exit 0/is_error false,
with staged/worktree hashes unchanged. Verdict: both human comments fixed,
no material defects. Receipts /tmp/fullsend-8913-wayne-claude-review-20261029/.
After review only comment wrapping/evidence wording and the existing identity
isolation fixture were polished; no further production behavior changed.
Focused race tests and staged lint repeated after that polish.

## Publication complete

Final focused race regressions after non-behavioral polish PASS (1.553s);
final staged lint/vet/secret/link checks PASS. All commit hooks PASS.
Created signed-off a4c6474662cc93b5d2401cfa0544f9d56d7b9faf,
fix(#8908): keep Workflow agent rows stable by index. Pushed normally to
origin/fix/8908-claude-workflow-progress. Remote ref and fresh PR8913 API
head readback both match this exact SHA; component checkout clean.

Refreshed PR description's AFTER example from the current model-free archive
replay so it shows stable #index (ID), preserving the rest of the body. Added
the explicit undocumented/internal protocol and patch-release caveat. Exact
body/title/head verified by GET after PATCH; no reviewer replies, thread
resolution, labels, merge or deployment. Publication receipts:
/tmp/fullsend-pr8913-wayne-description-20261029/.

Both human findings addressed. The optional newly recorded live 2.1.312
fixture is not supplied or claimed; evidence/qualification limits are explicit
in source, tests, docs and PR description. Broader event scope retained.
