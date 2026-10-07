# M3 Claude hook conflict: analysis and options

Date: 2026-10-05. Option 2 was accepted and implemented with the revisions
below. See [ADR-0007](../decisions/ADR-0007-claude-hook-checks-and-opt-out.md).
Relates to the [POC plan](../plans/fullsend-entrypoint-strategy-poc.md) M3
and the [completed M3 task](../tasks/done/fullsend-entrypoint-feature.md).
Code references are to `checkouts.fullsend_prototype/jctanner.fullsend` on
`feat/entrypoint-harness` (based on `7a2622076`).

## M3 outcome and evidence

M3 closed the upload/launch gap using runner-held trusted hashes, checks
before supported Claude child launches, and an independent outer-runner
check before result acceptance. Hooks remained enabled. A real Claude run
proved the configured canary hook executed and blocked Bash. Four tamper cases
(changed, deleted, replaced, unexpected hook-directory entry) failed closed,
and each verified sandbox cleanup. See the task for test results and markers.

The race-enabled Fullsend test target passed with 83.9% total statement
coverage; staged pre-commit checks passed. The target needed a temporary
`gh` stub under `/tmp` because legacy tests invoke the host `gh auth token`
after clearing token environment variables, causing indefinite waits. The
stub made that no-token condition deterministic and was not added to the
branch. Added fixture-level token neutralization for the encountered
Cloudflare and agent tests.

The original blocker is therefore cleared for M3's detection bar. Prevention
remains outside this milestone: OpenShell 0.0.116 blocks read-only uploads and
does not permit removing write access from a live sandbox. The documented
checkpoint checks do not detect helper bypass or tampering restored before a
check, and cannot undo external writes. Immutable installation remains a
separate follow-up.

## The conflict

On OpenShell 0.0.116, a read-only `/sandbox/claude-config/hooks` rejects
bootstrap hook uploads. A writable directory accepts them, but the fork's
`fullsend-claude` helper refuses to launch (exit 78). The gateway also refuses
to remove a write grant from a live sandbox.

## 1. The M3 bar is stricter than upstream's own Claude path

Upstream's agent-led Claude bootstrap already leaves hooks agent-writable.
`installClaudeHooks` (`internal/runtime/claude.go:420`) uploads scripts to `/sandbox/claude-config/hooks/`
and originally wrote `hooks.json` in the parent config directory (the fork
moved that settings file into `hooks/`), and
`docs/contributing/runtime-implementation.md:704` calls this "the same
residue Claude Code has with `claude-config/hooks.json` and its scripts". The inspected upstream Claude launcher has no equivalent file-integrity guard.

The writable-directory probe in `ClaudeEntrypointHelper`
(`internal/runtime/entrypoint.go:41`) is new in the fork and is what creates
the deadlock. M3 is effectively gated on a security level upstream does not
have. That is a scope decision, not a technical dead end.
[ADR-0006](../decisions/ADR-0006-claude-strategy-poc-scope.md) says to
replicate existing behavior, which motivates matching the agent-led level and recording the gap. It did
not itself authorize revising the security criteria; ADR-0007 now records that
explicit user decision.

## 2. More than parity: the Codex tamper-evidence pattern

Codex hit the same problem: its config directory is writable because the
agent runs as the same user. It uses **tamper evidence instead of
prevention** (`internal/runtime/codex_integrity.go`, `codex_run.go`):

- Embedded hook scripts have compile-time SHA-256 values. Digests for
  per-run rendered files (`hooks.json`) are recorded on the runner side at
  Bootstrap and are never read back from the sandbox.
- The launch guard uses `command -p sha256sum`/`cut`, so shell functions or a
  planted `PATH` cannot fake the check.
- An exhaustive `find` listing fails on symlinks or extra planted files.
- Integrity failures use distinct exit codes (97/98).

Adapting this to Claude replaces the read-only probe and follows an
established repository pattern. The implementation was live-verified on the
M2 OpenShell 0.0.116 environment. Codex also implements checks during hook
execution; copying its launch guard alone does not provide its full coverage.

**Caveat for entrypoints:** Codex's guard runs in a launch command the runner
issues through `openshell exec`. In entrypoint mode, the script launches
Claude children itself through `fullsend-claude`. That helper and the
entrypoint script are also uploaded, writable files. A child running with
`--dangerously-skip-permissions` could rewrite the helper, the hooks, or the
running bash script (bash reads scripts incrementally). A guard inside the
helper only checks between children, so pair it with:

- **A runner-side check after the run:** before teardown, the runner verifies
  the hook, settings, helper, and entrypoint digests via `openshell exec`
  before accepting results, retrying, or running publication post-scripts.
  Expected values and the verification command come from the outer runner.
  This detects modifications still present at verification time, not changes
  restored beforehand. It cannot prevent tampering or undo external writes.
  The writable helper itself is not an independent trust boundary.

## 3. Options for real prevention

- **Bake the hooks into the sandbox image.** Step 3 already needs a custom
  sandbox image. The hook scripts are static embedded assets, so put them and
  the helper at a path the policy marks read-only when the sandbox is
  created. No upload is needed, so the live-policy restriction does not
  apply. `hooks.json` is rendered per run; Claude Code's `--settings` should
  also accept inline JSON, which would avoid the file (verify on the pinned
  Claude version). Downside: it couples the image to the Fullsend version.
  Review that maintenance tradeoff with upstream; suitability is not yet
  established. Protect generated settings, launcher, and relevant environment
  as well as the static scripts.
- **Ownership instead of policy.** Run one experiment: if `openshell upload`
  or a bootstrap exec runs as a different UID from the agent, root ownership
  with `0555` would make the hooks non-writable without Landlock. The upload
  UID has not been checked. Also verify Claude cannot change the permissions
  or replace the files through a writable parent directory.
- **Newer OpenShell.** Refusing to remove a write grant from a live sandbox
  may be deliberate, because Landlock restrictions only apply to processes
  started after the rules are set. Check releases after 0.0.116 for file
  injection at create time or before the policy is applied; if none exists,
  file an upstream issue. Per the plan's version-pinning rule, any upgrade
  must re-pass the M2 checks.

Separately, the strategy policy must never grant write access to `/sandbox`
as a whole, because that cancels nested read-only paths (as the harness
reference notes).

## 4. Follow-up boundaries

- M3 is complete at the parity-plus-detection bar, including real Claude
  hook/tamper tests and repository gates. Prevention is tracked separately by
  [immutable hook installation](../tasks/pending/fullsend-immutable-hook-installation.md).
- The tests were slow, and several legacy fixtures stalled on host `gh auth
  token`. A temporary no-token stub let the full prescribed target finish;
  the final run passed both default and GitHub-tagged tests.
- Proceed with the strategy-script copy and later runner consolidation under
  the M3 checkpoint-detection limits documented above.

## Accepted sequence

1. M3 option 2 and the revisions above are complete. The
   [completed task](../tasks/done/fullsend-entrypoint-feature.md) records the
   trusted expected hashes, exact-file checks, real Claude execution, tamper
   cases, and failure handling.
2. Add [the sandbox hooks switch](../tasks/pending/fullsend-sandbox-hooks-switch.md)
   afterward: `security.sandbox_hooks.enabled`, default true. This is a
   separate capability, not a way to pass M3 without testing hooks.
3. Track [immutable installation](../tasks/pending/fullsend-immutable-hook-installation.md)
   separately; no prevention claim is made by M3's checkpoint checks.
