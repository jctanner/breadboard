# Late human gates do not stop managed STRAT writes

PR #85 comment 4381545482, reproduced on b8d67c3 using only the local Jira
emulator. Add human-sign-off or needs-attention after preparation, then call
the real comment, field or attachment helper. Both before and after target
binding, the write proceeds. The human snapshot omits labels and the ownership
guard checks only the source RFE.

Expected: stop before mutation or intent, preserve progress and artifacts.
The pipeline's exact current-run needs-attention effect must remain recoverable;
human-sign-off must always stop writes. These are recovery guards, not Jira CAS.

Evidence: /tmp/strat-pr85-three-concerns-red.log (initial reproduction).
Task: [approved review fixes](../../tasks/done/strat-pr85-review-b8d67c3.md).

Fixed in a0158d9: snapshot gates, reject initial binding and guard actual owned
writes. Allow only exact current-run needs-attention recovery intent; never
exempt sign-off. Regression and full offline suites pass (1,394 passed, six skips).
Evidence: var/run-data/20261026-strat-pr85-human-gates-publication-ownership/.
