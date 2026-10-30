# Leading SME section can be dropped by standalone push

Found while isolating PR93's split-bold history reproducer. An atypical Jira
description with SME input before the Strategy heading (including SME-only
drafts) can lose that section when push_strategy.py rewrites the RFE reference:
it slices updated_md from the Strategy heading and drops preceding sections.

The managed S1 push now validates the fully assembled outgoing SME section
against the actual live input before writing. Its regression confirms failure
without any Jira description mutation. Ordinary Strategy-then-SME layout works,
including formatting-only changes. Standalone human push retains its previous
behavior and needs a separate preservation repair for this atypical ordering.

Reproduction input: leading-sme fixture and
test_managed_push_validates_assembled_sme_before_writing in the strat-creator
checkout's tests/test_pr93_host_proof.py. The initial mixed formatting/layout
test at /tmp/strat-pr93-canonical-focus.log exposed the drop; the formatting-only
fixture was corrected to isolate the reviewer case from this separate layout
fault. Expected standalone behavior is to retain SME content regardless of
section order, or stop before writing. No live Jira affected.

Related: [PR93 repair](../../tasks/done/strat-pr93-host-proof-and-human-gate.md).
