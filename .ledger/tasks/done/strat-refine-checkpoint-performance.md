# Profile and fix refinement checkpoint timeouts

Authorized 2026-10-16 after the failed one-ticket Opus smoke. Profile and fix
the local hook without paid inference. Preserve the original archive and its
failed result. Work on the existing PR 85 feature branch.

- [x] Reconstruct the failed run's full source/context/artifact inputs in an
      isolated workspace; capture model-free baseline profiling with tracing.
- [x] Remove redundant verification and address the measured filesystem cost
      without weakening freshness, provenance or symlink checks.
- [x] Add regression checks for stale/altered inputs and tree traversal edge
      cases; rerun the full-size hook under the original tracing/deadline.
- [x] Run required repository checks, preserve profiling evidence in
      `var/run-data`, and update the hardening plan and bug record.

No Jira reset, paid batch, native model invocation or baseline rewrite in the
original archive is authorized by this task. A reconstructed fixture may record
its own provenance for the modified candidate, explicitly separate from the
historical baseline.

[Failure and existing evidence](../../bugs/fixed/strat-refine-checkpoint-hook-timeout.md).

## Measurements and current verification

One full-size replay with preserved symlinks and original strace flags takes
10.731 seconds before and 1.921 seconds after. An enforced ten-second deadline
reproduces the old SIGTERM and passes the fixed hook in 2.096 seconds. Metadata
calls decrease from 91,133 to 1,133. Plain execution: 1.386 to 0.366 seconds.
No new hook, agent, model call, freshness bypass or timeout increase was added.

Combined input/progress verification eliminates the duplicate full scan.
Directory-entry traversal removes repeated parent resolution and metadata
calls while still hashing all logical files and checking aliases/cycles.
Thirteen added regression cases exercise preserved aliases, unsafe aliases,
unchanged-size/timestamp edits and missing/empty/foreign progress. All 84
focused tests pass; `make test-unit` passes 1,080 tests with five optional skips.
Changed-file Ruff and descriptor validation pass. `make test` also passes 1,080
tests with six existing optional skips. Both required suites completed before push.

Full snapshot rejection checks under strace block forged receipt, altered
source, altered architecture and forged artifact provenance. Evidence is saved
under `var/run-data/strat-workflow-hardening/refine-checkpoint-profile-20261016/`.
The original run archive remains unchanged and the temporary profiling pod is
removed. Published signed-off commit `2a4b7c94b93a2d43bc25fe701e225e5738e226af`
to the existing PR 85 branch; its component worktree is clean. The published
commit's diff exactly matches the profiled patch. Final profiling archive
independently verifies 4,372 entries / 504,789,902 bytes with no problems.
The historical failed archive is untouched. No paid rerun or resume.
