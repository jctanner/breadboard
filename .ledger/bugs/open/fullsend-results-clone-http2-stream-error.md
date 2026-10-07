# Results Git clone HTTP/2 stream error

## Reproduction

Fresh batch pipeline 2057/job 4000, Fullsend bdedebeaf and strategy source
7244097: sandbox started, then entrypoint clone into artifacts failed with
`curl 92 HTTP/2 stream 3 was not closed cleanly: INTERNAL_ERROR`, unexpected
sideband disconnect, bad pack header, exit 128.

## Impact

Run aborted before Claude inference, issue locks or strategy writes. Historical
six issues unchanged, fresh RHAIRFE-4/5 unlocked without strategy links. Results
main stayed 54945d1. Logs/failed artifacts retained; sandbox deletion completed.
Stdout forwarding successfully exposed the clone failure in the CI log.

## Recovery

Retry only after verifying no Jira effects. A bounded fresh-job retry is being
attempted. If repeated, investigate the TLS passthrough transport and compare
HTTP/1.1 without disabling certificate verification or bypassing policy.

Bounded retry of 4000 succeeded without changing source or transport settings.
The intermittent transport issue remains open; do not claim a DNS fix.

## Likely cause (2026-10-07)

Pipeline 2061/job 4011 failed with the identical signature while the GitLab
emulator was OOM-killed serving this clone (512Mi limit; data-repo
`pack-objects` peaks ~205 MB at 16 threads). The image now caps
`pack.threads`. The 2057/4000 pod's restart history is gone, so this is
probable, not proven. See [trace/OOM bug](../fixed/gitlab-runner-trace-range-mismatch-stalls-terminal-status.md).
