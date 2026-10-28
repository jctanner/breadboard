# Scoped PR #85 fixes implemented

## Scope and status

The owner approved seven bounded fixes following the security review and
rfe-autofixer comparison. Implemented on `feat/s1-workflow-hardening`, based
on `85e8307`. On the user's subsequent commit/push request, published signed-off
commit `32700ec6ea4476d62a6b768aa598883196dcb76e` and verified it as the head of
[PR #85](https://github.com/fullsend-ai/strat-creator/pull/85). Worktree clean.

The Workflow, writable workspace, Jira writes during execution, shared Vertex
profile, numeric-only approval gate and reviewer dissent are retained. The
temporary Org Pulse certificate-verification exception remains in place.
Host-only Jira publication and immutable sandbox redesign remain separate
proposals. No new reviewer message or thread resolution was performed.

## Changes

| Item | Result | Verification |
| --- | --- | --- |
| Accidental live writes | Both direct preparation and pre-script treat unset/empty mode as dry-run. Live mode requires `STRAT_DRY_RUN=0`. All harnesses set `STRAT_MANAGED_RUN=1`; missing input stops helper writes, freshness verification and new Skill/Workflow launches. Local use without the flag still works. | Real pre-script/direct Python preparation against the isolated Jira emulator; fake-write and actual guard adapters with missing input. |
| Results publication | Added a read-only `check` mode to the existing secret redactor. Check result and handoff before artifact export, and generated/reused bundles before sealing/publication. Reject configured credentials, authorization material and unsafe files without rewriting validated bytes or reporting secret contents. | Planted tokens/auth material, binary files, symlinks and secret-bearing filenames; unsafe handoff/result stops before bundle sealing. Existing publication/retry cases pass. |
| SME input | Insert a missing Strategy boundary before existing SME/other sections so Business Need reconstruction does not discard human guidance. | Actual Jira import with and without Business Need heading preserves SME text exactly once and performs no Jira writes. |
| Failed-run cleanup | Export `owned-rfe-ids.txt.owner.json` alongside its key record. | Real outer shell with fake services preserves both files for run failures, release failures and success. |
| Org Pulse credentials | Require an HTTPS base URL without userinfo/query/fragment/whitespace; authenticated uploads follow no redirects. Keep the existing certificate exception. | Local HTTP/HTTPS destinations and 301/302/303/307/308 responses receive no redirected request; malformed URL cases stop before sending. Direct self-signed HTTPS upload still passes. |
| Skip reporting | Accept `RFE Key` as well as `RFE`; map reason/label columns from the header. | Skip-only publication and summary extraction, dry/live metadata, both Reason/Run orders and legacy label layout. |
| Trust documentation | Describe writable code/settings/state and real token authority. Hooks/hashes are quality/recovery evidence, not a malicious-agent containment guarantee; host readback cannot undo prior Jira writes. Document new modes and publication checks. | Full suite integrity checks, lint and whitespace validation. |

The managed-run flag is editable. Its missing-input check is accident protection,
not a resolution of Stoyan's malicious-agent trust-boundary finding. Publication
checks cover known configured secrets and selected authorization patterns, not
arbitrary encoding or all sensitive content. The permanent Org Pulse CA trust
issue and the broader CI business-artifact export follow-up remain separate.

## Validation and evidence

- Before repairs, focused groups reproduced seven context/mode failures,
  eighteen publication/SME/export/parser failures and ten URL/redirect failures.
- Repaired focused groups: 12, 24 and 22 passing tests respectively.
- Complete required suite: `env -u STRAT_WORKFLOW_SMOKE make test`, **1,230
  passed, six optional skips**, 362.72 seconds. Forty additional passing cases
  relative to the prior 1,190-pass baseline. Existing emulator deprecation
  warnings remain.
- Ruff, type descriptor validation, shell syntax and `git diff --check` pass.
- Evidence: `var/run-data/20261022-strat-pr85-scoped-review-fixes/`, 37 files
  including SHA-256 manifest. Includes patch, changed source/new tests, focused
  failures and results, full suite log and verification metadata. Configured
  credential scan and SHA-256 readback pass with zero findings.

All HTTP mutations were against isolated test services. No paid model call,
live Jira mutation, external export replay, deployment or production cutover.

Before commit, all 26 staged files were compared byte-for-byte with the tested
archive. The full staged-blob configured-secret/private-key/pattern scan found
zero credentials; its one exact pre-existing synthetic non-key fixture was
recognized explicitly. The existing evidence archive remains sealed and records
the pre-commit source; Git commit and API read-back establish publication.
