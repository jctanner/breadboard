# Restore regression coverage for the retained legacy cleanup

Owner supplied Federico Mosca's MR !18 comment on the deletion of
tests/test_cleanup_shell.py. Checkout checkouts.tmp/jtanner1/strat-pipeline,
feat/fullsend-workflow-cutover, clean at e8f3959. No local AGENTS.md/CLAUDE.md.

The earlier full-cutover commit removed the test file with the legacy CI path.
When e8f3959 restored the four legacy jobs, the tests were not restored. Their
after_script is still byte-for-byte the upstream implementation and legacy is
the default executor. The reviewer is correct; this is a coverage omission.

Restore the original upstream shell-level regressions unchanged, using the
actual YAML cleanup body under Bash errexit/pipefail. No runtime/CI behavior,
credentials, executor default or source-ref change. No extra hardening scope.

- [x] Restore original test file and verify its bytes match the original upstream baseline.
- [x] Run focused cleanup tests and the consumer suite; diff checks pass.
- [x] Scan credentials, retain evidence, commit and push to MR !18.

No public reply/thread resolution, model job, live Jira write, project setting,
manual pipeline or merge is authorized. Normal model-free MR CI may run on push.

Original 14 tests pass (0.41s); full consumer 148 pass (14.96s). Runtime/CI
untouched. Details: [evidence](../../notes/strat-pipeline-legacy-cleanup-tests-20261027.md).

Signed-off 200b04b1a6cf413280f60647f69f4adffdf94232 pushed/read back on MR !18.
One restored test file; matches baseline and no longer appears changed/deleted
in the MR diff. Credential scans zero, ten-file archive plus separate receipt
hash/readback verified. Component clean. MR description test count updated;
no public reply/thread resolution. New-head MR pipeline 2995309329 pending at
publication. No model job, settings change, live Jira write or merge.
