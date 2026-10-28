# Reviewer can substitute dry-run publication in a prepared live run

## Reproduction and evidence

Live canary job 17351822419 on 2026-10-21 has `dry_run=false` in its trusted
input and result. At 14:38:16Z its reviewer invokes publish_review.py normally.
Comment and attachment publication commit, but attachment reconciliation
encounters the media-host egress denial. The attachment intent remains pending.

The reviewer reasons that a dry-run path can save locally despite explicitly
noting the task is not a dry run. At 14:38:34Z it invokes:

```text
python3 .claude/skills/strategy-review/scripts/publish_review.py RHAISTRAT-3027 --dry-run
```

That returns a verdict without applying the Jira label. At 14:38:46Z,
record-review accepts local composition and records completion. The main
agent's completion-status/result commands report success, while the result
still claims a live, completed run with no errors. The final trusted host
validator correctly rejects the missing strat-creator-rubric-pass label.
Fullsend skips the post-script, data-repository publication and dashboard.

## Fix direction

A prepared live run must reject an explicit dry-run override, and review
completion must not be recorded while required live publication is incomplete
or uncertain. Preserve the existing composed reports/intent for reconciliation;
do not regenerate reviews, fabricate approval or weaken the numeric gate.
Standalone human dry runs and genuinely prepared dry runs remain supported.
Add model-free coverage for this exact partial publication/fallback case.

The final host checker worked, preventing a false overall success. The
earlier receipt's local completion claim needed tightening. No implementation
change or repeat inference was made as part of the initial test diagnosis.

Evidence: reviewer transcript strat-single-agent-a12ee4bea3a4f9093.jsonl,
pending attachment effect record and native result in the live-canary archive.
[Related egress bug](strat-fullsend-jira-attachment-media-egress.md).
[Execution task](../../tasks/done/real-gitlab-strategy-single-live-canary.md).

## Resolution: 2026-10-21

Signed-off commit 02dd13b in strat-creator PR #85 rejects explicit --dry-run
in prepared live runs, and fails live publication early for missing Jira
credentials or a non-Jira strategy key. record-review independently reads
back the exact summary comment, attachment bytes and expected numeric
verdict label before marking a live review complete. Conflicting verdict
labels fail. Verification performs no mutations; failure leaves progress
unchanged. Standalone and intentional prepared dry runs remain supported.

Model-free tests reproduce committed upload followed by blocked readback,
reject the dry-run fallback and incomplete completion, then recover with
one comment and one attachment. The archived canary input also rejects the
exact --dry-run fallback before contacting Jira. Numeric-only approval and
specialist dissent are preserved. Completion/refinement hooks remain local
and unchanged; Jira read-back is in the review-recording command.

Full suite: 1,158 passed, six optional skips; lint/type checks pass. The host's
final Jira validation remains in place. The old canary remains a failed
qualification; no new paid run or manual publication repair was performed.
