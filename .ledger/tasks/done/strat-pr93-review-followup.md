# PR93 review reproduction and repair

Owner authorized reproducing and fixing the PR93 findings on existing
feat/isolate-stale-batch-tickets, starting from clean signed-off 6ad16b5.
Fullsend and Qodo comments retained at /tmp/20261028-strat-pr93-review-check/.
No paid test, schedule change, live Jira write or review-agent dispatch.

## Cases

- [x] RFE edit between strategy push and refined-label publication.
- [x] Saved create skip becomes a deferred ticket.
- [x] Partial create's only remaining pending RFEs become deferred.
- [x] Keyless create handoff cannot reconcile verified deferred work.
- [x] Additional input change alters a saved deferral reason.
- [x] Reverted changes: retain ticket deferral only with independent external
  evidence, without readmitting the ticket or trusting forged progress.
- [x] Fully deferred HTML report and CLI error consistency.
- [x] Focused red/green tests, full make test, lint/type/diff/credential checks.
- [x] Signed-off commit pushed to PR93, readback/evidence archived.

Policy/process findings (protected paths/approval and fix-vs-feat naming) are
separate from runtime defects. Do not create a public issue, approve a review,
resolve threads or merge merely to satisfy a bot. Preserve shared-input and
unverifiable-input failures and the independent host publication boundary.

## Reproduction and implementation

Red: seven Python cases failed on the original 6ad16b5 (push-label race,
skip/deferral overlap, incomplete create timestamp, unstable reason, reverted
edit, report wording and missing-file error), plus two offline JavaScript
cases demonstrating missing-create handoff handling. Cases use local Jira only.

Repairs catch a label-write StaleTicket only after live independent deferral
verification. Other write, owner, source and unreadable errors remain fatal.
Effective create completion reconciles actual non-deferred coverage and saved
pending inventory; it cannot promote a missing timestamp alone. Original skip
and partial records remain intact; result/publication exclude deferred skip
rows. Missing create receipts get a read-only reconciliation rather than a
repeated Skill; fresh pending RFEs remain failed. CLI errors are explicit.

The first deferral reason stays informational. Reverts use new strat_history.py:
the host pins RFE and existing linked STRAT history cursors before agent work.
Host verification checks post-cursor protected changes against Jira itself.
Ordinary lock labels, older edits, foreign STRAT links and agent-provided cursors
are not proof. Structured SME and sign-off history can prove changes for pinned
STRATs. New STRATs without a pinned history cursor, unstructured historical SME
text and ambiguous numeric attention-label history cannot authorize reverted
deferrals without other independent evidence. Missing/unverifiable evidence
still fails closed; no host wall-clock inference or baseline rewrite.

Forty added regression cases (17 review/integration/control-flow, 23 history
checks). Focused repairs passed 124, then 121 cases with additional history
checks; dedicated set passed 36 plus the last four history cases (23 pure
history tests pass). Final full **1,503 passed/six skipped**, 733.53 seconds;
make lint/type and diff validation passed. Thirteen changed files committed;
no unrelated component change or live mutation.

PR preflight still open on expected 6ad16b5/main. Updater/controller:
/tmp/update-strat-pr93-followup.py; staging dirname
20261028-strat-pr93-review-followup. No public thread reply/resolution, issue,
human approval or /fs-fix dispatch has been made.

## Delivery

Signed-off **13a4f71b26afcd1d745183e7247ee9d8c5843fb3** pushed to the same branch.
[PR93](https://github.com/fullsend-ai/strat-creator/pull/93) description now reflects
the full behavior and limitations. Readback verifies exact head/main, 28 complete
PR files matching local Git, mergeable and clean component working tree. GitHub
Python 3.11/3.12, lint, Unicode and DCO checks passed; automated review remains
in progress. PR not merged; no paid Workflow smoke or schedule change.

Archive: var/run-data/20261028-strat-pr93-review-followup/, **27 files plus
manifest**, copied hashes verified. Includes complete original review pages
with IDs/dates, local triage, red/focused/full logs, follow-up and aggregate
patches, validation and PR receipts. Configured-secret/private-key scans cover
all 28 committed PR files and retained evidence: zero findings. Protected-path
approval remains a maintainer process item; no public issue/approval/thread
mutation was made. Existing fix prefix retained as an advisory naming choice.
