# S1 hardening 7: prevent duplicate side effects on restart

Handle the gap between tool side effects and journaled agent completion.
Make publication and other visible writes idempotent or verify their existing
effects before repetition, including agent-level retries and crash recovery.

Acceptance: crash/restart fixtures preserve required work without duplicate
publication or conflicting ownership; keep request retries distinct from agent restarts.

Done, focused repair 2026-10-14. [Plan](../../plans/strat-workflow-s1-hardening.md).

Implement durable write intent and read-back reconciliation for Jira clone,
link, comment, attachment and field writes; bind lock cleanup to its owner;
give results publication a stable run identity. Test response loss and process
death after the server commits, concurrent local recovery, uncertain absence
and conflicting ownership. Prefer isolated local services and zero inference
where the faults are in Python/HTTP/Git rather than model reasoning.

Implemented and locally pushed `80a11ed`: durable mutation intent, conservative
read-back reconciliation, clone marker and link recovery, stable review
publication, owner-bound cleanup/preparation, and immutable run publication with
sealed reports and repeatable summaries. Final full suite: 966 passed, seven
skipped. Twelve real HTTP commit/death-or-response-loss cases independently
verify; concurrency and actual post-script retry controls pass. Zero provider
calls or inference tokens. Complete private control archive verifies.

This closes the tested same-workspace/process recovery gap. It does not prove
native Workflow replay, Fullsend deployment, machine power-loss durability or
cross-host exclusivity. Jira label claims lack atomic fencing; the production
gap is tracked separately. [Evidence and limits](../../notes/s1-hardening-07-recovery.md).
