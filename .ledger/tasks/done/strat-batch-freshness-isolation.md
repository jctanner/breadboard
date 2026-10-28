# Isolate stale tickets within a Workflow batch

Owner authorized implementation on a new fork feature branch and an upstream
PR. Start from upstream main. Do not launch paid tests or change the real
schedule as part of this work. Schedule remains legacy.

## Contract

- RFE/STRAT input drift defers only its assigned ticket; preserve the baseline,
  mutation intent and artifacts, stop new writes/work for that ticket.
- Unchanged tickets may finish and publish verified outputs.
- Shared source/instructions, architecture, parameters or provenance failures
  still stop the batch. Unverifiable inputs cannot authorize publication.
- Host validation independently checks deferred and completed inventories,
  including edits after earlier successful steps. Every acquired RFE is accounted
  for; stale artifacts never enter completed publication.
- Failure reporting records a valid failed receipt even when inputs drift,
  without turning failure into publication authorization.
- Later jobs can reprocess changed inputs; never silently rebase the current run.

## Verification

- [x] Regression fails before implementation: edit one RFE in a multi-ticket
  batch after refinement/push; unaffected reviews/publication still work.
- [x] Changes before/during/after review, SME input, unreadable input and shared
  failures covered locally. Cleanup/recovery preserve safety.
- [x] Full `env -u STRAT_WORKFLOW_SMOKE make test`, lint and diff checks pass.
- [x] Commit signed off; secret scan; push and create upstream PR.

Related: [failure evidence](../../bugs/open/strat-batch-freshness-failure-isolation.md).

## Implementation

Branch feat/isolate-stale-batch-tickets starts at upstream main b75e838.
Ticket-specific live checks use the assigned owned RFE; local artifact/
provenance and shared input checks remain batch-wide. Batch helpers record
independently computed `deferred` inventory without rewriting the baseline.
Final results account for all acquired RFEs and exclude deferred artifacts.
The host recomputes deferrals and validates completed work and Jira read-back.
Native completion includes checked deferred RFE identities to reconcile only
those ticket failures; malformed verdicts on fresh tickets remain terminal.

A successful partial batch is reported completed with an explicit deferred
inventory and completed count; all-deferred is zero completed, not all work
finished. Metadata retains reasons. Current writes/composition for a deferred
ticket stop; in-flight calls may finish. Existing approval/human gates remain;
no label clearing or silent re-admission. A later eligible prepared run cannot
reuse a deferred push.

Failed-result reporting preserves a checked failure receipt even for shared
source drift or unreadable live inputs. Failed receipts never authorize host
publication. Successful partial validation now also captures regular files,
progress and mutation intent under host recovery/deferred-* before handoff
replacement; CI retains that recovery tree in its normal native archive.

Model-free red regressions reproduced cross-ticket blockage, suppressed failed
receipts and missing successful-partial recovery. New fault/JavaScript checks
and existing strict verdict tests pass. Final full suite: **1,463 passed, six
skipped**, 652.14 seconds. Final lint/type and diff checks passed. Staged and
committed 25 files scanned against configured credentials and service-account
private key material: zero findings. Root unrelated work remains untouched;
no live job or schedule change.

Signed-off **6ad16b5727abfcec2d5850402fb6cfc0ccaed6d9** pushed to the fork,
clean working tree. [Upstream PR #93](https://github.com/fullsend-ai/strat-creator/pull/93)
targets main; readback confirms exact head, 25 intended files, mergeable. DCO,
lint and Unicode CI passed at collection; Python 3.11/3.12 and automated review
are in progress. PR not merged; original operational bug remains open pending
merge/qualification. Paid smoke remains a separate owner decision.

Evidence: var/run-data/20261028-strat-batch-freshness-isolation/, **25 files
plus manifest**, hashes verified and configured-secret scan zero. Includes red
regressions, first/final full logs, source patch, validation, credential scans
and PR readbacks. Node CI uses the locally tested major version 22.
