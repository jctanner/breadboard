# Refined strategy content: Opus 4.6 versus 5.5

**I preferred the 5.5 strategy in all eight comparable cases.** Its main gain
was finding the awkward parts of the design: actual component boundaries,
missing dependencies, destructive-operation safety, and assumptions that need
validation. The 4.6 versions more often described a plausible happy path as
though the supporting platform behavior already existed.

This is one assistant's assessment of saved outputs from one batch per model.
It supports a preference for these outputs, not a general accuracy percentage
or a claim that every 5.5 strategy is ready to implement.

## What was compared

The same mixed-state fixture ran as `markov-run-bfc0b766` (4.6) and
`markov-run-296d9e2e` (5.5), using the same S1 candidate `6ed858b`, concurrency
ten and configured high effort. Eight tickets produced new refined content:

- Four started fresh. Their comparison includes both creation and refinement.
- Four started from identical seeded drafts. These isolate the refinement path
  more closely, although the drafts are sparse synthetic fixtures.
- Two only repeated reviews of unchanged strategies. They are controls, not
  additional generated-output pairs.

All paired RFE descriptions and comments match after ignoring terminal
whitespace. The four starting drafts match exactly. Both archives contain the
same 321 Markdown/reference-identity files in the frozen architecture context.
The two review-only strategy bodies are identical across models.

Before reading the strategy pairs, I fixed five criteria: RFE coverage and
scope, technical grounding, implementation detail, testability, and operational
failure behavior. A preparation script assigned A/B independently for each
pair, removed frontmatter and duplicate imported RFE text, and withheld model
labels, pipeline scores and role reviews. The 16 candidate bodies and their
source hashes were retained. Criterion ratings and preferences were frozen
before revealing the mapping. Original source files were never edited.

This was a model-label-masked assistant pass, not a fully blinded human study.
I already knew the run-level outcomes, writing style can reveal a model, and I
did not repeat reversed presentation orders or calibrate against human labels.
The exploratory 0–2 criterion ratings remain in the private evidence; they are
not quality percentages or substitutes for the concrete findings below. A
second look at selected pipeline reviews occurred only after the freeze.

## The eight comparisons

| Source RFE | Subject | Path | Preference | Main reason |
| --- | --- | --- | --- | --- |
| 11 | Workbench culling exemptions | Fresh + refine | 5.5 | Defines policy precedence, validates requester identity, rechecks current policy, and distinguishes temporary Events from durable audit history. |
| 12 | Pipeline artifact retention | Fresh + refine | 5.5 | Accounts for shared artifacts and cache invalidation, constrains deletion to managed storage, and isolates maintenance from the run path. |
| 13 | Scheduled feature materialization | Fresh + refine | 5.5 | Keeps feature-view identity and progress in the registry, and addresses concurrent registry writes, credentials and existing schedules. |
| 14 | Canary rollback | Fresh + refine | 5.5 | Catches the difference between Knative revisions and Standard-mode canaries; makes the actual serving path a prerequisite to verify. |
| 15 | Model Registry archive guard | Same draft + refine | 5.5 | Adds a real freshness signal, explicit server-side override authorization and client-path coverage; identifies cross-namespace disclosure risk. |
| 16 | Queue position and pending reasons | Same draft + refine | 5.5 | Accounts for borrowing, avoids a second admission calculator, and defines user-scoped visibility and degraded behavior. |
| 17 | Connection credential rotation | Same draft + refine | 5.5, with major gaps | Fits the existing Secret-based connection path better; avoids assuming atomic writes across PostgreSQL and Kubernetes. Neither design proves safe revocation. |
| 18 | Evaluation comparison export | Same draft + refine | 5.5 | Selects a supported job/provider, defines provenance and missing-value rules, uses an allowlist, and avoids a second backing-store authorization boundary. |

That is four preferences out of four fresh cases and four out of four
same-draft refinements. These are eight related tickets from one batch pair,
not eight independent model trials.

## Examples that decide the comparison

**Canary rollback:** the frozen architecture overlay says RHOAI uses
Standard/RawDeployment mode, without Knative revision-based rollback. Standard
mode's Gateway API canary support is newer and less mature. The 4.6 strategy
assumes baseline revisions and working traffic shifts; 5.5 calls out the mode
difference and requires validation of the actual fork and routing path. There
is also a direct internal contradiction in 4.6: its proposed absolute traffic
steps are 10, 25, 50 and 100, but its validation rule requires the steps to sum
to 100. Those numbers sum to 185.

**Retention:** 4.6 selects old completed runs and deletes their artifacts,
without establishing whether another unexpired run consumes the same cached
artifact. The 5.5 design adds that protection and requires deleted outputs to
be treated as cache misses. These are consequential data-loss and execution
failure cases, not differences in prose style.

**Queue visibility:** 4.6 treats a request above a ClusterQueue's nominal quota
as unable to fit. The frozen Kueue reference explicitly includes borrowing and
Cohorts. A request above nominal quota can therefore still be admitted. The
5.5 version accounts for borrowing and keeps admission classification tied to
Kueue's own results. It also notices conflicting namespace-label documentation
instead of silently selecting one label.

**Evaluation exports:** 5.5 names the lm-evaluation-harness adapter and its
missing provenance as actual work. It defines configuration fingerprints,
metric units, availability markers and allowlist serialization. The 4.6 version
leaves provider support open, proposes copying all evaluation settings, and
adds MLflow enrichment without specifying authorization of the backing reads.

## Better content still needs corrections

The credential-rotation case is the clearest shared problem. The 5.5 design
labels workbench adoption as inferred from container start time, then allows
adopted-or-verified consumers to satisfy "Ready to revoke". Timing alone does
not prove consumption of the exact credential revision, especially through
cached or derived Secrets. Keep inference separate from verified adoption and
require revision-bound evidence before declaring safe revocation. The 4.6
design has the same basic false-adoption risk.

Both credential designs also overstate their privilege model. The 4.6 text
suggests label-scoped RBAC and etcd encryption as protection for PostgreSQL
staging data. The 5.5 text treats PartialObjectMetadata reads as though they
establish separate Secret-data permissions. Metadata selection is response
content negotiation; that alone does not create an authorization boundary.
This conclusion follows from the documented [metadata API](https://kubernetes.io/docs/reference/using-api/api-concepts/#metadata-only-fetches)
and [RBAC resource rules](https://kubernetes.io/docs/reference/access-authn-authz/rbac/#referring-to-resources).

Other 5.5 follow-ups remain:

- **Feature schedules:** define whether an overdue run is delayed, coalesced or
  skipped. A CronJob deadline can expire; Forbid alone does not guarantee a
  queued run. Define interval semantics and make every entry path obey the
  same single-view lock.
- **Retention:** rechecking the registry narrows, but does not close, a race
  between registration and deletion. Pinning and newly created cache references
  need equally explicit safety rules.
- **Archive guard:** a database transaction alone does not establish the
  necessary isolation or locking against concurrent serving-state updates.
- **Queue reasons:** position and available quota do not establish that a
  higher-priority workload caused a wait. Preserve unknown when the scheduler
  evidence cannot establish the cause.
- **Canary rollout:** the serving-route prerequisite remains unresolved. A
  post-freeze reference check also confirms that the namespace Prometheus proxy
  and Thanos are distinct paths; the strategy conflates them. The controller's
  metrics identity and permissions need an explicit contract.

The post-freeze checks add caveats to the initial ratings. They do not change
the pairwise preferences, and the original frozen ratings remain available.

## Why more revisions do not mean worse strategies

The pipeline approved nine strategies with 4.6 and five with 5.5. Those counts
mix different generated content with different reviewing behavior. They are
not an independent content-quality measure.

The unchanged controls help separate those effects. The drift-alert strategy
is byte-identical in body across runs, but its pipeline score drops from
6/8 (approve) to 4/8 (revise). The unchanged training-recovery strategy drops
from 4/8 to 3/8, both revise. The RFEs and architecture-reference sets also
match. At least some of the change is therefore evaluation behavior or
variation, rather than deterioration of generated strategy text.

In this pair, the independent content preferences favor 5.5 even though its
own pipeline approves fewer strategies. Several of its remaining concerns are
real. We should preserve those findings rather than tune the gate to reproduce
4.6's approval rate. This assessment does not change the user's numeric-only
approval policy or establish a calibrated difference between reviewer models.

## Evidence and cost

Separate private evidence:
`var/run-data/strat-workflow-hardening/content-judge-opus46-vs55-20261018/`.
It holds the preparation script, masked pairs, shared drafts/RFEs/comments,
source mapping and hashes, frozen judgments, unmasked comparison, post-freeze
pipeline scores, reference checks and checksum manifest. Original run archives
and benchmark verdicts remain unchanged.

No new pipeline, relay inference request or external judge run was launched.
Additional provider spend is $0. This Codex conversation's own model usage is
not captured by the benchmark meter and is not included in that figure. This
was not an agent-eval-harness execution or a repeated multi-judge experiment.
