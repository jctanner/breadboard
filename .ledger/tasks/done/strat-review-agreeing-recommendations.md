# Accept repeated agreeing reviewer recommendations

User authorized this fix after the ten-ticket Opus run exposed two reports
whose identical revise recommendations appeared twice. Accept agreeing repeats
in live capture, composition and trusted host verification. Preserve original
report text, hashes, role attribution and the numeric-only approval policy.
Missing, malformed or conflicting recommendations must remain failures; only
architecture may use skipped. Keep the historical failed run unchanged.

Work in checkouts.tmp/jctanner-fullsend-ai/strat-creator on
feat/s1-workflow-hardening, initially clean at 6a05210. The plugin helper and
scripts/review_composition.py are identical regular files; update both.
Apply the same agreement rule in Breadboard's independent review_assessment
benchmark classifier. Keep the unrelated numbered-findings issue separate.

- [x] Regression checks cover agreement, conflict and original-byte preservation.
- [x] Both unchanged archived failing reports pass the repaired parser.
- [x] Required repository unit checks and diff checks pass.
- [x] Bug and plan record the local fix and validation.

Use local checks and archived evidence; no model inference or benchmark rerun
is needed. No remote push or Markov source-pin change is part of this task.

[Bug](../../bugs/fixed/strat-review-duplicate-recommendation-capture.md).

Status: done. The subsequent mixed-state execution authorized publication:
strat-creator fbc335bedb4a4eb97265da89d36bc29009a41fde is pushed on
feat/s1-workflow-hardening. The mixed-state tier uses that pin; historical
pins and archived failures remain unchanged.

Both helper copies accept one unique valid verdict across repeated fields and
preserve original report bytes/hashes. Invalid, missing and conflicting values
still fail; architecture-only skips and numeric-only approval remain enforced.
The independent benchmark checker now accepts agreeing repeated decisions too.

Validation: 47 composition tests; unit suite 575 passed / five skipped; full
suite 1,033 passed / seven skipped (265.78s); all 79 benchmark tests pass with
offline Markov execution. Changed component files pass Ruff. Both repositories
pass git diff --check. All forty archived reports pass the live parser, and
both formerly blocked reports pass the plugin helper, host helper and benchmark
classifier unchanged. Original failed run remains failed; unrelated benchmark
numbered-findings false negatives remain tracked separately.
