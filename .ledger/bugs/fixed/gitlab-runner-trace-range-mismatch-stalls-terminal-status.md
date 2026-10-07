# Bug: Trace range mismatch prevents runner finishing a failed job

## Summary

Pipeline 2061/job 4011 appeared stuck at the results clone while the API
reported running. The runner had finished: script failure after 211.75 s,
exit 1, execution pod removed. It could not deliver the last 2,367 trace bytes,
and the runner sends the terminal state only after the whole trace is accepted,
so the job stayed running. 776+ HTTP 416 retries were observed.

## Root cause (evidence-backed)

Three faults in sequence, all 2026-10-07 (UTC):

1. **Emulator OOM-killed mid-clone.** Pod `gitlab-emulator-747866cbd6-vzvv6`
   last state: `OOMKilled`, exit 137, 03:13:08, limit 512Mi. Its last request
   was `git-upload-pack` for `strat-pipeline-data.git` (03:13:07). Offline
   measurement on a copy of that bare repo (60.5 MiB pack, 11,176 objects):
   server-side `pack-objects --revs --all` peaks at ~205 MB with 16 threads
   (the pod sees all 16 host CPUs) and ~124 MB with one. The fresh app idles
   at ~203Mi; build job 4010 had uploaded a 20.9 MB artifact into the same pod
   at 03:10:22, and the artifact handler buffers whole bodies in memory.
2. **The killed clone is the script failure.** Recovered output:
   `curl 92 HTTP/2 stream 3 was not closed cleanly: INTERNAL_ERROR`,
   `fetch-pack: unexpected disconnect while reading sideband packet`,
   `fatal: protocol error: bad pack header`, entrypoint status 128, job exit 1.
   Not a slow clone. No Claude inference, locks or strategy writes ran.
3. **Trace protocol defects turned a lost response into a permanent stall.**
   The emulator had accepted `0-13949`. During the restart a PATCH
   `13950-14294` was committed but its response was lost (connection errors,
   then 502s); the runner kept its offset and later resent `13950-15009`.
   - The emulator rejected any start offset other than its size; GitLab
     (`AppendBuildTraceService`, `Trace#append`) writes the chunk at its start
     offset and replaces what follows, so this retry is normal.
   - The 416 carried `Range: 0-14294` (last index). gitlab-runner v19.1.1
     `network/patch_response.go` `NewOffset()` uses the number after the dash
     as the next byte to send; GitLab sends `0-<stored size>`. The runner was
     pinned at 14294 while the emulator required 14295: an infinite loop.
   - Storage decoded each chunk with `errors="replace"` and redacted it with
     `[MASKED]`, so a multibyte character split across chunks or a redacted
     secret also changed the stored byte count away from the runner's offsets.

The 03:13 restart was the OOM, not a deployment: the last emulator rollout
before it was 03:05:43.

## Fix (checkouts/gitlab-emulator, uncommitted at time of writing)

- `job_traces.raw` (BLOB, added at startup by `_ensure_sqlite_compat_columns`)
  stores the runner's bytes in its offset space; `size` is its length and
  `content` is derived display text. Legacy rows fall back to `content`.
- PATCH writes at the Content-Range start (truncate and replace) when
  `start <= size`; `start > size` returns 416. Every response sends
  `Range: 0-<size>`.
- Masked values are overwritten with equal-length NUL bytes in `raw` (no
  secret stored, offsets preserved) and shown as `[MASKED]`.
- Retry, erase and trace creation reset `raw` with `content`.
- Image sets `git config --system pack.threads 1` to cap fetch memory.

## Checks

- New `tests/test_trace_protocol.py`, 7 tests: Range size, lost-response
  overlap retry, 416 resynchronisation, multibyte split, masking offsets and
  no stored secret, legacy row resume, failed status after trace. Five fail on
  the previous HEAD.
- Related suites (trace protocol, pipelines API, web UI, admin, trace render,
  database): 189 passed; the 2 failures are the pre-existing
  variable-precedence tests, which also fail on clean HEAD.
- Full emulator suite: 743 passed, 3 failed; all three (two
  variable-precedence tests, `test_ci_yaml` richer `rules:if`) also fail on
  clean HEAD.
- `git diff --check` clean. Deployed with `make host-rebuild-gitlab`
  (03:31Z and 03:39Z) after confirming no other active CI jobs or agents.

## Recovery of job 4011

No database edit. After the fixed emulator started, the still-retrying runner's
PATCH `14294-16661` was accepted (23:33:30 EDT), then it sent the terminal
update. Stored trace: 16,662 bytes, `crc32:0a273b17`, equal to the runner's
reported checksum. Job 4011 `failed / script_failure / exit 1`; pipeline 2061
`failed`. RHAIRFE-6/7 inspected read-only: `New`, no links, no comments,
updated only at seeding (03:07:36); no strategy created by this batch.

## Live verification

Temporary branch on `admin/ci-testing` (project 1), pipeline 2064/job 4015:
60 lines of ASCII plus multibyte output over two minutes, then a nonzero exit.
The emulator was redeployed mid-job: three 502s, then the next PATCH
`7740-8825` was accepted; zero 416s. Stored trace 14,429 bytes,
`crc32:45f0a9fc` equal to the runner's, all 60 lines contiguous, no U+FFFD;
job `failed / script_failure`, pipeline `failed`. Exit code was 127 rather than
the intended 3 because the test YAML's unquoted `echo "final line: ..."` parsed
as a mapping; the emulator reported the runner's result correctly.
Branch deleted afterwards.

## Remaining limitations

- Memory headroom remains thin: 512Mi limit, ~203Mi idle app, ~124 MB per
  concurrent clone of the data repo even with one thread. Follow-ups: stream
  artifact uploads to disk instead of `request.body()`, and consider a larger
  limit in `deploy/k8s` for the emulator.
- Traces stored before this fix have no `raw`; if one was redacted, its byte
  count differs from the runner's and the runner resynchronises from the 416
  size (correct now), possibly duplicating or skipping a few bytes.
- A genuine NUL byte in job output displays as `[MASKED]`.
- The emulator accepts a mapping as a script line; GitLab rejects that YAML.
- The temporary admin PAT `trace-protocol-check-1791344300` cannot be revoked
  through the emulator API and remains.
- The earlier 2057/4000 results-clone failure
  ([bug](../open/fullsend-results-clone-http2-stream-error.md)) has the same
  signature; probably the same OOM, but that pod's restart history is gone.

## Related task

[Settings/log batch test](../../tasks/current/fullsend-settings-log-batch-test.md).
