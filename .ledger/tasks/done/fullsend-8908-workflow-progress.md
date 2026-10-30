# Fix Fullsend Workflow progress display

Owner authorized a feature branch and implementation in the rebased fork
checkout `checkouts.tmp/jctanner-fullsend-ai/fullsend` on 2026-10-29.
Base: clean main `d70721c50`; branch `fix/8908-claude-workflow-progress`.
Upstream bug: https://github.com/fullsend-ai/fullsend/issues/8908.

- [x] Read component instructions and relevant runtime/Go/documentation guidance.
- [x] Create isolated feature branch from the provided rebased main.
- [x] Reproduce missing live output with a no-inference regression.
- [x] Normalize task lifecycle and agent progress without treating declared
  phases as executed or changing usage accounting.
- [x] Render sanitized, bounded, deduplicated progress with concurrent identity.
- [x] Cover malformed/unknown events, terminal states, unchanged snapshots,
  redaction, metrics non-interference, and raw-stream preservation.
- [x] Update user documentation; run tests/race/vet and staged lint.
- [x] Verify patch coverage, final diff, and scope.

No live inference, runtime deployment, or schedule change is needed for this
parser/rendering fix. Publication has not been requested in this task.

## Implementation and evidence

Eight staged component files add normalized task lifecycle/Workflow agent
progress, bounded per-identity snapshot deduplication, sanitized and redacted
console/CI display, and user documentation. Static declared phases do not
become live progress. Prompt/result bodies and task usage counters are not
rendered or counted. The CLI supplies its existing opaque credential literal
redactor before normalization/truncation.

The new console regression failed against the base parser (empty display),
then passed after implementation. Focused regression tests pass. Runtime
race tests pass with 93.1% package statement coverage; all new parser and
renderer logic functions have 100% coverage (the empty interface marker has
no behavior). Staged `make lint`, including Go vet and offline Markdown links,
passes after installing the Makefile-pinned lychee 0.24.2 binary in `/tmp` and
verifying its SHA256 against the Makefile.

A model-free Go overlay test replayed the original archived stream, checking
SHA256 `2c8e2a453ac963664605c284b7721056fb9ebfaf72238d899fc3a3549236fe70`.
It produced 325 normalized task/agent events and 65 deduplicated display lines;
Read, Create, Refine, Push, Score, Review, Result, and completed were present.
The original archive was only read. The replay harness and rendered output
remain in `/tmp`; no private run artifacts enter the fork.

Validation artifacts: `/tmp/fullsend-8908-{runtime-tests,lint,replay,go-test}.log`,
`/tmp/fullsend-8908-runtime.cover`, `/tmp/fullsend-8908-archive-console.log`.
Full `make go-test` ran its default race/coverage suite but exceeded Go's
10-minute timeout in `internal/cli` (600.297s). No assertion failure or race
was reported; the runtime package passed within the full run (81.778s,
93.1%). The active test was
`TestRunAgent_VertexPreservesExistingGCPCredentials`, stopped in existing
`resolveToken` / `gh auth token` setup at run.go:564, before the changed
rendering code. A read-only Go overlay restored all changed source to main
and hid the new files: that isolated existing test passed on main (7.226s)
and on the patch (7.220s), with the same sandbox retry behavior. This
isolated comparison does not establish a passing full baseline suite.

The separate GitHub-tagged mintcore race/coverage suite passed (46.115s,
91.8%). Main make stopped before reaching it, so it was invoked separately
with the same environment settings and flags. Full-suite timeout remains a
validation limitation; no suite timeout was raised and no tests were skipped.
The generated partial coverage file was retained under `/tmp` and removed
from the checkout; only the eight intended source/doc files remain staged.
Changed parser function coverage is 93.3%, renderer dispatch 100%, and new
logic functions 100%; CLI run.go is excluded by the existing Codecov policy.
`git diff --check` and `git diff --cached --check` pass.
No model invocation, commit, push, PR, deployment, or upstream issue edit.

Local implementation complete; upstream bug remains open until delivery.
