# ADR-0003: Org Pulse joins the stack as the AI Engineering flavour, in demo mode

Date: 2026-09-29. Status: accepted.

## Context

`checkouts/org-pulse-core` and `checkouts/rhai-org-pulse` are one application
in two layers: core is the platform and publishes an npm package and three
images; rhai-org-pulse is the AI Engineering consumer whose images start
`FROM` core's at a pinned tag and add nine modules. Upstream deploys through
kustomize on OpenShift with an OAuth proxy, a managed MongoDB and a chatbot.
Breadboard wanted it as a first-class service on the same Makefile and
`deploy/` conventions as every other service.

## Decision

- **Layer: the AI Engineering flavour.** It is what the organisation runs,
  and it contains core. The build script constructs core's three images from
  the core checkout under the exact quay.io names the consumer's Dockerfiles
  expect, then builds the consumer on them, so both layers come from the
  checkouts and nothing is pulled from quay.
- **Mode: demo.** Core's Jira client is Jira Cloud only (REST v3) and its
  GitHub client names `api.github.com`, so neither emulator serves it as
  built. Live mode against real services needs credentials and egress the
  stack withholds. Demo mode serves fixtures and calls nothing.
- **MongoDB: a pod with a PVC**, the image upstream's compose file uses, so
  data survives restarts. The alternative, the in-memory server, is refused
  by core in production mode anyway.
- **Chatbot: left out.** It needs an LLM endpoint and key; add it when there
  is a use for it.
- **No OAuth proxy.** The backend's own local-dev fallback makes every caller
  the first `ADMIN_EMAILS` entry. Same standing as the rest of the stack's
  unauthenticated UIs.

## Consequences

`make host-deploy-org-pulse`, `host-rebuild-org-pulse`, `host-logs-org-pulse`
and the vagrant pair; `deploy/scripts/05l-build-org-pulse.sh`,
`26-deploy-org-pulse.sh`, `deploy/k8s/28-org-pulse.yaml`; certificate,
ingress, host-proxy route and dashboard link. Documented in
`docs/org-pulse.md`. Making Org Pulse talk to the emulators is a separate
plan of the Fullsend host-assumption kind; Observatory's existing import of
`org-pulse-config.json` is the natural starting thread.
