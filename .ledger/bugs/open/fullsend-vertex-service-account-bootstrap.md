# Fullsend strategy wrapper only bootstraps authorized-user ADC

## Summary

M6 requires a dedicated Vertex-only service account. The pushed strategy
wrapper currently adds `--from-gcloud-adc` to provider creation for every
credential file, and `fullsend-vertex-ai.yaml` declares only OAuth2
client-id/client-secret/refresh-token material. Those are authorized-user
inputs, not a service-account JWT refresh configuration.

## Evidence

The feature checkout at `bd20534f5b904ae7808d167ad3cde671e17d5ab1` has this
wrapper/profile. Local OpenShell source `d1155aa7` explicitly rejects
`type=service_account` in `read_gcloud_adc`, directing callers to a
service-account-key provider with gateway-managed JWT refresh. Its stock
`providers/google-vertex-ai.yaml` declares service-account refresh material.
That newer source is guidance, not proof of the pinned 0.0.112 image's API.

## Expected

Select bootstrap and refresh strategy by credential type, using the pinned
image's supported API; prove a dedicated Vertex service account in the real
strategy run. Preserve credential redaction and job-owned cleanup.

## Impact / status

Deferred capability; not an M6 blocker under the user's 2026-10-06
override to use the existing Breadboard Vertex credentials. No dedicated credential is currently available;
existing platform and project ADC inputs are both authorized-user. The CI job now uses the authorized-user type under that override. Verify pinned runtime
support, update the fork with unit/full checks, and perform real acceptance
once the required identity is provided.

## Related task

[M6](../../tasks/done/fullsend-strategy-poc-integration.md)
