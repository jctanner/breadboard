# Claude Workflows and scripted pipelines

## What the evidence says

Claude Workflows offer useful scheduling, separate agent conversations, and saved
results. They do not make the whole pipeline deterministic. In the tested design,
even routine script execution and result transfer pass through model decisions.

Our three-ticket comparison found S1 faster and slightly cheaper, but S2 delivered
all specialist assessments through the expected return path. Prefer an external runner:
bash for launching commands, Python for data handling and validation. Keep agents
responsible for the work that needs judgment.

Evidence date: 12 October 2026. Workflow behavior refers to Claude Code 2.1.296.
S1 means the native Workflow design; S2 means the bash entrypoint. An RFE is a
request for enhancement. Sources are listed at the end.

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

| Layer | S1: native Workflow | S2: external runner |
| --- | --- | --- |
| Scheduling | JavaScript chooses order and concurrency | Bash chooses order and invocation |
| Routine operations | An agent runs commands and reports results | Scripts run commands and parse results directly |
| Strategy and review content | Model judgment | Model judgment |

S1 makes the first layer deterministic while moving uncertainty below `agent()`.
The model chooses commands, interprets output, and decides what to return. The
harness then packages that return for the next layer.

For example, S2 reads state directly from a Python command. S1 asks an agent to
run that command and repeat the JSON. The command may succeed while the reported
value is wrong. In the Haiku batch, a completed refinement was returned as JSON
inside a string; the pipeline then left that strategy out of review. [2]

Extra transfers create extra places to fail. A deterministic loop can skip an
item an agent omitted; replay can reuse an incorrect result. Predictable
scheduling can therefore preserve mistakes and hide incomplete work.

S2's agents still make uncertain decisions internally. The external runner can
keep discovery, validation, checkpointing, and publication outside those
conversations. Model judgment remains uncertain.

### 3. The useful parts

- **Parallel work:** independent agents can overlap, with a concurrency limit.
- **Pipelines:** one item can reach review while another is still being scored.
- **Result-driven work:** an agent's returned list can drive a loop or fan-out.
- **Replay:** completed agent results can be reused after a restart, saving work.

Returned lists can silently omit items. Separate conversations can share files
and skill metadata. Neither guarantees a complete or isolated batch. [1, 5]

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

The specialist defect also affects ordinary CLI schema output. Tool restrictions
or direct structured assessment calls worked in fixtures; neither has been
validated in a repaired paid strategy batch. Cancellation did stop fixture
children. Request retries preserved completed tool work, while conversation
restarts repeated side effects. [3, 4]

The 30-second JavaScript guard is not a total workflow deadline. The token
budget was unset in the tested local launch path. External limits still matter.

### 5. Small primary context does not mean small total usage

In the repaired S1 batch, the primary agent's measured input grew from 24,103 to
26,887 tokens: an increase of 2,784. There were no primary model calls during
the roughly 50-minute background wait. Waiting happened in the harness.

One helper reached about 168,000 input tokens. Total job usage was 12.95 million
tokens across repeated requests and separate conversations, not one context
window. [2]

## B. How much testing is enough?

### 6. Spend according to the question

One run can expose a defect. Many successful runs are needed to estimate how
rarely defects occur.

Levels 1 and 2 follow the existing benchmark structure. Levels 3 and 4 below are
proposed follow-ups, not authorization to launch more runs.

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

Keep original S1/S2 versions as controls; name repairs as new variants. Repeating
a known failure adds little. Confidence campaigns should follow repairs and
stronger checks, including the scope checks both designs currently fail.

### 7. The budget arithmetic

One measured three-RFE pair used:

- S1: 12.95 million tokens and $21.55 API list-price equivalent.
- S2: 12.21 million tokens and $24.28 API list-price equivalent.
- Together: 25.16 million tokens and $45.83.

Ten pairs therefore cost roughly **10 × 25.16 = 252 million tokens** and
**10 × $45.83 = $458**. They require about 23 hours if run one after another at
the observed durations, before setup or quota waits.

Totals include uncached input, cache writes, cache reads, and output. Cached
input counts repeatedly. The pair produced about 481,000 output tokens, including
thinking. These categories have different prices; token totals alone cannot
predict the bill.

Projections assume similar three-RFE workloads. Empty batches can cost less;
large inputs, retries, setup, and independent grading add cost. Dollars are
historical API equivalents, not subscription charges. Recalibrate the smoke
estimate on the repaired infrastructure. Pin permission settings too: some
modes add classifier calls. [2, 6]

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

Sixty per design means 120 paid batch runs. These are total study budgets, not
additions to earlier rows. Qualifying only one candidate uses its own per-run cost.

Bounds assume independent, representative trials of a stable version. Twelve
specialists inside one batch are not twelve independent pipeline runs. Repeating
one RFE gives narrow coverage. Keep injected faults separate from estimates of
ordinary failure frequency.

“95% confidence” describes a method that covers the true rate in at least about
95 of 100 repeated studies under those assumptions. It does not mean the next
run is guaranteed to succeed. The rule applies only when there are zero failures;
otherwise use a failure-rate confidence interval. [7]

Ten pairs are a speed/cost pilot. Subtract S1's time from S2's for each pair;
report the average and spread. More runs depend on that spread and the difference
we care about. Quality needs a fixed rubric and independent, blind grading.
The failure-rate rule does not measure accuracy.

Our historical three-repeat Opus campaign could not complete within the available
Anthropic five-hour usage allowance. Quota consumption is separate from wall
time. Large studies need planned quota windows and must record aborted runs. [2]

## C. What S1 and S2 tell us

### 9. The strongest completed comparison

Both designs received the same three distinct RFE problem statements on the
repaired relay, once each, using Opus 4.6.
Mixed-state and ten-RFE strategy batches remain untested.

| Measure | S1: Workflow | S2: bash |
| --- | --- | --- |
| Job duration | 51.2 minutes | 88.7 minutes |
| Completed strategy/refine/review sets | 3 | 3 |
| Transport or quota failures | 0 | 0 |
| Substantive expected specialist returns | 2 of 12 | 12 of 12 |
| Benchmark result | Failed return check | Passed |
| Reported total tokens | 12.95 million | 12.21 million |
| Output tokens, including thinking | 216,778 | 264,161 |
| API list-price equivalent | $21.55 | $24.28 |

S2 took **88.7 − 51.2 = 37.5 extra minutes** and cost **$2.73 more**, about
13%. S1 overlapped two top-level strategy tasks; S2 ran the stages sequentially.
Scheduling explains much of the timing pattern, but content and latency also
differed. Bash can support concurrency; the measured S2 implementation did not
use that same schedule. [2]

One pair, retained files, and differing harness/relay revisions limit general
claims. Earlier single-RFE timings had unequal 120-second relay failures;
subtracting timeout seconds does not reconstruct an error-free measurement.

### 10. Delivery is not accuracy

The structured-output/text mismatch explains S1's ten missing returns. Some final
sections used earlier scorer reports. In the GLM test, transcript reads recovered
specialist prose. Missing returns do not prove fabricated reviews. [3]

Both Opus designs showed scope drift: every substantive specialist report
assessed the whole batch despite a per-strategy target. Both also published
aggregate approval alongside at least one specialist request for revision.
Correct target keys were present in the expanded prompts.

Check **delivery, correct target, faithful incorporation, and technical truth**
separately. Independent accuracy remains unmeasured. A passing job or a model
score of 7 out of 8 does not settle it.

### 11. Production recommendation

Use S2's external-runner approach as the foundation, with explicit result
contracts. Bash launches commands; Python parses data, checks identities and
required fields, persists checkpoints, and validates publication. Agents create,
refine, and assess strategy content.

Before production, require a complete input manifest, one persisted assessment
per strategy and role, preserved dissent, explicit error handling, safe retries,
external deadlines, and verified archives before cleanup. Add bounded concurrency
for independent work, with separate artifacts and controlled shared writes.
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
