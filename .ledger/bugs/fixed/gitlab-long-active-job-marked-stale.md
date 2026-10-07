# Long active CI job incorrectly marked stale and pending

## Evidence

User saw a pending/requeue warning for running batch 4000. Diagnostics used
started_at age >= 30 minutes without checking recent job or trace updates.
The template described every blocked diagnostic as pending, including running
jobs. Job 4000 continued producing progress and had a five-hour timeout.

## Fix prepared

Use latest started_at, updated_at and trace.updated_at to measure inactivity;
retain duration as informational metadata. Warning now refers to missing updates
and asks operators to check the runner. Template calls non-pending warnings
job activity warnings. Focused regression passed: an inactive 31-minute-old job
is flagged, then a fresh trace upload clears the stale flag without resetting
its started_at. Deploy after the current batch finishes.

## Status

Fixed and deployed after batch completion using make host-rebuild-gitlab.
Two scheduling diagnostic tests passed. Completed pipeline diagnostics report
4000 success/stale=false/blocked=false.
