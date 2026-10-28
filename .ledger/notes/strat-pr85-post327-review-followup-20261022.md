# Automated review after 32700ec

## Inventory and scope

Fetched the complete current PR #85 discussion: 137 entries, consisting of
17 regular comments, 34 reviews and 86 inline comments. Compared against the
previous 131-entry export, also accounting for updated rollup comments.
Current automated review is5618750397 on `32700ec`, submitted October 22 at
18:09:30Z. Three new inline comments are assessed below. The owner scope
comment6345317940 remains the project direction; this task does not introduce
host-only Jira publication, immutable sandbox changes or a paid smoke.

## Dispositions

| Finding | Decision and evidence |
| --- | --- |
| [4351850963: attachment history](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4351850963) | Accepted and reproduced. Matching any historical A permits false success after A→B→A while readers select B. Both strategy and review paths fail a real emulator publication-to-pull test. Repaired shared helper to compare only the newest exact-filename attachment using the readers' existing sort key. |
| [4351850956: Org Pulse certificate verification](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4351850956) | Valid risk, retained owner-approved temporary exception. HTTPS and redirect restrictions address different paths; they do not authenticate the server. Do not silently restore certificate verification or skip export against the owner's explicit decision. Permanent corporate CA trust remains a separate open follow-up. |
| [4351850971: missing authorization link](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4351850971), plus protected-path rollup | Process metadata, not a product defect. The owner has already publicly stated migration scope and explicitly authorized these repairs. No issue, approval or maintainer consent is fabricated. No governance/thread-resolution action or extra external comment is taken during this code repair. |
| HTTPS/redirect compatibility rollup | Deliberate bounded change, documented and tested in32700ec. Preserve the final HTTPS service URL requirement and no-redirect behavior. |
| Earlier skip-header, SME and dry-run findings | Latest Fullsend rollup explicitly marks them resolved by32700ec. Qodo rollup currently reports zero bugs/rule violations/cross-repo conflicts. |

## Attachment repair

`scripts/jira_utils.py:find_matching_attachments()` selects the newest attachment
with the requested filename and downloads only that candidate. An older match
cannot satisfy an upload or live review publication verification. Historical
copies remain append-only; a deliberate revision in a fresh run appends a new A
after B. Repeating the final A reuses the newest matching copy.

The generic side-effect journal is unchanged. If a pending or verified write
from this same run is no longer current, retry stops for reconciliation rather
than blindly posting again. The new test covers both statuses, alongside the
existing real lost-response and process-death controls. Equal creation times,
numeric ID tie-breaking, reversed API order and unrelated filenames are covered.

Eight new regressions fail on `32700ec`. Repaired focused run:39 passing tests,
including existing side-effect recovery and live review publication cases.
Complete required `env -u STRAT_WORKFLOW_SMOKE make test`: **1,238 passed,
six optional skips**,365.65 seconds. Ruff, type descriptors and whitespace
checks pass. Evidence, including the full discussion, current automated findings,
before/after regression XML, full suite log, source patch and files, is at
`var/run-data/20261022-strat-pr85-post327-review-followup/`.

No model call, real Jira write, external export, review reply or thread resolution
was performed.

## Publication

Signed-off commit `73c454bbc5c3a7f6907b3f2b3878c7a04d3477d6`
(Reconcile only the newest named Jira attachment) was pushed to the existing
fork feature branch. All three staged files match the tested archive, with
zero credential findings. GitHub API readback confirms the exact PR #85 head;
the component worktree is clean. Remote Python 3.11/3.12 tests, lint, Unicode
and DCO all pass. The original thirteen-file precommit archive remains sealed.

New automated review 5621646395 on `73c454b` requests changes, including three
additional functional/security concerns. They are recorded in the
[next review task](../tasks/pending/strat-pr85-review-73c454b.md); they were
not part of this attachment repair. No paid smoke has been launched.
Publication receipt and the new complete discussion export are archived at
`var/run-data/20261022-strat-pr85-attachment-fix-publication/`.
