# Strategy-content evaluation and agent-eval-harness

Inspected 2026-10-12. Source checkout: checkouts/agent-eval-harness, commit
21808e6daaf0c65847c2cea82aa40cb5916700b7. This is a source inspection and
integration proposal. This assessment did not run the harness, call a model or
build an adapter.

## Three different questions

The current benchmark measures execution: expected strategies and reviews,
correct targets, result delivery, publication, locks, runtime and usage. The
pipeline also pays agents to review its own strategies. Those reviews already
appear in the recorded pipeline token totals.

A separate content evaluator would judge the saved strategy against its RFE,
pinned architecture references and a fixed rubric. That adds new model calls and
cost. The evaluator should not inherit the producing agent's conversation or
use the pipeline's approval score as the answer key. Successful execution,
successful report delivery and technically sound strategy content need separate
results.

## What the framework actually supports

The repository is broader than model-output A/B testing:

- Deterministic Python checks, rubric-based LLM judges and tool-using agent judges.
- Explicit judge models independent of the producing model, per-judge overrides
  and repeated samples for judge stability.
- Pairwise A/B comparisons, thresholds, human-review examples, reports and MLflow.
- An opaque CLI runner for delegating execution to an external command.
- Container execution through Harbor, including Kubernetes/OpenShift support.
- A standalone scoring command over collected case outputs.

These are implemented surfaces, not a claim that our Breadboard/Markov scenario
already integrates with them. The CLI contract provides the extension point;
our job submission, reset, waiting, archive preservation and artifact mapping
would need an adapter. An accepted Fullsend ADR already adopts this contract for
its own functional tests, further showing that the framework is not limited to
comparing generated prose.

Relevant source: [runner contract](https://github.com/opendatahub-io/agent-eval-harness/blob/21808e6daaf0c65847c2cea82aa40cb5916700b7/docs/opaque-cli-runner-contract.md),
[scoring CLI](https://github.com/opendatahub-io/agent-eval-harness/blob/21808e6daaf0c65847c2cea82aa40cb5916700b7/skills/eval-run/scripts/score.py#L4012),
[Harbor execution](https://github.com/opendatahub-io/agent-eval-harness/blob/21808e6daaf0c65847c2cea82aa40cb5916700b7/deploy/harbor/README.md),
and [Fullsend's accepted framework decision](../../checkouts/fullsend-ai/fullsend/docs/ADRs/0051-agent-eval-harness-for-test-infrastructure.md).

## Judge selection is its own experiment

Using the same model as the producer is a reasonable baseline in a separate
evaluation context. It does not establish independent factual accuracy. Models
can share blind spots or favor particular output styles; research also documents
position and self-enhancement biases. A more expensive judge is a candidate to
test, not an automatic answer to those problems.

Keep one fixed primary judge for both pipeline designs and all compared producer
models. Letting each producer grade its own output mixes producer and judge
differences. On a small, human-labeled calibration set, compare the historical
same-model choice with other candidates.
Measure agreement with expert assessments, repeated-score stability, coverage
and cost. Use held-out cases to check the selected judge. Mask design/model
labels and original scores. For pairwise judgments, evaluate both presentation
orders and retain disagreements. Repeated judgments measure judge variability;
they are not additional independent pipeline trials.

The implementation resolves per-judge model before models.judge, then the
EVAL_JUDGE_MODEL environment fallback. On score.py's judges command, --model
sets the producer model for hook context; it does not override the judge model.
Judge changes belong in the judge configuration. See
[model resolution](https://github.com/opendatahub-io/agent-eval-harness/blob/21808e6daaf0c65847c2cea82aa40cb5916700b7/skills/eval-run/scripts/score.py#L2767)
and [judge research](https://arxiv.org/abs/2306.05685).

## Budget the work separately

The proposed ten pairs of ten-RFE batches produce 200 final strategy documents
if every expected artifact exists. Two judge models and two passes per document
mean **200 × 2 × 2 = 800 assessments** with one combined rubric per pass.
Four separate criterion judges would mean 3,200 assessments. API retries and
tool-using judge turns can add calls beyond those assessment counts.

Each model receives 400 assessments in that example. Its budget is 400 times
its measured mean assessment cost, summed across the two models. Track tokens
and costs by judge model, criterion and repeat. Full reference-document reads
can be substantial, so calibrate against representative context sizes.

**Total campaign cost = pipeline generation + additional content judging.**

The current 840M-token / $1,530 Opus projection covers pipeline work only.
Judge choice does not require regenerating the strategies: freeze the producer
outputs and re-score them. Keep separate judge-run IDs and result files, since
scoring merges results into summary.yaml. Do not count a whole batch's producer
cost once for every strategy exported from that batch.

The harness records judge usage separately from run_result.cost_usd, with totals
in summary.yaml judge_usage and per-model/per-judge breakdowns. It preserves
unknown costs as unknown. Direct Anthropic/OpenAI SDK judges can record tokens
without prices; provider-inline and runner estimates have different provenance.
For Anthropic, the usage adapter merges cache reads/writes into prompt_tokens,
so that summary alone cannot reproduce cache-priced API equivalents. Retain raw
usage categories and price them with the pinned model rates. Do not treat null
cost as zero. See [usage accounting](https://github.com/opendatahub-io/agent-eval-harness/blob/21808e6daaf0c65847c2cea82aa40cb5916700b7/skills/eval-run/scripts/score.py#L1441).

## Recommended integration

Keep Markov and Breadboard responsible for job execution and evidence collection.
Start by exporting frozen strategies into the harness's collected-case format,
with stable case IDs, their original RFEs, selected architecture references,
rubric version and source artifact hashes. Preserve run provenance separately
from the blinded judge input. Keep operational failures and missing artifacts
in the manifest; scoring only available documents must not hide missing work.

Run deterministic checks first, then post-run judges. Record judge errors and
coverage alongside scores; configure an error-rate gate, since ordinary means
and pass rates are calculated over cases that yielded values. Archive the
configuration, prompts, inputs, individual verdicts, rationales and raw usage
under var/run-data with the source benchmark run.

That would reuse the framework's scoring and reporting while preserving the
execution path we measured. If we later want the harness to initiate complete
end-to-end cases, implement its external CLI contract around the existing
driver, with explicit metrics export and external job cancellation. Its opaque
runner budget is advisory, and killing the local wrapper is not proof that a
submitted remote Kubernetes job was cancelled.
