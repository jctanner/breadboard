# GitLab emulator overwrites canceled job status with runner failure

## Evidence

M6 lifecycle job 3953 was canceled after its real sandbox reported readiness.
The cancel API returned `status=canceled`; the job pod disappeared while the
separate real strategy job 3955 completed successfully. The runner's final
update subsequently changed the test job to failed/unknown_failure.

## Expected / impact

Cancellation should remain the terminal job state when an ensuing runner
update reports termination. The emulator's classification differs from the
observed cancellation action and can mislead dashboard users.

## POC boundary

Record the API acknowledgment, captured readiness trace, and actual runtime
removal as cancellation evidence. Later explicit hard-kill retries correctly
settled as runner_system_failure. Scheduler/state-machine correction is
separate emulator work and does not negate the M6 runtime-cleanup proof.
