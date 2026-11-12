# CC-61: PR #8 review and fallback preparation

Original author: @durandom (Marcel Hild). Original head:
`3b18b726d143efc210b101d9d84267dcc5f6f42c`; merge base `5142f2f1c5`.
Work is isolated under `/tmp/cc61-pr8`. The live install is never edited or deployed.
Fallback branch: `pr8-breadboard-domain-lima`. Original commits remain unchanged.

## Round 1

Codex: request changes. Claude (CLI, read-only file tools, safe mode, no MCP):
request changes. Claude reviewed the original full diff and source, and observed
source changes during review. Subsequent rounds must use a frozen snapshot.

Fixed findings (Claude identifiers refer to its first review):

- B1: Split DNS opt-in; local-domain no-op precedes side effects; no package installs.
- B2: remove personal project identifiers, paths and Tailnet topology; examples use
  illustrative addresses. Seeded model configuration comes from deployment settings.
- B3: Lima mounts only the repository, never the home directory. Lima 2+ required.
- B4: render CA manifests on every component deploy path.
- S1–4: rotate CA keys on renewal, narrow default external constraints to actual
  service names, remove external wildcard, document feature gates and trust migration.
  Export current root directly; never export its private key.
- S5–7: parameterize Jira/Org Pulse and related conformance defaults, correct TLS
  documentation, exercise all real manifests and verify leaf/CA name consistency.
- S9–12: validate domains and instance names, invoke Lima through Python argv (no
  shell interpolation), use a repository-only mount and atomic mode-600 kubeconfig,
  remove implicit personal cluster selection and guard SSH option parsing.
- S14–21: refuse installation recreation unless explicitly authorized, check delete
  failures, use verified TLS consistently in shared seed helpers and git, label canned
  output synthetic and keep it out of Pi runs, share one workflow shim, compare it
  without whitespace churn, publish only the ELF binary's native architecture,
  support HTTP(S) remotes with escaped credentials, add the missing plugin tests.
  Dummy config bootstrapping is intentional for the conformance target.
- S22–28: rebuild by default, match cached tags exactly, fail on absent sandbox
  dependencies unless explicitly skipped, remove automatic cache/mount mutation,
  make hosts updates opt-in, revert unrelated OpenCode defaults, make Pi override
  explicit, and remove unused ref checkout mutations.
- S29–34: require --yes and wait/check reset operations, validate repository paths,
  escape data rows, remove invented healthy runners, correct compatibility claims,
  opt in to live tests, relax timing assertion, restore Go test environment/global
  state, and add offline real-manifest, ELF, TLS, Lima and fixture regression checks.

Explicit deferrals:

- S8: cache freshness for opt-in `FORCE_REBUILD=0`. Rebuild remains the default.
  The opt-in is documented as valid only for unchanged source, domain and CA; content
  fingerprints for every component would require a separate build-cache design.
- S13: hashes/offline mirrors for Tailscale, Rust and uv bootstrap installers and
  the Go download. Optional VM provisioning follows existing online HTTPS bootstrap
  conventions. The limitation is explicit in the maintained README. No credentials
  are mounted outside the repo; this VM is not a hostile-code security boundary.
- S15: automatic trust of `deploy/certs/ca.crt` is intentionally not added. Select
  a verified public CA explicitly with `BREADBOARD_CA_FILE` or system trust. This
  avoids silently trusting mutable/generated files; new and shared seed paths verify
  TLS. Remaining independent legacy seed clients predate this patch.

## Validation

Offline dashboard/domain/CLI/seed regression suite: 73 passed, 5 explicitly skipped
live-stack tests. Go proxy tests pass (ephemeral loopback mock servers). Plugin Node
checks pass. Changed shell scripts pass `bash -n`; Python compile checks pass.
`git diff --check` passes. Re-run after subsequent changes.

Not run: deployment, installation, trust-store modification, image builds, VM lifecycle,
Tailnet ACL/DNS, macOS/Lima/Rosetta, existing CA migration or real Fullsend execution.
These need a disposable environment and operator verification described in
`deploy/lima/README.md`. Historical ledger deployment evidence is author-reported,
not newly reproduced on corsair.

No DCO/sign-off requirement was found in tracked contribution instructions.
Human co-author credit is included when changing the author's code; no AI trailers.
