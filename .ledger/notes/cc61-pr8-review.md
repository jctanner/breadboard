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
- S1–4: require explicit CA migration before changing an existing root, narrow default external constraints to actual
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

Offline dashboard/domain/CLI/seed regression suite: 85 passed, 5 explicitly skipped
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

## Round 2

Claude: request changes on frozen `b0c5183`. Its missing seed-CA blocker was
already fixed by `35b8bb5`. The CA migration blocker is addressed by refusing an
existing incompatible issued CA before mutation, retaining the root key on routine
renewal, and validating all public leaf chains against the ConfigMap root.

Additional fixes: check existing Lima mounts, avoid implicit online status and
hardcoded runner scope, preserve genuine GitLab web URLs, pass the domain to
host-reset, correct behaviour defaults/operator guide metadata, preserve runner
build-context dotfiles, validate ticket sources, and remove duplicate/unused imports.

Additional explicit deferrals: the named legacy direct-token HTTP smoke remains a
`.local` compatibility fixture (not custom-domain TLS coverage); arm64 upstream-runner
image/checksum qualification needs its ignored component checkout and disposable
Apple Silicon build. These limitations are documented in the maintained Lima README.
New site-runner mint/private-forge env settings are justified there.
Historical author ledger logs describe superseded experiments, not current deployment
behavior; current review/runbook notes override them. Retaining this review note in
`.ledger/` follows repository policy for durable project evidence, not product docs.

## Round 3 (frozen `9012150`)

Claude: request changes for the same implicit CA/domain migration issue; accepted
S8/S13/S15 deferrals. The next snapshot guards both stored CA specification and
issued public constraints before any automatic CA apply, preserves the root key
on routine renewal, and exposes migration guidance to Linux/Vagrant operators.
All host deploy/reset/conformance Make targets forward the domain and explicit
DNS/hosts/cache options; Lima passes the same settings by argv. Seeding reads only
the public ConfigMap. Additional tests cover old-CA refusal, fresh clusters,
existing-home-mount rejection, absent runner metadata, and real GitLab URLs.

## Round 4 (frozen `20dea95`)

Claude: **NO BLOCKERS**, with three nonblocking should-fixes. All three are fixed
in the next delta: preflight follows K3s availability; non-rendering manifest applies
centrally guard domain/CA compatibility (fresh CA setup publishes the public root
before leaf applies); and the runbook explicitly requires deleting the old root
Certificate **and Secret** during a deliberately authorized maintenance migration.
Org Pulse's Make rebuild now uses the renderer too. Minor fixes restrict external
GitLab link schemes, isolate seed git TLS from global/system overrides, and handle
null Lima configuration. Future IPv6 constraint parsing remains explicitly deferred
because the current manifest contains only IPv4; unsupported inputs fail closed.

Final local validation: 85 Python tests passed, 5 live-stack tests skipped; Node,
Python compilation, all changed-shell syntax, full-diff whitespace and render-only
Make forwarding checks pass. Go proxy tests passed after its final code change.

## Round 5 (frozen `b6379de`)

Claude: **NO BLOCKERS**, confirmed all prior should-fixes closed, and reported two
new nonblocking should-fixes. Standalone emulator/Markovd scripts now use the complete
shared certificate bootstrap, and all identified domain-bearing host rebuild/seed
Make applies use the guarded renderer. An interrupted initial root publication has
an explicit authenticated recovery procedure rather than a silent trust fallback.
The Fullsend image build also checks compatibility before baking a domain into
profiles or importing images, preventing a wrong-default rebuild before deploy
preflight can reject it. No implementation changes remain outside these closures.
