# Unset manual inputs select the legacy dashboard trigger

GitLab.com's real CI lint dry-run on the current strategy pipeline plus the
new test job compiled build-dashboard on an ordinary push with no selected
strategy job. `$CONFIG_FILE != ""` also matches an unset/null variable; the
dashboard job has no job-local empty defaults for its three manual inputs.

The new local feature branch uses truthy `$CONFIG_FILE`, `$RFE_KEY` and
`$STRAT_KEY` checks consistently. Native GitLab lint now compiles only
python-tests on the default push. Actual nonempty manual inputs and schedule
conditions remain available. An explicit Fullsend selector excludes the old
jobs and their dashboard trigger. Its new trigger also requires real publication.

The patch is published as signed-off 7402726 on jtanner1/strat-pipeline branch
feat/fullsend-strategy-workflow in
[upstream draft MR !15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15).
Keep this bug open until the upstream fix merges. Native CI lint on the
published branch selects only python-tests for a default push. No dashboard
build was started during these checks.
