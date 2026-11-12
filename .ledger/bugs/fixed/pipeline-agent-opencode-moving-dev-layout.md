# Moving OpenCode dev branch breaks pipeline-agent build

## Reproduction

Fresh build resolves upstream dev to `5418e010d75dc3bb0b79e5cf0f32118a288864f7`.
The next build command fails: `cd: can't cd to packages/opencode`.

## Fix

Pin the existing integration fork to committed revision
`9f55fe01b9304cc34534dbf1e69b0f8c4bfc8c77`, whose build script is present at the
expected path. Fetch the exact revision (rather than passing a SHA to clone
--branch), verify HTTPS, and execute the built CLI's --version as a build smoke
check. The image's public CA bundle is installed explicitly.

The original PR selected this integration fork on a moving branch. A fresh deployment
now supplies concrete evidence for retaining that source with an immutable revision
instead of reverting to another moving branch. The image was built on the AVX-only test host and both builder and final runtime
`opencode --version` returned `0.0.0-local`. Claude review found no code blockers;
lockfile reconciliation and commit availability remain documented follow-ups.
