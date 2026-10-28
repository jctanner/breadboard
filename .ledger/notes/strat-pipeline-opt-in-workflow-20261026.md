# Stable scripted strategy jobs with an opt-in Workflow

Owner revised the GitLab MR !18 rollout: merging should preserve the existing
jobs, with an environment variable selecting the Workflow later. Existing
consumer branch feat/fullsend-workflow-cutover starts at c514513; fetched
upstream main remains 9bbac1e. Only the consumer changes in this task.

## Behavior

- STRAT_EXECUTOR defaults to legacy, with a Run pipeline dropdown offering
  legacy/fullsend. Empty and unknown values fail model-free validation.
- batch-jql, batch-config, single-rfe and reprocess-strat retain their original
  shell/Python commands, job defaults, cleanup, timeouts and selector behavior
  for supported invocation sources. They now clone CLAUDE_BRANCH=stable-1.x
  from the existing upstream CLAUDE_REPO. stable-1.x and tag 1.0.0 were verified
  at bb4887bc397eee9610ef4170b56a4c7cf8eef295; no source hash pin is configured.
- workflow-* counterparts use the unchanged Fullsend base, three remote
  registrations and upstream main. Their source interfaces must merge first;
  the consumer MR can merge while legacy remains selected.
- Exactly one executor family is selected in each pipeline. Both batch paths
  share strat-batch; singles/reprocessing remain unqueued. One dashboard trigger
  serves either path. Workflow dry/publication flags remain specific to that
  path. Push/MR sources cannot select model jobs or trigger the dashboard.
- No CI/project/schedule variable was changed. Existing pipelines keep their
  selected jobs; changing STRAT_EXECUTOR controls future pipeline selection.
  Legacy credential/runtime setup is preserved; Workflow retains direct Vertex,
  provided secrets, current architecture context and no model-relay dependency.

## Verification

Full consumer suite: **134 passed in 14.62s**. Cases cover both execution paths,
supported sources/selectors, conflicting selectors never selecting both families,
invalid switch values, queues, Workflow bootstrap and a real local Git clone
selecting stable-1.x even when main has different content.

Compared restored jobs directly with fetched upstream YAML: script bodies,
variables, timeouts, extends, stages, resource groups and cleanup match. The
remaining original selector rules match after the new executor/source guards.
The setup clone is the only setup difference. Added python-tests dependencies
for validation. All **50 embedded shell steps** pass bash -n.

GitLab upstream CI lint: **valid, no errors or warnings**. Read-only API checks
confirm no STRAT_EXECUTOR override at project scope or on active schedule
4222905 (main, 0 */6 * * *, America/New_York). Therefore the current deployed
configuration does not override the new legacy default. Settings untouched.

The actual consumer registrations still materialize against a synthetic local
snapshot of the tested strat-creator feature branch into single/batch/resume
harnesses with resolved commit and hashes. No remote model/provider calls or
live Jira actions. This does not claim a real GitLab/Fullsend smoke on upstream
main before PR #85 merges.

The initial default-sandbox test invocation could not lock the uv cache outside
the workspace; the authorized offline invocation passed. This was an environment
permission failure before tests, not a test failure.

Signed-off commit e8f3959f03d5df385a9ed2337c0ecd4d54ed4987 contains four files;
source and staged patch passed exact local-credential/pattern scans with zero
findings. Component worktree is clean. Twenty-file evidence archive sealed at
var/run-data/20261026-strat-pipeline-opt-in/.
Manifest and byte readback verified. No comments, project variables, schedules,
manual pipelines or merges are changed.

## Publication

Pushed e8f3959 normally to the existing feature branch and verified the remote
commit through Git and GitLab. MR !18 now reads "Add opt-in Workflow jobs with
stable scripted fallback"; its description explains the switch, source refs,
tests and source-merge prerequisite, preserving the author's signoff.

The strict initial metadata receipt check failed because GitLab removed the
description's trailing newline. A read-only follow-up confirmed the complete
text after trimming; no second MR mutation or source push was needed. Final
publication receipt/hash readback sealed separately at
var/run-data/20261026-strat-pipeline-opt-in-publication/.

The new-head merge-request pipeline 2992428660 passed on e8f3959. It runs
model-free repository checks, not the strategy jobs. MR remains open and needs
approval; it was not merged. No provider calls, live Jira mutations or deployed
cutover occurred. Project and active schedule executor settings remain unset,
so the YAML legacy default applies when this change merges.

## Merge confirmed on 2026-10-27

Owner merged !18 at 19:10:15Z. Upstream main is merge commit
b00078ee43ab7c4a0b6b0d9903eb5c7b60503618, with squash
c5e2b873500a889bd4f78ad13b1e6b7ac0bc01fd from source head 200b04b.
Read-only verification at 19:19Z confirms current main's CI bytes match the
tested branch. STRAT_EXECUTOR defaults to legacy; source is stable-1.x. No
project or active schedule executor override exists. The merge therefore keeps
the scripted path selected; no setting or schedule was changed by the agent.

Source PR #85 remains open on 364e1ca. Merge that source first, then explicitly
launch a manual single-ticket Workflow smoke with STRAT_EXECUTOR=fullsend.
Scheduled enablement remains a separate owner action. No job was launched.
Receipt: /tmp/strat-pipeline-merge-20261027T191933Z.json.

## Source PR merged; ready for an authorized smoke

Owner subsequently merged strat-creator #85 at 19:34:22Z on Oct 27. GitHub
confirms merged/closed from tested head 364e1ca. Upstream main is b295fe9;
ten required CI wrappers, harnesses, preparation/release, reprocess and Workflow
files match the tested revision's Git blobs. The consumer can now obtain those
interfaces from the configured upstream main branch.

GitLab !18 remains merged; its default and current observed project/schedule
selection remain legacy/stable-1.x. A manual one-ticket pipeline with
STRAT_EXECUTOR=fullsend is the next validation step when authorized. It does
not require changing the scheduled executor. No job or setting change in this
read-only merge check. Receipts:
/tmp/strat-pipeline-merge-20261027T194100Z.json and
/tmp/strat-main-interfaces-20261027T195836Z.json.
