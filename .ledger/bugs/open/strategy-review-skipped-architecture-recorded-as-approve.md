# Skipped architecture review recorded as approve

## Evidence

Batch 2057/job 4000, strategy RHAISTRAT-4 (2026-10-07 UTC): optional
architecture-context fetch returned HTTP 403; prose architecture check skipped.
At 02:03:54 the agent reported schema requires approve/revise/reject, and chose
approve because numeric scorer assigned architecture 2/2. It then persisted
reviewers.architecture=approve despite the skipped contextual check.

## Impact

An overall approve / 8/8 result does not establish a completed architecture
context review. Missing context and an unperformed criterion are obscured in
structured reviewer verdicts, even if prose mentions the limitation.

## Expected

Preserve missing-context/skipped evidence explicitly and prevent it from being
reported as a completed contextual approval. Align schema, review skills and
publication projections; decide how missing required context affects gates.

## Status

Open; discovered during user-authorized logging batch test. Do not silently
change this run's review outcomes or claim the architecture check was completed.

Same behavior occurred in RHAISTRAT-5 at 02:14:19 UTC: architecture=skip was
rejected, replaced with approve as "skipped = no concerns". Other prose
criteria request revisions. Preserve the actual final recommendation separately.

Update 2026-10-07: the missing context is explained by the
[sandbox Git fetch denial](fullsend-sandbox-architecture-context-git-fetch-denied.md),
fixed in strat-creator `3fd1563`. Pipeline 2067/job 4021 also ran
`/strategy-review RHAISTRAT-8` after the same failed fetch; its verdicts
were not inspected here. The fetch fix does not make earlier reviews valid. This
schema bug stays open: a fetch failure must still be reported as a skipped
check, never as approve.
