# Org Pulse rejects some historical aggregate strategy records

## Evidence

Post-merge real GitLab smoke pipeline 2996306877, job 17518703899, on
2026-10-27T20:55:11Z: exporter prepared 1,059 aggregate features, then reported
1 created, 0 updated, 1,040 unchanged and 18 entry validation errors.

Printed examples: RHAISTRAT-2186, -2200, -2201, -2322 and -2323. Errors include
invalid/missing recommendation, scores object and reviewer verdicts. The
remaining thirteen keys are truncated from the CI log, so their identities
were not established. This is an aggregate-data compatibility follow-up,
separate from the current smoke's validated RHAISTRAT-3074 result.

The current run's numeric 7/8 approval and testability revise are present in
sealed data and dashboard output. Org Pulse returned successful upload counts,
but a per-feature GET from the local host could not resolve its internal DNS
name. Counts alone do not prove which feature was created.

## Impact and next step

Exporter warnings are nonblocking, so a green pipeline can coexist with
rejected aggregate entries. Inspect all rejected identities and source
records before choosing migration, explicit exclusion or schema adaptation.
Do not weaken the new review contract merely to accept malformed history.
No application/source change or additional model run was made for this smoke.

Evidence: var/run-data/20261027-real-gitlab-postmerge-single-opus46/,
job trace lines 838-889 and verification.json.
