# ADR-0002: The Fullsend runner-label override (patch 0012) stays

## Status

Accepted, 2026-09-27. Runner consolidation plan, phase 4.

## Context

Fullsend's scaffold renders `runs-on: ubuntu-24.04`, its `DefaultGHRunner`,
and its reusable dispatch defaults every job to the same. On this stack that
label is served by the hosted stand-in, an upstream `actions/runner` on
`ubuntu:24.04` at enterprise scope, which is the honest place for generic
CI. Agent work cannot run there: it needs the OpenShell client, the route to
the gateway, the pinned tool inventory (`gh`, `yq`, `gitleaks`, `pre-commit`,
Go) and the compatibility layer `runner.py` provides - `GH_HOST`,
`GH_ENTERPRISE_TOKEN` and the OIDC variables injected into every step, and
the shims for `google-github-actions/auth`, `actions/setup-go` and
`actions/upload-artifact`. Whether the upstream runtime, the actions
themselves or the emulator could supply equivalents is unverified, and each
verification is a paid run.

Patch 0012 makes `RunnerImage` readable from `FULLSEND_RUNNER_IMAGE` in the
install's render options; unset, upstream behaviour is unchanged. The
dashboard passes `fullsend` and the scaffold renders `runs-on: fullsend`.
The conformance plan's G6 recorded this as a documented substitution.

## Decision

Keep the override. Two runner tiers need two labels, and a render-time
label is structural to that layout, not a deviation to be removed. The
alternative - making the agent runner a faithful hosted image so the stock
label suffices - would mean either reopening the agent runner's egress to
install tooling per job, which conformance item F4 closed on purpose, or
proving the compatibility layer redundant one paid run at a time.

## Consequences

- G6 is addressed, not resolved, and says so.
- Onboarding stays what ADR 0033 describes: `fullsend github setup
  <owner/repo>` with the agent runner at site scope, so no deployment
  follows a repository.
- The override is one variable on the dashboard deployment. A stack whose
  agent runner did carry the stock label would unset it and change nothing
  else.
- Revisit if upstream ever gains a per-install runner label of its own, or
  if the compatibility layer is shown redundant; the patch is the only
  thing this decision keeps alive.
