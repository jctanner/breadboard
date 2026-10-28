# Prepare the real GitLab Fullsend pipeline branch

## Goal

Create the user's fork checkout and feature branch, then implement the approved
manual Fullsend integration using direct Vertex and live architecture context.

## Acceptance

- [x] Fork cloned with safe authentication; local instructions read.
- [x] Feature branch starts from current upstream main.
- [x] Manual single/batch jobs follow the reference execution setup.
- [x] Existing jobs/schedule preserved and conflicting jobs excluded.
- [x] Vertex credentials remain secret; architecture source is fetched live.
- [x] Validation, publication, cleanup and diagnostic collection are wired.
- [x] Model-free tests and diff checks pass; limitations documented.

## Status

Completed locally on feat/fullsend-strategy-workflow from upstream 3995ac1.
The 87-test suite, native Fullsend dependency resolution, live architecture
fetch and expanded GitLab CI compiler checks pass. The component guide covers
secrets, manual inputs, qualification limits and remaining legacy-only modes.
[Implementation and evidence](../../plans/strat-pipeline-gitlab-fullsend.md).
Publication authorized on 2026-10-20: committed and pushed signed-off 7402726
to the fork's feat/fullsend-strategy-workflow, then opened
[upstream draft MR !15](https://gitlab.com/redhat/rhel-ai/agentic-ci/strat-pipeline/-/merge_requests/15)
targeting main. All 87 pre-publication tests and native GitLab CI lint pass.
The MR automatically starts a model-free test pipeline. No model job or Jira
write was launched. Runner/secrets and a separately authorized smoke remain
next steps; the component checkout is clean.
