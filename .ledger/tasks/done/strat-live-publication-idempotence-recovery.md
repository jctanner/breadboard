# Recover the live smoke review without another model run

## Authorization and scope

The user accepted the proposed publication-only idempotence test on
2026-10-21. Recover existing RHAISTRAT-3027 from the archived failed canary,
verify the already published summary and attachment, reconcile the pending
upload and apply the missing numeric verdict label with versioned helpers.
Repeat publication to check that no comments/attachments or content change.
No refinement, scoring, reviewer or other model calls.

## Acceptance criteria

- [x] Validate archived review provenance, reports, score and original write intent.
- [x] Confirm live RFE/strategy content is unchanged and there is no competing owner/job.
- [x] Preserve original failed-run evidence and distinguish standalone repair from Workflow replay.
- [x] Reconcile publication through current versioned helpers and read back all required effects.
- [x] Repeat the same publication with zero additional Jira mutations.
- [x] Archive pre/post snapshots, mutation audit and verification under var/run-data.
- [x] Record the remaining real OpenShell/full-pipeline qualification.

Do not close, clone, refine or rewrite tickets. Do not change the old run's
freshness baseline, result or completion receipt to make it appear successful.
Keep the RFE outside production release scope and leave schedules unchanged.

## Completed: 2026-10-21

Recovered publication at 19:20:19Z using the current versioned publisher from
02dd13b. Verified every archived recovery file against its manifest, review
provenance/scorer/four role reports and the exact 31,813-byte attachment.
The numeric decision is 8/8 approve; testability's revise recommendation is
preserved. Live strategy and SME/identity data match the original verified
push. Live RFE fields/comments match the old input after accounting only for
the original cleanup's two removed fixture labels. Neither was restored.

The existing summary comment and attachment are uniquely visible. Copied the
original effects journal for reconciliation, retaining the original run ID and
pending upload intent. Used a separate standalone artifact export; original
prepared input, progress, freshness baseline and failed receipts remain intact.
This is explicit manual publication repair, not Workflow replay or proof that
the old job passed.

First publication performs exactly one Jira PUT, adding
strat-creator-rubric-pass. The pending attachment record becomes verified
through exact-byte media readback with no upload. The second publication and
verification perform zero mutations, with exactly identical Jira snapshots.
One summary comment and one review attachment remain. RFE, strategy content,
status, links, review bytes, dissent and production schedule are unchanged.
An HTTP audit guard blocks any new comment/upload or unexpected mutation
before transport, and blocks every second-pass write. It records no credentials
or signed query strings. Zero model calls and zero token spend.

## Archive and validation

var/run-data/20261021-real-jira-publication-idempotence-recovery/ contains
result.json, live-readback.json, original evidence, standalone artifacts,
before/after Jira snapshots, effects-before/after records, write intent,
driver.py and http-audit.jsonl. manifest.sha256.json inventories 89 files;
configured Jira/GitHub/GitLab credential scan has zero findings. Audit confirms
the one expected PUT and media-host GETs. The first read-only setup attempt
needed canonical archive paths because var/run-data is a symlink; its error
is preserved separately. No Jira write occurred in that setup attempt.

Driver compilation and root diff checks pass; no component source changed.
No inference, GitLab job, data-repo push or dashboard trigger. The new OpenShell
policy was not exercised by this host-side operation. A full real CI/sandbox
smoke remains separate. The strategy now has its final label, so ordinary
discovery will skip it; use a separate fixture for a future fresh smoke rather
than clearing the verdict or closing/recloning this one.
