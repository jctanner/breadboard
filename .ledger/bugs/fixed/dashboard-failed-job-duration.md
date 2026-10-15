# Failed job durations keep increasing

Reported on `https://dashboard.local/jobs` on 2026-10-15. The list API uses
`now` when Kubernetes `status.completion_time` is absent, but Kubernetes sets
that field for successful completion, not failure. Failed jobs have a terminal
`Failed=True` condition with a stable `last_transition_time` instead.

Use the terminal timestamp in job/eval lists and job details; a terminal job
without a known end timestamp must not keep accumulating time. Verify with
regression tests and live polling after dashboard deployment.

## Resolution

Fixed on 2026-10-15. The Kubernetes orchestrator resolves end time from
`completion_time` or true `Complete`/`Failed` conditions. Job and eval lists
share the duration helper, and job details expose that end time so the modal
shows the same fixed duration. Terminal jobs without a known end time return
no duration instead of elapsed age. Active retries remain running even when
earlier pod attempts failed; terminal conditions take precedence over counters.
The jobs table also displays a valid zero-second duration.

## Verification

- `.venv/bin/python -m unittest discover -s tests -p test_dashboard_job_timing.py -v`:
  all 10 tests passed. Coverage includes advancing clocks, successful jobs,
  active retries, terminal conditions, unknown timestamps, zero duration, and
  job/eval list and job detail endpoints.
- Python compile checks, `node --check src/dashboard/static/js/jobs.js`, and
  `git diff --check` passed.
- `make host-rebuild-dashboard` completed; rollout confirmed the new pod ready
  with image `sha256:2a96d1d32373e661ee0cb6e514393076bb77569789c740a5e955d69966c315ea`.
- Playwright checked the actual deployed API and table across two automatic
  refreshes. All four failed durations stayed identical: 34, 32, 4,404 and
  1,402 seconds. The last job's detail modal showed `1402.0s`.
