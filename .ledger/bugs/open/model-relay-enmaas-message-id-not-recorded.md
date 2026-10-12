# Bug: EnMaaS message IDs are absent from relay telemetry

## Summary

GLM compatibility run `markov-run-23df27ac` captures message IDs such as
`chatcmpl-574acd89-d95d-4316-a529-33ae83901fab` in API response bodies.
Model Relay `src/backend.rs` observes upstream message IDs only through
`safe_id(..., "msg_")`, so these GLM IDs are discarded. Final archive confirms zero relay message-ID joins for 180 captured S1
responses; API dumps/index retain original IDs.

## Impact

Inference and token accounting are unaffected, but the existing exact join
between relay generation records and API response IDs cannot establish GLM
coverage. Use the archived job/time scope for current reconciliation; do not
claim exact generation ID matching for GLM.

## Expected fix

Support the verified EnMaaS `chatcmpl-<UUID>` message-ID format with bounded,
validated identifiers and regression tests; retain the credential-safe logging
boundary. Review upstream request-ID formats separately. This is a deferred
observability fix, not grounds to alter S1/S2 or rerun this validation.
