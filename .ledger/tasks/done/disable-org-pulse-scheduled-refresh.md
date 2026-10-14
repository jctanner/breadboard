# Task: Disable Org Pulse's scheduled refresh

## Goal

Suspend `org-pulse-sync-refresh` in the live `ai-pipeline` namespace and
persist `spec.suspend: true` in the authoritative deployment manifest.

## Status

Done, 2026-10-14. User requested disabling the repeated refresh jobs.
Before the change, the CronJob ran every fifteen minutes and had no active jobs.

## Acceptance criteria

- [x] Set `suspend: true` in `deploy/k8s/28-org-pulse.yaml`.
- [x] Update maintained Org Pulse deployment documentation.
- [x] Suspend and verify the live CronJob.
- [x] Validate the manifest and run `git diff --check`.

## Evidence

- Applied `kubectl patch cronjob org-pulse-sync-refresh -n ai-pipeline
  --type=merge -p '{"spec":{"suspend":true}}'` successfully.
- Live readback reports `SUSPEND=true` and no active jobs.
- YAML parsing confirms the named CronJob has boolean `spec.suspend: true`.
- `git diff --check` passes. Updated `docs/org-pulse.md` to record the default.
- Historical jobs remain available; no service image rebuild was required.
