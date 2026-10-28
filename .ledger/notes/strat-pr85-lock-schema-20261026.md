# PR #85: owned RFE human gates and reviewer type contract

Owner approved exactly the two reported items after the 0d60824 review, with
one bounded audit of acquisition/release. No new sandbox redesign, accepted TLS
change, allowlist change, paid run, live Jira action, public reply or merge.

## Lock acquisition and nearby recovery paths

Reproduced needs-attention and human-sign-off arriving after the first read in
fresh and recovered acquisition. The final read checked owner/processing only.
It now also rejects human gates before returning any acquired key. Failure
retains the durable candidate list, including earlier successful claims, for
the actual host cleanup script. A recovered owned claim is recorded before
rejecting an already-present gate, so a rebuilt local record still permits
owner-checked cleanup. Foreign/conflicting owners remain refused.

The bounded audit covered initial/recovery/final reads, durable record writes,
the preparation wrapper's nonzero handling, downstream owned mutations and the
host release script. The lock reader now uses the existing strict label-list
validator. Owned mutations reject a source RFE human gate even if it was
captured in the initial freshness baseline. STRAT's exact current-run verdict
recovery exception remains intact; it does not apply to source RFE gates.
Cleanup remains separate from work freshness and preserves human/unrelated
labels. Tests use real local Jira writes and the actual release script twice
to verify reconciliation and idempotence.

Jira label checks are conflict detection and recovery guards, not an atomic
lease. The change does not claim to eliminate every inter-request race or
contain a compromised agent with its own token/code access.

## Reviewer descriptor

Align types/rfe-strategy/type.yaml with artifact_utils.SCHEMAS: all reviewer
roles accept pending, and architecture also accepts skipped. Comments explain
their meaning as provisional/absent context rather than inferred approval.
No runtime enum expansion or numeric decision change. Numeric recommendation
remains approve/revise/reject. A parity regression compares independently
maintained descriptor fields with runtime; a separate control keeps provisional
values out of the recommendation enum.

## Verification

Before fix: **19 failures, two passing controls** in 13.74 seconds. The controls
cover conflicting ownership and the unchanged recommendation vocabulary.
Cases include fresh/recovered/already-gated claims, cleanup of earlier batch
claims, malformed labels, and gated RFEs already present in a valid baseline.

Focused suite: **172 passed** in 160.79 seconds. The single final full offline
suite passed: **1,434 passed, six optional skips** in 564.24 seconds, with the
model-calling smoke disabled. Ruff, descriptor validation and git diff --check
pass. No model calls or live Jira writes.

Signed-off commit: 364e1cab4917dc2d5a6e84699be7d24fecaa02b3. Five source files
and the staged patch passed the local-credential/pattern scan before commit
(zero findings). Component worktree clean. Evidence destination:
var/run-data/20261026-strat-pr85-lock-schema/.

Sealed 17 files before push, zero credential findings, manifest and byte
readback verified. Pushed 364e1ca normally; Git and the GitHub API confirm the
exact PR head. PR #85 remains open, non-draft and conflict-free. DCO passed;
other new-head CI checks were pending at publication. Separate sealed receipt:
var/run-data/20261026-strat-pr85-lock-schema-publication/.
