# Claude Workflows or scripts for our strategy pipeline

We wanted to know whether Claude's Workflow feature was a better way to run our
strategy pipeline than the bash and Python scripts we already had.

The job is the same either way: take an RFE, create a strategy, refine it, and
review it before publication. Four review agents check whether the proposal is
feasible, can be tested, stays within the RFE's scope, and fits the architecture.
Each is assigned one of those areas, so we can
compare their findings and preserve disagreements in the final review.

We tested two implementations. In the **Native Workflow**, JavaScript inside
Claude coordinates the agents. In the **Scripted Pipeline**, bash and Python
coordinate separate Claude calls. The archived runs call these S1 and S2.

We did more than a single comparison:

- **Level 1, Haiku:** three reference runs per design on the single-RFE scenario,
  after fixing the architecture-context setup.
- **Level 1, Opus 4.6:** three completed runs per design. An account-limit failure
  required a separately launched replacement after the allowance reset.
- **Level 1, GLM 5.3:** one single-RFE run per design, checking whether both
  implementations worked with another model.
- **Level 2, three RFEs:** one Haiku Workflow run, then Opus batches for both
  designs, including additional attempts after infrastructure and quota failures.
  There was no GLM batch run.
- **Investigation:** API captures, system-call traces, job logs and saved artifacts
  to examine context growth, concurrency, token use, review delivery and recovery.
  Controlled tests against the Claude binary checked the suspected failure
  mechanisms, restart behavior and limits.

The evidence here comes from our benchmarks and analysis of Claude Code 2.1.296,
through 12 October 2026. We reproduced specific failures; we have much less
evidence about average performance or how often failures occur. Part B proposes
the additional testing needed to answer those questions, with token and dollar
estimates so we can decide whether that evidence is worth the cost.

I'd keep the scripted approach as our production foundation. The Workflow has
useful scheduling features, but it also puts model decisions into routine steps
that scripts can handle directly.

## A. What the Workflow feature actually does

### 1. JavaScript coordinates the work

A Workflow is a JavaScript program running inside the Claude process. The main
agent launches it through a tool call and gets a receipt. The program then runs
in the background until it returns a result or a failure notification.

The JavaScript chooses an order, loops through lists, and can run agents in
parallel. Each `agent()` call starts a separate model conversation.

The JavaScript cannot directly read files, call an API, or execute a shell
command. It asks an agent, which can use Bash and other tools, then report back.
There is no separate JavaScript subprocess taking over the job. Even running
a Python helper requires a model to make the tool call.

### 2. Determinism only gets us part of the way

The top layer is ordinary code. Given the same inputs, it follows the same rules.

Below that layer, a model chooses tool calls, interprets their results, and
returns information to the program. The harness, meaning the code around the
model, also decides how to package that information. A perfectly repeatable loop
can still make the wrong decision if its information is incomplete or wrong.

In the Haiku batch, a refinement had finished, but its completion record came
back as JSON tucked inside a string. The Workflow expected a different shape and
left that strategy out of review. The handoff changed what the next step believed
had happened.

In the scripted version, Python can read that completion record directly and
validate it. We can test that routine operation without asking a model to repeat
the answer.

Deterministic orchestration can move uncertainty into the steps underneath it.
Successful execution and a useful returned result are separate things to check.
Both designs still rely on model judgment for strategy content.

### 3. A completed review can still lose its report

We found a second problem in the way reviewer reports were returned. A reviewer
could write its assessment, finish with a structured-output tool call, and have
the parent receive only “Skill execution completed.”

The harness selected text from the last assistant record, which had no text,
and substituted the completion message. The assessment remained in the transcript.
That explains ten missing expected reports in the Opus Workflow batch. We
reproduced it with controlled responses on the same installed release.

This defect also exists in ordinary Claude CLI calls using the affected schema
configuration. Our scripted path avoided it, but bash cannot fix every Claude bug.
Tool restrictions and direct structured assessments worked in controlled tests;
neither remedy has been validated in a repaired paid strategy run.

In a GLM Workflow run, the agent recovered reviewer prose from transcripts.
Some Opus final sections used earlier scoring material. A missing return does
not prove a final review was invented. We need to check where its findings came
from and whether they survived. Recovery must happen before a decision, or the
pipeline must revisit that decision.

### 4. Parallelism helps, and complicates debugging

The Workflow has useful built-in support for overlapping agents, limiting their
concurrency, and letting one ticket reach review while another is still being
scored. It can also use returned lists to decide what work to launch next.

We deliberately ran the scripted stages in sequence for debuggability and log
sanity. Bash can run work in parallel too. In either design, overlapping work
needs separate logs, clear ticket identifiers, and rules for shared writes.
Separate agent conversations do not mean separate filesystems.

The primary agent's context stayed fairly small while helpers worked. In the
completed Workflow batch, its input grew from 24,103 to 26,887 tokens:
**26,887 − 24,103 = 2,784 more tokens**. During the roughly 50-minute background
wait, there were no primary model calls.

The architecture reviewer reached **167,579 input tokens** after reading the
platform and component documents in architecture-context. The job's 12.95 million
total tokens include separate conversations and repeated requests. That total
is usage across the job, not the size of one context window.

### 5. Restart and completion need their own checks

The Workflow can reuse saved agent results after a restart. That saves work,
but results can become stale when shared files change. If an agent finishes a
write before its result is saved, restarting can repeat the write.

Our controls showed that a failed parallel branch can return `null` while the
outer Workflow reports completion. A successful CLI exit can also disagree with
the Workflow outcome. We have to check that the expected work happened.

The short JavaScript execution guard is not a deadline for the whole job. Our
local launch path had no Workflow token budget set; even a configured budget can
be exceeded by the last agent before the next check. External limits still matter.

These findings describe Claude Code 2.1.296 with the Workflow settings used in
our benchmark and controlled tests. The benchmarks ran in Kubernetes jobs
submitted through Breadboard's job API. Markov coordinated test setup, job
submission, waiting and checks. Fullsend's runner and the OpenShell sandbox
were not used. Running either design through those systems still needs its
own integration testing.

## B. How much testing we need, and what it costs

### 6. Start small, then test the things that can break

We ran **level 1** with Haiku, Opus and GLM. For future smoke tests, I'd still
start with one Haiku run per design per scenario to check the wiring and artifacts.
Historical Haiku usage suggests roughly 12 million tokens per pair, but needs
recalibration after infrastructure repairs.

For **level 2**, we started with one Haiku Workflow batch, which exposed the
completion-record mismatch. We then ran Opus batches for both designs and obtained
one completed comparison pair. GLM was tested only at level 1. The three RFEs were
different enough to avoid deduplication.

We can put both token and dollar figures on the Opus workloads. A pair means
one Workflow run and one scripted run. These dollar figures use **Claude Opus 4.6
(`claude-opus-4-6`) API list prices**:

| Workload | Runs per design | Tokens per pair | Opus 4.6 API equivalent per pair |
| --- | --- | --- | --- |
| Level 1, one RFE | 1 | About 8.9 million | About $14.18 |
| Level 2, three RFEs | 1 | 25.16 million | $45.83 |

The level 1 row averages three historical pairs; the level 2 row is one completed
pair. Earlier single-RFE runs had transport interruptions, so these are recorded
usage estimates, not guaranteed future costs. The Haiku token estimate is separate;
we have not verified GLM provider pricing.

After that, test missing reports, wrong targets, empty batches, duplicates,
failed writes, broken streams, quota limits, crashes, cancellation and stale
saved results. Mocks can test much of the harness without provider tokens; live
cases test model behavior.

Fix delivery and scope problems before funding a confidence study. Keep original
versions as controls and name repairs separately.

Our production pipeline accepts up to ten RFEs per run, every six hours. The
average is around three, but that does not tell us the most common batch size or
how often we reach ten. We need full ten-RFE tests before claiming readiness for
that limit, alongside empty, one-RFE and three-RFE regression cases. A full batch
means **10 strategies × 4 reviewers = 40 expected reports**.

We are keeping the production batch limit at ten. Reducing it to three would cut
nominal capacity from **4 × 10 = 40** to **4 × 3 = 12 RFEs per day**, before failures
or delayed runs. Smaller benchmark batches are not a reason to reduce capacity.

### 7. A comparison study is a bigger commitment

For a proposed **level 3** pilot, run **ten batches of ten RFEs per design** with
Opus 4.6: twenty batch runs, or 100 RFE executions per design. Each pair uses
the same ten RFE problem statements in both designs; vary the contents across
pairs and keep RFEs distinct within each batch. Ten pairs is a planning choice,
not a guarantee of a useful comparison.

All dollar figures use the Opus 4.6 pricing basis above. These are usage
equivalents, not subscription invoices or measurements of our account allowance.
The Haiku smoke estimate covers tokens only.

We have only measured a completed three-RFE pair. To budget the larger workload,
start with a rough assumption that usage grows with the number of tickets:

**25.16 million × 10 ÷ 3 ≈ 84 million tokens per ten-RFE pair**

**$45.83 × 10 ÷ 3 ≈ $153 per ten-RFE pair**

Using those rounded estimates, ten pairs means roughly **840 million tokens and
$1,530 for pipeline work**, plus independent grading. These are projections,
not measured ten-RFE costs. Caching, longer contexts, repeated reads and retries
can change the rate of growth. Measure a full-size pair before committing to the
repeats.

Totals include input, cache writes, cache reads and output at different prices.
The measured three-RFE pair's roughly 481,000 output tokens already include
thinking. Fewer total tokens can still cost more. Runtime at ten RFEs also needs
measurement, including whether jobs finish before the next six-hour window.

Our historical three-repeat Opus campaign could not finish within the available
Anthropic five-hour usage allowance. That account quota is separate from job
duration. Larger studies need quota windows and must record spend on aborted runs.

### 8. Clean runs do not establish zero risk

For proposed **level 4** reliability claims, we need more runs. With zero observed
failures, a useful approximate 95% upper bound on the failure rate is:

**3 ÷ number of independent runs**

For 60 clean runs, **3 ÷ 60 = 5%**. Sixty successes still leave uncertainty about
the true failure rate.

| Clean ten-RFE runs per design | Approximate upper failure rate | Projected tokens, both designs | Opus 4.6 budget, both designs |
| --- | --- | --- | --- |
| 10 | 30% | 840 million | $1,530 |
| 30 | 10% | 2.52 billion | $4,590 |
| 60 | 5% | 5.04 billion | $9,180 |
| 300 | 1% | 25.2 billion | $45,900 |

These total budgets use the rounded ten-RFE projections above. Sixty runs per
design means 120 jobs; testing only one design uses its own per-run cost. Add
content-judging spend separately to every row.

The calculation needs independent, representative runs of a stable version.
Forty reviewers in one batch are not forty independent pipeline trials.
Repeating one ticket gives narrow coverage. Keep injected faults separate.
The bounds describe the ten-RFE cases we sample. Estimating the failure rate
across ordinary production also needs its actual mix of smaller and full batches.

“95% confidence” means the method covers the true rate about 95 times out of
100 repeated studies under those assumptions. It cannot guarantee the next run.
If failures occur, use a failure-rate confidence interval instead of this shortcut.

For time and cost, compare the average difference and its spread. Quality needs
a fixed rubric and independent blind grading; accuracy needs reference facts or
expert checks. This formula cannot tell us which strategy document is better.

These larger studies are proposals. The evidence we have today is much narrower.

### 9. Level 5: Judge the strategy content

Level 5 is a separate evaluation of the resulting strategy content. It can use
saved outputs from earlier levels; we do not need to finish the level 4 reliability
study first. The pipeline already pays for its four review agents. Independent
judging adds new token spend and should use the original RFE, architecture
references and a fixed rubric, without seeing the pipeline's own score as an
answer key.

Using the proposed level 3 pilot as an example, **20 batches × 10 strategies =
200 documents**. Two judge models with two passes per document means
**200 × 2 × 2 = 800 assessments**, using one combined rubric per pass. Each model
grades 400 times; multiply that by its measured average cost, then add the two
totals. Four separate criterion judges would multiply the assessment count by
four. Retries add spend.

I'd keep our same-model judge as a baseline and test other judges against a small
set of human assessments. Higher price alone does not establish a better judge.
Each chosen judge should grade both pipeline designs and all compared producer
models. Hide their labels and check agreement and consistency. We can change
judges on saved strategies without paying to regenerate them.

I inspected agent-eval-harness. It supports code and LLM judges, pairwise
comparisons and an external-command execution contract. I'd use it to score
our exported artifacts while Markov and Breadboard keep running the jobs. That
still needs an artifact adapter. Judge tokens and costs belong in a separate
budget; missing prices must remain unknown. The [framework assessment](strat-workflow-content-eval-harness-assessment.md)
records the inspected version, accounting limits and proposed integration.

### 10. Every change adds some validation work

Suppose we insert another script between two skills. We must check the script
and the agent's behavior around it: the right command ran, failures were handled,
the output survived, and the next skill got the right input. A predictable script
can still have an unpredictable handoff. This can happen within an existing agent.

Use focused regression tests, failure cases and live integration checks. A full
Workflow-versus-script study is unnecessary for every edit. Claims of better
speed, cost or quality need repeated old/new comparisons with other settings fixed.

Earlier successes describe the earlier version. Keep evidence for unchanged
components, but revalidate changed steps and downstream behavior before carrying
forward a reliability claim.

Both designs need regression testing. Direct execution lets routine operations
be tested without model decisions; prompt or agent-input changes still need live
checks. I'd expect this to matter over the pipeline's lifetime, although we have
not measured maintenance savings.

## C. What the completed runs tell us

### 11. The Workflow finished sooner

Our strongest completed comparison used the same three distinct RFE problem
statements, one run per design, with Opus 4.6.
Each strategy had four review agents: feasibility, testability, scope
and architecture. That gives **3 × 4 = 12 expected reports** per design.

| Measure | Native Workflow | Scripted Pipeline |
| --- | --- | --- |
| Scheduling | Two overlapping top-level tasks | Sequential stages |
| Job duration | 51.2 minutes | 88.7 minutes |
| Strategy sets processed | 3 | 3 |
| Transport or quota failures | 0 | 0 |
| Expected reviewer reports delivered | 2 of 12 | 12 of 12 |
| Recorded Opus tokens | 12.95 million | 12.21 million |
| Output tokens, including thinking | 216,778 | 264,161 |
| Opus 4.6 API list-price equivalent | $21.55 | $24.28 |

The scripted run took **88.7 − 51.2 = 37.5 extra minutes** and cost **$2.73 more**,
about 13%. Scoring and review occupied about 34 minutes in the parallel Workflow
and 68 minutes in the sequential pipeline. Overlap helps explain the time gap,
and bash can overlap the work too. Different content and response times prevent
us from assigning every saved minute to parallelism. The dollar gap also mixes
design, caching and content effects.

We registered a smaller retest: one fresh sequential three-RFE run per design on
common infrastructure, matching top-level agent concurrency. The estimate is
roughly $46 API equivalent. It addresses scheduling, not readiness for ten-RFE
batches. It remains unrun, awaiting paid-run authorization. Its results will go
in a separate table.

One pair cannot establish a general speed or cost ranking. Retained shared files
and changes to test infrastructure also limit comparison. Earlier timings had
unequal 120-second transport failures; subtracting those seconds cannot recreate a
clean run.

### 12. Delivered reports still need to be right

The delivery difference is more concrete. Our checker compares the expected
report text against what the receiving agent actually got. It confirms 2 of 12
for the Workflow and 12 of 12 for the scripted run. That count needs no confidence
interval; predicting the delivery rate in future runs does.

Delivery is only the first check. In both Opus designs, every substantive
reviewer report assessed the whole batch despite being given a specific
strategy target. Both also published aggregate approval alongside at least one
reviewer's request for revision. We need to check the right strategy was reviewed
and that findings and dissent survived into the final document.

Technical accuracy remains unmeasured; an agent's score of 7 out of 8 cannot
establish it. Both designs used separate review conversations per strategy, so
this pair cannot measure the savings or contamination from shared review sessions.
Mixed-state and ten-RFE batches remain untested.

### 13. I'd keep scripts in charge of production coordination

I'd use bash to launch work and a small amount of Python to parse results,
validate ticket identities, save checkpoints and check publication. Agents would
create, refine and review strategy content.

We still have to build the checks. Exit zero is insufficient, and shell scripts
do not automatically prevent duplicate writes after a restart.

Before production, require complete input lists, persisted reports per strategy,
preserved dissent, safe retries, deadlines and verified archives before cleanup.
Parallelism needs bounded jobs, separate logs and controlled shared writes.
Keep the ten-RFE batch limit and six-hour schedule, and validate full-size runs
against both. Our three-RFE evidence is an intermediate baseline.

I'd also keep bash thin. We already have job and run infrastructure; we should
use it instead of turning one shell script into a whole workflow engine.

The Native Workflow remains useful for exploratory work with overlapping agents
and saved results. I'd revisit it for production after the deployed version passes
delivery, scope, restart and limit tests. For our pipeline today, I'd keep model
decisions in the work that needs judgment and ordinary code around it.

## Evidence behind this report

The [original report](claude-workflows-vs-scripted-pipelines.md) keeps the more
compact technical presentation. These records contain the underlying evidence:

- [Benchmark plan and run records](../plans/strat-workflow-eval-plan.md), including the [Workflow run](../tasks/done/strat-workflow-tier2-s1-opus-relay-fixed-repeat.md) and [scripted run](../tasks/done/strat-workflow-tier2-s2-opus-rate-limit-retry.md).
- [Workflow runtime analysis](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-analysis.md) and [conversation/file sharing](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-information-sharing.md).
- [Reviewer handoff diagnosis](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-specialist-handoff.md), [review provenance](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-review-provenance.md), and [fresh reproduction and delivery checks](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-benchmark-hardening.md).
- [Restart, cancellation, retry and limit controls](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-workflow-operations.md) and [permission-classifier analysis](../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-auto-mode-analysis.md).
- [Matched-concurrency retest plan](../plans/strat-workflow-matched-concurrency-retest.md), registered but not run.
- [Content-evaluation framework assessment](strat-workflow-content-eval-harness-assessment.md), including separate judge budgets and source references.
- [NIST confidence-interval guidance](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm) and [the zero-event risk calculation](https://qualitysafety.bmj.com/content/early/2013/08/19/bmjqs-2013-002246?versioned=true).
