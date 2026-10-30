# PR93 creation and review-recorder boundaries

Owner authorized reproducing the two new medium automated findings, fixing
them, then local Claude review. Model preference remains claude-opus-5-5.
Start: clean feat/isolate-stale-batch-tickets at 17a684f.

- Gate after preparation but before first record-create: verify candidate
  identity/source/ownership and host change evidence, retain unaffected records.
- Typed freshness during review/publication verification: preserve it through
  internal recorder calls so batch recovery can reconcile it independently.
- Cover retries, unrelated failures, forged/unprovable deferrals and ownership
  conflicts. Numeric approval policy and shared/unreadable failure behavior stay.
- Focused regressions, lint/type/schema, independent read-only Opus 5.5 review,
  then full make test on the final source. No paid Workflow smoke or live Jira.
- Archive review/source/test receipts after credential scanning. No public
  comment, merge, schedule change or automatic deployment.

Comments: discussion_r4406334441 and discussion_r4406334447, review 5690011195.
GET snapshot: /tmp/strat-pr93-review-refresh-20261029T010115Z/.

Reproduced: initial 12-case set had ten failures and two existing gate controls
passing on 17a684f. Eight first-record creation cases and RFE edits in both
recorder verification paths fail. Red log: /tmp/strat-pr93-recorder-red.log.

Local repair: creation stages candidate mappings, records unaffected snapshots,
and verifies only typed ticket drift against a unique owned expected source
and independent host evidence. Missing human snapshots remain absent. Evidence
discovery uses create pairs, so host verification/retries recheck an unbound
deferred candidate. A final batch check catches late/shared input changes.
Review and publication verification re-raise typed errors before generic CLI
formatting, preserving prepare-reviews' existing independent reconciliation.

Twenty-five new cases cover before/during creation, existing/new STRATs, sign-off
and attention gates, retries, source/ownership/link/history/old-gate controls,
both review verification phases, genuine RFE/gate changes and unproven claims.
First repaired set: 12 passed. Full focused set: **95 passed**, 367.67 seconds.
Lint/type/schema pass. Source is uncommitted on the same feature branch.

First Opus 5.5/high read-only review confirmed both original reported cases
repaired. It identified two related boundaries: a structured SME edit before
the first create snapshot, and an external needs-attention label arriving at
the publication verifier's label read. Both reproduced. The initial SME test
used an emulator plain-text description without heading semantics; that
history correctly cannot prove SME drift. The recovery test now uses the
existing structured-ADF SME fixture. Unrecognized history stays fail-closed.

Creation now types only the create-phase SME mismatch, preserving independent
source/owner/change proof and leaving malformed frontmatter fatal. It also
rejects a typed error scoped to another RFE. Publication checks live human
gates on the same label read before numeric verdict consistency; its own
current-run attention effect remains exempt. Generic verification failures
are not reclassified. New set: **30 passed**, 177.18 seconds, including a local
SME edit with no Jira change, which correctly remains fatal. Independent
Opus 5.5 verification of the follow-up corrections is running; full final
suite and evidence archive remain pending.

Final Opus 5.5/high verification completed in 187.54 seconds, source unchanged:
no remaining material defects; both original findings and both follow-ups
resolved within the stated independent-evidence limits. Completed review calls
report $2.0208774 and $1.1219686 (CLI list-price estimates). A preceding
verification attempt was interrupted because the capture runner assumed every
event.message was an object; a permission-denied status uses a string. Fixed
the capture code and restarted the read-only review. Its partial stream/usage
is retained separately; no final cost result exists for that attempt.

Reviewer noted the local-only SME negative test could assert its exact error
message more strongly. It already requires failure, no saved progress and no
Jira description mutation; positive recovery/owner/history controls exercise
the associated paths. This is a nonblocking test-strength suggestion. No
additional runtime changes were needed after final review. Full make test is
running on that unchanged source with model-calling smoke disabled.

Completed locally: **1,566 passed, six skipped**, 1,062.92 seconds (17m42s),
`env -u STRAT_WORKFLOW_SMOKE make test`, exit zero. Final lint and descriptor
schema checks pass; source still matches final Claude verification. No further
implementation changes were made after that review. Component and ledger
diff checks pass.

Evidence archived at
`var/run-data/20261029-strat-pr93-recorder-boundaries/`: **89 files plus hash
manifest**, every copied file verified. Includes both completed reviews, the
interrupted verification stream, original comment snapshot, reproduction and
passing logs, source snapshots/diffs, runner scripts and verification metadata.
All 32 pending PR source files and all retained evidence scanned against
configured credentials/private-key material with zero findings. Separate raw
HTTP/syscall/Kubernetes/MLflow captures were not generated for this local task;
the CLI streams and local emulator test logs are retained.

Changes remain uncommitted on feat/isolate-stale-batch-tickets at 17a684f:
six tracked files modified and one new 30-case regression module. No commit,
push, public PR mutation, paid Workflow smoke, live Jira write, deployment or
schedule change. Aggregate freshness bug remains open pending delivery and
live qualification.

Owner then authorized commit and push. Rechecked exact source/receipt hashes
against the tested archive, scanned all 32 pending PR files and the seven-file
staged patch with zero configured credential findings. Signed-off commit
**e9bcdc3a03af3ae65a0712b8d0a1c5e24cc3f4f8** (`fix: preserve batch recovery at
recorder boundaries`) pushed normally to origin/feat/isolate-stale-batch-tickets.
GitHub GET verification confirms PR93 main base, exact head, all 32 expected
files and mergeable state; local checkout clean. Existing full-suite and Opus
5.5 results apply to byte-identical committed source. DCO, lint and Unicode
checks passed; Python 3.11/3.12 tests and automated review were running at the
03:24:55 UTC readback. Publication receipts archived separately at
`var/run-data/20261029-strat-pr93-recorder-publication/`, **16 files plus hash
manifest**, copied hashes verified and zero configured credential findings.
No merge, public review comment, live smoke, Jira write or schedule change.
