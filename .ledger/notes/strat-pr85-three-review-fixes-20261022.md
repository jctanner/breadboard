# Three review fixes after 73c454b

## Scope

The owner requested repairs for comments 4354198477, 4354198483 and 4354198490
on strat-creator PR #85. Work started from clean
`73c454bbc5c3a7f6907b3f2b3878c7a04d3477d6` on `feat/s1-workflow-hardening`.
Org Pulse certificate/hostname verification remains the accepted temporary
exception. Numeric scores remain the sole approval gate. No model calls, live
Jira mutations, exports, review replies, deployments or cutover are involved.

## Repairs and evidence

| Finding | Repair | Regression evidence |
| --- | --- | --- |
| Final Jira review readback | Trusted host validator calls the existing read-only `publish_review.verify_publication` for every live strategy, retaining clone membership and provenance label checks. It verifies the exact summary, newest exact-filename review attachment and consistent numeric verdict labels. | Ten cases: approve and revise, each with missing/altered comment, missing/superseded attachment or added opposite verdict label after record-review. All ten falsely passed host validation before repair. The repaired verifier detects each change without a mutation and preserves progress. |
| Frontmatter title delimiters | Root and bundled scope hooks use `artifact_utils.read_frontmatter`, which recognizes delimiter lines rather than arbitrary `---` substrings. The bundled CLI locates vendored helpers only in its hook entrypoint; trusted host imports do not change their module search path. | Six cases: quoted/unquoted titles in artifact/local workspaces, plus actual root and bundled hook subprocesses with vendored helpers. Each fails before repair and passes afterward. Existing ticket identity/path restrictions remain. |
| Recovery credential pathnames | CI scrubber checks all relative pathnames, including directories and empty directories, before content redaction. Credential-bearing names fail export with a generic error. Binary errors omit filenames; the CLI suppresses tracebacks for these rejections. | Seven new failing cases cover file/directory/empty-directory names, binary errors, and actual failure capture plus the outer CI wrapper. Unsafe generated CI output is removed, private recovery is preserved, locks are released, and an existing run failure is not replaced by the scrub failure. A previously successful run becomes failed if its export is unsafe. |

Before repair: 23 regression failures, four existing cleanup controls passing.
After repair: all 27 selected checks pass in 39.38 seconds. The HTTP observer
initially targeted urllib's default opener rather than the Jira helper's custom
opener; corrected the test to observe both paths before accepting this result.
Comment edit/delete is modeled at readback because the isolated Jira emulator
lacks those endpoints; publication, record-review, attachment changes and
label changes use the real emulator. No live service is involved.

## Validation and source state

Full required `env -u STRAT_WORKFLOW_SMOKE make test`: **1,261 passed,
six optional skips**, 406.12 seconds. Ruff, type descriptors and whitespace
checks pass. Eight component files changed, including the mandatory bundled
scope copy and three test modules. They were subsequently committed and pushed
as recorded below.

Source, complete patch, before/after regression XML/logs and full suite log are
retained under `var/run-data/20261022-strat-pr85-three-review-fixes/`, with a
credential scan and SHA256 manifest. The pre-existing synthetic non-key fixture
in `tests/test_fullsend_ci.py` is explicitly recognized by the archive scanner;
no real credentials are permitted. Earlier sealed archives remain unchanged.

## Publication

At the owner's explicit request, published signed-off commit
`0707b5baf546b2e0712cb4f9861a8f7705b4815f`
(Fix final review readback and recovery artifact checks) to
`jctanner-fullsend-ai/strat-creator:feat/s1-workflow-hardening`.
All eight staged files exactly match the tested archive; the complete staged
credential scan has zero findings. GitHub API readback confirms this exact
PR #85 head, and the component worktree is clean. The original eighteen-file
precommit archive remains sealed with its original base/state metadata.
No remote review replies, paid smoke, live mutations, deployment or cutover.
CI/review results for the new head have not been assessed here.

## Limits

Final Jira readback checks current state, without undoing prior writes or
preventing changes after verification. It does not contain a malicious agent
holding a raw Jira token. Credential detection covers known values and existing
authorization patterns; arbitrary encodings and unknown sensitive content are
not proven absent. Rejected CI output is removed from the generated export,
while private host recovery intentionally remains available for reconciliation.

Other compatibility/documentation review comments are tracked separately in
[the assessment queue](../tasks/pending/strat-pr85-review-73c454b.md).
