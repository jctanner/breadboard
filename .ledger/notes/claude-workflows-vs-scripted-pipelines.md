# Claude Workflows and scripted pipelines

## What the evidence says

We compared two ways to turn enhancement requests into strategy documents:

- **Native Workflow:** JavaScript running inside Claude Code coordinates the agents.
- **Scripted Pipeline:** external bash and Python scripts coordinate Claude calls.

Workflows offer scheduling, separate conversations and saved results. Routine
script execution and result transfer still pass through model decisions.

Our three-ticket comparison used a parallel Native Workflow and a sequential
Scripted Pipeline. The Workflow finished faster at a slightly lower recorded
cost; the Scripted Pipeline delivered every specialist assessment through the
expected path. Prefer external bash/Python coordination with validated results;
keep agents responsible for judgment.

Evidence date: 12 October 2026. Workflow behavior refers to Claude Code 2.1.296.
The benchmark records label these designs S1 (Native Workflow) and S2 (Scripted
Pipeline). An RFE is a request for enhancement. Sources are listed at the end.

**Scope:** 2-of-12 is an existence proof with a reproduced mechanism, not a
failure-rate estimate. This configured path dropped completed assessments;
controlled responses explain how. One pair cannot establish general performance,
quality or reliability rankings. The recommendation concerns these integrations. [3, 8]

## A. What a Workflow actually does

### 1. A program running inside Claude

A Workflow runs JavaScript in a restricted environment inside the Claude process,
without a separate JavaScript subprocess. The main agent calls the Workflow tool,
receives a launch receipt, and later receives a result or failure notification.

The program can branch, loop, and combine results. Each `agent()` call starts a
separate model conversation with permitted tools, including Bash and services.

The program cannot directly read files, make network requests, or start shell
commands. Those actions go through an agent. Current time and randomness are
also blocked. [1]

### 2. Determinism has layers

Deterministic means the same inputs lead to the same program decisions.

| Layer | Native Workflow | Scripted Pipeline |
| --- | --- | --- |
| Scheduling | JavaScript chooses order and concurrency | Bash chooses order and invocation |
| Routine operations | An agent runs commands and reports results | Scripts run commands and parse results directly |
| Strategy and review content | Model judgment | Model judgment |

The Native Workflow moves uncertainty below `agent()`: a model chooses commands,
interprets output and returns a value; the harness packages it for the next layer.

For example, the Scripted Pipeline reads state directly from a Python command.
The Native Workflow asks an agent to repeat that command's JSON. In the Haiku
batch, a completed refinement was returned as JSON inside a string; the pipeline
left that strategy out of review despite successful underlying work. [2]

Separately, the Skill harness selects the last assistant record's text: a final
structured tool call can hide earlier specialist prose. These are transcription
and result-projection boundaries, not faulty JavaScript loops. [3]

Extra transfers add failure points. Deterministic loops can skip agent-omitted
items; replay can preserve incorrect results and hide incomplete work.

The Scripted Pipeline can keep discovery, validation and publication outside
conversations. Its agents still make uncertain internal decisions.

### 3. The useful parts

- **Parallel work:** independent agents can overlap, with a concurrency limit.
- **Pipelines:** one item can reach review while another is still being scored.
- **Result-driven work:** an agent's returned list can drive a loop or fan-out.
- **Replay:** completed agent results can be reused after a restart, saving work.

| Native Workflow concurrency | Scripted Pipeline concurrency |
| --- | --- |
| Built-in agent limits, task grouping and separate conversations | The author controls job pools, processes and per-job logs |
| Agents still mediate effects/results; files can remain shared | The author must implement limits, cancellation and log separation |

Both designs need log and shared-write discipline under concurrency. Separate
conversations are not filesystem isolation. Sequential logs are easier to follow;
the original author's intent is unverified. Matched-concurrency performance and
parallel safety remain unmeasured in this strategy comparison. [1, 5]

Returned lists can silently omit items; conversations can share files and skill
metadata. Completeness and isolation need checks. [1, 5]

### 4. Completion has several meanings

These are reproduced behaviors in the tested release:

| Observed behavior | Production consequence |
| --- | --- |
| A specialist's final structured response can become only “Skill execution completed” | Check that the actual assessment arrived |
| A failed parallel branch can become `null` while the Workflow completes | Check every expected result |
| Resume re-executes an agent whose result was not saved | A write or publication can happen twice |
| Replay reuses results after shared files change | Cached work may be stale |
| Budget checks occur at agent launches and completion | The last agent can overshoot the budget |
| CLI status and Workflow outcome can disagree | Read durable state and validate business results |

Ordinary CLI schema output shares the specialist defect. Tool restrictions and
direct structured assessments worked in fixtures, not a repaired paid strategy
batch. Cancellation stopped fixture children. Request retries preserved completed
tool work; conversation restarts repeated side effects. [3, 4]

A fresh mock run on the installed release, still 2.1.296, preserved earlier prose
on disk but returned only the acknowledgement. It tests prescribed responses,
not model failure frequency; newer releases remain untested. [8]

The 30-second JavaScript guard is not a total workflow deadline. The token
budget was unset in the tested local launch path. External limits still matter.

**Applicability:** neither Fullsend deployment was validated here. Runtime findings
transfer only when version/configuration preserve the tested path; wrappers can
change it or add validation. Relay/scaffold details do not automatically transfer.
Both integrations need pinned sandbox evidence, receiving results and business
checks. [1–4, 8]

### 5. Small primary context does not mean small total usage

The repaired Native Workflow's primary input grew from 24,103 to 26,887 tokens:
2,784 more. Its roughly 50-minute background wait involved no primary model calls.

One helper reached about 168,000 input tokens. The job's 12.95 million tokens
count repeated requests and separate conversations, not one context window. [2]

## B. How much testing is enough?

### 6. Spend according to the question

One run can expose a defect. Many successful runs are needed to estimate how
rarely defects occur.

Levels 1–2 follow the existing structure; 3–4 are proposals, not run authorization.

| Level | Runs | Token planning estimate | Purpose |
| --- | --- | --- | --- |
| 1: smoke, one RFE | One Haiku run per design per scenario | About 12 million per pair, using historical single-RFE usage | Check wiring; no quality claim |
| 2: batch baseline, three RFEs | One Opus run per design | 25.2 million per pair, measured | Expose batch behavior |
| 2: fault and edge coverage | One control per case per design; repeat only to resolve a question | Zero provider tokens with mocks; live cases need separate budgets | Check failure handling and boundaries |
| 3: comparison pilot | Ten Opus runs per design, over varied batches | About 252 million total | Measure cost/time variation and independent quality |
| 4: reliability claim | 30, 60, or 300 representative runs per design | See below | Bound the failure rate |

After smoke, prioritize missing results, wrong targets, empty batches, duplicates,
failed writes, broken streams, quota limits, crashes, cancellation, and stale
resume. Mocks test harness behavior; a smaller live subset tests model behavior.

Keep original versions as controls; name repairs as variants. Confidence campaigns
should follow repairs and stronger checks, including the scope checks both fail.
Repeating a known defect adds little.

### 7. The budget arithmetic

One measured three-RFE pair used:

**12.95 + 12.21 = 25.16 million tokens**, and **$21.55 + $24.28 = $45.83**
API list-price equivalent for the Native Workflow and Scripted Pipeline together.

Ten pairs use roughly **10 × 25.16 = 252 million tokens** and **10 × $45.83 = $458**:
about 23 sequential hours at observed durations, before setup or quota waits.

Totals include uncached input, cache writes/reads and output. Cached input counts
repeatedly. The pair's roughly 481,000 output tokens include thinking. Category
prices differ; token totals alone cannot predict the bill.

These are three-RFE projections. Empty batches can cost less; large inputs,
retries, setup and independent grading add cost. Dollars are historical API
equivalents, not subscription charges. Recalibrate smoke usage on repaired
infrastructure and pin permission modes, which can add classifier calls. [2, 6]

### 8. Zero failures still leaves uncertainty

With zero failures, a simple approximate 95% upper bound is:

**Upper failure-rate estimate ≈ 3 ÷ number of independent runs.**

For 60 clean runs, **3 ÷ 60 = 5%**. Zero observed failures does not establish
zero risk. The table applies separately to each design.

| Clean runs per design | Approximate upper failure rate | Tokens for both designs | API equivalent for both |
| --- | --- | --- | --- |
| 10 | 30% | 252 million | $458 |
| 30 | 10% | 755 million | $1,375 |
| 60 | 5% | 1.51 billion | $2,750 |
| 300 | 1% | 7.55 billion | $13,750 |

Sixty per design means 120 paid batch runs. These are total budgets, not additions
to earlier rows; qualifying one candidate uses its own per-run cost.

Bounds need independent, representative trials of a stable version. Repeating
one RFE gives narrow coverage. Keep injected faults separate from ordinary
failure-frequency estimates.

“95% confidence” describes a method that covers the true rate in at least about
95 of 100 repeated studies under those assumptions. It does not mean the next
run is guaranteed to succeed. The rule applies only when there are zero failures;
otherwise use a failure-rate confidence interval. [7]

The checker is deterministic; real agents are not. Counting reports in a fixed
archive needs no confidence interval; predicting future delivery rates does.
Twelve calls sharing a run/schema are not twelve independent trials. [8]

Ten pairs are a speed/cost pilot: subtract Native time from Scripted time and
report the average and spread. Required repeats depend on that spread and the
difference we care about. Quality needs a fixed rubric and independent, blind
grading; technical accuracy also needs reference facts or expert checks.
The failure-rate rule cannot measure either.

Our historical three-repeat Opus campaign could not complete within the available
Anthropic five-hour usage allowance. Quota consumption is separate from wall
time. Large studies need planned quota windows and must record aborted runs. [2]

## C. What the two designs tell us

### 9. The strongest completed comparison

Both designs received the same three distinct RFE problem statements on the
repaired relay, once each, using Opus 4.6.
Mixed-state and ten-RFE strategy batches remain untested.
Each strategy has feasibility, testability, scope and architecture reviewers:
**3 strategies × 4 reviewers = 12 expected reports**.

| Measure | Native Workflow | Scripted Pipeline |
| --- | --- | --- |
| Scheduling | Two overlapping top-level tasks | Sequential stages |
| Job duration | 51.2 minutes | 88.7 minutes |
| Completed strategy/refine/review sets | 3 | 3 |
| Transport or quota failures | 0 | 0 |
| Substantive expected specialist returns | 2 of 12 | 12 of 12 |
| Benchmark result | Failed return check | Passed |
| Reported total tokens | 12.95 million | 12.21 million |
| Output tokens, including thinking | 216,778 | 264,161 |
| API list-price equivalent | $21.55 | $24.28 |

The Scripted Pipeline took **88.7 − 51.2 = 37.5 extra minutes** and cost
**$2.73 more**, about 13%. Scoring/review spanned about 34 minutes in the parallel
Workflow versus 68 in the sequential Scripted Pipeline. Bash can overlap this work.
Equal-concurrency performance is untested; different content/latencies prevent
assigning every minute to parallelism or claiming an inherent Workflow speedup. [2]

The $2.73 gap does not isolate design, cache or content effects. Equal-concurrency
cost is unmeasured. A [pre-registered retest](../plans/strat-workflow-matched-concurrency-retest.md)
proposes one fresh sequential run per design on common infrastructure, pending
paid-run authorization; this original table stays.

One pair, retained files and differing harness/relay revisions limit performance
claims, not the reproduced projection defect. Unequal 120-second relay failures
confound earlier timings; subtracting them cannot reconstruct a clean measurement.

Run provenance: [Native Workflow](../tasks/done/strat-workflow-tier2-s1-opus-relay-fixed-repeat.md)
and [Scripted Pipeline](../tasks/done/strat-workflow-tier2-s2-opus-rate-limit-retry.md).

### 10. Delivery, content and recovery

**Separate checks:** delivery means the report arrived; scope means the correct
strategy was assessed; incorporation means findings/dissent survived composition;
accuracy means findings are true. Shared scope defects do not erase the delivery
difference; successful delivery does not excuse scope drift.

The structured-output/text mismatch explains the Native Workflow's ten missing
returns. Some final sections used earlier scorer reports. In the GLM test,
transcript reads recovered specialist prose. Missing returns do not prove
fabricated reviews. [3]

An upstream fix or validated specialist configuration can remove this defect
from CLI or Workflow, but cannot validate other model transcriptions. Retrieval
must precede decisions or trigger reconciliation; finding prose later does not
establish that the Haiku batch's omitted review ran. The tested scripted path
needed no transcript recovery; another schema configuration could expose the
same nested Skill bug. [3, 8]

Both Opus designs showed scope drift: every substantive specialist report
assessed the whole batch despite a per-strategy target. Both also published
aggregate approval alongside at least one specialist request for revision.
Correct target keys were present in the expanded prompts.

Independent accuracy remains unmeasured. A job pass or model score of 7 out of 8
does not settle it.

[The reusable delivery checker](../../scripts/claude_binary_analysis/check_specialist_delivery.py)
checks expected strategy/role/tool IDs against receiving results, without transcript
recovery. Complete hashed reference reports reproduce 2 of 12 versus 12 of 12;
the other axes are not graded. [8]

**Isolation versus reuse:** both designs used per-strategy review conversations.
Shared-session savings versus cross-ticket contamination need a separate test:
identical documents, shared/separate sessions, tokens and blind quality/scope scores.
Older shared-session production costs do not answer it for this pair.

### 11. Production recommendation

Use the Scripted Pipeline's external-runner approach as the foundation, with
explicit result contracts. Bash launches commands; Python parses data, checks
identities and required fields, persists checkpoints, and validates publication.
Agents create, refine, and assess strategy content.

Before production, require complete input manifests, persisted assessments per
strategy/role, preserved dissent, safe retries, deadlines and verified archives
before cleanup.

Choose concurrency deliberately: sequential logs are easier to read and debug.
Parallel work needs bounded jobs, separate strategy logs/artifacts, event
identifiers and controlled shared writes.
Neither shell nor Workflow supplies exactly-once writes automatically.
External scheduling requires explicit progress and resume code; keep the shell
thin rather than building a whole workflow engine in bash.

Native Workflow is useful for exploratory agent work. Revisit it for production
when the deployed version passes delivery, scope, restart, and limit controls.
Its scheduling advantages are real; status notifications alone cannot establish
business completion.

## Sources

1. [Workflow execution and determinism](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-analysis.md): 16 core controls and capability/fan-out probes.
2. [Benchmark plan and measured results](../plans/strat-workflow-eval-plan.md): identities, usage, outcomes, and archives.
3. [Handoff diagnosis](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-specialist-handoff.md) and [review provenance](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-review-provenance.md): 21 controls, 32 archived calls.
4. [Workflow operations](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md): 28 controls.
5. [Subagent information sharing](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-information-sharing.md): conversation and state boundaries.
6. [Permission classifier](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-auto-mode-analysis.md): five controls; ancillary model calls.
7. [NIST confidence intervals](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) and [zero-event risk estimation](https://qualitysafety.bmj.com/content/early/2013/08/19/bmjqs-2013-002246?versioned=true).
8. [Fresh reproduction and delivery checks](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-benchmark-hardening.md): R2/R3 archive, manifests, source hashes and reusable assertion.
