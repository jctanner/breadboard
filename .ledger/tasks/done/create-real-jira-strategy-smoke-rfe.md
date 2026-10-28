# Create the real Jira strategy smoke-test RFE

## Goal

Use the user's `.env.jira` credentials to create the agreed synthetic workbench
session-timing RFE in RHAIRFE. Leave qualifying release labels and Target
Version unset so the ticket is not eligible for scheduled strategy discovery.

## Acceptance

- [x] Inspect create permissions, issue type and required fields.
- [x] Prepare the agreed content and check for an existing matching smoke RFE.
- [x] Create once, preserving any uncertain request for reconciliation.
- [x] Verify actual ticket content and lack of pipeline eligibility.
- [x] Record the ticket key/link without exposing credentials or starting jobs.

No approval/quality labels, strategy generation, scheduler change or paid test
is authorized by this ticket-creation request.

## Result

Created [RHAIRFE-3739](https://redhat.atlassian.net/browse/RHAIRFE-3739)
on 2026-10-20 using `.env.jira` in memory. Feature Request, New, Minor;
summary and all six acceptance criteria verified by immediate API read-back.
No existing ticket matched the unique smoke label before creation.

Labels are `strat-pipeline-smoke` and `strat-workflow-smoke-20261020`.
Target Version, fix/affect versions, qualifying release/quality labels and
issue links are unset. This is outside the current configured strategy
discovery gates. The smoke labels themselves do not exclude a ticket.

One create request, with intent saved before writing; key/verification receipt
saved to `/tmp/jira-strat-smoke-ticket-receipt.json`. No credentials were
printed, and no model job or scheduler change was made.
