# Port S1 hardening onto the Fullsend fork

Status: done. Local feature branch is committed and clean; no model run or push.

User request, 2026-10-15: work in
`checkouts.tmp/jctanner-fullsend-ai/strat-creator`, create a feature branch,
bring in Wayne Sun's upstream PR #83, then layer our S1 hardening on top.

Preserve the tested historical checkout/branch and benchmark pins. Start from
the new fork's main and retain upstream changes. Resolve integration conflicts,
run the component's required local tests and record the resulting commit chain.
No paid model test, benchmark launch, deployment or public PR is needed here.

Read the destination CLAUDE.md; full `make test` is required before any push.
PR head fetched from fullsend-ai/strat-creator: 6b78355ebc450ff4737fd10ba4857c26086ceac0.
Historical S1 tip: f3508786a1e2200731b25dfeda7e01ef772d32ce.

## Integration

Created `feat/s1-workflow-hardening` from fork/main
`b3961721822d709034c346d642b533fd9573fcb3`, matching upstream/main at fetch.
Merged the exact PR head with merge commit `46cb96e`. Its eight original
Wayne Sun commits remain in the graph. Resolved only the Makefile conflict,
keeping both PR Workflow targets / Fullsend lint coverage and the newer
upstream type-descriptor validation. New upstream release-3.8 settings,
descriptor/schema, validator and jsonschema dependency remain intact.

Replayed the complete local follow-up series after the PR head:

| Original | New branch | Change |
| --- | --- | --- |
| 1bd7f17 | db42db0 | Pinned architecture snapshot support |
| c49b43c | 37674fe | Reviewer delivery |
| 9ec3db8 | b804d7c | Assigned-ticket scope |
| 107e7af | 248c388 | Diagnostic flags / recursive launch guard |
| 4102e7a | 7b3b9ce | Frozen-RFE scope in Fullsend workspaces |
| 30cf850 | deaed7b | Refinement receipts |
| 7cfcada | 4eac463 | Verbatim review composition |
| 4c32d21 | e49b02d | Saved business completion checks |
| b6a228d | 1af9ec2 | Headless completion expectation |
| 80a11ed | 4bc406d | Side-effect recovery |
| 0e7e752 | 1f594d0 | Source/input freshness |
| f350878 | d5817e7 | Anthropic schema compatibility |

All twelve applied without conflicts. Both Workflow copies and the S1 scripts
match the tested historical source. Apart from the upstream additions, the
only extra cleanup removes an inherited blank line at EOF in one test.
The external benchmark's architecture-judgment vocabulary issue is outside
this component and was not silently changed by the port.

## Verification and resulting branch

- Full `make test`: **1,005 passed, seven skipped**, 267.92 seconds, with
  STRAT_WORKFLOW_SMOKE=0 and an isolated local Jira emulator. Log:
  `/tmp/strat-fullsend-s1-port-tests.log`. No live model calls.
- `scripts/validate_types.py`: rfe-strategy descriptor passes.
- All 88 paths changed by our follow-up series match the tested historical
  source. Newer upstream config, type files and dependencies match origin/main.
- Focused review-score tests: five passed after the whitespace cleanup.
- Full branch `git diff --check origin/main..HEAD` passes.
- Both origin/main and PR #83's exact head are ancestors of the branch.
- Historical eval/s1-hardening remains clean at f350878; main is unchanged.

Final branch: `feat/s1-workflow-hardening`, tip
`6a05210215247b287bb0fb61ed02e423c9de8692`. The tip commit only removes an
inherited blank line at EOF. The fork's origin remote is unchanged; a
`fullsend` remote names https://github.com/fullsend-ai/strat-creator.git.
The new branch has a clean working tree and is local. No model job, live service
reset, deployment, public PR or push was performed.
