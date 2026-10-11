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

## Update (2026-10-11): the setting didn't reach managed accounts

`SHIM_UPSTREAM_TIMEOUT_SECONDS=600` was deployed at 23:39 UTC on
2026-10-10, before the opus smoke run (`markov-run-f2f3b733`, S2 round 3
re-run as `markov-run-5884ad2a`). Streams were still cut at exactly 120 s:
13 relay records with `upstream_stream_error`, `latency_ms` 120000–120002,
8–14 output tokens each. Claude Code retried each from the start.

- **Cause:** the setting only applies to the environment-configured
  upstream (`src/main.rs`). Managed upstream profiles, which the deployment
  uses (`tanner-jc-personal`, Claude OAuth), build their client in
  `UpstreamProfile::backend` (`src/projects.rs`) with a hard-coded 120 s.
- **What gets cut:** opus writes about 40–45 tokens/s, so any turn longer
  than about 5k output tokens. These were the scorer writing its result,
  reviewers writing their reviews, and refine. One S2 architecture reviewer
  was cut four times running on the same request.
- **Cost in the opus run:** S1 0, 1, 2 cuts and S2 0, 4, 6 cuts per round,
  2 minutes each, so up to 12 minutes of a 37.6-minute run.
- **Fix:** `checkouts/model-relay` `59d6f06` adds
  `backend::upstream_timeout()`, used by both paths. Tests pass (28),
  clippy clean. Not pushed or deployed yet; it needs
  `make host-rebuild-relay` while no run is in progress.
- **Telemetry:** these cuts are recorded as `upstream_stream_error`, not
  `timeout_error`, so suggested fix 3 still stands.

Close after the deploy, once a run shows no `latency_ms` at 120000.

## Update (2026-10-11): user rebuilt and redeployed; deployment verified

The user completed the rebuild and redeployment. The running pod
`model-relay-55bcd9875f-n9tmb` started at 11:55:42 UTC, is ready and has
zero restarts. Its actual environment has
`SHIM_UPSTREAM_TIMEOUT_SECONDS=600`.

The public health endpoint's build ID is
`2a27f2b3251e389bb7bacefff579c4eb5a781957c48cb169e92bc3658f4c7550`.
Recomputing the Dockerfile's source fingerprint from the clean checkout at
`59d6f06` produces the same ID, confirming the fixed source is deployed.

No further rebuild is needed. Runtime verification remains pending: the
private health endpoint has no newly persisted requests since this restart
(`last_persisted_at_unix_ms: 0`). At the next authorized run, confirm that
managed-account streams can complete beyond 120 seconds and that errors
no longer cluster at the old 120-second cutoff. A successful request with
latency above 120 seconds is evidence for the fix, not a failure. Keep this
bug open until runtime evidence is available; no new model run was launched
for these read-only deployment checks.
