# S1 hardening 7: prevent duplicate side effects on restart

Handle the gap between tool side effects and journaled agent completion.
Make publication and other visible writes idempotent or verify their existing
effects before repetition, including agent-level retries and crash recovery.

Acceptance: crash/restart fixtures preserve required work without duplicate
publication or conflicting ownership; keep request retries distinct from agent restarts.

Pending, after item 6. [Plan](../../plans/strat-workflow-s1-hardening.md).
