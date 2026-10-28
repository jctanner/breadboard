# Opus 5.5: one mixed-state ten-ticket batch

Markov run [markov-run-296d9e2e](https://markovd.local/runs/markov-run-296d9e2e),
submitted once through markovd-cli on 2026-10-18 at 21:34:24 UTC.
Model job script-run-workflow-all-claude-opus-5-5-1018-213456-cf6af9 ran
21:34:56–22:00:14 UTC: **25m18s**. Native Workflow wf_056dcd70-75b completed
in **23m19s**, with all 34 Workflow agents on their first attempt.

## Outcome

All pipeline stages exit 0. All ten acquired RFEs complete with ten distinct
strategies and forty selected specialist assessments. The full mixed-state
checks pass: four fresh clones, eight refinement/push paths, two verified
review-only paths, preserved controls and released locks. Model-free repeat
passes, acquires nothing, skips the human-only control, exits 78 and makes
zero model calls. No automatic paid retry or replacement run occurred.

The pinned benchmark is **FAIL solely on reviewer_outputs_returned**. It
accepts 41 of 42 specialist returns, with two extra testability launches for
RHAISTRAT-12 and RHAISTRAT-2. There are forty required target/role pairs.
RHAISTRAT-1 scope is rejected despite its delivered 6,119-character report:
"Scope assessment: The capability is right-sized but loosely bounded."
The checker expects a canonical verdict at the start of that field. Removing
only the grammatical subject in memory makes classification pass.

This is a [checker false negative, subsequently fixed](../bugs/fixed/strat-review-gate-scope-subject-false-negative.md).
Independent audit confirms all forty selected reports match their actual
receiving Skill results, native producer transcripts, provenance hashes and
verbatim final review incorporation. Mechanical scope checks find no foreign
ticket headings, IDs or tool paths. Original reports, checker and FAIL remain
unchanged. The initial analysis made no repair; the subsequent model-free fix
is recorded below. This is not independent content judging.

The scope audit records 490 allowed and 42 denied operations. The agents
recovered; no scope problem is recorded by the audit. Reviewer transcript
overlap peaks at ten, with the four selected roles per ticket still sequential.
The additional specialist launches do not constitute Workflow-agent retries.

## Model, source and runtime evidence

Benchmark 0b890213a1c5defad3c2ad5df50f8353e2d3bfdc changes only configuration,
its offline check and README. S1 remains 6ed858b2294a29457153a90f187a801022c21e8b
from the Fullsend fork. Fixture batch-mixed-ten-distinct-v2, concurrency ten,
configured high effort, numeric-only approval and capture/failure policy match
the preceding Opus 4.6 case. Actual seed/read-back confirms all eighteen RFE
subjects/descriptions match the distinct fixtures and the ten acquired keys
have the expected four create/four refine/two review resume points.

The late process-inspection attempt found that the job had already completed;
there is no live primary-PID environment snapshot. Retained runtime evidence
instead confirms Claude Code 2.1.296, primary init model claude-opus-5-5, native
Workflow default model claude-opus-5-5 and all 791 request/response model checks
on that exact ID. Actual requests specify high effort 780 times and low effort
11 times under existing agent settings. Job metadata sets cap ten, native
capture and stop-on-native-failure. The archived native Workflow script matches
both candidate source copies byte-for-byte (SHA-256
9960ef103b8a5c222084b6f8aae7c9d945cdce055ac126acf7eb3c333ff1cfed).
Kubernetes image digest matches the qualified Opus 4.6 image:
sha256:2a7c01426967e6a7e1566525057a81b0060026969cb6f2f8430a7e1abfd6115e.

The existing Vertex provider inventory was extended with the exact model.
A separate one-token probe succeeded through the same relay ADC credentials
before any Jira reset. No provider fallback was used. All 791 captured model
responses uniquely join successful, complete, non-synthetic relay records on
vertex-strat-evals with Google service-account authentication and the exact
requested/resolved model. Relay capture additionally contains 52 count-token
operations and one separate non-stream generation; the job's reported usage
comes from its 791 API response captures.

## Comparison with the preceding mixed Opus 4.6 case

| Metric | Opus 4.6 | Opus 5.5 |
| --- | ---: | ---: |
| Model-job runtime | 30m07s | 25m18s |
| Accounted tokens | 32,138,772 | 37,261,081 |
| API calls | 855 | 791 |
| Standard API list-price equivalent | $51.48 | $42.80 |
| Selected final reports delivered/preserved | 40/40 | 40/40 |
| Specialist launches | 40 | 42 |
| Numeric decisions | 9 approve / 1 revise | 5 approve / 5 revise |
| Pinned benchmark | PASS | FAIL: one format false negative |

In this pair Opus 5.5 takes 4m49s less job time, approximately 16%, and its
API equivalent is approximately 17% lower, despite approximately 16% more
tokens. Model rates and category mix differ. Separate generations and one run
per model cannot establish general speed, cost or accuracy rankings.

The selected Opus 5.5 role recommendations are 39 revise and one approve;
numeric scoring still approves five strategies under the configured policy.
The dissent is retained. More revision recommendations alone do not establish
better technical judgment; inputs include deliberately incomplete seeded work.

Usage categories: 1,584 uncached input, 4,583,034 cache creation, 32,002,321
cache read and 674,142 output. Total **37,261,081**; 245,235 thinking tokens are
already included in output. No recorded API errors, rate limits or unreadable
response captures. The CLI records **$42.80481020**, standard list-price basis,
not an invoice. The tiny preflight probe is separate from these job totals.

## Evidence and archive

Campaign: var/run-data/strat-workflow-hardening/pr85-mixed-ten-vertex-opus55-20261018/.
Read-only observer PID 1071434 collected terminal evidence from 22:01 through
22:20:26 UTC. The final archive contains 13,930 files / 18,848,434,120 bytes,
complete/final, with no capture errors. Independent checksum verification passes
and final receipts are published. It includes raw API dumps, strace, native
state/transcripts, Jira, shared databases/files, MLflow, logs and relay telemetry.

Independent read-only audit is retained under the campaign's separate analysis/
directory: audit.json, analyze_run.py, relay-reconciliation.json,
final-verification.json and a checksum manifest. The audit records forty
matching producer/receiver/provenance/review joins, no scope problems, phase
timings and the in-memory format diagnostic. Its initial archive-complete=false
observation predates finalization; final-verification.json records the completed
verification. No model work was performed by the audit.

## Scope-checker follow-up

At the user's request, role-assessment-v3 now accepts the bounded scope subject
before a canonical judgment. The unchanged receiving-channel replay moves
39/40 to 40/40, changing only RHAISTRAT-1 scope. Genuine failing controls remain
failed; original verdict/report bytes remain unchanged. Five authored regression
methods and the full offline suite pass: 114 tests, two optional skips.
Published d3a8a8f, all 81 Markovd-imported files verified. No new model job or
inference tokens; revision-rate analysis remains deferred. [Repair details](../tasks/done/strat-review-scope-subject-checker.md).
The separate model-free evidence archive under analysis/checker-scope-subject-fix-20261018/
is complete/final and checksum-verified (27 files / 2,649,699 bytes).

## Subsequent content comparison

The user then requested judging the saved refined strategies against 4.6.
One assistant pass, with criterion ratings/preferences frozen before revealing
producer labels and pipeline scores, preferred 5.5 in all eight new-output
pairs. Four fresh/create/refine and four identical-draft refinements were
compared; the two unchanged review-only cases were excluded from that tally.
Their pipeline scores still decrease (6 to 4 and 4 to 3), so approval counts
cannot serve as direct content-quality rankings. Material defects remain in
both versions, especially false credential-adoption readiness. No new pipeline
or provider judge call was made. [Content assessment and limitations](strat-content-opus46-vs55-20261018.md).

## Subsequent revision investigation

All 20 paired scorer reports and deterministic final decisions reconcile;
parser/composer agree on all 81 possible score vectors. The four additional
revise outcomes are mostly real readiness gaps, with a debatable queue-scope
penalty. Separately, both extra testability calls arose from prose-bearing
Recommendation fields failing capture; neither strategy was rewritten.
Numeric-only gating remains unchanged, no provider call or source repair.
[Evidence and recommended next steps](strat-opus55-revision-analysis-20261018.md).
