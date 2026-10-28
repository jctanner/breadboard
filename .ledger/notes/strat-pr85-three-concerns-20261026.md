# PR #85: late human gates, interrupted copies and managed ownership

Owner approved the three new substantive concerns in review 5657803549 on
b8d67c3. The low-priority missing-CI-source default remains deferred. Accepted
Org Pulse TLS and writable-sandbox/Jira authority scope is unchanged.

## Fixes

1. **Late human gates (4381545482).** Include human-sign-off and needs-attention
   in live STRAT human snapshots. Reject gates when first binding a target and
   at each owned mutation, even before a target has a saved snapshot. Human
   sign-off is never exempt. Needs-attention is exempt only when the exact
   server, target, payload, contract and current-run pending/verified effect
   explains this run's own verdict. Pending covers death after Jira applied the
   label but before local acknowledgement. Ordinary bookkeeping labels do not
   invalidate the human snapshot.
2. **Mid-copy publication (4381545489).** Copy into a unique private file inside
   the data clone's .git directory; fsync, verify the expected hash, then
   atomically replace the destination and fsync its parent. Existing matching
   files are not recopied. A SIGKILL orphan cannot enter the strict published
   inventory or a Git commit. Mismatched existing final bytes still refuse
   recovery and preserve sources. A normal caught failure removes the temporary
   file; abrupt death can leave private temporary bytes in .git.
3. **Missing managed owner (4381545501).** Validate both run_id and lock_owner
   before effect reads, pending intent or mutation. Direct ownership guards
   also reject malformed data. Prepared JSON cannot select standalone behavior.
   A private in-process context type distinguishes an explicitly requested
   standalone persistent journal; ordinary human helpers remain usable.

These are recovery checks within the accepted trust model. Jira has no label
compare-and-swap; matching local intent is not malicious-agent containment or
proof that no other actor touched the same label. Atomic copying assumes the
ordinary data clone filesystem; a cross-filesystem replace fails safely.

## Offline evidence

Corrected pre-fix reproduction: **27 failures, 5 passing controls**. The initial
exploratory log also contains two control failures caused by an incorrect test
attachment-count assumption, corrected before changing implementation. The
pipeline pushes strategy text inline; that fixture retained one review attachment.

Focused fix/recovery suite: **129 passed** in 108.53 seconds. Covers real local
Jira comment/field/attachment boundaries before and after target binding,
wrong-run/server/payload/target and rejected label intents, unconditional sign-off
blocking, own-verdict lost acknowledgement without duplicates, invalid owner
inputs, standalone controls, actual child-process SIGKILL mid-copy, normal copy
failure, bad copied bytes and genuine destination conflicts.

The first full suite found one old shared host-validation fixture that omitted
ownership and preloaded final verdict labels. Its 34 consumers failed during
fixture setup; 1,360 other tests passed and six optional cases skipped. Updated
that fixture to use real owned RFEs, prepared lock_owner and labels applied by
the real publisher. The guards were not relaxed.

Corrected shared-fixture/readback checks: **11 passed** in 45.49 seconds.
Final full offline suite: **1,394 passed, 6 optional skips** in 534.95 seconds.
Ruff, type descriptors and git diff --check pass.

Signed-off commit: a0158d937af4e87a7d5ee51e2b67e2485ffc98a3. The eight changed
source files and staged patch passed an exact local-credential and credential-
pattern scan before commit (zero findings). Component worktree is clean.
No model calls, live Jira writes, deployment, cutover, PR comment/reply or merge.
Evidence sealed before push in
var/run-data/20261026-strat-pr85-human-gates-publication-ownership/ (25 files,
zero credential findings, manifest and byte readback verified).

Pushed the normal PR feature branch without force. Git and GitHub API read back
the exact a0158d9 head. PR #85 is conflict-free and non-draft. GitHub had not
yet listed checks for the new head at publication time. Separate sealed receipt:
var/run-data/20261026-strat-pr85-human-gates-publication-ownership-publication/.
