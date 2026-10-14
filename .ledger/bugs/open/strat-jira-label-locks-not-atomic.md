# Jira processing labels do not provide an atomic distributed lease

Discovered while implementing S1 hardening #7, 2026-10-14.

The original check-then-add processing label has no owner or compare-and-swap.
The repair adds durable host lock intent, a run owner label, read-back conflict
detection and owner-bound cleanup. It stops a recovered worker or cleanup from
adopting/clearing a foreign or mixed claim. Local retries serialize through a
file lock and every pipeline write rechecks its acquired RFE's owner.

This does not provide distributed fencing. Two independent hosts can both read
an unlocked issue, and one can begin work before a later competing label add
becomes visible. Subsequent checks detect the conflict, but do not undo earlier
work. Do not describe Jira labels as an atomic lease or exactly-once ownership.

Concurrent-job qualification needs an atomic coordinator/lease backend and
fencing enforced at the mutation boundary. No such deployment contract is
introduced by this focused restart repair; keep this requirement separate from
the completed crash-after-commit fixtures.

[Hardening plan](../../plans/strat-workflow-s1-hardening.md)
