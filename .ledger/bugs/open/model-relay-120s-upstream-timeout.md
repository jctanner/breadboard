# Model Relay cuts off upstream calls at 120 seconds

Component: `checkouts/model-relay`, deployed as `model-relay` in
`ai-pipeline`. Found 2026-10-10 during the strat-workflow smoke re-run
(`markov-run-41e56ed5`, S1 round 1, job
`script-run-workflow-all-claude-haiku-5-5-1010-180408-0d4a57`).

## Evidence

- **Relay log:** two `completion: failed` records at exactly
  `latency_ms: 120002` and `120001` (18:16:21 and 18:24:49 UTC),
  `claude-haiku-5-5`.
- **The job's API dumps:** a request at 18:14:21 got its answer only at
  18:16:21, 3 output tokens after Claude Code's retry. That's 2 minutes of
  dead time, and with the second failure at least 4 minutes of a 21-minute
  run.
- **Cause:** `src/main.rs` builds the upstream client with
  `SHIM_UPSTREAM_TIMEOUT_SECONDS`, which defaults to **120** (clamped 1–600),
  passed to reqwest's `.timeout()`. That is a whole-request timeout, which
  also covers reading a streamed body, and our deployment doesn't set it.

## Impact

- **Stalls cost 2 minutes each,** because the call is only abandoned after
  120 seconds and then retried.
- **Legitimate long calls get cut off.** Haiku already took 97s for one
  23k-token thinking turn in this run. Opus generates several times
  slower, so on the opus tier normal heavy turns would exceed 120s, be
  killed and be retried.
- **Benchmark numbers are affected:** run times and call counts include
  these stalls, at random.

## Suggested fix

1. Set `SHIM_UPSTREAM_TIMEOUT_SECONDS=600` (the maximum) on the
   `model-relay` deployment.
2. In the relay, replace the whole-request timeout for streams with an idle
   (no bytes for N seconds) timeout, so slow-but-progressing streams
   survive and stalled ones are dropped quickly.
3. Record timeouts separately in telemetry (`timeout_error` exists in
   `backend.rs`), so runs can report how many calls hit them.

Not applied yet: the change would affect a run in progress, and the user
asked to pause after the re-run.
