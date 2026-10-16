# Ten-ticket S1 Opus run: review capture rejects repeated verdicts

## Outcome

Run markov-run-fbc62d49 used Breadboard 0359a9a, Fullsend fork candidate
6a05210, claude-opus-4-6, ten distinct RFEs and Workflow cap ten, one iteration.
The Kubernetes model container ran 19:39:06–20:30:30 UTC on 2026-10-15,
51m24s, and exited 1. Native Workflow wf_de5c4dad-f4d failed after 44m47s;
Claude's outer CLI exited 0. The host validator rejected partial business
completion and prevented the post-script from publishing the batch bundle.
Markov completed its orchestration and recorded a failed benchmark result;
Markov completed does not mean the underlying model job passed.

| Work | Result |
| --- | --- |
| Strategy creation | 10/10 |
| Refinement and push | 10/10 |
| Numeric scoring | 10/10 |
| Role reports delivered to callers | 40/40 |
| Role reports captured for composition | 38/40 |
| Final reviews recorded and published | 8/10 |
| Lock cleanup | Exit 0; all ten claims released |

RHAISTRAT-3 and RHAISTRAT-7 have no final published review or review provenance.
Both scored 7/8, approve, but completion correctly requires the reviewer reports
and publication evidence as well as numeric scores.

## Cause

RHAISTRAT-3's feasibility reviewer returned an 8,564-character assessment with
`**Recommendation**: revise` in its opening summary and conclusion.
RHAISTRAT-7's 7,878-character testability assessment gives the recommendation
before its requested changes and repeats it as the final line.
Both occurrences agree. The live review-composition parser requires exactly one
recommendation line and rejects the second occurrence. Those reports therefore
never become feasibility.json / testability.json in their respective sessions.
Composition and publication stop; record-review cannot create the missing
provenance. The workflow rejects the callers' approve/needs_attention=true
receipts and its final completion check throws:
`result: business completion not verified (failed, check 1)`.

Replaying the current report_verdict function on both unchanged archived bodies
reproduces the error. Removing only the duplicate identical line in memory
makes both pass as revise. This did not change any saved report or result and
used no inference. The parser needs to tolerate repeated agreeing decisions
while rejecting conflicting or missing decisions, preserving original text.
[Bug](../bugs/fixed/strat-review-duplicate-recommendation-capture.md).

The Skills include Recommendation in their output template and also instruct
the reviewer to end with exactly one Recommendation line. That does not clearly
state the parser's stronger requirement of one occurrence anywhere in the
entire body. The two observed reports end with the required line, after an
earlier agreeing verdict. Prompt ambiguity likely contributed; the agent's
internal reason is unverified. Clarify the full report layout as well as making
decision extraction tolerate agreeing repeats.

Further native-trace inspection found no explicit planning to repeat the verdict
in the two producing reviewers' recorded reasoning. Their agents are
ae6f7f8cdac0287f0 and ab8e7bc014b1a1cf0; the matched API response files are
be2c94b4-f2ff-4dd5-abb6-931c712a0f77.response.json and
5166be71-0ba4-4c1c-b573-cbb3a19ab638.response.json, whose thinking is redacted.
The receiving Workflow agents do explicitly diagnose the duplicate lines after
the hook failure. That post-failure diagnosis should not be treated as evidence
that the producing reviewers intentionally chose to repeat the verdict.

The historical benchmark additionally rejects feasibility bodies for
RHAISTRAT-2, -4 and -10, although the live hook captured and composed them.
This repeats the [numbered-findings false negative](../bugs/open/strat-review-gate-numbered-findings-false-negative.md).
The run still genuinely failed because two final reviews are incomplete.

## Runtime and provider observations

The ten refinement agents started together at 19:51:18 UTC. Scoring/review uses
the ten-worker Workflow pipeline, while each ticket's four reviewer Skills
remain serial within its caller. Reviewer fan-out optimization stayed deferred.
Nothing here isolates the effect of batch size from concurrency; both changed.

Relay export contains 949 Opus streaming generation records and 146 Opus token
counting records. One streaming request returned 502 at 20:12:17 UTC; the other
1,094 Opus records returned 200. All forty role reports were nevertheless
delivered, and the terminal failures explicitly identify duplicate verdicts.
The shared project/time-window export also includes one successful nonstreaming
Haiku 4.5 generation record near startup; its origin is not attributed by this
audit. The job's captured requests and native Workflow agents use Opus, so that
separate record should not be silently counted as an Opus workflow request.

The outer CLI's zero exit again does not establish native or business success.
The explicit completion guard and independent host validator correctly fail
closed. The cleanup record and archived Jira readback both confirm that all ten
RFE processing and owner labels were removed, including the two unfinished
reviews. No paid retry, resume or second run was submitted.

## Archive

Final capture under var/run-data/strat-workflow-hardening/:
fullsend-vertex-opus-ten-rfe-c10-20261015/markov-run-fbc62d49/20261015T203122658615Z.

The collector and detached observer independently verified 10,935 files /
20,472,635,632 bytes, complete/final, no capture-source errors. Final receipt
published; independent observer confirmation at 20:47:46 UTC. Includes 1,898
API body files, 7,392 syscall trace files, native state/journal/transcripts,
prepared inputs/progress, all retained artifacts, Kubernetes resources/logs,
Jira/MLflow/Observatory snapshots, context, source and relay telemetry.

Launch context and observer result are retained beside the capture. Historical
FAIL results and archived files remain unchanged.
