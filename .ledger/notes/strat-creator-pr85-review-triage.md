# PR 85 review triage against retained tests

2026-10-16. Review comments exported to /tmp/strat-creator-pr85-comments.txt.
Assessed feature head f5691f7. No model calls, PR responses, review dismissals
or component code changes were made for this assessment.

## Disposition

One clear rebuttal: 4295376653 says the top-level schema restriction lacks an
observed source. The original Opus run markov-run-687db37c has four agent errors
in native wf_03ee11ea-2e4:

```text
API Error: 400 tools.9.custom.input_schema: input_schema does not support
oneOf, allOf, or anyOf at the top level
```

The comment is about tool input schemas sent by the tested endpoint. General
structured-output JSON Schema support does not overturn that observed rejection.
Keep the implemented plain-object schema and cross-field checks; add the exact
error/source to the code rationale. This does not assert every provider has
the same restriction or require removing successfully accepted nested features.

4295376627 needs a factual correction, not wholesale dismissal: actual native
2.1.296 controls observed the forked Skill hook payloads and StructuredOutput
hooks. The documented probe captured twelve Skill events; real native controls
blocked invented outputs. The live mixed run captured all 36 reports and
matched their receiving tool results, provenance and composed text. This is
empirical runtime evidence, not just invented unit-test input. Requests for
sanitized checked-in event fixtures and pinned-runtime qualification remain
reasonable, and undocumented behavior still creates a version dependency.

4295376550 overstates review-only failure as universal: two real review-only
imports completed in the mixed Opus run. Its underlying round-trip concern is
valid. An independent local probe with HTML comments and a list adds six blank
lines through markdown_to_adf/adf_to_markdown and changes strategy()'s proof.
The fixture's successful cases do not qualify all imported or oversized bodies.

## Important correction to the successful-run interpretation

Run markov-run-5d3327ed has a valid completed business result and passed host
validation. It also contains runtime workarounds and missing hook enforcement:

- All nine review callers first received the outside-repository scorer error.
  There are twelve rejected begin calls across those nine agents. Each caller
  copied the scorer result into repo/tmp/strat-assess/<KEY> and retried begin.
  This confirms Qodo 4283079900; success did not repair the source contract.
- All nine scorer agents lack Bash and executed no shell preflight. Their
  transcripts show scoring proceeding despite the required check-only command
  being unavailable. This confirms 4295376508; these fresh reviews do not test
  that scorer recovery branch.
- The refinement StructuredOutput hook process 2664 began at 14:10:26.986711Z
  and was killed at 14:10:36.977960Z, 9.991249s later. The final completion hook
  process 5901 began at 14:32:21.645266Z and was killed at 14:32:31.626709Z,
  9.981443s later. Both SIGTERM signals came from primary Claude PID 151.
  Both hooks have timeout=10; execution continued. Only the earlier initial
  refinement audit exists; the reconciliation and completion audit receipts
  were not written. This supports 4295376534 on the tested 2.1.296 runtime,
  irrespective of the separate older-image deployment issue.

Source/trace evidence is under the mixed run's immutable archive. Guard trace
filenames end in .2664 and .5901; source paths are the bundled plugin guard
scripts. The host independently checked final work, so these findings do not
invalidate the saved completion result. They invalidate a claim that this
successful job proves every guard ran or that only external checker work remains.

## All inline comments

| Comment ID | Topic | Assessment |
| --- | --- | --- |
| 4283079900 | Outside-repository scorer path | Retain. Observed in all nine review callers; model staged files and retried. |
| 4283079907 | Skip-only publication lacks pipeline data | Retain. Local empty extraction exits zero without output; mixed processing does not test all-skipped publication. |
| 4283079918 | Recovery can lack score file | Retain. Source requires the file after a branch that skips generation; no successful batch exercises that interruption. |
| 4283079924 | Owner sidecar prevents state-directory reuse | Scope qualification. Documented deployment uses a new mktemp state dir per run; reuse with a new owner is outside that contract. The leftover sidecar is real. Human review already acknowledges this. |
| 4283079931 | Jira ADF normalization and equality | Needs production/normalizing-response qualification. Exact comparisons exist; emulator success cannot rebut this. Avoid normalizing away meaningful attrs such as links. |
| 4295376508 | Scorer cannot run shell preflight | Retain. All nine live scorers executed no Bash. |
| 4295376515 | Incomplete review/provenance poisons recovery | Retain. Source verifies any existing review file; a crash after apply_scores is outside the successful batch's coverage. |
| 4295376522 | Pinned Fullsend runtime differs | Retain. Benchmark captures say 2.1.296; harness image is documented as 2.1.286. Fullsend/OpenShell was not used in these jobs. |
| 4295376534 | Live verification exceeds hook budget | Retain, with stronger evidence. Two actual critical hooks were terminated at about ten seconds and execution continued. |
| 4295376541 | Failed-receipt guard contradicts retry instructions | Retain. Blocking failed same-run relaunch was intentional; prompts/feedback/iteration policy still describe that relaunch. Passing run does not test this failure contract. |
| 4295376550 | Review-only import hash and round trip | Qualify always-fails claim; retain defect. Two imports passed, but local complex-body round trip changes the proof. |
| 4295376556 | Interrupted source cleanup breaks publication recovery | Retain as source-supported interruption gap; successful cleanup does not cover a partial-delete restart. |
| 4295376565 | Reused push misses live published read-back | Retain as source-supported. Current-run pushed marks are checked live; reused push loop checks local proof without the equivalent published read-back. No concurrent Jira edit was injected. |
| 4295376573 | CRLF capture/compose/verify mismatch | Retain, locally reproduced: capture and compose succeed; verify raises Exported report attribution/content disagrees. |
| 4295376586 | Dry-run telemetry marked production | Retain as source-supported; prepare_publication does not pass validated dry_run and removes agent-result before extraction. Paid run was not dry-run. |
| 4295376600 | Test scripts copy all user native state | Retain. Scripts default to ~/.claude and copy projects/tasks. Isolated benchmark jobs do not establish developer-machine capture scope. |
| 4295376611 | Copy drift/new tests omitted from unit target | Retain. Named parity test compares four files, unit target omits new suites. Full make test ran, so full-suite evidence remains valid. |
| 4295376627 | Hook shapes not runtime-observed | Correct factual premise. Real native probes and live capture exist; retain request for sanitized fixtures and runtime pinning. |
| 4295376640 | SubagentStop ignores active stop hook | Retain as source-supported failure-path concern; normal successful stop does not test repeated exception/re-entry. |
| 4295376647 | Old smoke stubs violate current format | Retain. Stub says Verdict without required target/Recommendation; this opt-in paid smoke test was skipped by the full suite. Other live tests do not make this fixture pass. |
| 4295376653 | Schema restriction has no observed source | Rebut. Retained real Opus 400 errors explicitly name top-level oneOf/allOf/anyOf. |

The review summary also mentions DCO, the PR body and installer ownership of
.fullsend/config.yaml. Benchmark results do not answer those process/deployment
concerns. No broad rejection based on model-job success is warranted.

## Local verification performed

Read archived review/scorer journals, native versions, completion/checkpoint
receipts and selected process trace lifetimes. Replayed the original provider
errors from native journals. Ran model-free complex Markdown round-trip,
CRLF capture/compose/verify and empty publication extraction probes. No source
or archived evidence changed. Full historical benchmark result remains intact.

## Authorized remediation

The user authorized PR dispositions and all relevant repairs after this triage.
Replies were posted on the schema claim (4297175847), the hook-evidence premise
(4297176077), and the universal import-failure claim (4297176309). Only the schema
thread was resolved immediately; the valid parts of the other two stayed open
for fixes. No broad review dismissal was made.

The repair moves score files into repository tmp/, runs recovery before
restricted scorers, separates local short-hook checks from live readback, blocks
Pre/PostToolUse hook timeout failures, aligns the image/runtime and terminal
failure contract, retains failure handoff, normalizes published import identity
and ADF readback, resumes partial cleanup, preserves CRLF bytes and dry-run
telemetry, bounds stop-hook correction, isolates test state, and updates fixtures
and parity/unit coverage. Installer-owned config is removed; the deployment
maintainer can register the three unchanged harness paths in the external fleet.

Native 2.1.296 controls passed refinement, composition, normal completion,
missing-report failure, post-completion reporting failure, scope isolation and
forced hook timeout cases. All use loopback mocks and zero provider calls.
The independent benchmark checker now accepts all 36 unique retained mixed-run
role reports; 97 benchmark tests pass with one optional test skipped. Historical
source pins, run archives and eval-result.json files are unchanged.

The original owner-sidecar comment is a contract qualification: a new run gets
a fresh state directory; reusing one under a different owner remains forbidden.
Old unsigned commits require a separate DCO/history decision. New remediation
commits will be signed off; no published history is silently rewritten.

Published remediation: f941955, with signed-off commit, 1,067 passing tests in
each required target (five/six optional skips), twenty follow-up responses and
all 21 original inline threads resolved. The remaining DCO history issue is
tracked separately. See [completed remediation](../tasks/done/strat-creator-pr85-remediation.md).

Historical DCO follow-up completed with user authorization: 15 signoffs added,
authors/dates/trees preserved, old tip backed up on the fork, feature branch
updated by exact force-with-lease to 18cdf46. GitHub DCO passes.
