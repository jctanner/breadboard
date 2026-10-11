# Session log

## 2026-10-07 — Removed redundant standalone Fullsend smoke milestone

User confirmed native Fullsend already works in Breadboard and wants runtime
checks deferred until the branched pipeline is wired. Removed the pending smoke
task and renumbered the active plan: A1 checkout, A2 prompts, A3 CI/single run,
A4 batch/events. Runtime pins and any integration fixes are part of A3;
event interface selection is part of A4. Updated dependencies, ADR and index.
Earlier entries below retain the superseded numbering. Planning only.

## 2026-10-07 — A2 clarified as a native-agent smoke test

Narrowed A2 to a reproducible released-Fullsend/native-Claude probe on the
existing runner: Opus 4.6, read-only Jira/Git access, validated result,
pre/post scripts and runtime cleanup. Reuse prior infrastructure evidence.
Strategy lock/resume work remains A3/A4 and actual event dispatch remains A5.
Updated task, plan and index; no smoke job or model call started.

## 2026-10-07 — Agent-led CI uses a new strat-pipeline branch

User specified the existing GitLab strat-pipeline repository for the new CI
pathway. Updated the plan, A4/A5, ADR and index to publish
feat/fullsend-agent-led-poc there, consuming the public strat-creator fork's
feat/fullsend-agent-led-strategy prompts through released Fullsend. Preserve
main, the script-led branch and shared project variables. No branches created,
CI published or model jobs launched.

## 2026-10-07 — A1 narrowed to repository preparation

User specified the first milestone order: checkout in the new folder, correct
upstream remote, rebase/publish origin/main from upstream/main, then create the
new feature branch. A1 now covers only that setup with recorded ancestry and
source SHAs. Native compatibility is A2; prompts/single/batch-events move to
A3/A4/A5. Plan, dependencies and index updated; no Git operations performed.

## 2026-10-07 — Divergent native-agent strategy POC planned

User requested strat-single/strat-batch prompts through unmodified released
Fullsend, following rfe-creator/rfe-autofixer. Added separate plan, ADR-0012 and
pending A1–A4 tasks. Proposed checkout/branch:
checkouts.fullsend_agent_led_poc/jctanner.strat-creator at
feat/fullsend-agent-led-strategy. Inspected native agent/pre/post/schema
reference and its read-only Jira difference. A1 gates release compatibility,
failure cleanup and event support; later milestones prove single/batch runs.
No checkout creation, service reset, CI publication or model work performed.

## 2026-10-06 — M8 batch delivery

Completed batch-discover and normal-pipeline cleanup; source efcf946 pushed,
520 unit / 784 full passed (1 skipped). No-model controls 2052/3991 passed.
Real batch 2053/3993 created and reviewed RHAISTRAT-2/3 on Opus 4.6 from
fresh RHAIRFE-2/3. Both reviews approve 8/8. Results, direct Org Pulse reads
(after standard Jira sync recovery), dashboard 2055/3996 and cleanup verified.
Recorded Org Pulse reset-era stale-key ingest bug; DNS follow-up remains open.
Moved M8 task to done and updated plan/index. No recurring schedule or live
test job remains; one maintained runner.

## 2026-10-06 — GitLab browser CI downloads

Fixed project and CI Lab trace/artifact links to use UI session routes.
Added guarded plain-text trace download, including nested project paths.
Rebuilt GitLab emulator; verified job 3993 trace and archive return 200 with
UI login and 404 anonymously. Focused private-project regression passed.
Recorded findings in bugs/fixed/gitlab-ui-ci-download-session.md.

## 2026-10-06 — Missing Claude CI progress diagnosis

Job 3993 raw trace has 22,497 lines (~3.4 MB), no truncation/limit warning.
Batch harness uses stream_format none. Fullsend RunEntrypoint copies stdout
only to iteration-1/output.jsonl, not host stdout; stderr reaches CI.
Artifact stdout is 3,705 bytes / 67 lines. Our stream-claude.py ignores
assistant messages and renders stream_event deltas, but Fullsend's helper
uses stream-json without --include-partial-messages. Claude transcripts
still contain 355 assistant records across 17 files. Recorded logging gap;
no workflow rerun or code change during diagnosis.


## 2026-10-06 — CI progress fix delivered

Pushed Fullsend bdedebeaf stdout forwarding and strat-creator 7244097 completed
assistant rendering. Published both emulator branch pins with live output
credential masking (including private Vertex credential fields). Full Go race
suite, vet/lint, 787 strategy tests (1 skipped), and four caller tests passed.
Replayed actual 3993 transcripts into 97 KB readable output. Optional deployed
probe 2056 canceled during slow GitHub fetch before sandbox execution; recorded
verification limit. Moved logging bug to fixed and updated the plan. Existing
historical jobs, processed RFEs and exact Opus 4.6 pin preserved.


## 2026-10-06 — Logging batch test and stale-warning fix

Completed fresh two-RFE batch 2057/4000 (33m48s successful attempt) after safe
pre-inference results-clone retry. RHAISTRAT-4 approve8/8; RHAISTRAT-5 numeric
approve6/8 with three prose revise verdicts. Actual 367 assistant records all
Opus4.6; stdout visible and 31/31 long lines intact after ANSI removal. Both
locks released; archive/trace credential scans zero; gateway/containers/network
removed; old six issue hashes unchanged. Results and direct Org Pulse verified
(after standard stale-key recovery), fresh dashboard2059/4003 passed on retry.
Recorded architecture-context 403 / skipped-as-approve evidence gap. Fixed and
deployed user's inaccurate active-job stale/pending warning; two tests passed,
browser trace/artifact downloads verified. Plan/index/receipt updated.

## 2026-10-06 — Claude unused-directory warning

Removed only `/tmp/strat-assess` from disposable strategy CI settings; preserve
hooks, other permissions and workspace trust state. Source 78bc04c pushed;
525 unit / 789 full tests passed (1 skipped). Both CI pins published. Diagnostic
publisher accidentally created default capability pipeline 2060; canceled,
no strategy/model job selected. No RFE replay. Live Claude warning absence is
not separately verified. See tasks/done/fullsend-strategy-unused-directory-warning.md.

## 2026-10-06 — Strategy entrypoint banner

Added requested three-line startup banner before validation/setup. Source
774cf10 pushed; 790 full tests passed (1 skipped). Both future CI pins published
without creating pipelines; active 2061/4011 retains previous pin. Plan and done
receipt updated, Bash syntax and root/component diff checks passed.

## 2026-10-06 — Restart bounded batch after emulator trace repair

Verified deployed fix receipt and clean/unprocessed RHAIRFE-6/7. User-authorized
new pipeline 2065 / batch4017 with source774cf10, including startup banner;
prior failed attempt preserved. Batch remains in progress.

## 2026-10-07 — CI workspace trust and stderr isolation

Implemented authorized trust merge/atomic write and per-invocation stderr;
clears historical working logs after clone, exports invocation logs on cleanup.
Source3343f23 pushed;792 full tests passed/1 skipped. Both future CI pins
published without pipelines. Current4017 remains untouched. Live warning
absence needs a future job on the new pin. Done receipt and fixed bug updated.

## 2026-10-07 — Reserved Vertex profile migration task

Created tasks/pending/strat-use-builtin-vertex-provider.md at user request.
Records job4017 warning, refresh compatibility investigation, migration and
bounded diagnostic acceptance. No implementation or runtime changes.

## 2026-10-07 — Injection scanner follow-up task

Created pending/fullsend-bash-injection-scan-false-positives.md at user request.
Records8 matches from job4017/script774cf10 and acceptance for preserving genuine
security detection while excluding Bash count/PID/length syntax. No code changes.

## 2026-10-07 — Visible entrypoint architecture fetch

Entrypoint now fetches context before Claude, prints/retains stdout+stderr and
status, with180s timeout and existing optional-context behavior. Native fetch
reports curlHTTP errors and propagates Git failures. Source43a6457 pushed;
795 full tests passed/1 skipped, Bash syntax/diff checks passed. Both CI pins
published without new jobs; running4017 unchanged.403 cause remains unverified.

## 2026-10-07 — One-RFE batch started

No eligible RFEs after successful2065. Seeded fresh8, verified discoverysize1,
started2067/4021 with source43a6457 and exact expectedkey8. Build4020 running;
batchpending. No processed issues replayed. Start-taskdone, runtime pending.

## 2026-10-07 — Architecture fetch diagnostic confirms Git transport403

Inspected4021 trace: setup reaches Git clone, HTTP403 then exit128, before
Claude starts. Initial GitHub API listing did not fail.403 cause still unknown;
existing optional context behavior allows review to continue. New trust fix
shows zero trust warnings in inspected trace. No running-job edits.

## 2026-10-07 — Architecture clone policy live verification complete

Published3fd1563 pins, ran no-model diagnostics.2069/4025 fetch succeeded but
alias assertion failed; corrected cone-mode symlink handling,5 tests passed.
2070/4027 passed fetch3.7s,1025 docs/36 overlays and supervisor denial probes.
Cleanup0/no pod/container/job network; archive scan27 entries clean. No model
or RFE work. Fixed bug/done verification task/plan receipts updated.

## 2026-10-07 — One-RFE batch on verified policy started

User requested another batch size1. No eligible existing issues; seeded fresh9,
verified exact native discovery, triggered2071/4029 with source3fd1563.
Build4028 running, batchpending; no processed issues replayed. Runtime pending.

## 2026-10-07 — Verified-policy batch outcome

Status request:2071/4029 success in21m39s; RFE9->STRAT9 reviewapprove8/8,
all reviewersapprove. Architecturefetch0, no trust warnings, lock released,
cleanup0. Start receipt updated with outcome and downstream verification limit.

## 2026-10-07 — Repeat single-RFE batch started

User requested another size1 batch. Seeded fresh10 after native eligibility
returnedempty, verified exact discovery, triggered2073/4033 on source3fd1563.
Build4032 running; batchpending. No processed-issue replay; runtime pending.

## 2026-10-07 — Agent-led POC A1 complete

Cloned fork into `checkouts.fullsend_agent_led_poc/jctanner.strat-creator`,
added upstream, fetched both. Fork main already equalled upstream main
(`cc1ba8c`), so no rebase or push. Created local
`feat/fullsend-agent-led-strategy` at `cc1ba8c`; baseline lint passed, `make
test` 768 passed/1 skipped. Next: A2 prompts.

## 2026-10-07 — Agent-led POC A2 at breakpoint B2.1

Added A2 breakpoints. Built strat-single harness/prompt, shared preflight,
validator, handoff/publish post-script and owned-lock release; 43 new tests,
full suite 811 passed/1 skipped. Released Fullsend 0.43.0 `lock` resolves the
harness. Uncommitted; waiting for B2.1 verdict.

## 2026-10-07 — B2.1 verdict: go with host-side locking

User chose host-side locking after the emulator repro showed a repeated
`lock --locked-keys-file` call empties the owned record while the lock stays.
Batch discovery also moves to the pre-script; agents get keys, not JQL.
ADR-0012 amended, plan contract and A2 verdict log updated. Next: B2.2.

## 2026-10-07 — Agent-led POC A2 at breakpoint B2.2

Moved discovery and locking into the host pre-script (`prepare_run.py`,
explicit `STRAT_STATE_DIR`, because 0.43.0 gives pre-scripts no
`FULLSEND_RUN_DIR`). Added strat-batch, validated against the host run
record, and added resume, partial-lock and full pre-script tests. 62 agent
tests; full suite 830 passed/1 skipped. Uncommitted; waiting for B2.2 verdict.

## 2026-10-07 — Agent-led POC A2 complete

B2.2 go; stayed on Fullsend 0.43.0 (v0.45.0 adds no pre-script run dir or
always-run hook). Wrote `.fullsend/README.md`, committed and pushed
`feat/fullsend-agent-led-strategy` at `508ea33` (830 passed/1 skipped on the
committed tree). A2 moved to done. Next: A3, awaiting go.

## 2026-10-07 — Agent-led POC A3 at breakpoint B3.1

Published `feat/fullsend-agent-led-poc` (from main `14d8131`, head `7677bfd`).
Pipeline 2075 failed: Fullsend 0.43.0 rejects unset harness host variables,
so CI now exports optional ones as empty. Pipeline 2076 (strat-batch, no
work) succeeded on released 0.43.0: gateway up, context fetched, native skip
(exit 78), no model, clean teardown. Waiting for the B3.1 verdict.

## 2026-10-07 — B3.2 attempt 1: real run, validator false failure

Seeded RHAIRFE-11 (DSP artifact retention). Pipeline 2077 ran native
strat-single on Opus 4.6 (parent and 6 subagents): RHAISTRAT-11 created,
refined, pushed and reviewed, approve 6/8. The host validator wrongly
required unanimous prose reviewers, so publication was skipped; locks were
released and cleanup was fine. Fixed in fork `a2b888a`, CI repinned. A
second RFE scenario is ready; waiting for go.

## 2026-10-07 — B3.2 succeeded (attempt 2)

Seeded RHAIRFE-12 (Model Registry serving guard). Pipeline 2078/job 4039:
native strat-single on Opus 4.6 (parent and 6 subagents), RHAISTRAT-12
approve 8/8, validated including the Jira readback, published to
strat-pipeline-data (`28c3825`, summary `2db3a1b`). Org Pulse read back after
the documented `releases:jira-sync` stale-key recovery. Fresh dashboard
2079/4040 shows the run. Lock released, clean teardown, 0 credential hits.
Waiting for the B3.2 verdict.

## 2026-10-07 — A3 complete (B3.3 failure paths)

Pipelines 2080 (context failure before lock) and 2081 (invalid key) failed in
the pre-script as intended: no sandbox, no lock, no Jira change, clean
teardown, 0 credential hits. A3 moved to done with the remaining
differences recorded. Next: A4, awaiting go.

## 2026-10-08 — A4: scheduled batch, mid-batch stop, retry fix, recovery

Scope amended: event triggers and polling are out (user). Batch is wired to
a GitLab schedule with `resource_group: strat-batch` (2082, no-work). Batch
2083 stopped mid-batch on a headless `end_turn`; the user chose rfe-creator's
retry with resume (fork `9350c89`). Batch 2084 (RHAIRFE-15/16) succeeded and
published, with no cross-contamination and a truthful revise. Recovery 2086
imported RHAISTRAT-14 via Path A with no duplicate clone; refine repeated as
predicted. The comparison with the script-led POC is recorded. Waiting for
the verdict to close A4.

## 2026-10-08 — A4 closed; follow-up milestones A5–A7

User verdict: close A4 and put the open items in new milestones. A4 moved
to done. Added to the plan, each with a pending task and breakpoints:
- **A5:** Org Pulse stale-key fix, GitLab emulator bridge ordering (native
  dashboard trigger), and publishing RHAISTRAT-11 from retained artifacts.
- **A6:** in-run retry and partial/blocked locks proven in CI; closes the
  end_turn bug.
- **A7:** GitLab runner job pods left in `Error`.

Next: A5, awaiting go.

## 2026-10-08 — A5 B5.1 and B5.2

B5.1: GitLab emulator bridges now wait for their stage and `needs`
(emulator `3fc4480`); Org Pulse runs `releases:jira-sync` after an ingest
touching a stale key (rhai-org-pulse `718ffa29`); the agent-led CI has a
`build-dashboard` trigger. No-model pipelines 2087 (bridge skipped) and 2088
(child 2089 after the job) showed the ordering. Breadboard `858e944`.

B5.2: seeded RHAIRFE-17 (KServe canary rollback). Pipeline 2090 produced
RHAISTRAT-17, approve 6/8, published as run `20261008-164143`. The stale
pre-reset Org Pulse key recovered automatically, and the native trigger
rebuilt the dashboard (2091) after the results commit. No manual steps.
Waiting for the B5.2 verdict; next is B5.3 (publish RHAISTRAT-11).

## 2026-10-11 — First strat-workflow tier 2 harness prepared

Implemented the agreed three-RFE F1 scenario and `tier2-smoke`, preserving
tier 1 and both pinned designs. One selected Haiku design/run per invocation;
batch completeness, per-item checks, reviewer return evidence, and model
checks added. Twelve offline tests plus Markov validation, Python compile,
shell syntax, and diff checks passed. Retained Haiku dump replay catches S1
lost reviewer outputs and passes S2. No commit, push, sync, Jira write/reset,
or new model run. Analysis is in the
[evaluation plan](../plans/strat-workflow-eval-plan.md); the
[implementation task](../tasks/done/strat-workflow-tier2-three-rfe-smoke.md)
is complete. Next: separately authorize publication and the single S1 run.

## 2026-10-11 — Single S1 tier 2 pass launched

User authorized launch. Committed/pushed `2cf4540`, synced/imported the exact
benchmark source, and submitted `markov-run-02336f23` at 13:47:49 UTC: S1
only, Haiku, three RFEs, one repeat, no artifact wipe. Seed passed for
RHAIRFE-1/2/3; S1 job
`script-run-workflow-all-claude-haiku-5-5-1011-134802-315418` is running in
refinement after creating three distinct strategies. First 12 requests all
Haiku; all three refine helpers also report Haiku. No S2 or repeat. Run/evidence details
are in the evaluation plan; the current launch task now awaits completion
analysis.

## 2026-10-11 — S1 completed; run-data evidence capture

User added mandatory preservation of all available evidence before resets.
Implemented a host collector, SQLite online backups, paginated relay/Jira
exports, SHA-256 verification, and local pre-wipe/per-seed receipt guards.
S1 Markov run completed at 14:18:35.968 UTC; its job failed validation.
Collected a verified final capture under
`var/run-data/strat-workflow/markov-run-02336f23/20261011T143354300275Z/`:
20 successful sources, including full retained shared artifacts, Jira,
MLflow (33 traces/488 spans), Observatory, logs, and exact API/strace files.
After user feedback on visibility, unpacked job evidence into browsable
`api-dumps/`, `strace/`, and `artifacts/` directories, retaining tarballs.
S1 has 605 API files and 3,698 strace files. Expanded capture: 4,694 files,
1,601,583,672 bytes; checksums verified and receipt refreshed.
Twenty offline tests, workflow validation, compile, and diff checks passed.
No reset, S2, repeat, commit, push, or sync; guard publication remains pending.
Analysis/evidence/limitations recorded in the evaluation plan; detailed S1
failure and context analysis remain pending in the S1 task.

## 2026-10-11 — First S1 batch failure cause confirmed

Inspected archived raw API requests/responses, executed Workflow prompt,
progress, final results and validation. RHAISTRAT-2 refinement succeeded but
its helper returned nested JSON in `recorded`; S1 rejected the value and
excluded that strategy from scoring/review. Independently, 14/16 reviewer
Skill returns lacked prose, reproducing tier 1 output loss. No timeout-stop
message; the Workflow completed within its 30-minute wait, Claude exited 0,
and saved relay health has zero drops/storage errors. Recorded both open
bugs and evidence in the evaluation plan. No design changes or new run.

User follow-up: added the model-error versus Workflow-robustness distinction
explicitly to the plan. Haiku's malformed return suggests a formatting or
instruction-following error; one run does not establish weaker reasoning
as the cause. S1's permissive schema and lack of persisted-state reconciliation
are separate robustness findings. Reviewer output loss remains separate.

Runtime estimate requested: re-read the three historical S1 Opus Workflow
streams from the retained shared archive and compared phase durations with
the current two-slot Haiku refine schedule. Recorded an estimated 50 minutes
(planning range 40–60) for a complete three-ticket Opus S1 batch, with
concurrency/retry assumptions and the need for a longer background-wait
budget than 30 minutes. No configuration change or model run performed.

## 2026-10-11 — Single S1 Opus batch authorized and prepared

User authorized one S1 Opus 4.6 three-ticket run. Added separate `tier2-opus`
selection/model checks, forwarded a 90-minute S1 wait override, and added a
bounded terminal-run wait mode for detached archive collection. Designs and
Haiku smoke defaults unchanged. No active jobs/runs; previous Haiku archive
reverified and live receipt guard passes; relay health is clear. Twenty-three
offline tests plus Markov, compile, shell syntax, and diff checks passed.
Next: publish/sync this harness and submit the single authorized batch.
