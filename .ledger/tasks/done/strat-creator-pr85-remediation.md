# PR 85: dispositions and implementation remediation

Authorized 2026-10-16: mark the evidence-rejected review assertions, then fix all
relevant issues. Work on Fullsend fork feat/s1-workflow-hardening, starting
f5691f7; do not rewrite historical benchmark source/evidence. Local/native
controls first; GLM only for any necessary live iteration, one run per scenario.
No Haiku/Opus inference is authorized for this task.

- [x] Reply to schema comment as rejected with actual provider error; mark only
      unsupported assertions in hook/import comments, retaining their valid work.
- [x] Put scorer artifacts inside the repository; move preflight to a capable
      mechanical helper and recover completed/partial reviews without rescoring.
- [x] Keep live Jira work out of short hooks, enforce timeout failure behavior,
      require supported runtime/version and align harness images to it.
- [x] Align terminal failed-receipt behavior, prompts and validation feedback;
      preserve failure handoff/progress for a later verified run.
- [x] Normalize review-only import proofs safely, use full attachment content,
      and recheck prior published strategy live before reuse/publication.
- [x] Compare Jira ADF semantically without losing meaningful attributes.
- [x] Make publication recovery tolerate interrupted cleanup; handle empty/skip
      and dry-run bundles explicitly.
- [x] Preserve CRLF report bytes through capture/composition/verification.
- [x] Bound SubagentStop failure handling; isolate native test capture directories.
- [x] Update all smoke fixtures, duplicated-file parity coverage and unit target;
      add sanitized observed hook fixtures and cite the schema rejection.
- [x] Repair independent benchmark report-format false negatives with retained
      positive/negative report replays, without editing historical results.
- [x] Drop installer-managed config from PR and document manifest registration.
- [x] Run focused checks, make test-unit, make test and required native controls;
      publish signed-off commits and update PR description/dispositions.

DCO on historical commits must be assessed without silently rewriting published
benchmark commit identities or attesting for other authors. No force push is
implicitly authorized. Keep component instructions and current numeric-only
approval policy; preserve historical runs/pins and unrelated Breadboard edits.

[Evidence-based review triage](../../notes/strat-creator-pr85-review-triage.md).

## Completion

Pushed signed-off strat-creator commit f941955b343b985fa8ae22f7c3e321899a3aa588
to feat/s1-workflow-hardening. Twenty follow-up replies document fixes or the
state-owner contract qualification; their twenty threads were resolved. Together
with the separately rebutted schema thread, all 21 original inline threads are
addressed. PR title/body and the installer-ownership conversation were updated.

make test-unit: 1,067 passed, five optional skips. Full make test: 1,067 passed,
six optional skips. Ruff, descriptor validation, both plugin validations and
diff checks pass. Seven actual-Claude native control cases pass with zero
provider calls. The independent checker passes 97 tests (one optional skip)
and replays all 36 retained mixed-run reports successfully.

Raw control data, failed fixture attempts, sources, API dumps, native traces,
logs, test output, replay classifications and checksums are archived under
var/run-data/strat-workflow-hardening/pr85-review-remediation-20261016/. No
paid model smoke or Fullsend/OpenShell deployment was rerun. Historical eval
results and source pins remain unchanged.

[Historical DCO signoffs](../pending/strat-creator-pr85-historical-dco.md) remain
a separate process decision. The new commit is signed off; no force push or
certification for another author has been performed.
