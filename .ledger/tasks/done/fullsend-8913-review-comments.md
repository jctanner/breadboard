# Address upstream PR 8913 review comments

Owner requested addressing review comments and explicitly excluding the scope
creep objection: broader runtime display coverage was owner-authorized.
PR: https://github.com/fullsend-ai/fullsend/pull/8913
Base/head at start: clean fix/8908-claude-workflow-progress, 7f266ee9f.
Review snapshots: /tmp/fullsend-pr8913-reviews-20261029/.

Action plan:

- [x] Reproduce/fix Qodo sparse hook identity (4416426231), sparse agent
  context/presence and clearing (4416426245), distinct-run hidden inheritance
  and agent/parent conflation (4416426213).
- [x] Generate synthetic pattern-redaction fixture rather than storing a
  credential-shaped literal (4416426201); preserve fallback scanner coverage.
- [x] Document repeated snapshots for custom OnEvent consumers (4416624215).
- [x] Move event types to event.go and update interface tests (4416624223).
- [x] Move shared output helper to renderer.go (4416624231).
- [x] Move generic renderer tests out of Claude wire tests (4416624238).
- [x] Fix decoder doc-comment prefix (4416624245).
- [x] Validate runtime/CLI race tests, coverage, staged lint/vet/links/replay.
- [x] Read-only Opus 5.5 review, fix any material follow-up findings.
- [x] Signed-off follow-up commit and push to the existing PR branch.

Scope-creep 4416624206 is deliberately not implemented per owner instruction.
No review replies, thread resolution, dispatch labels or merge authorized.
Existing commit/push authorization remains in force for this PR work.

## Implementation and validation

All three Qodo behavior findings reproduced before fixes in
/tmp/fullsend-8913-review-red.log. Sparse hook identity is retained as bounded,
sanitized subject/context by hook ID, with explicit clearing. Workflow agent
wire presence maps into Set flags for labels, phases, tools, errors and boolean
metadata; absent fields preserve prior display context, explicit empty/false
clears, and changing tool name does not retain a different tool's old summary.
A distinct named run has independent visibility; promotion of anonymous rows
still retains SAME-generation hidden/terminal state. Hidden agent events
retain their own key and cannot substitute for parent task state.

Moved event definitions into event.go, added interface coverage (including
the previously unlisted fallback type), moved printProgress into renderer.go,
and moved runtime-independent tests into task_progress_test.go and
status_progress_test.go. Wire tests stay under claude_* files. Task event docs
state repeated-snapshot/custom-consumer reconciliation semantics. The decoder
comment starts with its function name. Scanner-shaped fixture is generated
from a fixed prefix and repeated zeros, preserving fallback scanner coverage
without a complete credential-shaped literal stored in source.

Focused race regressions PASS (1.785s); full runtime race PASS (84.546s,
93.3% package statements); CLI iteration event consumer race PASS (1.071s);
staged make lint/vet/secret/Markdown links PASS; original archive replay PASS
(325 normalized task/agent events -> 55 lines). Changed render/merge/identity
functions 100%; task decoder 98.6%, status decoder 93.2%. Diff checks PASS.
Logs: /tmp/fullsend-8913-review-{red,focused,runtime,cli,lint,replay}.log and
runtime/focused .cover profiles. Read-only Opus 5.5 review running at
/tmp/fullsend-8913-claude-pr-review-20261029/ against the exact staged delta.
No model-driven live Workflow run, dispatch label, E2E approval bypass,
review reply, thread resolution, merge or deployment. Existing full CLI
suite timeout qualification remains unchanged.

## Opus follow-up, final verification and publication

Initial read-only Opus 5.5 review confirmed the PR fixes but identified a
recovery edge: omitted error/blocked/cached metadata could persist after a
state transition. The suggested retrying -> running -> completed regression
failed before correction (/tmp/fullsend-8913-recovery-red.log). Made those
three fields state-relative: same-state sparse snapshots retain known values;
state changes clear omitted transient metadata, and explicit supplied/cleared
values still apply. Added a direct hidden-agent/visible-parent renderer test
and clarified the event contract and user docs.

Final focused race checks PASS (1.769s); final full runtime race PASS
(83.209s, 93.3% statements); final CLI consumer race PASS (1.074s); final
staged lint/vet/secret/links PASS; original archived stream replay PASS
(325 normalized task/agent events, 55 display lines). Changed merge/render/
identity helpers 100%; task decoder 98.6%, status decoder 93.2%.

Final read-only claude-opus-5-5 review completed in 54.98s,
exit 0/is_error false, and confirmed the material recovery issue fixed with
no new material defect. Patch and worktree hashes unchanged during review.
Receipts: /tmp/fullsend-8913-claude-final-review-20261029/.

Created signed-off commit 8e1fd40284bcb17184bd10633d3da6f9b9888cd5,
fix(#8908): preserve sparse progress metadata; all commit hooks PASS. Pushed
normally to origin/fix/8908-claude-workflow-progress. Remote ref and upstream
PR 8913 API readback both match that exact SHA; component checkout clean.
Broader event scope deliberately retained. No review replies/resolutions,
labels, merge, live Workflow inference, or deployment performed.
