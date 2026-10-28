# Fix live Jira attachment verification and publication completion

## Goal and authorization

The user requested adding both diagnosed live-canary fixes to strat-creator
PR #85: permit the attachment verification endpoint and prevent dry-run
fallback/incomplete publication from being recorded as a completed live review.
Work on existing feat/s1-workflow-hardening, starting at 630fcca.

## Acceptance criteria

- [x] Reproduce the committed-upload/blocked-read and dry-run fallback without models.
- [x] Allow api.media.atlassian.com:443 for the existing Python Jira client.
- [x] Do not forward Jira credentials to attachment redirect hosts.
- [x] Prepared live runs reject dry-run override or missing write credentials.
- [x] Review recording verifies required live publication and preserves recovery.
- [x] Standalone/prepared dry runs and fast local completion hooks keep working.
- [x] Full source tests, lint, regression controls and native policy checks pass.
- [x] Commit/push to PR #85 and record remaining real-run qualification.

## Constraints

No additional paid run, live Jira repair, schedule change or consumer MR merge.
Preserve uncertain-write reconciliation, exact content/dissent and numeric-only
approval. Keep the host's final Jira-readback gate. Do not add network work to
the completion/refinement hooks that were optimized to avoid timeouts.

## Completed: 2026-10-21

Published signed-off 02dd13b4b0bf59b3621c060b60a1732440f6f284 to the existing
feature branch and verified PR #85's remote head. Checkout is clean. The
shared policy allows the specific media endpoint only for Python. The
attachment client limits credentials to the exact Jira origin and rejects
unsafe redirects. Existing uncertain-write reconciliation remains intact.

Prepared live publication rejects --dry-run and missing credentials. Before
recording review completion, read-only Jira verification requires the exact
comment, attachment bytes and expected numeric verdict label, without the
opposite label. A partial publication leaves progress incomplete. Recovery
reuses the already committed upload/comment; it does not duplicate them.
Approval remains numeric-only with dissent retained. Fast hooks are unchanged.

## Evidence

- Focused tests: 112 passed, including eight publication and eight redirect/
  policy cases. Local HTTP servers and Jira emulator; no model calls.
- Full make test: 1,158 passed, six optional skips, 322.65s. First full run
  exposed one old fixture recording a live review without publication; it now
  publishes to the emulator before recording, and passes.
- make lint, type descriptor validation, diff checks and staged secret scan
  pass. Twelve changed source files, no configured secret matches.
- The archived live input rejects the exact --dry-run fallback before Jira
  contact. The repaired downloader reads the existing cloud attachment
  without writes and matches archived SHA256
  8980ce1906e611bc109cc032aeeeadce719a6e99f84d13bb1e8b53ff500f2aee.
- Actual branch-based CI bootstrap and native Fullsend 0.47.1 dependency locks
  pass against published 02dd13b for strat-single and strat-batch. Runtime
  source receipt: /tmp/strat-minimal-consumer-9inb21xf/result.json.
- Local test logs: /tmp/strat-live-publication-focused.log and
  /tmp/strat-live-media-full-tests-final.log; cloud read receipt:
  /tmp/strat-jira-media-readback-result.json.

## Remaining qualification

The original canary remains failed. Host-side cloud readback and native
dependency locks do not exercise the new endpoint inside a live OpenShell
sandbox. No additional paid run, live Jira repair, consumer MR !16 merge or
production schedule change was performed. A subsequent read-only check after
the user's merge notification verifies MR !16 landed as fe9ca62 with passing
main CI. New manual Fullsend jobs now follow this source branch instead of
the earlier main pin. The legacy schedule still uses its original executor.

[Egress resolution](../../bugs/fixed/strat-fullsend-jira-attachment-media-egress.md).
[Publication resolution](../../bugs/fixed/strat-live-review-dry-run-fallback-completes.md).
