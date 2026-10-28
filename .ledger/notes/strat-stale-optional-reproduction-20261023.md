# Stale optional review context reproduced on fbbbc6e

## Scope

The owner requested reproduction of comment 4359883142, without a repair yet.
Used clean strat-creator `fbbbc6eb10e67472d15bad0a80b850873bce8d95` and an
external pytest probe. The component checkout is unchanged. No model call,
real GitLab job, live Jira/export action, remote reply, commit or push.

## Reproduction

The probe uses the existing Jira emulator and Fullsend host fixtures, including
the real pre-script: a pinned local source clone, vendored workspace, qualified
RFE gates, owned acquisition and live freshness baseline. Child CLI processes
run with `STRAT_MANAGED_RUN=1`; no freshness helper is mocked or disabled.

1. Create one eligible RFE and linked strategy with a valid prior review attachment.
2. Run normal host preparation; expected skips is empty and freshness is live.
3. Start the real importer. Inject SIGKILL immediately after its normal atomic
   copy publishes the prior review, before task publication or completion.
4. Confirm the local prior review exists, but task and import receipt do not.
5. Delete only the remote review attachment through the emulator API.
6. Retry the normal importer CLI. It exits 0 and writes a completion record that
   omits the review, while the old review remains on disk byte-for-byte.
7. Invoke import again: exit 0 with `already_imported=true`; the stale review persists.
8. Run normal `record-create` and state `read`: both exit 0, including live
   freshness/progress verification. The stale review still exists afterward.

The documented strategy-refine revision branch reads an existing prior review
and uses its findings. This probe establishes that the stale file survives and
remains eligible for that branch; it does not invoke a model or claim to observe
actual model consumption or an eventual strategy-content change.

## Control and result

One clean prepared import with no remote review and no local leftover creates
no review file. It completes with an inventory that correctly omits that file.
Both observation tests pass in 6.71 seconds. A passing reproduction assertion
means the defect was observed, not that implementation correctness passed.

The issue is confirmed in managed recovery, including a real process death and
live freshness checks. Production impact is conditional on interrupted
publication leaving optional context that a subsequent remote read omits.

## Evidence

External probe, logs/XML, CLI outputs, fault marker, original/stale review bytes,
Jira snapshots, prepared run, completion receipt, progress and relevant source
are retained at `var/run-data/20261023-strat-stale-optional-reproduction/`.
Archive includes credential scan and SHA256 manifest. The bug remains open;
no implementation or test file was added to the component repository.
