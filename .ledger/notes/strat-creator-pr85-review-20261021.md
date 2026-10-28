# PR #85 follow-up reviews, October 21

Fetched 116 entries (12 conversation comments, 31 reviews, 73 inline comments)
against unchanged head 02dd13b. The preceding export contained 91 entries;
25 entries are new. GitHub also updates historical inline diff metadata on
push, which does not make those old comments new findings. Full export:
/tmp/strat-creator-pr85-review-latest.txt.

Latest review 5604386129 and preceding reviews 5602871240/5589244425 contain
the following distinct requests. A reused finding ID describes two separate
cleanup failures; both are in scope.

| Finding | Latest comment ID | Disposition / planned validation |
| --- | --- | --- |
| Unknown dry-run values silently authorize live work | 4340475678 | Fix strict shared/pre-script parsing; malformed direct invocations make no Jira calls or target changes. |
| Identified skip-only runs omitted from history | 4340475694 (also 4339270279, 4328295557) | Preserve intentionally empty sealed publications; test actual publication through summary extraction. |
| Cleanup stops before later owned RFEs | 4340475707 | Attempt every recorded key, preserve outstanding record and foreign owners, then report failure. |
| Cleanup from target blocked by changed freshness | 4339270287 | Isolate owned release from pipeline work context; changed RFE/source must not prevent owner-verified cleanup. |
| Prepared import can retain missing Business Need | 4340475715 (also 4339270296) | Establish section structure before reconstruction, fail before replacing a task if the reference remains. |
| Concurrent summary retry republishes stale aggregate | 4340475723 (also 4339270302) | Regenerate after every successful synchronization; deterministic local Git race includes both publications. |
| All-provisional Org Pulse dry run crashes | 4340475733 (also 4339270308, 4328295562) | Return a successful diagnostic with no API call when filtering leaves no features. |
| Org Pulse consumer contract confirmation | 4340475743 (also 4339270317, 4328295569) | Consumer fix is merged as 7ba9353e in owner repo PR #1789; document primary consumer contract/evidence. Deployment remains unverified. |
| Docstring comma | 4340475749 (also 4339270322) | Fix punctuation. |
| Dry-run bullet separated from list | 4340475757 | Keep rules together, followed by prepared-run qualification. |
| Protected governance/infrastructure paths | Updated summary 6294590490 | Existing maintainer authorization/linked-issue and human approval requirement; tests do not replace it. Do not fabricate approvals or create an authorizing issue on someone's behalf. |

No Stoyan-authored security review appears in this export (authors are
Fullsend/Qodo bots, waynesun09 and jctanner). Additional security feedback is
expected and remains pending. No review replies or thread resolutions are
authorized in this task.

The GitLab changes enable opt-in smoke tests only. No production cutover has
occurred, and the original six-hour executor remains unchanged.

## Local repairs

- Strict shared preparation accepts only empty/0 or 1/true. The pre-script
  rejects malformed values before cloning, vendoring, cleaning or Jira calls;
  direct prepare_run invocations reject them before reading context/state.
- Owned release runs from a temporary host directory with pipeline effect
  context unset. It still verifies the exact remote owner, processes every
  recorded key despite conflicts/API errors, and retains the record until all
  releases succeed. Changed RFE/source inputs do not prevent cleanup.
- Prepared imports add section boundaries before reference reconstruction,
  then reject an unresolved Business Need before replacing the task. Standalone
  human warning behavior is retained. Empty/nonempty RFE and existing/missing
  Strategy heading cases cover preservation and successful reconstruction.
- History accepts intentionally empty identified publications only when their
  zero-strategy metadata matches its seal. Empty legacy/unsealed runs stay
  excluded. Skip parsing accepts current Reason tables (with/without Run) and
  legacy Labels/Missing tables without treating separators as RFEs.
- Summary generation/commit now occurs after every successful rebase and before
  every push attempt. Synchronization errors stop the post-script. An actual
  second Git publisher inserts its run and summaries between generation/push;
  retry must include both runs, then a same-run replay must leave remote HEAD
  unchanged. Immutable run publication and the current pointer are retained.
- An empty post-filter Org Pulse feature list exits successfully before sample
  indexing or any API call in both dry-run and ordinary diagnostic modes.
- The README links the owner repository's merged validator and data contract
  at 7ba9353e/PR #1789, explains last-completed-result retention and separates
  consumer deployment from merge evidence. Fixed both punctuation/list nits.

Initial focused reproductions produced 12 implementation failures plus two
fixture eligibility errors; the latter fixtures now supply the configured
release/quality labels. A second publication reproduction produced four
failures (two skip-only modes, seal validation and the concurrent publisher)
and two passing controls. After repairs, all 108 focused checks pass in
160.04s. Six additional format/heading variants are included in the full suite.
Lint and type descriptor checks pass. Full suite and publication follow below.

Refreshed comments before full-suite completion: still 116 entries, no new IDs
or changed bodies, so additional security feedback has not arrived in this
snapshot. No PR messages, thread changes, inference or live Jira mutations.

## Published and verified

Signed-off commit b3c10ecbecefb8f5fc50738d7b0a7390afd01021 is pushed to the
existing PR #85 feature branch; GitHub API confirms that exact head and the
PR remains open/draft. Full make test: **1,189 passed, six optional skips**,
346.81s. All 31 additional regression cases pass, along with the prior suite.
make lint passes Ruff and type descriptor validation; shell syntax and
root/component diff checks pass. Fourteen changed files pass the staged
configured-secret check with zero findings. Checkout is clean after commit.

The actual branch-based consumer bootstrap and native Fullsend 0.47.1
dependency locks pass on published b3c10ec for strat-single and strat-batch.
Receipt: /tmp/strat-minimal-consumer-0dbtlti2/result.json. These checks do not
run a sandbox, model or live business publication. No strategy smoke or
benchmark was launched, and there was no production cutover.

All current actionable code/documentation findings in the inventory are
addressed in source. The consumer-contract question is supported by the
owner repository's merged PR and linked versioned implementation. Formal
protected-path authorization/maintainer approval and the expected additional
security review remain external follow-ups. No authorizing issue, approval,
review reply, dismissal or thread resolution was fabricated or sent.
