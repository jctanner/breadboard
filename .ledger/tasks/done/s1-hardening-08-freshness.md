# S1 hardening 8: validate replay freshness

Track relevant input, instruction, Skill and source identity when saving reusable
phase results. Changed shared files must invalidate or explicitly reject stale
results, even when the original prompts/options still match.

Acceptance: unchanged inputs reuse valid work; changed inputs do not silently
reuse incompatible results. Record the chosen freshness contract.

Done, focused repair 2026-10-14. [Plan](../../plans/strat-workflow-s1-hardening.md).

Chosen policy: reject changed or unverifiable inputs within a run, preserving
artifacts and mutation intent. A later job may reuse refinement/push only with
matching provenance and live read-back; legacy or changed provenance falls back
to refinement. Native journal replay stays unsupported on the S1 entry path.
Validate with isolated local change/retry cases before considering inference.

Published local candidate `0e7e752`: host baseline, phase provenance, live input
and publication read-back, source/context checks before reuse/writes, strict
same-run refusal and verified later-job continuation. Loaded hook refuses native
journal replay. 990 component tests pass, seven skipped; three native
zero-provider controls independently verify from the finalized private archive.
Earlier fixture failures retained. Zero inference, no deployed reset or
historical pin change. [Contract and evidence](../../notes/s1-hardening-08-freshness.md).
