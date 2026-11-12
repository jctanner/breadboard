# Fullsend upstream PR status (2026-11-06)

Handoff note for any agent resuming work here: where the CC-1 upstreaming
campaign stands, what has already been done, and what is left. Counterpart
infrastructure lives on rhlaptop (see bottom).

## The campaign in one paragraph

All 18 upstream-bound gap drafts were filed 2026-11-02 (CC-1) after a
two-model review (GLM + DeepSeek; drafts and evidence in
`docs/fullsend-issue-drafts/`, numbers in `cc-1-filing/filed-issues.json`).
Upstream's coder/fix agents opened PRs for 14 of them; every PR was verified
end to end on this stack's conformance path (a non-github.com forge, which
upstream does not test) with the matching local patch skipped, and the
results were posted on each PR. The umbrella is
[fullsend#9036](https://github.com/fullsend-ai/fullsend/issues/9036);
the host-assumption cluster hangs off it as sub-issues.

## PR state as of 2026-11-06

Verified, rebased onto current main (2026-11-06), conversations resolved,
waiting on maintainer merge:

| PR | issue (draft) | local patch to drop on merge | notes |
| --- | --- | --- | --- |
| fullsend#9049 | #9044 (20) | 0004 | in the merge queue (rh-hemartin enabled auto-merge) |
| fullsend#8955 | #8952 (12) | 0008 | the 2026-10-30 trial; rebased once already (docs-only conflict) |
| fullsend#9052 | #9037 (02) | 0007 | verified twice: initial head failed (no caller threading), /fs-fix revision passes (run 1860) |
| fullsend#9050 | #9039 (13) | 0011 | verified no-regression (scenario does not drive github setup/set directly) |
| fullsend#9051 | #9041 (15) | 0014 | verified (run 1905) |
| fullsend#9053 | #9040 (14) | 0013 | verified (run 1865) |
| fullsend#9055 | #9046 (22) | 0009 | verified (run 1910) |
| fullsend#9056 | #9038 (11) | 0005 + 0006 carried | PARTIAL: run path fixed and verified, dispatch-path allowlist gap remains ("domain not in allowlist", run 1924); second /fs-fix stalled; #9042 (16) is blocked on this |
| agents#1870/1871/1873/1872/1869 | #1864/#1865/#1866/#1868/#1867 | agents 0001/0005 | all verified on the agents tree; agents repo has no config migration issue |

Open follow-ups owned from the jtanner side:

- **fullsend#9158** (stacked on #9049's branch): the workflow wiring the
  coder app cannot push (workflows permission boundary) — passes
  `vars.OPENSHELL_GATEWAY_ENDPOINT` from `reusable-dispatch.yml` and
  `reusable-prioritize.yml` via a dedicated channel, precedence over the
  runner env, validated single https:// URL. Cross-reviewed (Claude +
  Codex) before push. Needs its own conformance run with a repository
  variable seeded on the emulator before merge.
- **fullsend#9054** (#9043, draft 19): rh-hemartin requested changes with
  a design question ("why not keep pointing at github.com where we
  develop?"); the owner replied 2026-11-06 with the runtime-vs-development
  argument and the token-stays-with-its-issuer point. Awaiting his
  response. Deliberately NOT rebased while the discussion is active.
- **Drafts 21 (#9045) and 23 (#9047)**: triaged upstream as features, no
  PRs; design decisions are maintainer-side.
- **Draft 26 (#9048)**: coder run failed at push on the workflows
  permission boundary; the fix needs human authorship (the #9158 pattern
  works for this).
- **Draft 24**: never filed; held because both review models concluded the
  premise may be vacuous on github.com (issues.edited carries only
  title/body changes).

## Operational lessons (these WILL bite again)

1. **Stale branch config aborts dispatches.** Main migrated
   `.fullsend/config.yaml` off `create_issues` (v0.54 era); any branch
   based before that fails review/fix dispatches with
   `config.yaml: create_issues is no longer supported`. All fullsend-repo
   PR branches were rebased 2026-11-06 for exactly this reason. If a new
   branch shows the error, rebase it (cherry-pick -s onto main, force-push
   with lease).
2. **The coder app cannot push `.github/workflows/` changes** (deliberate
   workflows-permission boundary). Human authorship is required; use the
   jtanner token which carries the workflow scope.
3. **DCO**: human-authored or human-rebased commits need `-s`
   (Signed-off-by matching the committer). Bot-authored commits pass
   without it.
4. **Merge blockers are usually unresolved review conversations**, not
   code. Every fresh review round can open new threads; each needs a real
   disposition (fixed-and-outdated / documented non-regression / do the
   documentation ask). Do not rubber-stamp.
5. **The fix gate skips /fs-fix on ready-for-merge PRs**; removing the
   label first unblocks it. The fix agent's rebases can be wrong (it once
   pushed a 113-commit diverged history) — verify with
   `compare/base...head` before trusting its claims.
6. **Repository variables on the emulator**: the conformance stack can
   seed them (it already serves FULLSEND_RUNTIME that way); needed for
   #9158's verification.

## Counterpart infrastructure on rhlaptop

- `notes/fullsend/gap-drafts/` — drafts, filed-issues.json,
  conformance-queue.json, review files, the ralph loop state and digests.
- `scripts/cc1_conformance.sh` — the serial PR-verification runner
  (canonical restore after every item, runner CLI cache purged per run,
  seed-source guard against concurrent checkout use).
- `scripts/cc1_ralph_loop.sh` + systemd timer `fullsend-ralph-loop.timer`
  (6-hourly) — watches the issues AND the PRs (head SHAs, merges,
  approvals) and writes digests; it flags conformance runs, maintainer
  questions, and merge-triggered patch drops.

When a PR merges: mark the matching draft `fixed-upstream` in
filed-issues.json, flag the local patch droppable at the next rebase, and
watch #9036's checklist. #9049 (in the merge queue) is the first one.
