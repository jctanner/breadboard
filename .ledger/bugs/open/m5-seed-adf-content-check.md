# Bug: M5 repeat verification skips structured description content

## Finding

`var/demos/fullsend-entrypoint-poc/jira-seed/prepare.py:134-136` compares the
seed description with `source.DESCRIPTION` only when Jira returns a string.
The deployed v3 API returns an ADF dictionary. Any nonempty description
dictionary therefore passes this part of repeat verification, including
one whose text has changed or whose document content is empty.

## Impact

Low; does not block M6. Independent read-only review on 2026-10-06 confirmed
that live RHAIRFE-1's entire ADF document exactly matches the original fixture
after the emulator's text-to-ADF conversion. The current seed is correct;
the reusable verification does not fully enforce its content-preservation claim.

## Follow-up

Validate the description for both response forms, for example by checking
the v2 plain-text representation against the source or normalizing the ADF
response. Verify that changing an ADF text node causes the check to fail.
Do not reset or alter the live issue to test this condition.

Related: [M5 completion and review](../../tasks/done/fullsend-strategy-seed-rfe.md).
