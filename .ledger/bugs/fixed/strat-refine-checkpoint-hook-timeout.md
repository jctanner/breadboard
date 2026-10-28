# Refinement checkpoint exceeds its ten-second hook budget

Observed 2026-10-16 in one-ticket Opus smoke `markov-run-64a6b4f4`, candidate
`18cdf46716a291439e766d9341eb8e0a03702d52`, Claude Code 2.1.296.

## Failure

Creation and refinement succeeded for RHAIRFE-1 / RHAISTRAT-1. The checkpoint
agent ran `strat_pipeline_state.py refine-status` and received valid readiness
JSON identifying RHAISTRAT-1 as refined. It submitted that same JSON through
StructuredOutput. `refine_checkpoint_guard.py` exceeded its configured
ten-second timeout on all five attempts; `onFailure: block` rejected them.
Claude's structured-output retry cap then failed the native Workflow.

The failure is inside the Workflow before push, scoring or reviewer launches.
The host monitor detected the native failure and stopped the primary; the
independent validator correctly rejected missing final output. This is not
merely an external checker false negative. All claims were released. API
captures show Opus throughout and no recorded relay/rate-limit errors.

## Cause confirmed from archived syscalls

The guard disables live Jira reads, but `load_input(live=False)` still hashes
source/instructions and the complete architecture tree. `load_progress(...,
live=False)` calls `verify_progress`, which calls the same full verification
again. The captured baseline contains 453 logical source files and 1,846
architecture files: 2,299 files per complete scan, or 4,598 across two scans,
plus directory/symlink validation and Python import work.

The initial read guard, before a progress file existed and therefore before
the second verification applied, completed in 5.60 seconds. Its trace has
45,657 `newfstatat` calls. The five later guards were killed by SIGTERM at
approximately ten seconds, with 82,736–85,209 `newfstatat` calls and
4,984–5,096 `openat` calls already performed in each attempt. Their traces
show continued architecture file scanning, no `connect` calls, and successful
`flock(..., LOCK_EX) = 0`, so a Jira wait or blocked progress lock is not the
observed stall. Each failed guard alone produced about 60 MB of syscall trace.

Relevant trace suffixes: `.260` (initial successful guard), `.681`, `.689`,
`.831`, `.933`, `.959` (five timed-out checkpoint guards). Source inspection
and those traces establish excessive repeated local verification under the
instrumented job's deadline. Tracing contributes overhead; its precise share
has not been measured by a matched replay without tracing. The agent's direct
helper call eventually returned successfully at about eleven seconds.

Tests with smaller fixtures did not establish the full snapshot's hook budget.
Fix duplicate work and verify the full-tree execution budget; retain the
refinement and freshness guarantees. Do not restore fail-open behavior to make
this run appear successful. No new inference is needed to profile this path.

## Evidence

Campaign root:
`var/run-data/strat-workflow-hardening/pr85-reviewed-vertex-opus-one-rfe-20261016/`.
Final capture:
`markov-run-64a6b4f4/20261016T231100432769Z/`.

Under `jobs/script-run-workflow-all-claude-opus-4-6-1016-225441-c61df7/artifacts/`:

- `workflow-failure-stop.json`: exact native error and monitor action.
- `native-projects/**/agent-a4530224cd9ba56e6.jsonl`: valid helper output and
  five hook timeout results, with timestamps.
- `native-projects/**/workflows/wf_d4cc1cf8-410.json`: native failed state,
  four step agents, no scoring/review.
- `repo-tmp/strat-progress.json`: create/refine recorded; no push/review.
- `run-summary.json`, `eval-result.json`: pipeline exit 1, benchmark FAIL,
  cleanup success, model identity and usage.

The final run archive is complete and independently verified, with published
receipts. No paid retry or resume has been performed for this bug.

## Repair verified and published

Authorized model-free profiling reproduced the cutoff with the exact source
and architecture hashes, seven Git symlinks, original absolute working path,
pipeline image/Python 3.13.16 and CPU/memory settings. Single matched replay:

| Measurement | Before | After |
| --- | ---: | ---: |
| Plain hook | 1.386 s | 0.366 s |
| Hook under original strace flags | 10.731 s | 1.921 s |
| Traced, enforced ten-second cutoff | killed at 10.014 s | passes in 2.096 s |
| newfstatat calls | 91,133 | 1,133 |
| openat calls | 5,452 | 2,831 |

The candidate adds a combined input/progress loader to verify the baseline
once. Tree traversal uses directory-entry metadata and checks resolved aliases
per directory, retaining every logical path and every content hash. No hashes
are cached between checks. External/dangling aliases and cycles still fail;
same-size/same-mtime edits are detected. Both plugin hook copies match. The
configured ten-second timeout and blocking failure policy are unchanged.

All 84 focused checks and 1,080 unit checks pass. Full-size traced mutations
of returned JSON, source, architecture content and progress provenance all
exit 2 within the deadline, with original fixture bytes restored. `make test`
also passes 1,080 tests. Unit/full suites have five/six existing optional skips.
Ruff, descriptor validation and diff checks pass. Signed-off commit
`2a4b7c94b93a2d43bc25fe701e225e5738e226af` is pushed to the existing
`feat/s1-workflow-hardening` branch / PR 85; component worktree is clean.

Profiling evidence, exact inputs/patch, cProfile data, raw strace, pod metadata,
controllers and test logs are retained separately under
`var/run-data/strat-workflow-hardening/refine-checkpoint-profile-20261016/`.
The original failed archive is unchanged. The profiling pod had no credentials,
secret mounts or service-account token and was removed after evidence capture.
These mechanical replays do not establish that an end-to-end model run passes.

Final profiling archive independently verifies 4,372 entries / 504,789,902
regular-file bytes, with no problems. `verify_archive.py` and `manifest.json`
permit a later checksum replay. This closes the measured hook-performance
defect; the historical smoke remains a failure and no paid retest was launched.
