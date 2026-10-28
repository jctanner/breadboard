# Assess the automated review on 73c454b

## Context

The attachment reconciliation repair was committed and pushed as `73c454b`.
Remote CI passes. A subsequent automated review requests changes:
[review 5621646395](https://github.com/fullsend-ai/strat-creator/pull/85#pullrequestreview-5621646395),
submitted October 22 at 22:29:35Z. Complete discussion export now has 148 entries:
18 regular comments, 35 reviews and 95 inline comments. Nine new inline findings
are listed below. The owner subsequently requested the three concrete repairs;
those are now implemented, tested and published as 0707b5b in
[the repair task](../done/strat-pr85-three-review-fixes.md). No paid smoke.

## Already decided: Org Pulse verification

The owner reaffirmed that Org Pulse certificate and hostname verification
remain disabled for now. Repeated review comment
[4354198471](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198471)
is an accepted temporary exception, excluded from active fixes and smoke-test
blockers. Permanent CA trust is a future follow-up.

The separate Jira review publication finding concerns checking published review
comments, attachments and verdict labels after agent completion. It does not
concern Org Pulse TLS or hostname verification.

## Findings to assess

| Comment | Concern | Disposition / next action |
| --- | --- | --- |
| [4354198477](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198477) | Jira review publication readback | Reproduced and repaired in 0707b5b. Trusted host calls the existing read-only publication verifier; ten regressions cover both numeric verdicts and missing/changed summary, newest attachment and conflicting labels after recording. Unrelated to Org Pulse verification. |
| [4354198483](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198483) | Frontmatter with `---` in a title | Reproduced and repaired in 0707b5b with the shared parser. Six regressions cover artifact/local metadata and actual root/bundled hook subprocesses. |
| [4354198490](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198490) | Credential-bearing recovery pathnames | Reproduced and repaired in 0707b5b. Names are checked before export, errors omit filenames/tracebacks, and the actual CI wrapper drops unsafe generated output while preserving private recovery and cleanup. Seven new regressions pass. |
| [4354198495](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198495) | Runtime pin affects human plugin sessions | Exact version pin is deliberate and already documented in the human review guide. Assess the local-plugin tradeoff against the qualified hook/transcript adapter; do not silently relax the runtime gate. |
| [4354198499](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198499) | Bundled plugin duplication | Check existing documented stopgap and mandatory parity tests; track eventual removal separately rather than redesigning now. |
| [4354198505](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198505) | Reviewer enum documentation | Check schema and current docs for `pending` and architecture-only `skipped`, then fill a concrete documentation gap if needed. |
| [4354198511](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198511) | Owned-lock cleanup documentation | Current Fullsend README already documents refusal and owner-aware cleanup. Check whether shared CLI/root docs need a pointer; preserve foreign-owner refusal. |
| [4354198515](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4354198515) | Shared helper exceptions/clone marker documentation | CLAUDE.md already describes read-only retries, uncertain writes and clone-marker semantics. Check public helper docs before adding duplicate text. |

The rollup repeats the protected-path/authorizing-issue process finding. The
owner's public scope comment remains the authority; do not fabricate an issue
or approval. Qodo currently reports zero bugs/rule violations/cross-repo conflicts.

## Acceptance

- [ ] Reproduce and disposition relevant new findings against current source.
- [ ] Implement bounded repairs with offline regression coverage if confirmed.
- [ ] Preserve owner decisions, numeric-only approval and current architecture.
- [ ] Complete required full suite before any further code push.
- [ ] Archive evidence and record limitations before the live smoke.

## Evidence

Publication receipt, complete discussion, cleaned current review and staged
credential scan are at
`var/run-data/20261022-strat-pr85-attachment-fix-publication/`.
Prior tested source and 1,238-pass suite remain sealed in
`var/run-data/20261022-strat-pr85-post327-review-followup/`.

Remote tests run 39863368000, Unicode 39863368077 and DCO all pass on `73c454b`;
Fullsend review run 39863365462 completed successfully as a review execution,
but its reviewer requested changes. The empty legacy combined-status API says
pending despite the completed check runs; this is not a failed CI test.
