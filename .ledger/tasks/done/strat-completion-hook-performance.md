# Profile and optimize the ten-ticket completion hook

Follow-up to the failed fresh ten-ticket Opus run, 2026-10-17. Use the same
model-free profiling/repair approach as the refinement checkpoint. No paid
batch, Jira reset or native model invocation. Preserve historical archives.

- [x] Reconstruct all ten tickets and original source/context hashes, symlinks,
      absolute path, image/resources and tracing; measure baseline hook cost.
- [x] Remove measured redundant work without changing approval policy, hook
      timeout, blocking behavior or artifact/freshness/provenance coverage.
- [x] Replay the whole batch and altered-input negatives under the ten-second
      traced deadline; add regression coverage and run required repository tests.
- [x] Preserve evidence under `var/run-data`, publish the verified feature-branch
      fix and update the bug, task and hardening plan.

Base: PR 85 branch `feat/s1-workflow-hardening`, commit 2a4b7c9. The final hook
verifies progress twice, then each per-ticket review starts another full
freshness scan. Use private validation functions within one call rather than
adding an externally selectable validation bypass or caching between calls.
Exact changes depend on the measured profile.

[Observed failure and repair](../../bugs/fixed/strat-completion-hook-ten-ticket-timeout.md).

## Measurements

The replay matches all 453 source and 1,846 architecture hashes, 113 receipt
input hashes, ten strategies and preserved internal symlinks. It runs at the
original absolute path in the same image digest (Python 3.13.16), CPU/memory
settings and `strace -ffttv -s 1024` configuration, without credential mounts.

| Measurement | Before | Candidate |
| --- | ---: | ---: |
| Plain hook | 2.858s | 0.643s |
| Traced hook | 20.423s | 2.465s |
| Traced ten-second deadline | killed at 10.017s | passes in 2.601s |
| Full freshness checks per invocation | 12 | 1 |
| Traced openat calls | 32,116 | 3,186 |
| Trace bytes | 81,091,443 | 9,634,165 |

These are single matched mechanical measurements, not reliability statistics.
The cProfile runs are separate measurements; neither traced hook connects to
the network. Original archive and its failed native verdict remain unchanged.

The implementation separates full input/progress verification from private
business/review validation. Standalone public review/business entrypoints
still verify freshness. Completion verifies once, then checks all ten tasks,
forty reports, scorer outputs, provenance and policy decisions. No skip flag,
cross-call cache, added agent/hook, changed timeout or policy relaxation.

The new regression reproduces twelve scans before the repair. All 140 focused
checks now pass. Eight final full-size traced rejection cases exit 2 within 0.45–2.60
seconds: forged return receipt, changed source/context, changed tenth-ticket
role/scorer/provenance, missing tenth review progress and symlinked report.
Where relevant, the outer receipt hashes are recomputed to prove independent
underlying validation still rejects the tampering. Source/context cases retain
size and modification time. Both required repository suites subsequently pass
as recorded below.

Evidence: `var/run-data/strat-workflow-hardening/completion-hook-profile-20261017/`.
Raw fixtures, source patch, profiles, traces, controllers and test logs are
collected. Both temporary profiling pods are removed. The initial candidate
omitted its bundled review helper; full-suite integrity checks caught that.
The test controller also passed umask 077 to a permission fixture. The bundle
now matches, normal umask 022 is used for test subprocesses, and both failed
checks pass. Initial evidence/logs are preserved in `preliminary-bundle-copy`,
excluded from final candidate figures. The final candidate was reprofiled with
the same image/resources; the unchanged original baseline is explicitly reused.
The stronger source-negative case remains valid Python and fails specifically
at freshness validation, rather than merely breaking module syntax.

The corrected `make test-unit` passes 1,089 tests with five existing optional
skips; `make test` also passes 1,089 tests with six existing optional skips.
Changed-file Ruff (including the bundled copy), descriptor validation, staged
allowlist, redacted Gitleaks and diff checks pass.

Signed-off commit `6ed858b2294a29457153a90f187a801022c21e8b` is pushed to the
existing PR 85 feature branch. Its four-file patch exactly matches the final
profiled source/test patch, and the component worktree is clean. Final profiling
archive independently verifies 10,093 entries / 852,391,176 bytes with no
problems. The original ten-ticket run archive also re-verifies unchanged.
Cleanup verification confirms no profiling pod remains. No model invocation,
deployed Jira reset or paid retry. This local repair does not regrade the old
native FAIL; a future authorized fresh run must pin the new source commit.
