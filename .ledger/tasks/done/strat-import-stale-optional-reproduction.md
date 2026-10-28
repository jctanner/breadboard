# Reproduce stale optional import context on fbbbc6e

## Scope

The user requested reproduction of review 4359883142, not an implementation fix.
Use the isolated Jira emulator and the real prepared-run/freshness path. Leave
the component repository clean. No model call, live Jira/export action, remote
reply, push or deployment.

## Acceptance

- [x] Interrupt import after a prior review is published but before completion.
- [x] Remove the remote attachment and retry through the real importer CLI.
- [x] Check stale local review, completion inventory and repeated import behavior.
- [x] Check whether record-create and freshness verification permit continuation.
- [x] Run a clean control with no prior review and record evidence/limitations.
- [x] Archive sanitized source, results and snapshots; update the reported bug.

## Result

Confirmed on clean fbbbc6e. Two observation tests pass in 6.71s: the real managed
recovery retains a stale review outside completion inventory and passes normal
continuation/freshness checks; the clean control leaves no review. No model was
invoked, so actual model consumption is not claimed. Component code is unchanged.

[Evidence and limitations](../../notes/strat-stale-optional-reproduction-20261023.md).
Thirty-one-file archive at `var/run-data/20261023-strat-stale-optional-reproduction/`
passes credential scanning (zero findings) and hash readback. Relevant source
hashes match the actual managed-run baseline. The bug was subsequently repaired
locally in [the follow-up task](strat-import-optional-context-fix.md); the original
reproduction archive remains sealed.
