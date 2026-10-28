# Fix the two approved findings on 0d60824

Read-only review check on 2026-10-26. PR #85 is open, non-draft and conflict-free
at 0d608244f57f831e66c30c8ba4b2890ec5f2cb56. Current-head Python 3.11/3.12,
lint, Unicode and DCO checks all passed. Review still requests changes.

Full pagination: 48 reviews, 139 inline, 27 regular comments. Since the a0158d9
snapshot: two review submissions in one automated round, six new inline
comments, one new regular completion comment and three updated sticky comments.
Raw snapshot: /tmp/strat-pr85-post0d608-review-20261026T221617Z.json.
Review: https://github.com/fullsend-ai/strat-creator/pull/85#pullrequestreview-5659641749.

## New finding

[4382955258](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4382955258),
medium, scripts/lock_issues.py:198: a human gate added between the initial RFE
label read and owned lock write is visible in the final read, but lock_owned
checks only ownership/processing there and still returns the RFE as acquired.
The initial/resumed-owned path does reject human gates; the post-write check
omits them. Source inspection supports the narrow race. No runtime reproduction
yet; do not claim an observed production failure or atomic Jira lease.

Suggested next work: inject needs-attention/sign-off during the acquisition
write, ensure no work is authorized, and retain the durable candidate record
so owner-checked cleanup can release this run's claim. Consider both fresh
acquisition and recovery while preserving foreign-owner refusal and batch
cleanup behavior. A new baseline must not legitimize the intervention.

## Resolved and repeated

The new rollup explicitly resolves all three previous findings: publication
ancestor symlinks, malformed Jira labels and CLAUDE.md wrapping.

Other inline comments repeat accepted Org Pulse TLS/Jira authority, broader
allowlist trust, deferred missing CI source and pending-reviewer semantics.
The pending comment now asks for schema documentation. artifact_utils.py
already includes pending in the enum and CLAUDE.md explains its provisional
meaning; downstream consumers were tested. However, source inspection finds
the declarative types/rfe-strategy/type.yaml still lists only approve/revise/
reject for reviewers.* and claims the enum matches recommendation. This is a
concrete descriptor/runtime mismatch to align, rather than an observed consumer
failure. See [descriptor bug](../../bugs/open/strat-review-type-pending-enum.md).
Tracking-issue/protected-path process comments repeat prior requests. Preserve
owner-approved scope; do not fabricate issue links or approvals.

No source edits, model calls, live Jira writes, public replies, thread resolution
or PR merge in this check. Component remains clean.

## Authorized implementation

Owner approved the lock-acquisition race and descriptor/runtime alignment.
Bounded audit covers the initial, recovered and final acquisition reads, durable
candidate records and owner-checked release. Retain numeric-only approval and
the previous accepted/deferred scope. No paid model smoke, live Jira writes,
public reply, deployment or merge.

- [x] Reproduce human intervention during fresh and recovered acquisition.
- [x] Reject final human gates and preserve candidate records for cleanup.
- [x] Align and document pending/skipped reviewer enums without changing numeric recommendations.
- [x] Run focused checks and one full offline suite; scan, archive, commit and push.

Red: 19 failures, two passing controls. Focused green: 172 passed. Bounded
audit/fix covers acquisition reads, candidate persistence, matching-baseline
source-RFE writes and real host cleanup; shared label validation used. Descriptor
parity and recommendation-vocabulary checks pass. Single final full suite:
1,434 passed, six optional skips in 564.24s. Signed-off 364e1ca pushed/read back
on PR #85, non-draft and conflict-free; component clean. Source/staged patch and
17-file evidence archive scanned with zero credentials; hashes and byte
readback verified, publication receipt sealed separately. DCO passed, other
new-head CI pending at publication. No model calls, live Jira writes, deployment,
public replies or merge. Accepted/deferred scope unchanged.
Details: [implementation and evidence](../../notes/strat-pr85-lock-schema-20261026.md).
