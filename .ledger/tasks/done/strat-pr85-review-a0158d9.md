# Fix the three approved new findings on a0158d9

Read-only status check on 2026-10-26. PR #85 remains open, non-draft and
conflict-free at a0158d937af4e87a7d5ee51e2b67e2485ffc98a3. Python 3.11/3.12,
lint, Unicode and DCO checks passed. The reviewer still requests changes.

Fetched all pages: 46 reviews, 133 inline comments, 26 regular comments. Compared
with the preserved b8d67c3 snapshot: two new review submissions in one automated
round, eight new inline comments, one new regular completion comment and three
updated sticky comments. Snapshot:
/tmp/strat-pr85-posta015-review-20261026T210330Z.json.

## New reported concerns

- [4382320349](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4382320349),
  medium: results publication checks files but not every destination ancestor.
  A directory symlink tracked in the data repository could redirect writes
  outside the results checkout. Requires write access to that repository;
  predates the latest commit. Source inspection supports reproducing this path:
  mkdir/copy/replace precedes the manifest's ancestor-symlink check.
- [4382320355](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4382320355),
  low: require labels to be present and a list of strings before gate checks
  and freshness capture. Missing currently defaults to empty; a string becomes
  characters. Null currently errors rather than silently passing. Normal Jira
  responses provide a list; this is malformed-response hardening.
- [4382320374](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4382320374),
  low: reflow the long CLAUDE.md freshness paragraph.

No reproduction or implementation in this status check. No source changes,
model calls, live Jira writes, PR comments/replies or thread resolutions.

## Resolved and repeated findings

The latest Fullsend rollup explicitly marks late STRAT human gates, interrupted
artifact copying and missing managed ownership resolved by a0158d9. Qodo's
remaining active bug is the accepted Org Pulse TLS exception.

Other new inline comments repeat Org Pulse TLS, general Jira authority,
repository-wide allowlists, the deferred missing CI source default and pending
reviewer semantics. The latter is already documented and covered through its
downstream consumers. Tracking-issue/protected-path requests also repeat prior
process findings. Preserve owner-approved scope and upstream-main requirements;
do not fabricate an issue or reviewer approval.

Latest review:
https://github.com/fullsend-ai/strat-creator/pull/85#pullrequestreview-5658796463.

## Authorized implementation

Owner approved fixes for the three new items. Repeated TLS, general Jira
authority, allowlist, pending-reviewer and process findings remain outside scope.
No model calls, live Jira writes, public replies, deployment or merge.

- [x] Reproduce tracked destination-parent symlinks and preserve ordinary publication/recovery.
- [x] Reject missing, null and malformed labels before gate checks or freshness capture.
- [x] Reflow the freshness paragraph without changing its instructions.
- [x] Run focused checks and the full offline suite; scan credentials, archive, commit and push.

Red: 19 failed and one control passed. Retained four escaped artifact hashes
from actual local cloned-repository fixtures. Green focused: 148 passed. Shared
path checks run before saved-state reads and all copies; a common list-of-strings
validator protects Jira gate, ownership and freshness checks. Static checks pass.
Full offline suite: 1,413 passed, six optional skips in 545.67s. No model calls
or live Jira writes. Signed-off 0d608244f57f831e66c30c8ba4b2890ec5f2cb56
pushed normally and read back over Git/GitHub. PR #85 remains non-draft and
conflict-free; component clean. DCO passed, remaining new-head CI pending at
publication time. Six changed source files/staged patch and the 19-file evidence
archive scanned with zero credentials. Archive hashes/readback verified, plus
a separate sealed publication receipt. No public reply, deployment or merge.
Details:
[implementation/evidence](../../notes/strat-pr85-path-label-20261026.md).
