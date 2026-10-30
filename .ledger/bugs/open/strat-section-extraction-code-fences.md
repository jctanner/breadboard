# Strategy and TLDR extraction stops at headings inside code fences

Medium availability issue, pre-existing. extract_strategy_section and
extract_tldr_section in scripts/push_strategy.py use heading regexes without
tracking fenced code blocks. A valid Strategy with a `## ` shell comment can
be truncated inside its fence; a TLDR with a `### ` line has the analogous
attachment-stub problem.

Opus 5.5 identified this while checking PR93 SME preservation. Both authored
emulator cases reproduced: encoded ADF swallowed the later SME section even
though the Markdown-only SME check passed. The managed publisher now checks
the exact normal/stub ADF against current live SME input before any remote
description or attachment write. Both cases refuse safely and preserve Jira.
Valid fenced examples can therefore fail the run; the parser still needs a
separate fence-aware extraction repair. This guard prevents silent SME loss
and prevents the publisher from manufacturing change-history evidence.

Evidence: /tmp/strat-pr93-adf-red.log and
/tmp/strat-pr93-adf-final-focus.log; two encoded_sme cases in
tests/test_pr93_host_proof.py. Final static review confirms the guard closes
both paths. No real Jira was affected. Related task:
[PR93 repair](../../tasks/done/strat-pr93-host-proof-and-human-gate.md).
