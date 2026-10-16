# Critical StructuredOutput checks time out and execution continues

Observed in markov-run-5d3327ed, candidate f5691f7, Claude Code 2.1.296,
Opus 4.6, nine acquired RFEs at batch cap ten.

Refinement guard Python PID 2664 ran 14:10:26.986711–14:10:36.977960 UTC
(9.991249s); final completion guard PID 5901 ran
14:32:21.645266–14:32:31.626709 UTC (9.981443s). Each received SIGTERM from
primary Claude PID 151 and was killed. Both hooks are configured timeout=10.
Their final audit events were never written. Workflow accepted the structured
returns and continued to complete. The host validator independently passed.

Hook paths call live input verification and Jira reads, whose cumulative
latency can exceed the hook budget even against the local emulator. Do not
infer enforced hook completion from a successful native Workflow. Review
comment 4295376534 is supported by actual traces. Keep heavy live verification
outside this short hook boundary, preserve explicit deterministic validation,
and qualify timeout behavior with the deployed runtime. Fix not yet made.

[PR triage](../../notes/strat-creator-pr85-review-triage.md).

## Fixed in source, 2026-10-16

strat-creator commit f941955 on feat/s1-workflow-hardening. Short hooks use local evidence with no Jira network requests; long helpers and host validation retain live readback. Pre/PostToolUse commands specify onFailure: block. A real 2.1.296 timeout control blocks the first call and observes only the later permitted Workflow execution. Stop/SubagentStop timeout blocking remains unclaimed.
No paid model batch was rerun for this remediation; historical evidence is unchanged.
