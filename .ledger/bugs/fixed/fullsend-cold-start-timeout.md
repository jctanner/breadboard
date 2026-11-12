# Fullsend killed healthy cold sandbox startup

## Status

Fixed by 352f463 and verified by strict conformance run 9.

Fullsend's default readiness budget is 120 seconds plus a 10-second subprocess
buffer. Healthy cold workspace/runtime startup on the test host exceeded it,
causing creation retries to destroy a sandbox just before it could become Ready.

The runner now sets the existing FULLSEND_SANDBOX_READY_TIMEOUT to 5m. A positive
harness sandbox_timeout_seconds still overrides it; Fullsend caps both at 600
seconds and retains bounded retries. No provider, policy, TLS or agent execution
limits were relaxed. The runner environment reports 5m and the conformance harness
has no timeout override. Run 9's successful sandbox_create span took 137.542
seconds, beyond the old hard deadline, proving the longer budget took effect in
the actual Fullsend process. All subsequent strict checks pass.
