# Bug: Forked local Skill reports success after a transport failure

Native Claude 2.1.296 runs `/strategy-refine` as a forked Skill. In the SME
test it exhausts transport retries and returns `API Error: Connection dropped
(ECONNRESET)`, but the process exits 0 and its final stream-json result says
subtype=success, is_error=false, num_turns=0. No refinement is written.

The local test must validate business artifacts and the final result text;
process exit status alone is insufficient. The existing S1 prepared-run
completion checker already provides a separate business outcome boundary,
but standalone local human commands do not traverse that Workflow boundary.

Observed on 2026-10-19, candidate 6ed858b, local refinement
13:57:54–14:35:58 UTC. API capture/strace/native session and the unchanged
artifact are retained with the SME campaign. CLI reports $1.67866 for this
attempt; that is not a billing reconciliation and failed-stream usage can be
incomplete. [Related transport cause](../fixed/ingress-proxy-model-response-write-deadline.md).

Do not patch the native binary or weaken the qualified-runtime check. Preserve
the failed result, strengthen the test's pass criteria and decide whether a
supported CLI/runtime fix or a documented local-command wrapper is needed.
