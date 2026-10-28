# Bug: Default strat-creator Fullsend setup still needs portable bootstrap fixes

## Scope

Originally observed at `6ed858b`. Fullsend smoke 2100 passes with
Breadboard's deployment adapter, which works around two general defects that
remain in the source defaults. No Workflow JavaScript change is indicated by
the successful smoke.

## Default architecture fetch

`scripts/fetch-architecture-context.sh` uses cone sparse checkout for the
selected release and overlays. This also includes sibling aliases whose target
versions are excluded, so strict freshness hashing rejects the resulting tree.
2097 reproduced the failure. Breadboard used the prior benchmark's immutable
selected-release/overlays snapshot instead. Fix the default fetch itself with
a precise subset and regression coverage for sibling aliases; keep freshness
rejection intact. Pinned local-snapshot mode must continue to work.

## Host preflight checks the sandbox runtime on the host

All three `.fullsend/strat-*/strat-*.yaml` files invoke
`scripts/check_claude_runtime.py` from `validation_loop.preflight_check`.
Released Fullsend executes that preflight on the CI host. Claude is installed
inside its sandbox, so a host without Claude fails, and a host version does not
prove the sandbox version. The local adapter checks host Python dependencies
there instead. Retain the existing plugin SessionStart and pre-launch
freshness guard's qualified-runtime checks inside the actual sandbox; do not
weaken the version requirement. Include required host helper dependencies.

## What stays local

The relay.local endpoints and provider secret names, local certificates,
OpenShell relay executable allowlist, CI launch debug syntax and evidence
redaction/archive tooling belong in the deployment fixture. Do not copy local
credentials or endpoint configuration into the public feature branch.

Related: [passing native smoke](../../tasks/done/fullsend-claude-workflow-opus-single-smoke.md).

## Update: 2026-10-20

PR 85 commit 85e5cb3 fixes the host preflight in all three harnesses: only Python
dependencies are checked on the host; sandbox version hooks remain intact.
Its shared `.fullsend/ci/` setup supplies the tested precise live-context subset
for the GitLab consumer. The generic fetch script's default sparse-checkout path
is unchanged, so keep the bug open for that remaining default behavior.

Native direct registration also exposed missing local companion resolution in
the released Fullsend 0.47.1 binary. Shared setup now materializes the verified
package into private runtime state. Actual published-source bootstrap and
native locks pass for both agents. This is packaging evidence, not a new paid
runner smoke. [Consumer simplification](../../tasks/done/strat-pipeline-minimal-fullsend-consumer.md).
