# Fix the three approved findings on b8d67c3

## Evidence and status

Latest review [5657803549](https://github.com/fullsend-ai/strat-creator/pull/85#pullrequestreview-5657803549),
submitted 2026-10-26T19:27:03Z on b8d67c334697dc3297c67b608584f4d4dd600060.
Fetched all pages: 44 reviews, 125 inline comments, 25 regular comments.
PR remains ready for review and conflict-free; changes requested. Current-head
Python 3.11/3.12, lint, Unicode and DCO checks all passed.

Raw read-only API snapshot: /tmp/strat-pr85-postb8-review-20261026.json.
No source edit, reproduction, paid run, remote reply or thread resolution in
this status check. Checkout remains clean on the correct PR branch.

## New findings to address

| Comment | Assessment from current source |
| --- | --- |
| [4381545482](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4381545482) | Live STRAT freshness omits labels. Human sign-off added during a run can escape freshness verification. Need a regression at a real mutation boundary. Distinguish pipeline-owned needs-attention/verdict changes from external human gates so ordinary review publication does not invalidate its own progress. |
| [4381545489](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4381545489) | Identified results publication still copies directly into its final destination. A truncated destination causes persistent conflict on recovery. Same failure class as the now-fixed summary write, in a different code path. Verify interrupted-copy behavior, then use a verified atomic sibling copy while retaining genuine-conflict refusal. |
| [4381545501](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4381545501) | Missing/empty lock_owner bypasses check_owner. Normal preparation supplies it and managed freshness protects prepared parameters, so this is malformed-input hardening rather than proof of an ordinary managed bypass. Require valid ownership for actual managed live input while retaining explicit standalone/local behavior. |
| [4381545524](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4381545524) | CI validator defaults absent source to web. Low-priority hardening: actual GitLab supplies this value, and live mutation/publication still require explicit flags. A strict CI interface can reject missing source without changing standalone harness semantics. |

## Repeats and scope

- TLS bypass and sandbox Jira authority repeat owner-accepted security scope.
- Repository-wide remote prefixes are broader than currently needed; this is
  allowlist hardening/scope documentation, not an observed untrusted-resource
  load. The owner explicitly requires following upstream main after merge;
  do not turn this into a new commit-pin requirement.
- Pending reviewer fields are intentional, documented in CLAUDE.md and tested
  through JSON/report/dashboard consumers. Preserving stale prior verdicts
  would break current-run provenance. No new implementation defect is shown.
- Tracking-issue/protected-path approval findings remain process requests;
  do not fabricate an issue, approval or changed owner scope.

The new Fullsend rollup marks numeric version ordering and inherited DRY_RUN
resolved. Qodo marks interrupted summary writes and the missing-review lookup
resolved; its only active bug is the accepted Org Pulse TLS exception.

## Authorized implementation

Owner requested fixes for exactly the three substantive concerns. The missing
CI source default and broader allowlist/security/process comments remain outside
this implementation. No paid model smoke or live Jira action is authorized.

- [x] Reproduce late human gates at a real mutation boundary, preserving own verdict writes.
- [x] Reproduce partial publication copies; retain genuine conflict protection.
- [x] Reject missing/empty/malformed managed ownership; preserve explicit standalone use.
- [x] Run focused regressions and the full offline suite; archive evidence.

Prepared live inputs must not opt out of ownership. Human sign-off must never
be normalized away. Needs-attention is both a human gate and a pipeline verdict;
only a matching current-run pending/verified effect may explain that transition.

Corrected red run: 27 failures, 5 controls passed. Focused suite: 129 passed.
Full-suite discovery found an old shared host fixture without ownership and with
preloaded verdict labels (34 dependent setup failures, 1,360 other passes).
Corrected that fixture to use owned RFEs and real publisher-applied verdicts;
11 focused host/readback checks pass. Final full suite: 1,394 passed, six optional
skips, 534.95 seconds. Copies stage inside .git, outside the immutable run
inventory, before atomic replacement.

Signed-off a0158d937af4e87a7d5ee51e2b67e2485ffc98a3 pushed to PR #85 and read
back over Git and the GitHub API. Conflict-free, ready/non-draft; new-head remote
checks had not yet appeared at publication time. Component clean. Source/staged
patch and 25-file evidence archive scanned with zero credentials; manifest and
readback verified. Publication receipt sealed separately. No paid model calls,
live Jira writes, deployment, cutover, public comment/reply or PR merge.

Details: [implementation and evidence](../../notes/strat-pr85-three-concerns-20261026.md).
