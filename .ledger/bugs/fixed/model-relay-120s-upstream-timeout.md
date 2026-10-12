# Model Relay cuts off upstream calls at 120 seconds

Status: fixed and deployed 2026-10-11. See the final resolution below;
earlier entries preserve the investigation and incomplete first fix.

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

## Update (2026-10-11): 120-second stream failures persist after deployment

The completed S1 Opus batch `markov-run-7845a7f1` supplies contradictory
runtime evidence to the deployment preflight: archived relay telemetry has
**19 failed requests**, all `upstream_stream_error`, all HTTP 200 with
partial usage, at **120001–120003 ms**. Seventeen upstream message IDs
join directly to this S1 job's API response dumps. No completed stream in
the captured relay request set exceeds 120 s (maximum 117873 ms).
The final failed request is `d1785652-a347-43e6-a33e-a28b2a5aba95`,
16:15:27.484–16:17:27.487 UTC, upstream message
`msg_011CfvkMc7Fn1udh9GchZnGJ`, captured in S1 response dump
`caf79707-c5cf-48db-8c94-8cde59918347.response.json`.
The RHAISTRAT-3 architecture Skill task reports failure, with parent tool
result `API Error: Connection lost mid-response. The response above may be
incomplete.` Exact attribution of that task's final request remains pending.

The relay classifies `upstream_stream_error` when its upstream response
byte stream returns an error (`src/backend.rs`), locating the observed
failure on the relay-to-provider streaming path. It does not show an
initial inability to connect to the relay. Current deployment configuration
still specifies `SHIM_UPSTREAM_TIMEOUT_SECONDS=600`, and archived logs
retain the previously verified fixed-source build ID. Thus the 120 s
pattern is strong timeout evidence but does not establish which remaining
layer imposes it. The deployment evidence alone was insufficient to close
this bug. Raw upstream error details are discarded by `Some(Err(_))`.
Do not claim the managed-account fix is effective based on configuration
alone. No further deployment or model rerun was performed for this check.

Evidence: verified archive
`var/run-data/strat-workflow/markov-run-7845a7f1/20261011T162230677725Z/`,
`relay/requests.json`, `logs/model-relay.log`, S1 `api-dumps/` and
`artifacts/workflow/stream.jsonl`. Relay storage health is clean (zero
drops, pending writes and storage errors); that measures evidence storage,
not upstream inference reliability.

## Update (2026-10-11): remaining timeout source identified

Confirmed: this run selects `tanner-jc-personal`; the live admin
`upstream-profiles` endpoint reports `managed: true`, `auth_mode:
claude-oauth`, `synthetic: false`. This is a UI-managed account, using
`accounts::Manager::build`, not `UpstreamProfile::backend`.

`src/accounts.rs:208` still passes **`Duration::from_secs(120)`** into
`Upstream::new`. The latter sets reqwest's whole-request `.timeout(timeout)`
in `src/backend.rs:326`. Consequently this account's relay HTTP client
has a 120 s deadline despite `SHIM_UPSTREAM_TIMEOUT_SECONDS=600`.
Commit `59d6f06` fixed the configured-profile constructor in `projects.rs`,
but missed this separate managed-account constructor. The matched build
fingerprint therefore proves the partial fix deployed, not that all
account paths honor the setting. Earlier deployment assurances were too
broad.

The observed ~120 s failures are consistent with this local client
deadline. `upstream_stream_error` does not establish a provider-initiated
disconnect: it also covers reqwest timeouts while consuming the response
body, because the streaming branch discards the actual error. The relay
did not wait 600 s. Fix this constructor to use the shared timeout helper,
add a meaningful regression check for managed accounts and distinguish
stream timeouts from other read errors. No implementation or deployment
change has been made during this diagnosis.

## Resolution (2026-10-11): managed-account fix deployed and tested

`accounts::Manager::build` now uses `backend::upstream_timeout()` rather
than a hard-coded deadline, covering new and restored UI-managed accounts.
Streaming reqwest timeout errors are recorded as `timeout_error` instead
of the generic `upstream_stream_error`; HTTP 200 and partial usage are
retained for failures after the response headers have been sent.

A synthetic regression exercises this constructor's actual HTTP client
and production forwarding/telemetry path against local SSE. An isolated
1 s setting times out during the 1.5 s response; a 3 s setting completes
the same response. Both cases distinguish a separate broken stream from
a timeout and check partial/complete usage. No paid provider calls.
All 29 tests, formatting and clippy pass on the host and in the production
image's pinned Rust 1.90 build.

`make host-rebuild-relay` succeeded. Pod `model-relay-f46688557-5tflw`,
started 16:54:20 UTC, is ready with zero restarts; configured timeout 600 s
and managed OAuth account `tanner-jc-personal` are retained. Deployed public
health build ID matches the tested Dockerfile source fingerprint exactly:
`84bb7c79a09bfcb0c29dd7edd517605bfcf293994d95a9dbe4818a0fdc40b8c0`.
Storage health has zero drops, pending writes or errors. This closes the
identified hard-coded managed-account deadline and missing timeout
classification. An actual paid provider stream beyond 120 s has not been
retested; that observation belongs to the next separately authorized run.
Changes remain in the component working tree, uncommitted/unpushed.

## Runtime confirmation (2026-10-11): S1 repeat completes beyond 120 s

Authorized S1 repeat `markov-run-c5ba3904` completed at 17:55:45 UTC.
Archived relay telemetry records **335 complete requests, zero failures**:
283 streaming generations, 50 token-count requests and two preflight
generations. All 283 streams join to S1 API dumps. **Seven streams finish
beyond the old 120 s cutoff**, from **124.211 to 170.314 s**, with complete
usage; all seven upstream message IDs match this job's response dumps.
Every captured request has repaired build ID `84bb7c79...dc40b8c0`.
Storage health has zero drops/errors/pending writes. This is real provider
runtime confirmation that the identified 120 s deadline is removed;
the configured 600 s ceiling itself was not reached in this workload.

Example longest stream: request `7d261b1f-e5f7-4b63-9577-626a7f7480a0`,
upstream message `msg_011CfvrKgJfdvLUJPyJqy461`, 170314 ms, complete.
Verified evidence:
`var/run-data/strat-workflow/markov-run-c5ba3904/20261011T175615927646Z/relay/requests.json`.
The separate S1 reviewer-return benchmark gate still fails and is not a
relay streaming failure. No further model test was launched.
