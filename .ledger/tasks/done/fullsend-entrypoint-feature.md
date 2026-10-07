# M3: Implement Fullsend entrypoint support

Follow steps 1, 2, and 5 of the
[POC plan](../../plans/fullsend-entrypoint-strategy-poc.md) in the user's
Fullsend fork on `feat/entrypoint-harness`.

## Acceptance criteria

- [x] Confirm [M1 Podman in k3s](../done/podman-in-k3s-feasibility.md) passed before implementation; recorded evidence reviewed.
- [x] Confirm [M2 OpenShell gateway](../done/openshell-podman-gateway-m2.md) passed; recorded artifacts reviewed.
- [x] Runtime scope confirmed: Claude only; Codex/Pi entrypoint support deferred.
- [x] Implement entrypoint validation, composition, launch, and lifecycle.
- [x] Demonstrate a plain script with no runtime and supporting files/input/output delivery.
- [x] Provide agentless Claude bootstrap and verified Claude child invocation.
- [x] Replace the writable-directory refusal with option 2's integrity checks, as specified below.
- [x] Demonstrate real hook execution and rejection of changed/deleted/replaced files and unexpected directory entries.
- [x] Verify from the outer runner before accepting results or invoking publication post-scripts; unavailable verification must not become success.
- [x] Reject unsupported entrypoint runtime/parser selections with clear errors.
- Coverage threshold deferred by user direction to the [pre-PR task](../pending/fullsend-entrypoint-patch-coverage.md); the measured 72.73% is not a pass.
- [x] Update the execution contract docs to describe option 2, its checkpoint limits, and failure diagnostics.

## Status

Accepted as complete for the POC after the user deferred the coverage gate
on 2026-10-05. Functional fixes passed re-review. Implementation is on
`feat/entrypoint-harness` at `8f628aec6`, based on `7a2622076`.
See [ADR-0008](../../decisions/ADR-0008-defer-poc-coverage-gate.md) and
[the review record](../../bugs/open/fullsend-m3-review-gaps.md). Coverage remains
outstanding before upstream PR preparation, not a blocker to the next POC task.

Before preparing an upstream PR, reconcile this branch with the final merged
ADR and its commit/DCO requirements.

## Review corrections before completion

- [x] Pin effective default hook environment values against inherited changes, including an omitted egress allowlist.
- [x] Retain bounded sandbox diagnostic output and child transcripts on failure, timeout, and cancellation without publication or replay.
- [x] Close the documentation finding.
- Full-feature coverage transferred to the deferred pre-PR task; measure from the actual PR base.

## Implementation contract: option 2 with revisions

- Keep hooks enabled for M3. Allow bootstrap uploads and replace the new
  writable-directory refusal with checks of the installed files.
- Keep expected fingerprints in the outer Fullsend process, calculated from
  trusted source/rendered bytes, never from files after agent execution.
  Include enabled hook scripts, hook settings, helper, and entrypoint. Bind
  hashes to exact filenames and reject missing files, symlinks, substitutions,
  and unexpected hook-directory entries. Account explicitly for legitimate
  runtime files such as Python caches.
- Verify before the entrypoint starts and before supported Claude child
  launches. Use trusted tools and known security environment values; sourcing
  a writable environment file or reading a writable expected-hash manifest
  must not silently defeat verification. Reuse relevant Codex mechanisms,
  but do not claim its full protection from copying its launch guard alone.
- Independently verify from the outer runner after execution, before accepting
  results, validation retries, or publication post-scripts. On failure or
  cancellation, preserve diagnostic artifacts and clean up; an unavailable
  check must not turn an incomplete run into success. Do not replay work.
- Document the limit: checks detect modifications present when checked.
  A writable helper can be bypassed; temporary changes restored before a
  check can escape detection. These checks do not prevent changes during a
  child run or undo external writes already made.
- Real Claude hook/tamper proofs, full race-enabled tests, and staged lint
  were reported complete. Review found that the patch-coverage gate was not
  met; the user subsequently deferred that gate under ADR-0008. Passing a
  no-runtime script or merely uploading hooks is not sufficient evidence.

Follow M3 with [the hooks switch task](../pending/fullsend-sandbox-hooks-switch.md).
Immutable installation is tracked [separately](../pending/fullsend-immutable-hook-installation.md)
and does not gate M3. Strategy migration and single-runner consolidation remain later tasks.

## Notes

- Added `entrypoint.command` argv validation, local path containment including
  symlink targets, whole-mapping base replacement, one-pass `${NAME}` argument
  expansion from `env.sandbox`, `none`/Claude stream handling, generic script
  upload, and no implicit retries after launch/timeout/non-zero exit.
- Entry-point runs skip default Claude credential checks and runtime bootstrap
  unless config or a run override explicitly selects a runtime. Explicit
  entrypoint runtime support is Claude-only; the child helper carries model,
  hook settings, and Claude plugin directories.
- A real no-runtime OpenShell run passed in a disposable M2-compatible Podman
  gateway pod. It verified argv with spaces, normalized event delivery,
  `host_files`, `agent_input`, output collection, and sandbox cleanup. Marker:
  `M3_NO_RUNTIME_OPENSHELL_PASS`.
- The M2 OpenShell 0.0.116 gateway cannot enforce a read-only hook directory
  after upload: read-only blocks uploads, and policy changes cannot remove
  write access from a live sandbox. Option 2 therefore keeps expected hashes
  in the outer Fullsend process, checks them before supported Claude child
  launches, and verifies independently after execution. It detects changes
  present at those checkpoints; helper bypass and tamper-then-restore remain
  limitations. Immutable installation remains a separate follow-up.
- A real Vertex-backed Claude run executed the configured canary PreToolUse
  hook and blocked its Bash command. The Claude child completed and the
  sandbox was deleted. Four outer-runner tamper cases (changed, deleted,
  replaced, unexpected hook-directory entry) failed closed before result
  acceptance, and each case verified sandbox deletion. Marker:
  `M3_OUTER_TAMPER_CHECKS_PASS`.
- `make go-test` passed with race detection for default and GitHub-tagged
  suites: 83.9% total statement coverage. The CLI package passed at 80.4%
  after scanner coverage cases were added. Function-level inspection reported
  94.4% for `scanEntrypointContent`, 95.7% for `ClaudeEntrypointHelper`,
  82.5% for `RunEntrypoint`, and 88.9–100% for integrity helpers. Staged
  `uvx pre-commit run` passed, including gofmt, go vet, and docs links.
- The full test target needed a temporary `gh` executable under `/tmp` that
  returned no token. Legacy fixtures call `gh auth token` directly after the
  target clears `GH_TOKEN` and `GITHUB_TOKEN`; otherwise the host command can
  wait indefinitely. The stub was not added to the fork. Test-only
  neutralization was added to the affected Cloudflare and agent fixtures.
- Initial `scanEntrypointContent` function coverage was 50%. Added tests for
  fail-closed and fail-open read errors, critical fail-open, and a clean
  script; the updated race-enabled CLI profile reports 94.4%.
- Review correction: `EntrypointSecurityEnv` now pins effective `TIRITH_FAIL_ON`
  and `TIRITH_REQUIRED` defaults and always exports the egress allowlist,
  including an empty value. A helper execution test injects hostile inherited
  values and confirms the child receives the runner-selected defaults.
- Review correction: entrypoint failures, timeouts, cancellations, and
  integrity failures now make a 45-second best-effort extraction of at most
  128 output files and transcripts before sandbox cleanup. These artifacts
  remain diagnostic; failed runs do not retry or publish. Tests cover the
  failure/no-replay checks and bounded extraction behavior.
- Review correction: the user reference documents option 2's file hashes,
  checks, checkpoint limits, and failure handling. Staged pre-commit passed;
  affected package tests passed with coverage instrumentation across CLI,
  runtime, and sandbox. The changed executable-line estimate is 150/200
  (75.0%), meeting the enforced floor. `git diff --cached --check` passed.

- Independent re-review: the original default-environment test and focused
  race-enabled CLI/runtime/sandbox tests pass. Documentation and bounded
  diagnostic retention fixes are accepted. The coverage closure claim is
  superseded: whole-feature coverage is approximately 72.73%, as recorded
  in the reopened review finding.
