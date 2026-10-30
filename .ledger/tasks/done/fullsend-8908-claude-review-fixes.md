# Resolve Opus 5.5 review findings for the Fullsend progress patch

Owner authorized fixing the findings on 2026-10-29. Component branch remains
fix/8908-claude-workflow-progress; no commit, push or PR requested.
Read-only Opus 5.5 review (472.32s, $1.9684758) is retained in
/tmp/fullsend-8908-claude-implementation-review-20261029/review.md;
reviewed staged patch/worktree hashes matched at completion.

Actionable findings reproduced before fixes:

- Duplicate terminal task messages drop prior tool/error context.
- Repeated unkeyed warnings/denials/notifications are mistaken for snapshots.
- Requesting/null cycles add per-request console and CI chatter.
- Late first run_id splits unknown-run identity and loses hidden/terminal
  metadata; unannounced new runs misroute later run-less completion.

Red regressions: /tmp/fullsend-8908-review-red.log. All four categories failed
on the reviewed implementation; the optional-run hidden exposure is therefore
confirmed with a synthetic stream, not merely a speculative source concern.

Fixes underway also isolate subtype wire fields, sanitize final composed
messages, share the output sink, wrap the doc link, and ensure real task starts
reset matching agent state. Cache eviction and upstream-truncated credential
fragments remain documented/unverified qualification concerns; no claim of
universal compatibility with future producer schemas.

- [x] Reproduce actionable review findings.
- [x] Implement fixes and regressions.
- [x] Runtime/CLI race tests, coverage and staged lint/vet/link checks.
- [x] Replay original archive and inspect final scope.
- [x] Follow-up read-only Opus 5.5 review of the repaired patch.

## Implementation and validation

Terminal notifications are partial updates; prior tool/error context survives,
and worker_restart explicitly replaces the detail. One-off messages with no
usable ID bypass state deduplication. Requesting events are ignored; null
status can only recover a previously tracked compaction state. Optional run
IDs promote unknown-run rows in place, and known old runs cannot steal the
current run's run-less updates. Explicit starts reset matching agent state;
new unannounced runs inherit a prior hidden task classification.

Status wire decoding is isolated per subtype, final composed strings are
sanitized, the progress output sink is shared, and the runtime docs link is
wrapped. Existing identity test now supplies two explicit run IDs when it
means two distinct runs; a first late ID is correctly treated as promotion.

Runtime race suite: PASS (83.894s, 93.3% package statement coverage).
CLI display-path race checks: PASS (1.069s). Final staged lint, vet and link
checks: PASS. Original archive replay: PASS, 325 task/agent events / 55 display
lines, expected phase names and completion preserved. No raw archive writes.
Changed identity/renderer/sink functions: 100%; status decoder 92.9%, task
decoder 98.0%, shared parser 93.5%. Diff checks pass.

Logs: /tmp/fullsend-8908-review-{red,focused,runtime,cli,lint,replay}.log;
coverage: /tmp/fullsend-8908-review-runtime.cover. Follow-up read-only Opus 5.5
review is running under /tmp/fullsend-8908-claude-review-fixes-20261029.
Earlier full CLI suite timeout remains a qualification limit; no timeout
ceiling changes or unrelated full-suite rerun.

## Follow-up review and final restart edge

First follow-up Opus 5.5 review completed read-only in 166.45s ($0.73263),
with patch/worktree hashes unchanged. It verified terminal merges, occurrences,
quiet status cycles, subtype isolation and composed-message sanitation. It
found F1: a new anonymous start erased named old-run history, allowing a late
known old run to adopt the restart. The exact new synthetic regression failed
before the correction (/tmp/fullsend-8908-review-f1-red.log).

Corrected the identity helper to preserve named-run rows across anonymous
starts and check known-run history before anonymous promotion. Only unseen
explicit runs can adopt anonymous rows. Focused progress race regressions
pass (1.701s). Final full runtime race suite, staged lint and replay repeated;
Opus 5.5 is independently verifying this final delta in
/tmp/fullsend-8908-claude-final-review-20261029.

## Completion

Final runtime race suite PASS: 92.238s, 93.3% package statements. Final staged
lint/vet/links PASS. Final verified original-stream replay PASS: 325 task/agent
events and 55 display lines, expected phase names/completion preserved.
Final focused regression race run PASS (1.701s); earlier CLI display-consumer
race run PASS (1.069s). No runtime API or CLI wiring changed after that check.

Final Opus 5.5 review completed read-only in 52.61s
($0.216989), exit 0/is_error false. Verdict: F1 resolved, no
new material defect and no blocker on the final delta. Staged patch and
worktree hashes both remained identical throughout the review. Final review
and receipts: /tmp/fullsend-8908-claude-final-review-20261029/.

All actionable findings requested by the owner are repaired. Remaining
qualification limits (the previous full CLI timeout, producer-truncated
opaque credential fragments, schema-only newer status qualification and
bounded-cache eviction) remain explicit, not claimed resolved.
Fourteen intended component files remain staged on
fix/8908-claude-workflow-progress. No commit, push, PR, or deployment.

## Owner-authorized commit and push

Owner explicitly requested commit and push after review completion.
Created DCO-signed commit `7f266ee9f` (fix(#8908): render Claude Workflow
progress), with all pre-commit and commit-message hooks passing. Pushed
`fix/8908-claude-workflow-progress` to origin
`git@github.com:jctanner-fullsend-ai/fullsend` and set upstream tracking.
No PR created or deployment performed. Component checkout clean.

## Owner-opened upstream PR and requested description examples

Owner opened https://github.com/fullsend-ai/fullsend/pull/8913 at exact head
7f266ee9f7d5835b44f17986c365d6bb7546e1fc and requested BEFORE/AFTER fullsend
run examples. Updated the PR body with actual recorded pre-fix heartbeat
lines and selected lines from the final patched parser's replay of the same
captured stream (325 task/agent events, 55 display lines). Explicitly labeled
the after example as model-free replay, normalized the before log's runner
prefix/emoji encoding, and marked elisions. Full nested output and producer
filter limits, runtime-vs-business completion distinction, exact validation
commands and earlier full CLI timeout limitation are retained.

Filled the empty Summary/Changes/Testing/Related Issue template sections with
verified facts; DCO/title checks marked, human authorship/explanation checkbox
left for the owner. Title and head unchanged. PATCH succeeded and fresh GET
verified the exact full body. Prepared text, token-free credential scan,
before/update/readback receipts: /tmp/fullsend-pr8913-description-20261029/.
No source changes, commits, model runs, comments, merges or deployments.
