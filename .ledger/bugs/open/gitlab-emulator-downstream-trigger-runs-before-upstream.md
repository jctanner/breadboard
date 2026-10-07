# GitLab emulator dispatches downstream bridges before upstream completion

## Reproduction and evidence

M6 pipeline 2033 dispatched dashboard pipeline 2034/pages job 3945 while
connectivity job 3942 was running and single-rfe job 3943 remained manual.
Bridge job 3944 immediately became success.

`checkouts/gitlab-emulator/app/api/pipelines.py` `_create_pipeline` creates
all downstream pipelines directly after persisting parent jobs; it does not
wait for upstream stages or blocking manual jobs.

## Expected / impact

The dashboard should build only after strategy results are committed.
Current behavior can publish a stale dashboard and report success even if
strategy fails. Adding an explicit `needs: [single-rfe]` expresses the intended
contract but does not correct the emulator's eager bridge implementation.

## POC recovery

Preserve the native trigger, record this production difference, and dispatch
and verify a fresh dashboard build after successful results publication.
Emulator scheduler correction remains separate work; do not claim the early
build proves final results were rendered.
