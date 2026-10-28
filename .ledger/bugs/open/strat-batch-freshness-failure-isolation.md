# One changed RFE blocks the entire Workflow batch

## Evidence

Real GitLab pipeline 2996960969 / job 17523658071, upstream strat-creator
b75e838, Opus 4.6, one iteration. Six RFEs acquired. All six strategies were
refined and pushed by 2026-10-28T01:15:58Z. RHAIRFE-3785's description changed
at 01:20:31Z; Jira attributes changelog 94274070 to Ana Biazetti's account.
Account attribution does not establish manual human activity.

scripts/strat_freshness.py::verify checks all baseline RFEs. At 01:21:04Z,
review composition for RHAISTRAT-2959 was rejected because RHAIRFE-3785 changed,
although 2959 belongs to unchanged RHAIRFE-3078. All six review completions
were blocked; accepted review progress remained empty. Result finalization
also failed the freshness check. The completion hook then rejected three
StructuredOutput calls because no completion checkpoint existed. This was a
cascade from input drift, not evidence of a separate malformed-schema defect.
The job ended at 01:37:41Z, about 16 minutes after the first rejection.

## Impact

A valid stale-input refusal for one ticket prevents five unchanged tickets
from completing. Partial Jira work is retained, but the batch has no normal
failed-result receipt, host publication is skipped, and remaining agent work
continues after a definitive rejection. All six locks were released correctly.

## Follow-up

Owner policy and implementation decision pending. Consider isolating changed
tickets from unchanged work and/or stopping remaining work promptly, with an
explicit failure receipt that cannot authorize stale publication. Preserve
freshness protection: do not silently refresh a baseline, ignore real edits,
or approve the changed ticket using its old inputs. No source patch or paid
rerun authorized as part of this diagnosis.

Evidence: var/run-data/20261028-real-gitlab-workflow-batch-retest/verification.json
and the native ZIP, Workflow journal, transcripts, Jira snapshots/changelog.

Related: [live batch qualification](../../tasks/done/strat-placeholder-repair-live-batch-20261028.md).

## Authorized repair

Owner subsequently requested a new feature branch and PR. Implementation and
verification are tracked in [batch freshness isolation](../../tasks/done/strat-batch-freshness-isolation.md),
on feat/isolate-stale-batch-tickets from main b75e838. Per-ticket deferral,
independent host verification, filtered publication, diagnostic failure receipts
and successful-partial recovery snapshots are implemented. Full local suite:
1,463 passed/six skipped; lint/type/diff and credential checks pass. Signed-off
6ad16b5 is proposed in [PR #93](https://github.com/fullsend-ai/strat-creator/pull/93),
which is open and mergeable. Repair remains pending merge and live qualification.
No paid rerun or schedule switch was performed.
