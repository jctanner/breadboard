# Handoff: strat-workflow orchestration evaluation

Written 2026-10-11 to hand this work to a new agent session. Read this whole
file first, then the plan it points to. The plan is the full record; this
note is the map and the operating instructions.

**Status update 2026-10-11:** the plan supersedes historical next steps in
this handoff. Relay `59d6f06` has already been rebuilt/redeployed and
verified; the separate `tier2-smoke` three-RFE harness is implemented and
validated, with tier 1 preserved and the two design pins unchanged. The
user has now authorized commit/push, markovd sync/import, and exactly one
S1 Haiku batch (`repeats=1`, `wipe_at_start=false`). S2 remains unauthorized.
See the plan's latest sections and
[current launch task](../tasks/current/strat-workflow-tier2-s1-first-pass.md).
Successful requests over 120 seconds are expected after the timeout fix;
verify the absence of errors at the old cutoff, not latency alone.

## 1. What the work is

We are evaluating two orchestration designs for the strat-creator strategy
pipeline (create → refine → push → score → review), running them in
Breadboard's integrated stack against the Jira emulator:

| ID | Design | strat-creator PR | Pinned eval commit |
| --- | --- | --- | --- |
| S1 | Claude Workflow (`workflows/strat-pipeline.js`), launched by `var/benchmarks/strat-workflow/scripts/run-workflow.sh` | #83 | `eval/pr-83` = `1bd7f1718c7ed10f2900691c0e9eaea2b8e48e43` |
| S2 | bash entrypoint (`.fullsend/scripts/strategy-entrypoint.sh`) | #80 | `eval/pr-80` = `0287b838d2bc59a2569cf2dd971aad7ad2d76dad` |

- **The benchmark** is the Markov directory workflow
  `var/benchmarks/strat-workflow/`, run by markovd. Read its `README.md`.
- **The full plan, results and every finding** are in
  `.ledger/plans/strat-workflow-eval-plan.md`. Its tail has these
  sections, in order:
  - the haiku smoke re-run;
  - the tool-call analysis;
  - the opus smoke run and its statistics table;
  - the reviewer output contract;
  - whether haiku predicted the opus results;
  - how much confidence 3 runs buy (control flow vs handoffs);
  - primary context growth, the process boundary and background-task
    completion behavior.
- **The plan's tier 2 section** ("Tier 2: full tests (larger, mixed
  batches)") is the designed next phase.

## 2. Where things stand

**Done:**
- The haiku smoke tier: `markov-run-41e56ed5`, 3 rounds × S1/S2, all passed.
- The opus smoke tier: `markov-run-f2f3b733`, 3 rounds. S2 round 3 failed on
  an account usage-limit 429 and was re-run alone as `markov-run-5884ad2a`.
  All 6 valid runs passed.
- Full analysis of both, recorded in the plan.

**Key findings,** with detail in the plan:
1. **S1 loses reviewer output.**
   - **Cause:** the review step's `VERDICT` schema makes Claude Code offer
     `StructuredOutput` ("MUST call exactly once") inside the forked
     reviewer skills. A reviewer that calls it returns no prose.
   - **Opus:** 12/12 reviewers lost; the review agent wrote the reviews
     itself, and once overrode two reviewers' "revise".
   - **Haiku:** 15/22 lost; the reviewers were rerun.
   - **S2:** 0. Both commits' skills intend reviewers to return text, so
     this is a PR #83 defect.
2. **On opus, S1 ≈ S2 on cost (~$7/run), time (~25 min less relay cuts),
   tokens and files read.** At n = 3 only differences of about 3 sd are
   detectable.
3. **S1's control flow is deterministic JS too.** Its handoffs (read, record,
   push, result) are LLM-transcribed script output: about 3 + 3 per RFE.
   S2 runs those scripts directly.
4. **Haiku was a good harness shakedown** but mispredicted the opus
   time, cost and quality comparisons.
5. **Every run so far is a single RFE, so batching is untested.** That is
   where the designs differ most:
   - S1 has parallel refine, pipelined review, per-item failure isolation
     and resume state (`strat_pipeline_state.py`).
   - S2 is sequential, `set -Eeuo pipefail` (all-or-nothing), with no
     resume.

**Current recommendation:**
- **For single-RFE jobs, S2,** with high confidence.
- **For batches, open until tier 2.** S1 as written in PR #83 must not ship
  because of finding 1.

## 3. Next steps, in order

Ask the user before each run. Never start a run on your own initiative.

1. **Commit the uncommitted plan sections.**
   `.ledger/plans/strat-workflow-eval-plan.md` has the reviewer
   output contract, haiku predictiveness, and the 3-run confidence
   analysis, plus the context-growth and Workflow execution analysis.
   Then ask before pushing.
2. **Record the batching insight in the plan's findings** (finding 5 above),
   revising the recommendation. The user agreed it matters; it is not
   written yet.
3. **Deploy the relay timeout fix,** `checkouts/model-relay` commit `59d6f06`
   (local only, not pushed).
   - **The problem:** managed upstream profiles hard-coded a 120 s timeout,
     ignoring `SHIM_UPSTREAM_TIMEOUT_SECONDS=600`. 13 opus turns were cut
     and retried at 2 min each.
   - **The deploy:** `make host-rebuild-relay`. The auto-mode classifier
     denies it for agents, so ask the user to run
     `! make host-rebuild-relay`. Only do this when no run is in progress:
     the restart breaks in-flight calls.
   - **Verify:** after the next run, no relay record has `latency_ms` of
     120000 or more. Then close
     `.ledger/bugs/open/model-relay-120s-upstream-timeout.md`.
   - **Push** the relay repo (`git push origin main` in
     `checkouts/model-relay`) when the user approves.
   - **Also close** `model-relay-telemetry-drops-under-load.md` if drops
     stay 0 and per-job relay counts match the API dumps (the opus run
     showed 0 drops).
4. **Design and build tier 2 batch tests** for S1 and S2 on opus. Follow the
   plan's tier 2 section (F1–F11, batches of 3 and 10). Measure:
   - wall-time scaling at 1, 3 and 10 RFEs, and S1's actual concurrency;
   - failure isolation, by injecting a Jira write failure (F9);
   - resume after create or push (F6, F7);
   - handoff failures at scale.

   **Usage limit:** a batch of 10 on opus is about 1,000 calls, and the
   Claude OAuth account hit its usage limit at about 610. Plan rounds
   around it, or ask about switching the relay to a Vertex upstream.
5. **Draft the PR #83 report** (the reviewer leak plus the plumbing-handoff
   design) from the plan's findings. Ask the user before posting anything
   anywhere.
6. **Optional:** isolated handoff-reliability trials (the read, push and
   result steps run many times on their own). Cheaper than full runs for
   reliability numbers.

## 4. Rules the user has set

- **Pause after each run and dig into the results.** Don't start new runs,
  tiers or variants without an explicit go-ahead.
- **Don't block on long polls or foreground sleep loops.** Check once and
  report, or use one background wait that notifies you. Report ETAs from
  job start times.
- **Never print the relay admin key.** Read it into a variable and redact
  it from output:
  `KEY=$(kubectl get secret model-relay-admin -n ai-pipeline -o jsonpath='{.data.admin-api-key}' | base64 -d)`,
  then pipe through `sed "s/$KEY/<k>/g"`.
- **Commits:**
  - only when asked;
  - run `git diff --check` and the smallest relevant compile/test first;
  - end messages with `Co-Authored-By: <your model> <noreply@anthropic.com>`;
  - push only when asked.
- **The ledger:** read `.ledger/agentic_work_ledger.md` before creating
  ledger files. `checkouts/` repos are separate; read each one's
  AGENTS.md/CLAUDE.md first.
- **The S1-vs-S2 analysis is opus vs opus.** Haiku is reference only.
- **Mirror the reference pipelines; don't invent new criteria** (memory:
  "Follow reference pipelines").

## 5. How to run things

**Launching a benchmark run** through the markovd API. All var values must
be **strings**: a JSON boolean gives "invalid request body".

```bash
S=<your scratch dir>
kubectl get secret github-emulator-tls -n ai-pipeline -o jsonpath='{.data.ca\.crt}' | base64 -d > $S/emulator-ca.crt
CA=$S/emulator-ca.crt; M=https://markovd.local/api/v1
# preflight: the run refuses to start while pipeline jobs are active
for st in running pending; do curl -s --cacert $CA "https://dashboard.local/api/jobs?status=$st" | python3 -c 'import json,sys;print(sum(1 for j in json.load(sys.stdin) if j.get("phase")))'; done
TOK=$(curl -s --cacert $CA -X POST $M/auth/login -H 'Content-Type: application/json' -d '{"username":"admin","password":"admin"}' | python3 -c 'import json,sys;print(json.load(sys.stdin)["token"])')
curl -s --cacert $CA -X POST -H "Authorization: Bearer $TOK" -H 'Content-Type: application/json' $M/runs \
  -d '{"workflow_name":"var-benchmarks-strat-workflow","vars":{"only_tests":"S1,S2","variants":"opus","wipe_at_start":"false"}}'
```

**Run settings:**
- **`wipe_at_start` defaults to `"true"` and deletes all earlier
  evidence:** the artifacts volume, MLflow and Observatory. Always pass
  `"false"` unless the user says otherwise.
- **Other vars:** `tier`, `only_tests`, `variants` (`haiku` =
  claude-haiku-5-5, `opus` = claude-opus-4-6, in `vars/models.yaml`),
  `repeats`, `breadboard_ref`, `job_timeout`.
- **The commit:** markovd passes the imported Breadboard commit as
  `workflow_source_commit`; the opus runs used `4648532`. Jobs clone
  scripts from that pushed commit. A benchmark change needs a push, then
  a markovd project sync and import. See the README, "Running it from
  markovd".
- **Tiers:** only the smoke tier exists in `vars/tiers.yaml`, and the only
  scenario is `data/scenarios/smoke-one-rfe.yaml`. Tier 2 needs new
  scenarios, tiers and checks.

**Monitoring:**
- `kubectl get jobs -n ai-pipeline`. Job names include the design and model,
  e.g. `script-run-workflow-all-claude-opus-4-6-…` (S1) and
  `script-strategy-entrypoint-all-claude-opus-4-…` (S2).
- `kubectl logs job/markov-run-<id> -n ai-pipeline` for the runner.
- The per-run summary is at
  `/app/artifacts/benchmarks/strat-workflow/<markov run id>/summary.md`, in
  the dashboard pod.

**Evidence,** in the `pipeline-artifacts` volume, read through the
dashboard pod (`deploy/pipeline-dashboard`):
- **API dumps:** `/app/artifacts/apibodies/<job>/`, with `*.request.json`,
  `*.response.json` and **`index.jsonl`**. The index pairs every request
  with its response exactly (`request_file`, `response_file`,
  `message_id`, `session_id`), and usage includes cache tier and
  `inference_geo`.
- **strace:** `/app/artifacts/strace/<job>/`.
- **Job outputs:** `/app/artifacts/scripts/<job>/`. Review files are under
  `output/strategy-run/strat-reviews/` (S2) and `publish/results/strat-reviews/`
  (S1).
- **MLflow** (`http://mlflow:5000`, experiments 1 = S1, 2 = S2) traces only
  each `claude` process's top-level conversation, not sub-agents or forked
  skills. Use the API dumps for counts.

**Analysis scripts** are in `var/benchmarks/strat-workflow/scripts/`. Run
each inside the dashboard pod:
`kubectl exec -i -n ai-pipeline deploy/pipeline-dashboard -- python3 - <job…> < script.py`

| Script | Output |
| --- | --- |
| `tool_calls.py` (`--jsonl` for records) | Every tool call per agent, errors, empty forked-skill results, reviewer `StructuredOutput` calls, repeats |
| `concurrency.py` | Busy time, calls in flight, unanswered requests |
| `strace_timing.py` | Per-process timing: model in flight, tools alive, overhead |
| `conv_breakdown.py` | Conversations (agents), calls and tokens |
| `arch_requests.py` | Architecture-doc requests per agent |
| `file_reads.py` | Files opened, from strace |
| `context_growth.py` (`--json` for time series) | Per-conversation input context, exact indexed request/response pairs, growth and missing-response counts; identifies S1's primary separately |
| `summarize.py`, `check_run.py` | Used by the workflow itself |

**Script caveats:**
- `conv_breakdown.py` and `arch_requests.py` still attribute final
  responses by time order. They could switch to `index.jsonl` pairing.
- The role mapping keys on prompt tails: S1's forked refine shows as
  "plumbing" in `conv_breakdown.py`.
- File-open totals are dominated by the scorer's whole-context Grep
  sweeps (about 1,844 opens each) and are noise.

**Relay telemetry** goes through the admin API at
`http://model-relay-admin:8081/api/private/v1/`:
- `telemetry/requests?limit=500&order=desc&cursor=…` lists requests;
  records have `latency_ms`, `error_type`, `http_status` and
  `upstream_message_id`, which matches `index.jsonl`'s `message_id`;
- `health` gives drop counters.

Call it from the dashboard pod with the admin key, as above.

**The strat-creator source:**
- **The emulator copy:** `https://github.local/opendatahub-io/strat-creator`.
  Clone with `GIT_SSL_CAINFO=<ca file>`, then fetch the two pinned SHAs.
- **The host checkout with eval branches:**
  `/home/jtanner/workspace/github/jctanner.redhat/2026_10_09_strat_creator_workflow_debate/checkouts/gh/strat-creator`.
- **Files that matter:**
  - `.claude/skills/strategy-review/SKILL.md` and
    `strategy-*-review/SKILL.md`, the same in both commits;
  - `workflows/strat-pipeline.js` (S1);
  - `.fullsend/scripts/strategy-entrypoint.sh` (S2, including
    `batch-discover` mode);
  - `tests/fixtures/workflow-smoke/` (PR #83's stub skills).

## 6. Known pitfalls

- **`make host-rebuild-relay` and other shared-resource deploys are
  denied** by the auto-mode classifier. Ask the user to run them with `!`.
- **Claude Code doesn't retry the account usage-limit 429.** The job fails
  outright; re-run only that test afterwards (`only_tests`, `repeats: "1"`).
- **Tool results can end with `<system-reminder>` blocks.** Strip them
  before matching result text; `tool_calls.py` does.
- **strace timestamps have no date.** `strace_timing.py` unwraps jobs that
  cross midnight UTC.
- **Skill frontmatter settings aren't enforced:**
  - the reviewer skills' `model: opus` is ignored, so reviewers run on the
    session model;
  - `allowed-tools` pre-approves tools but doesn't restrict them.
- **Seed jobs are always named `…claude-haiku-5-5…`.** That's the seed
  step's label, not the run's model.
- **Scratch outputs from the last session**, not durable: the session
  scratchpad `…/scratchpad/{rerun,opus}/` held analysis text, jsonl and
  review copies. Regenerate them from the evidence with the scripts above.

## 7. Evidence inventory (all kept; wipe was off)

**Haiku (`markov-run-41e56ed5`):**
- S1: `script-run-workflow-all-claude-haiku-5-5-1010-180408-0d4a57`,
  `…-184025-84f4f2`, `…-191947-f4cef2`.
- S2: `script-strategy-entrypoint-all-claude-haiku-1010-182709-92cd57`,
  `…-190601-ccd332`, `…-193703-26e17e`.

**Opus (`markov-run-f2f3b733`, plus `markov-run-5884ad2a` for S2 r3):**
- S1: `script-run-workflow-all-claude-opus-4-6-1010-234154-2647bf`,
  `…-1011-003101-159e0e`, `…-1011-013249-74e51a`.
- S2: `script-strategy-entrypoint-all-claude-opus-4-1011-000645-d25283`,
  `…-1011-005848-d3cae0`, `…-1011-042540-5f963f` (the re-run).
- Excluded, failed on the usage limit:
  `script-strategy-entrypoint-all-claude-opus-4-1011-020151-d0246c`.

**Costs at list prices:**
- Opus A/B: $42.54 total (S1 $20.84, S2 $21.70; all 5-minute cache writes,
  `inference_geo: global`).
- Haiku A/B: $2.77.
- Prices are from https://platform.claude.com/docs/en/about-claude/pricing.
