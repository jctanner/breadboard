# PR93 host deferral proof and late human-gate isolation

Owner authorized repairing both latest Fullsend runtime concerns, then having
local Claude independently verify the result as in the previous round.
Start: clean feat/isolate-stale-batch-tickets at 13a4f71.

- Reproduce host acceptance of forged STRAT human/publication snapshots with
  unchanged Jira. Require independent host-anchored evidence for exclusions.
- Reproduce sign-off/needs-attention between push and label publication.
  Isolate only independently verified ticket changes; ownership, shared-input,
  unreadable and unrelated failures remain fatal.
- Add negative and positive regression coverage; full make test, lint and diff
  checks. No live Workflow smoke or schedule change authorized here.
- Run read-only local claude -p verification with explicit claude-opus-5-5, retain usage
  and findings, and assess them before completion. No GLM.
- Retain reproduction, tests and review evidence under var/run-data after
  credential scanning. Do not post PR comments or merge without instructions.

Source review/comments: /tmp/strat-pr93-review-refresh-20261028T154244Z/.
High discussion_r4402069815; medium discussion_r4402069824 on upstream PR93.

## Reproduction and implementation

Both concerns reproduced. Corrected exploit regression used the exact generated
completion: six forged human/publication cases were accepted by the original
host validator, and a seventh create-only case reported completion without
refinement/review. Evidence: /tmp/strat-pr93-host-proof-exploit-red.log. Initial
late-gate and combined-failure tests also failed before repair (15 failed,
one unrelated-error control passed; /tmp/strat-pr93-host-proof-red.log).

STRAT snapshot mismatches now pass through strategy_changed: they can detect
drift, but batch exclusion additionally requires independent evidence unless
the RFE already has a trusted deferral. Existing host-pinned Jira cursors prove
protected edits; a live blocking human gate with a unique Cloners link may
also prove current intervention, including a newly created STRAT. Recoverable
numeric verdicts do not count. Without proof, new/current/reverted STRAT
mismatches remain fatal, and docs state this conservative limitation.

HumanGateChanged subclasses ValueError; the push loop catches only this or
StaleTicket before independent exclusion reconciliation. check_owner verifies
unique acquired source and ownership before checking the STRAT human gate.
Concurrent ownership/link/source/unreadable/unrelated failures remain fatal.

Eighteen new regression cases cover forged staff, summary, priority, status,
gate and publication snapshots, unfinished creation, cross-RFE proof, our own
numeric verdict, late gates on existing/new STRATs and combined failures.
Focused run: 178 passed/one legacy unprepared-history fixture path failed;
that path was corrected and all 39 repair/history checks plus two added
controls pass. Final lint/type/schema checks pass.

Full offline suite (1,527 collected) and independent read-only Opus 5.5 review
are running against the same unchanged repaired tree. Paid Workflow smoke is
disabled. Review staging: /tmp/20261028-strat-pr93-host-proof/claude-review/.
Source-content fingerprints cover dirty tracked files and the new test file.
No source commit/push, PR comment, live Jira mutation or schedule change yet.

## Opus 5.5 findings and reproduced follow-up

First independent review completed in 466.91 seconds, CLI token estimate
$2.3537664, source unchanged. It confirmed both original reported paths fixed,
but found an old-gated-clone variant (high), pipeline-authored SME history
(medium, initially conditional), and the same late-gate race in review recovery
(medium). Five authored emulator regressions failed before their repairs.
The first full suite independently passed 1,521 tests/six skips in 825.55s;
retained as /tmp/strat-pr93-host-proof-first-full-test.log, not final-source proof.

The host now records existing clone gates/status and a successful complete
clone inventory. Current gate proof requires this run's create pair and a
unique live link, rejects active/completed clones, and compares pinned gates.
An unpinned STRAT must be absent from the successful host inventory. Forged
progress alone and forged create pairs both fail the old-gate reproducer.

Managed record and push reject artifact SME changes against actual live Jira
SME text, comparing canonical ADF to permit Markdown formatting round trips.
Standalone human push remains available. Review recovery catches only the typed
gate/stale exceptions and immediately verifies the affected RFE's deferral.
The old message-prefix catch is replaced by the exception type. Active-status
constants are shared with prepare_run. Existing journal/direct-credential trust
limits are now explicit; no malicious-agent containment is claimed.

Follow-up: 88 focused checks pass; 28 history/SME comparison checks pass; final
lint/type/schema and diff checks pass. Twenty-eight total added cases against
13a4f71. Final full suite and a necessary second Opus 5.5 verification are now
running on the final tree. The second review cap is $7.64, keeping aggregate
review caps within $10. Its prompt supplies the first report and asks for
verification of F1/F2/F3, the original findings and normal-helper paths.
Stage: /tmp/20261028-strat-pr93-host-proof/claude-verification/. Relative patch
paths are corrected in final captures; the original review capture is retained.

## Canonical SME follow-up

Second Opus 5.5 review: 411.79 seconds, CLI estimate $2.0674066. Original two
findings, F1 and F3 verified fixed. Remaining D1: semantically equal split-bold
SME could pass canonical write checking but count as a raw-string history edit.
Two regressions reproduced it; one fixture initially also exposed a separate
leading-SME layout loss. The formatting fixture now isolates normal ordering.

canonical_staff is shared by write validation, current SME comparison and
history evidence. Formatting-only content no longer causes a deferral; fresh
reviews are still required, and valid subsequent reviews allow host completion.
The fully assembled outgoing managed description is also checked, blocking
SME loss before any write in an atypical layout. Three exact controls pass;
earlier broad canonical run had 52 passes/one layout-related failure. Separate
standalone layout issue is tracked, with managed behavior protected.

Second full suite was interrupted on its old source after 849 passes/five
skips, 593.42s, to avoid mixing revisions; this is not final verification.
Its log is retained separately. A focused final Opus 5.5 check of D1 will run
under a $5.57 cap, keeping total review caps within $10. D2 is an accepted input
actor-attribution limit: inventory proves absence of a prior link, not entity
creation, and state-change proof does not establish a human actor. Docs and
code comments now state that distinction. No new actor service/credential.

Final exact D1 and assembled-payload controls: three passes. Managed push now
checks its fully assembled outgoing content, preventing the discovered leading
SME drop before writing. The standalone layout issue is tracked separately in
bugs/open/strat-push-leading-sme-layout.md. Thirty-one added regression cases
in total. Lint/type/schema pass. Final full suite and a narrow third Opus 5.5
check of the remaining D1 correction are running on the frozen final tree.
Stage: /tmp/20261028-strat-pr93-host-proof/claude-canonical-verification/.
Includes an incremental patch reconstructed from the exact previous reviewed
source; read-only source-content fingerprints are enabled. Prior review
reports and superseded test logs remain retained, not replaced as evidence.

## Exact encoded payload preservation

Third Opus 5.5 review: 226.64 seconds, $1.0704446 CLI estimate. It verified D1,
but identified B1: unbalanced fences produced by section extraction could pass
the Markdown check while encoded ADF swallowed SME content. Normal and TLDR
attachment cases both reproduced against the emulator. The pre-B1 full suite
passed 1,534/six skips in 857.98s; retained separately, not final-source proof.

_verify_managed_description now validates managed context and compares the exact
outgoing ADF's SME representation to a fresh actual Jira description. It runs
before normal PUT and before any attachment/stub mutation in the fallback.
The same canonical SME comparison is used throughout. All **89** focused
proof/history/attachment checks pass; lint/type/schema pass. Thirty-three new
cases in total. Final full suite and a narrowly scoped fourth Opus 5.5 check
are running, with aggregate review caps still below $10. Final stage:
/tmp/20261028-strat-pr93-host-proof/claude-adf-verification/.

## Completion

Final frozen-source full suite: **1,536 passed, six skipped**, exit zero,
872.91 seconds (14m32s), 1,542 collected. All 33 added regressions pass, as do
the existing integration/native controls. Final lint/type/schema and diff
checks pass. Final independent Opus 5.5 report confirms the exact normal and
attachment guards are closed with no concrete defects in that correction;
preceding reports verify the original findings and the other follow-ups.

Archive: **var/run-data/20261028-strat-pr93-host-proof/**, **96 files plus
manifest**, all copied hashes verified. All 31 files in the full pending PR's
working tree and the retained evidence passed configured-secret/private-key
checks with zero findings. Includes every review prompt/stream/report/usage,
before/after source fingerprints, complete and incremental patches, original
automated reviews, red/green logs, superseded runs, final verification and
assessment. Remaining-budget caps accounted for actual preceding review costs;
four reviews cost an estimated **$5.997457** in CLI list-price token accounting.

Changes are **local and uncommitted** on feat/isolate-stale-batch-tickets,
parent HEAD 13a4f71. No commit/push, public PR comment, merge, real Jira change,
paid Workflow smoke or schedule change. Merge/live qualification is separate.
Known actor/journal/CAS limits and the pre-existing fence/standalone-layout
follow-ups are explicitly recorded; they are not represented as solved.

Owner subsequently authorized publication: signed-off **17a684f** is pushed
and verified as PR93's exact head, with a clean component working tree and all
committed blobs matching this tested/reviewed source. DCO passed; other CI/review
checks started. [Publication receipts](strat-pr93-host-proof-publication.md).
No live smoke or schedule change.

Final Opus 5.5 static verification completed: **B1 closed on normal and
attachment paths; no concrete defects in this correction**. 113.93 seconds,
$0.5058394 estimate, source-content fingerprints unchanged. Across four
necessary verification calls after reproducing corrections: **$5.997457**
CLI-estimated list-price token cost. Original findings, F1/F3 and D1 were
verified in the preceding reports; all reports are retained. No claim of a
live Workflow smoke or actor attribution. Remaining full suite is pending.
The fence-aware extraction and standalone leading-SME layout issues are
tracked separately; managed guards prevent writes in those cases.
