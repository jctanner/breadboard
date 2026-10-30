# Route every Fullsend agent's model traffic through Model Relay

## Goal

Decided by the user 2026-10-29: use Model Relay for all Fullsend model access
in this stack, so no Google credential enters a sandbox.

## Context

Two setups exist today:

- **GitHub-emulator path** (conformance, `fullsend-dev/triage-target`): Vertex
  directly. The runner mounts Secret `gcp-credentials` (`credentials.json`, an
  `authorized_user` gcloud ADC login — a person's long-lived refresh token) at
  `/var/run/secrets/gcp/credentials.json` (`deploy/k8s/23-github-actions-runner.yaml`),
  with `CLAUDE_CODE_USE_VERTEX`, `CLOUD_ML_REGION` and
  `ANTHROPIC_VERTEX_PROJECT_ID` from `pipeline-secrets`. With no WIF inputs,
  `fullsend run` uses that file, and the harnesses' `host_files` copy
  `${GOOGLE_APPLICATION_CREDENTIALS}` into the sandbox as
  `/tmp/.gcp-credentials.json`. The `vertex-ai` provider declares no
  credential, so the real refresh token is inside the sandbox. Production uses
  a short-lived WIF token file in the same mount.
  `docs/fullsend-compatibility-profile.md` does not list this substitution.
- **GitLab demos** (`var/demos/fullsend-claude-workflow/ci/configure.py`):
  already relay-based. `host_files` emptied, `CLAUDE_CODE_USE_VERTEX=0`,
  `ANTHROPIC_BASE_URL=https://relay-api.local`, and a local `model-relay`
  provider injects `ANTHROPIC_API_KEY` as a placeholder from
  `MODEL_RELAY_API_KEY`, with a profile allowing only `GET /v1/models`,
  `POST /v1/messages` and `count_tokens` on `relay-api.local`.

## Acceptance criteria

- [ ] Plan written: how the GitHub-emulator path adopts the demo's pattern
  (harness changes as a local patch vs `base:` composition vs repository
  `.fullsend/` overrides), relay API key provisioning per role, and the
  runner's Vertex env/secret removal
- [ ] No `gcp-credentials` mount on the Fullsend runners
- [ ] Conformance passes with model traffic visible in the relay console
- [ ] Compatibility profile records the relay substitution

## Status

Pending — after the v0.52.0 rebase deploy and conformance run
([task](../current/fullsend-v052-patch-rebase.md)).
