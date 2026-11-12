# Fresh conformance target has no README

## Status

Fixed by 227674c; strict conformance run 9 passes all 10 operations.

After the activation and startup-budget repairs, an earlier workflow was green
but strict conformance correctly failed. Structured results recorded missing
target-repo/README.md and a failed read_file README.md. Fresh targets contain
.fullsend and .github, with no operator README. A synthetic result may still pass
schema validation and the post-script even after an operation fails, so the green
workflow alone was insufficient. Strict agent-success checks were retained.

Both checkout witnesses now use the event shim that the preceding target seeder
actually writes. FULLSEND_SHIM_PATH is shared by producer and scenario. Credential,
identity, artifact and schema assertions remain unchanged. Regression tests run
the producer against a fake Contents API, verify the scenario's witness really is
written, and verify a second seed is idempotent. The real run confirms .github
survives the sandbox copy, all 10 operations succeed and both exit codes are 0.
