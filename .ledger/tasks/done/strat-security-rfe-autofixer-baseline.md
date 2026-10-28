# Compare strategy security proposals with rfe-autofixer

## Goal

The user wants a consistent security baseline with rfe-autofixer and does not
want strat-creator to lead a broad new security architecture during migration.
Check current real upstream source before adopting that comparison.

## Completed

- [x] Fetch current GitLab main, referenced harness/provider/profile/policy,
  and current rfe-creator main with credentials kept out of output.
- [x] Distinguish the legacy runner from the manual Fullsend dry-run path.
- [x] Compare filesystem access, Google/Jira credentials, egress and publication.
- [x] Record evidence limits and correct the proposed work's approval status.
- [x] Archive source evidence and verify relevant configuration without models.

## Result

Current pipeline efc285d; pinned harness 83cbc27, current creator main36ef1a0.
Shared writable `/sandbox`, uploaded Google key and broad Vertex profile do
not make us unique. However, reference Fullsend declares read-only Jira and
provider-mediated credentials; outer CI calls host submit in dry-run mode.
Legacy runner passes raw Jira token into sandbox with read-write egress.
Ten Fullsend jobs in the latest 100 jobs are all manual/unstarted; no successful
Fullsend execution or production safety is inferred from configuration.

[Assessment](../../notes/strat-pr85-stoyan-security-review-20261022.md) now states
host-only writer is an unapproved option. Incremental changes and agreement on
a common threat model precede any redesign. No component changes, remote
mutations, new inference, reviewer messages or production cutover.

Evidence: `var/run-data/20261022-rfe-autofixer-security-comparison/`.
