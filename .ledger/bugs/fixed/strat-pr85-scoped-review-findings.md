# Strat-creator scoped PR #85 findings

## Defects

Direct shared preparation treated missing/empty dry-run mode as live. Managed
helpers could fall back to standalone mode when run input disappeared. Results
publication lacked the CI secret checks. A missing Strategy heading could
cause reconstruction to discard SME input. Failure export omitted the owner
sidecar. Org Pulse accepted plaintext URLs and followed redirects carrying
credentials. Skip extraction did not recognize `RFE Key` headers.

## Resolution

Fixed locally on feat/s1-workflow-hardening (base85e8307), within the owner's
approved scope. [Implementation and evidence](../../notes/strat-pr85-scoped-review-fixes-20261022.md).
Complete suite: 1,230 pass/six optional skips; lint/types/shell/diff pass.
Thirty-seven-file evidence archive passes configured-secret scan/hash readback.
User-authorized signed-off 32700ec is pushed and verified as PR #85 head;
staged credential scan passes and component worktree is clean.
Core adversarial-agent containment is an explicitly retained
limitation, not claimed fixed. Org Pulse's owner-approved CA exception remains.
