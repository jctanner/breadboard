# Retro, prioritize, scribe and fix ran on images k3s does not have

Found 2026-11-08 in the behaviour-test T2 rerun (BT-B4):
`retro-cel-route.feature`, "an on-demand retro trigger skips the retro on
close and keeps /fs-retro".

## Symptom

```
Sandbox creation attempt 1/3 failed (sandbox create failed: signal: killed
(output: Created sandbox: fs-ret-557e52685e40 ... [4.5s] Image pulled)), retrying in 5s...
Error: creating sandbox: sandbox creation failed after 3 attempts
```

Each attempt took about 130 s, which is Fullsend's sandbox readiness timeout
(`readyTimeout` + `readyCtxBuffer`), and was then deleted.

## Cause

OpenShell creates sandbox pods with `imagePullPolicy: Never`. Agents patch
0004 points three harnesses at the CA-bearing local images 05i builds:

- `triage` at `fullsend-sandbox-local:k3s`;
- `code` and `review` at `fullsend-code-local:k3s`.

Four harnesses kept their upstream digests, which k3s does not have:

- `retro`, `prioritize` and `scribe` pin `fullsend-sandbox@sha256:8e17e612…`;
- `fix` pins `fullsend-code@sha256:8c5953b8…`.

A probe sandbox from the retro digest stayed `Pending`. Its `workspace-init`
container was in `ErrImageNeverPull`. Prioritize passed T2 only because its
scenario never starts the agent. Even with the image present, an upstream
image would lack the internal CA, and the forge handshake would fail.

## Fix

- Agents patch 0004 substitutes the local images in all seven harnesses.
  The four added ones pin the same digests as triage and review, so the
  existing local builds cover them.
- `deploy/scripts/05i-build-fullsend.sh` fails if any harness pinning a base
  repository uses a digest other than the one its local image is built from.
  The check was exercised with the real pins (no mismatch) and with a
  substituted digest (code, review and fix reported).
- 0001–0006 apply in order. The mirror was reseeded at `ae132427` (source
  `e41be7b4`).

Not yet verified end to end: that needs the T2 rerun after the 05i rebuild.
