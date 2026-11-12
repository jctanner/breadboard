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

## Final verdict (round 6, implementation head `cea968c`)

Codex: **NO BLOCKERS**. Claude CLI: **NO BLOCKERS**; both round-5 should-fixes
closed, no regressions. Every mandatory should-fix is closed or acceptably deferred.
The final read-only review is retained locally at `/tmp/cc61-claude-round6.txt`.

Optional round-6 nits explicitly deferred: friendlier traceback when initial public
root publication is interrupted (the failure is safe and recovery is documented);
the redundant final `03` hint to run `04` again (idempotent/cosmetic); and static tests
asserting particular shell/Make command spellings (would mirror implementation).
Fresh standalone deployment qualification needs a disposable cluster and remains
unverified, per the user's prohibition on deployment against the live install.

Publication: the approved fallback branch is pushed to jctanner/breadboard. No commits
were pushed to durandom's fork. #8 remains open without comments or reviews. Original
16 commits remain unchanged. Current main `95a1399` was merged without rewriting them.
The replacement PR is prepared in `/tmp/cc61-pr-body.md`, but GitHub CLI reports no
logged-in API account. SSH push authentication works; API auth is the sole remaining
publication dependency. The human was asked to run `gh auth login`; no credentials
were read from environment files. Do not claim manual-merge readiness until the new
PR exists. Use a merge commit to preserve the original commits and authorship.

## Pushed commit inventory (first-parent additions after original head)

- `e044b74` fix(deploy): preserve domain constraints and safe host defaults
- `001c9c3` fix(fullsend): publish native assets and isolate synthetic CVE results
- `a8cefef` fix(cli): verify TLS and respect operator cluster selection
- `cac6441` fix(deploy): confine Lima mounts and make host changes opt-in
- `59d2a8b` fix(seed): verify transport and guard destructive operations
- `2a03dd0` test(proxy): isolate route configuration and cover custom-domain streams
- `b0c5183` Merge remote-tracking branch 'origin/main' into pr8-breadboard-domain-lima
- `35b8bb5` fix(deploy): bootstrap seed TLS without changing host trust
- `73c1320` test(tls): verify allowed and forbidden names with OpenSSL
- `d303c83` fix(seed): paginate existing fixtures before creating tickets
- `7e25d73` docs(ledger): track PR 8 review and publication status
- `9012150` fix(deploy): print configured domains in service access instructions
- `96ac0d4` fix(tls): refuse implicit CA migration before deployment changes
- `20dea95` fix(compat): preserve real forge links and validate existing VM mounts
- `b6379de` fix(deploy): guard all domain applies and retain fresh-install flow
- `cea968c` fix(deploy): share certificate bootstrap across component entry points

## Publication completed

Replacement PR: https://github.com/jctanner/breadboard/pull/10 (open, not draft),
created after the human explicitly authorized using the token in `.env.github`.
The token was read in memory and passed only in HTTPS authorization headers; no
credential values were printed or written to artifacts. The source PR #8 was
rechecked: still open at `3b18b726d143efc210b101d9d84267dcc5f6f42c`, unchanged.
The replacement PR credits @durandom, retains his 16 commits, includes the validation
and accepted deferrals, and requests manual merge with a merge commit. No PR comment,
review, label, closure, or merge was performed. The reviewed implementation remains
`cea968c`; subsequent changes are ledger-only publication records.

## Remote Linux qualification follow-up (2026-11-12)

The human subsequently authorized a separate Fedora test host and a custom domain.
The live launch checkout remains untouched. Work continues in the isolated copy
`/tmp/cc61-w530-bootstrap`; PR #10 remains the approved fallback, and #8 is unchanged.

Fresh deployment exposed and fixed: unattended Podman short-name resolution,
upstream OpenCode layout drift, unsupported declared Node engine range, non-root
public-CA readability under umask 0077, incomplete grouped-image resumes, empty CA
placeholders, public-only certificate serialization/cleanup and remote HTTPS/SNI
instructions. The x64 OpenCode artifact is explicitly baseline; source/fetch pins
verify HTTPS. All code changes retain original authorship with maintainer fix commits.

| Build review round | Codex disposition | Claude disposition | Closure |
| --- | --- | --- | --- |
| 1 | Fresh build repairs under test | Approve with should-fixes | Runtime smoke, qualified bases, documented build-input deferrals |
| 2 | Node trust/copy fixes identified | Changes requested for old-CPU target | Explicit baseline artifact and deeper target execution later closed CPU concern |
| 3 | Final runtime gate required | Conditional approve; wording fix | Final Node image and package-engine wording verified/fixed |
| 4 | Non-root CA and partial resume fixed | No blockers; portable builder/empty-CA should-fixes | RUN chmod and fail-closed CA input |
| 5 | Portable CA checks under test | Changes requested for CPU; PEM/cleanup should-fixes | Baseline, X509 serialization, cleanup and upgrade notes |
| 6 | No blockers after target smokes | Approve; bundle-count recommendation | Bundle rejection and relative-root cleanup added |
| 7 | No blockers | Approve; precise validation wording | Parseability wording and mixed legacy/trusted bundle rejection |
| 8 | No blockers | Approve; missing OpenSSL parse-failure test | Corrupt DER and standalone legacy/trusted cases added |
| 9 | No blockers | Approve; optional test assertions | Exact error assertions and valid-base64 invalid DER added; all pass |

Current focused suite: **106 passed, 5 live tests skipped**, including 48 isolated
CA-input cases. Shell syntax and whitespace checks pass for the current PR diff
against main (`95a1399`) and for the new fix commits. Whitespace inherited from
older main's patch files is outside this PR diff and has not been reformatted.

Observed on the test host: K3s/cert-manager Ready; nine certificate chains validate;
an outside-name leaf is rejected and domain drift is refused. The final agent runs
as its non-root user on a CPU without AVX2, loads OpenCode configuration with the
MLflow plugin configured, and verifies custom-domain HTTPS from Node. Both Fullsend
sandbox variants trust the public CA as UID 10001; supervisor bundle is mode 0644
and trusts that CA. Native Fullsend/OpenShell CLI help passes inside the runner;
runner Fullsend bytes match the staged release asset. Seven core HTTPS routes
return 200. Dashboard links use the custom domain. Demo seeding twice leaves the
same 25 Jira/GitLab tickets and correct link domains.

Full-stack build/deployment and Fullsend execution qualification are still ongoing;
these checks do not yet establish complete end-to-end readiness.

Accepted nonblocking follow-ups: reconcile the fork's Bun lockfile and multi-target
build filter; keep the pinned fork commit reachable (no tag/protection changes are
authorized here); pin other pre-existing moving build inputs; improve opt-in tag-only
cache fingerprints/unfinished-alias recovery (default forced rebuild is safe and the
runbook requires it after changes/interrupted imports); consolidate existing Fullsend
CA extraction; qualify Python certifi clients where internal HTTPS is introduced;
and handle legacy manual CDPATH/space-containing project paths separately. Current
host/Make paths are absolute and do not exercise those legacy path limitations.
Client DNS/trust-store setup, real model inference, interactive OpenCode TUI, macOS
Lima/ARM and legacy Docker runtime qualification remain outside the passed checks.


## Host operator and Fullsend seed follow-up qualification

The ordinary operator's bundled K3s kubectl continued selecting the root-only
server config after the old copy target succeeded. The replacement target installs
a protected user config, backs up differing operator data, preserves explicit
KUBECONFIG and adds an idempotent interactive Bash fallback. A fresh interactive
Bash on the test host now runs kubectl without sudo; the root server file remains
0600. Other shells use the documented explicit export.

Fresh Fullsend seeding exposed two further failures: sudo ownership checks after
isolating Git configuration, and transient emulator SQLite locks. Each seed Git
command now trusts only its controlled resolved checkout through a temporary
protected global configuration, disables hooks/helpers and filters inherited Git
redirects. Lock retries are bounded and restricted to replay-safe operations.
Duplicate creation conflicts are confirmed by reading the expected resource.
The complete seed subsequently succeeded on the test host.

The first conformance attempt failed at Mint because the UI App inventory omits
permissions. Bootstrap now reads canonical REST App grants, verifies the installed
grants, refuses malformed metadata, and reports rollback failures for newly created
mismatches. Existing installations are never deleted by verification rollback.
All bootstrap HTTPS requests verify the selected public CA. Authenticated checks
inside Mint confirmed all eight actual installation maps match their App grants;
no keys, JWTs or tokens were exported by those checks.

| Follow-up review round | Codex disposition | Claude disposition | Closure |
| --- | --- | --- | --- |
| 10 | Kubeconfig fix under test | No blockers; backup/root/mode should-fixes | Protected backup, root refusal and mode tests added |
| 11 | Seed ownership/retries under test | No blockers; protected scope/hooks/retry evidence | Temporary global config, hooks disabled, actual lock response confirmed |
| 12 | Grant source corrected | No source blockers; conflict/grant tests requested | GET-confirmed 422s, varied role-map tests, eight real grant checks |
| 13 | Source approvable; integration blocked | No source blockers; rollback/type guards requested | New-only mismatch cleanup and malformed metadata guards |
| 14 | Source approvable; integration blocked | No source blockers; rollback reporting/env tests requested | Failure diagnostics, existing-installation regression and inherited-env filtering |
| 15 | No blockers within documented single-operator trust boundary | No hard source blockers; hardening/test/documentation should-fixes | HTTP timeouts, malformed errors, more inherited-env filtering, distinct rollback IDs and failure branches; partial bootstrap documented |

Current focused regression suite: **161 passed, 5 live tests skipped**. Shell
syntax and PR whitespace checks pass. All application deployments are Available;
cluster/certificate validation and a custom-domain in-cluster DNS probe pass.
Strictly verified HTTPS routes and idempotent demo seeding remain qualified.

**Integration is not qualified. Ready for manual merge: no.** A second conformance
attempt passed Mint, checkout and setup but failed while activating the OpenShell
sandbox's effective configuration (ConfigurationInvalid). An independent sandbox
probe without attached providers reproduced that activation failure. The public
OpenShell runtime capability probe passes both in an isolated Podman container
and in a hardened K3s pod on this host; no host-wide security controls were
weakened. Metadata does not explain the remaining runtime activation failure.
Diagnostic log inspection awaits explicit permission after automatic approval
review rejected earlier exports because they might contain credentials/session
material. No raw diagnostic logs were exported after those rejections.

Accepted source deferrals: operator-owned local Git configuration stays within
the operator's existing sudo trust boundary; eight-App bootstrap is not atomic
and retains earlier valid reconciliations on a later failure; pre-existing token
arguments deserve a separate protected-file/stdin cleanup; Bash-only shell setup
is documented. Real model inference, client DNS/trust configuration, macOS Lima
and ARM remain unqualified. No Model Relay upstream accounts were explicitly
provisioned for this qualification.

Review 15 deferrals: untrusted/shared root seed checkouts are unsupported, as now
explicitly documented; root seeders operate on the trusted operator's committed
integration checkouts and controlled temporary repositories. Disabling every
possible local Git configuration/attribute command would require redesigning the
seed flow and is not claimed here. HTTPS-only Git protocol enforcement is deferred
because helpers also perform local fixture operations; inherited protocol overrides
are removed. A separate shell CA-selection fixture is deferred because the actual
bootstrap successfully selected the cluster CA and verified the emulator chain,
and TLS context assertions cover the Python grant reconciliation. OpenSSL was
already a required host dependency for the CA/deployment flow.


### Wider mirror security audit (rounds 16–18)

Round 16: Codex and Claude identified source symlink reads, unwrapped Git callers,
canonical requested-grant verification, repository selection and inventory shape
checks. All are fixed, with executable regressions. Git environment handling now
clears inherited Git controls rather than keeping an incomplete denylist.

Round 17: Claude requested changes for fetched/source links in composite-action
mirroring and CVE fixture staging. Codex also identified fetched parent/broken-link
cleanup hazards in the Fullsend mirror. Shared guards now reject linked ancestors,
replace final destination links without following them, and clear whole upstream
mirror working trees without traversing fetched links. The selective CVE fixture
writer preserves unrelated repository content. Directory collection supports a
symlinked operator checkout root; App grant mismatches have a precise error.

A real agents checkout contains legitimate tracked fixture links, so upstream
mirrors preserve final symlinks as link text without reading their targets rather
than aborting on them. Ancestor links and escaping source paths remain forbidden.
Source action/plugin links are refused. The real privileged copy probe succeeds
for 54 Fullsend files and 482 agents entries, preserving 12 links. Real plugin
staging generates 16 dummy files and 15 Pi files; three composite actions copy
through guarded paths. Those probes use controlled temporary directories and do
not publish new fixture commits or execute models.

The stricter canonical-grant/repository-selection bootstrap succeeds against the
real cluster-selected public CA. A repeat run also succeeds with existing org-wide grants (both systemd runs exit 0).
End-to-end sandbox activation remains blocked as documented in
[the open qualification bug](../bugs/open/w530-openshell-configuration-activation.md).


| Wider follow-up round | Codex verdict | Claude verdict | Closure |
| --- | --- | --- | --- |
| 16 | Should-fix mirror reads and exact grant checks | No delta blockers; conditional trust concern | Final-link preservation, ancestor rejection, isolated Git calls, exact requested grants/selection/inventory checks |
| 17 | Request changes for fetched-link hazards | Request changes: composite and CVE writers | Both writers guarded; fetched mirror cleanup and source reads covered by real filesystem regressions |
| 18 | No blockers after fixes | No source blockers; linked-walk/destination test suggestions | Directory links under linked SOURCE tested; upstream destinations guarded; directory leaves rejected |
| 19 | No source blockers; integration blocked | No blockers; confirm CVE fixture test | Actual stage_files uses guarded output(); complete suite passes 161/5; integration gate remains open |

Final source should-fixes are closed or explicitly deferred. Faithful upstream
link targets are retained, rather than validated/rewritten for consumers: the seed
host reads only link text; agents Actions is disabled; normal Fullsend reuse reads
workflow contents through Git/API. A consumer that independently checks out and
follows an absolute/escaping upstream link must enforce its own filesystem
boundary. This documented consumer hardening is a nonblocking follow-up accepted
by both reviews. A separate nested-copy end-to-end fixture is optional: filesystem
component tests plus real privileged copies of all 536 source entries already
exercise collection/copy/link semantics. The final existing-directory CVE case is
confirmed by executing the actual stage_files, not a copied test implementation.

No fork-main push, force-push, merge, PR comment/review, label or closure occurred.
The replacement PR stays work in progress for integration despite source approval.
