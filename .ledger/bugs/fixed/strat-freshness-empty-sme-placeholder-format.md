# Freshness guard treats a formatting variant of the empty SME template as input

## Reproduction and evidence

First real scheduled Workflow pipeline 2996590097, batch job 17520981396,
strat-creator b295fe9, Opus 4.6/high, one iteration, 2026-10-27. Job failed
after 30m16s. Native recovery and Jira readback reproduce the cause offline.

The create baseline records RHAISTRAT-3075 human `staff` as empty. Its refined
artifact contains only the standard empty SME placeholder, with the template's
em dash replaced by three ASCII hyphens. `strat_freshness.staff()` ignores only
an exact literal match to STAFF_INPUT_TEMPLATE, so it returns this otherwise
equivalent placeholder as nonempty input.

The skill agent invoked push_strategy.py for RHAISTRAT-3075 at 22:24:50.562Z.
Jira changelog records the AIPCC Agentic Jira Bot description update at
22:24:53.121Z. Comparing the saved target baseline against current Jira changes
only `staff`; summary, priority, status and human-gate fields are equal. The
live staff text equals STAFF_INPUT_TEMPLATE.replace(em_dash, "---") exactly.
There is no human description edit in this issue's four-entry changelog.

Offline controls on the unchanged tested source:

- staff(STAFF_INPUT_TEMPLATE) returns empty.
- staff(the same template with ASCII triple hyphen) returns nonempty.
- Existing normalize_for_compare equates these two placeholder strings.
- Adding a real SME instruction remains different after that normalization.

The run then failed freshness checks throughout progress/result handling:
`freshness: live strategy/staff inputs changed: RHAISTRAT-3075`.
Even `result --failed workflow` could not write agent-result.json because it
re-enters the freshness check. Fullsend correctly rejected the missing result,
did not retry the model, skipped host publication and released all three locks.

## Impact

A benign placeholder rendering difference blocks otherwise eligible real
work. Three local strategy files and two new Jira STRAT clones exist, and the
3075 refined description reached Jira, but no refinements/reviews were accepted
into final progress. This is a failed partial batch, not a completed batch
misreported only by an external benchmark checker.

## Fix boundary

Canonicalize only the recognized empty placeholder before treating it as SME
input, accounting for the publisher/parser's formatting normalization. Keep
meaningful SME additions and changes protected; do not disable freshness or
ignore arbitrary staff text. Add a regression using this exact recovered
placeholder plus controls for genuine SME text. Check failure-result handling
separately so it can describe the stale run without asserting successful work.

No source patch, extra inference or Jira mutation was performed in diagnosis.
Owner subsequently approved schedule rollback: at 22:56:10Z the override was
removed and legacy inheritance verified; ownership and other settings unchanged.
Evidence is in the sibling 20261027-strat-workflow-schedule-rollback archive.
The source defect remains open; repair and paid retesting are separate.

## Repair prepared

Fix branch fix/empty-sme-placeholder-freshness in the owner's fork is published
as **0b69019** with upstream **PR #92**:
https://github.com/fullsend-ai/strat-creator/pull/92.
Known empty-template dash variants and invisible comments are ignored;
genuine SME input is not normalized. Red: five failures/five controls; green
freshness suite: 86; required full suite: 1,444 passed/six optional skips;
full lint/schema and staged credential checks passed. No paid model run.
Failed-result reporting is outside this narrow patch.

## Upstream fix merged

Owner reported PR92 merged. Read-only API verification at 2026-10-28T00:40Z
confirms merge at 00:38:47Z as b75e8384454f606a2e8b187bf09cbd0dd2ce14e9.
Upstream main points to that commit. The implementation and regression-test
Git blobs both match tested 0b69019 exactly. This closes the source defect;
it does not establish a successful live rerun.

Schedule GET still confirms legacy inheritance, owner jtanner1, batch ten,
unchanged six-hour cron; next due 04:00Z / midnight New York. No schedule
change, model run, Jira mutation or source-checkout change made by this merge
verification. Fresh live qualification requires a new host-prepared run,
not replaying the stale failed run's source baseline.

Evidence: var/run-data/20261027-first-real-scheduled-workflow-batch/,
failure-analysis.json, Jira changelog, native recovery and source transcripts.
