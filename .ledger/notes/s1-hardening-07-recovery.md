# S1 hardening 7: recover writes without publishing twice

Completed 2026-10-14 on local `eval/s1-hardening` at
`80a11edee190e84775c88c77981b7f19b9ac2e44`. Historical benchmark branches and
pins are unchanged. Fullsend's entrypoint is unchanged.

## The gap

A tool can finish its Jira write before its caller records completion. A crash
in that interval leaves finished external work behind an incomplete agent or
progress record. Restarting the agent alone does not tell us whether to send
the write again. The old path could clone twice, append another review comment
or attachment, release another run's processing label, or publish a new results
directory under a fresh timestamp.

## The repair

`scripts/strat_side_effects.py` writes and fsyncs intent before a pipeline
mutation. Its ledger lives in `tmp/strat-effects/`, independently of Claude's
agent journal. Each retry first checks Jira, and a verified local record also
requires fresh read-back. The same workspace's callers serialize through a
file lock. Run, operation and payload identity must match.

- **Clone and link:** create a searchable clone marker in the ticket's original
  request. Recovery resolves that marker and Cloners links uniquely, then
  finishes a missing link. Multiple matches stop recovery. A pending create
  with no visible match stops rather than assuming search proves absence.
- **Comment and attachment:** reconcile the exact ADF body and named attachment
  bytes. Changed retry summaries or attachment content under the same operation
  slot stop. Duplicate matching remote entries are not silently adopted.
- **Fields and labels:** read back the desired effect before recording success.
  An acknowledged or previously recorded write that is no longer visible needs
  reconciliation. HTTP retries remain available for reads, including POST
  search; mutation requests are not blindly repeated after transient errors.
- **Completed review:** `scripts/publish_review.py` verifies the saved composition
  and source hashes, builds one deterministic summary with dissent, and finishes
  the original comment, full attachment and numeric verdict labels. Recovery
  skips scoring and specialist generation. Numeric scores remain the sole gate.
- **Ownership:** host lock intent precedes acquisition. A run owner label is
  rechecked at each pipeline write; cleanup requires the matching owner. Foreign,
  mixed and orphaned claims are not cleared automatically. Repeated preparation
  preserves the verified run; lost host receipts and outstanding lock intent
  stop preparation before it erases recovery data.
- **Results:** the host seals the validated handoff and generated reports once.
  Publication uses `RHAISTRAT/run-<run_id>` and an immutable content manifest.
  Partial copies, local commits awaiting push and already accepted pushes reuse
  the same run. Different content under that identity fails. Summary discovery
  accepts these directories and reuses a saved generation timestamp, so a
  post-script retry does not manufacture another summary commit. Reconciliation
  does not move `current` over a newer committed run; interrupted pointer updates
  can still finish. The whole post-script serializes within its host workspace.

The Skills now use these helpers for writes and do not fall back to an MCP
mutation or a raw POST after an error. This is application recovery, not a
security sandbox against arbitrary code executing with Jira credentials.

## Validation and spend

The final required `make test` suite passes **966 tests**, with seven opt-in or
unavailable-tool checks skipped, in **221.36 seconds**. Ruff and both repository
diff checks pass. A staged credential-pattern scan reports no findings. The
component is clean and pushed to the authorized local hardening branch.

The isolated controls use real HTTP requests to the local Jira emulator and
local bare Git repositories. Each scenario is an authored fixture; no model
generates or judges its content.

| Control | Result |
| --- | --- |
| Six write types, SIGKILL after commit | Restart resolves existing clone/link/comment/attachment/description/label; no duplicate mutation |
| The same six types, committed write followed by authored HTTP 503 | Read-back recognizes success; no blind request retry |
| Eight concurrent same-workspace comment callers | One comment |
| Lost response with no visible effect | Pending intent stops the next caller; no repost |
| Changed summary, duplicate remote matches or conflicting owner | Publication/cleanup rejected |
| Death after review comment, before remaining publication | Same composed sources preserved, one summary and one full attachment; numeric approval and dissent retained |
| Death after owned lock acquisition and after release | Same owner recovered; cleanup does not repeat the mutation |
| Copy interruption and manifest-to-pointer interruption | Original immutable run resumes |
| Commit before push, accepted push retry, fresh clone reconciliation | One run and unchanged accepted commit |
| Actual host post-script invoked again | Remote commit, sealed bundle and run count unchanged; both strategies remain in production summary |

An independent replay of captured HTTP/child/ledger records verifies all
**12** commit-before-death/lost-response parameter cases and their **24** strace
files. Verification passes again from the finalized archive, not just the live
pytest directories.

**Provider calls: 0. Inference tokens: 0.** No GLM, Haiku or Opus was needed to
test these Python/HTTP/Git mechanics. No deployed Jira, relay, MLflow or cluster
reset was performed.

The initial focused fault revision passed 19 tests. The first full suite had
963 passes and two fixture failures: an older dry-run gate test deleted its
host receipt while reusing prepared input, and the new post-script test counted
three strategies in a two-strategy fixture. Tests now isolate fresh dry-run
preparations and use the real inventory. The final revision also covers death
after the publication manifest but before updating `current`. Earlier evidence
and source snapshots are retained; no unchanged paid scenario was rerun.

## Private evidence

Finalized and independently checksum-verified capture:

`var/run-data/strat-workflow-hardening/07-recovery/controls/20261014T175415784848Z/`

It contains the exact candidate Git archive, prior source patch/new-file
snapshot, all test logs, selected Jira/Git recovery fixtures, child outcomes,
**116 HTTP record files**, **92 strace files**, and the independent replay
result and verification/archive scripts. **7,072 files, 81,379,029 bytes**;
76 fixture symlinks are preserved as target metadata without following them.
These are local Jira HTTP records, not model-provider API dumps. No Claude
runtime was exercised in this item, so it has no new native state/journal or
MLflow model trace to archive.

Manifest SHA-256:
`adf49f396ff85899898b7e6d26d3c3da1294eead010ca5e57c9dc74bf22bb7b4`.

## Limits and follow-up

Preserve the sandbox workspace/ledger and host state when recovering. A pending
write not visible through read-back is intentionally blocked: Jira indexing can
lag, so deletion of intent is not a valid automatic recovery policy. A lost
workspace, a normalized/changed remote payload or an overwritten effect needs
explicit reconciliation. The tests cover process death, not machine power loss.

Owner labels detect recovery conflicts but **are not an atomic distributed
lease**. Independent hosts can race before either observes the other. An atomic
coordinator and mutation fencing remain a separate production requirement.
[Recorded gap](../bugs/open/strat-jira-label-locks-not-atomic.md).

The inspected Org Pulse implementation keys features by ticket and treats an
unchanged reviewedAt as unchanged; incoming run_timestamp supplies that identity.
The sealed source timestamp prevents a retry from inventing a new review time.
Org Pulse's deployed behavior and overlapping bulk requests were not tested in
this item. No exactly-once event delivery is claimed.

The actual native Workflow replay path, Fullsend/OpenShell deployment,
cross-host concurrency and full production batches remain separate
qualification. Broader stale input/source reuse was subsequently addressed by
item 8. On 2026-10-14 item 9's limits/cancellation proposal was
[rejected as not a bug](../tasks/done/s1-hardening-09-limits.md).

[Plan](../plans/strat-workflow-s1-hardening.md).
