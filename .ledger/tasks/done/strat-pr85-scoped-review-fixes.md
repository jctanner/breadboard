# Implement scoped PR #85 review fixes

## Authorization and scope

The user approved the seven bounded fixes after posting the owner's scope
decision on PR #85. Keep the current Claude Workflow, writable workspace,
in-sandbox Jira publication and numeric-only approval gate. Host-only Jira
publication and immutable sandbox redesign remain separate proposals.

## Acceptance

- [x] Direct harness defaults to dry-run; only explicit live mode writes.
  Missing input in a managed run refuses helper writes without breaking
  standalone interactive skills. Describe this as accident protection.
- [x] Publication checks outgoing artifacts for configured credentials before
  sealing/pushing; unsafe output stops without publishing or printing secrets.
- [x] Missing Strategy heading preserves existing SME input during import.
- [x] Failed-run exports retain lock ownership sidecar for later cleanup.
- [x] Org Pulse requires HTTPS and refuses cross-origin credential forwarding;
  preserve the user-approved temporary certificate verification exception.
- [x] Skipped-ticket parser recognizes `RFE Key` and maps columns by header.
- [x] Documentation states the actual guard/credential trust assumptions.
- [x] Relevant offline regressions, complete required suite, lint and whitespace
  checks pass; preserve sanitized evidence under var/run-data.

## Baseline and limits

Clean feat/s1-workflow-hardening at 85e8307. Local fake HTTP/temporary fixture
testing only; no model inference, live Jira/export replay, paid smoke, reviewer
reply, thread resolution, deployment or production cutover is authorized here.
No component commit/push requested by this instruction.

See [review assessment](../../notes/strat-pr85-stoyan-security-review-20261022.md).

## Completion

All seven bounded fixes are implemented locally on feat/s1-workflow-hardening,
based on 85e8307. Focused failures reproduced before repairs: seven context/mode
cases, eighteen publication/SME/export/parser cases and ten unsafe URL/redirect
cases. Focused repaired groups pass (12, 24 and 22 tests).

Full `env -u STRAT_WORKFLOW_SMOKE make test`: 1,230 passed, six optional skips,
362.72 seconds. Ruff, type descriptors, shell syntax and diff checks pass.
Thirty-seven-file archive including SHA manifest:
`var/run-data/20261022-strat-pr85-scoped-review-fixes/`. Configured-secret scan
and hash readback pass; no configured credential findings.

[Implementation notes](../../notes/strat-pr85-scoped-review-fixes-20261022.md).
No live integration rerun, model call, review reply/resolution, deployment or
cutover occurred during implementation.

## User-authorized publication

The user subsequently requested commit and push. Verified all 26 changed files
match the archived/tested bytes. Staged full-blob scan checks configured tokens,
private-key fragments and credential patterns; zero findings (one exact existing
synthetic non-key test fixture explicitly recognized). No sensitive files staged.
Created signed-off commit `32700ec6ea4476d62a6b768aa598883196dcb76e`, pushed to
origin/feat/s1-workflow-hardening and verified GitHub reports that exact SHA
as PR #85 head. Component worktree is clean. No forced update, new review reply,
thread resolution, benchmark run or deployment.
