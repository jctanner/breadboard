# Fix Model Relay managed-account streaming timeouts

## Authorization

2026-10-11: user requested "lets fix model-relay" after identifying the
remaining hard-coded 120 s deadline in UI-managed account construction.

## Acceptance criteria

- [x] Managed-account client honors the shared configured upstream timeout.
- [x] Streaming timeouts are distinguishable from other stream errors.
- [x] Synthetic regression verifies effective streaming deadline and telemetry.
- [x] Format, tests, clippy and repository diff checks pass.
- [x] Rebuild/redeploy and verify deployed source fingerprint, account routing,
      configured timeout, readiness and telemetry storage health.
- [x] Record evidence in the relay bug and evaluation plan; no paid model rerun.

## Status

Done. The completed S1 Opus run's verified archive and published receipts
preserve evidence before deployment. Component has no AGENTS.md or CLAUDE.md.
No strategy design change is involved.

Changed `accounts::Manager::build` to use the shared configured timeout.
Response-body timeout errors now retain `timeout_error`; other read errors
remain `upstream_stream_error`, without logging raw provider bodies/errors.
Regression uses isolated child processes to set 1 s and 3 s budgets and
the actual managed-account HTTP client against a local 1.5 s SSE response.
It verifies both timeout and successful completion, partial/complete usage
telemetry, and a non-timeout broken stream. Only fixture authentication is
substituted; no provider calls are made.

All 29 tests, format and clippy pass on the host and inside the production
image's Rust 1.90 build. Pre-redeploy query found zero in-progress relay
requests among the latest 500 records. `make host-rebuild-relay` succeeded.
Expected Dockerfile source fingerprint:
`84bb7c79a09bfcb0c29dd7edd517605bfcf293994d95a9dbe4818a0fdc40b8c0`.

Deployment verified: pod `model-relay-f46688557-5tflw`, started
2026-10-11 16:54:20 UTC, Running/ready with zero restarts. Actual image ID:
`sha256:304f7e3e627347c13c8cfe1064355543a8e4d7a4d476c85b02a16d77cac47057`.
Public health build ID exactly matches the source fingerprint above.
Pod configuration retains `SHIM_UPSTREAM_TIMEOUT_SECONDS=600`; the
`tanner-jc-personal` managed OAuth profile is restored, synthetic=false.
Private storage health reports zero dropped records/requests/events,
pending writes and storage errors. This is deployment and synthetic-test
verification, not a new measured provider stream longer than 120 seconds.
No S1/S2 rerun, commit or push performed.
