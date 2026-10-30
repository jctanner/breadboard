# October 29 scheduled Workflow batch qualification

## Result

Native schedule 4222905 launched pipeline **3006130966** at 22:05:32 UTC
(6:05 PM New York). Workflow job **17591617217** passed in **48m04s**, finishing
at 22:54:53 UTC. Parent pipeline passed at 22:54:56 UTC; downstream dashboard
pipeline **3006261958** also passed. Input check and Python tests passed.
No extra run or retry was launched while checking results.

Source receipt identifies upstream main **987a2005e1bac1e4282b01961e77cd46499ae388**,
Fullsend 0.47.1, claude-opus-4-6/high, concurrency ten, one iteration. Native
metrics report $29.0947765 estimated model cost. Retain that as reported
telemetry, not an independently reconciled invoice.

Five RFEs were discovered, four acquired. RHAIRFE-1535 was skipped because
its linked RHAISTRAT-2405 was already approved. Three existing strategies
resumed at refinement; RHAIRFE-3803 started at creation.

| RFE | Strategy | Numeric gate |
| --- | --- | --- |
| RHAIRFE-896 | RHAISTRAT-1141 | Approve |
| RHAIRFE-3226 | RHAISTRAT-2636 | Approve |
| RHAIRFE-3516 | RHAISTRAT-3029 | Approve |
| RHAIRFE-3803 | RHAISTRAT-3084 | Approve |

The native completion receipt reports four completed/reviewed strategies,
zero errors and zero input-change deferrals. Workflow and lock-release exits
are both zero. Read-only post-run checks confirm the published pair inventory
matches all four acquired RFEs, each live STRAT has its correct clone link
and rubric-pass label, review comments exist, and dashboard publication passed.
Numeric scores remain the approval policy; this is not independent content
judging or human sign-off.

## Scope of qualification

The merged normal/resume path passed a real scheduled GitLab + Fullsend +
OpenShell batch and publication. No live input-drift deferral occurred, so
this run does not directly exercise PR93's input-change race. Those cases
remain covered by the archived fault tests. Jira snapshots were taken after
the run, not before it. Do not claim the run processed ten RFEs: ten was the
cap, four was the actual acquired workload.

## Cleanup and evidence

Removed only the temporary schedule executor override at **00:02:31 UTC
October 30 / 8:02 PM October 29 New York**. Readback confirms inherited legacy,
unchanged owner/ref/cron/source/batch cap and next midnight occurrence.
[Cleanup receipt](restore-strat-schedule-legacy-20261029-evening.md).

Evidence: `var/run-data/20261029-real-gitlab-evening-workflow-batch/`, including
native artifact ZIP, Claude transcripts/debug/OTel and sandbox logs as captured
by Fullsend, GitLab logs/status, exact source/metrics/result receipts, Jira
snapshots/comments/attachments, published data and dashboard job logs.
`verification.json` records the independent post-run checks and limits.
Archive hashes verified for **130 files plus manifest**; configured credential
scan found zero matches, including decompressed native ZIP members.
Raw API dumps, syscall traces and separate MLflow capture were not configured
on the upstream runner; the availability receipt states that explicitly.
Rollback evidence: `var/run-data/20261029-strat-workflow-evening-rollback/`,
ten files plus verified hash manifest, configured credential scan zero.

## Committed publication audit

At 2026-10-30 00:06:55 UTC, a read-only audit of data repository main commit
**b78befbc4f366fb30ace9bd46ae5c00075ed3651** confirms the run directory has
exactly **51 files**: the 48 completion artifacts, generated pipeline-data and
HTML report, and publication manifest. Every remote Git blob ID matches the
archived bytes; all 50 publication SHA-256 entries and 35 provenance hash
references match. No missing or unexpected files.

Inventory includes four refined strategies, sixteen specialist reviews, four
combined reviews, four scorer reports, four review comments, four provenance
files, eleven source snapshots and the batch table. STRAT/RFE frontmatter
and provenance identities match each completed pair. Both live summary.json
and summary-production.json include this run with four reviewed/approved
strategies. This verifies publication integrity and identity, not a fresh
assessment of strategy quality.

Audit receipts: `var/run-data/20261029-strat-data-publication-audit/`.

## Content inspection, separate from publication integrity

Read the four strategies' technical approaches, acceptance criteria, risks,
open questions and SME sections, plus reviewer conclusions and dissent.
All four task and four combined-review frontmatters validate against the
local repository schemas. The SME text on all three existing strategies is
unchanged after whitespace normalization against its saved original. The
four subjects remain distinct; no obvious cross-ticket topic substitution
was found in the inspected text. This is editorial inspection, not an
independent source-code validation of every architecture claim or a new
paid content-judging experiment.

- **1141 / Python index:** Concrete CR/watch/config-file/env/CA/lifecycle plan,
  testable disconnected scenarios and explicit SME decisions. All four
  specialist recommendations approve, with remaining concerns retained.
  The strategy explicitly identifies Product acceptance needed for the RFE's
  individual-override criterion, since SME direction chooses global precedence.
- **2636 / coexistence:** SME scope narrowing and specific route ownership,
  upgrade and same-name collision checks are represented. Three reviewers
  request revisions concerning conditional sizing, handoff evidence and test
  criteria. A separate direct-reading finding: G4 universally forbids matching
  Workspace resources while describing valid Workspace webhooks, rather than
  forbidding cross-generation matching. [Content bug](../../bugs/open/strat-coexistence-webhook-criterion-wording.md).
- **3029 / CSP:** Detailed directive set, two serving paths, browser capture,
  dev-policy derivation and enforcement tests follow the SME direction.
  Testability reviewer still requests CI-feasible telemetry/throttle checks,
  an iframe-fallback criterion, invalid-mode behavior and deep-link coverage,
  despite the independent numeric scorer assigning 8/8.
- **3084 / OpenChamber:** Coherent validation/community-deliverable scope and
  explicit gateway/client support boundaries. The least settled execution
  plan: basic client compatibility remains an assumption, the version/model/
  deployment matrix is unspecified, and reviewers request streaming/SSE,
  browser-mode CORS/credential handling and additional failure cases.

Numeric scores remain the chosen sole gate: 1141 approves 6/8 with unanimous
specialist approval; 2636 approves 7/8 with three revise recommendations;
3029 approves 8/8 with one revise; 3084 approves 6/8 with two revise. The saved
Disagreements sections preserve these differences. Do not equate rubric-pass
with unanimous readiness. Strategy files are roughly 3,200–6,400 words and
combined reviews 6,100–7,600 words each; repetition and raw reviewer lead-ins
make the audit trail more cumbersome to read than the structure implies.

Assessment: credible, useful drafts for SME review, with concrete unresolved
items; successful orchestration/publication does not guarantee content quality.
No source/artifact/Jira mutation or additional model call for this inspection.
