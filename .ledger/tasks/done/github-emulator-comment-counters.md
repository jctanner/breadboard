# Task: Accurate issue and PR response counters

## Status

Done.

## Confirmed causes

Issue and PR REST serializers hardcode comments=0; PR serializer also hardcodes
review_comments=0. PR stats are computed only for GET detail, leaving list/create/
update responses with placeholders. Search shares the issue serializer. Existing
unrelated diff-download changes remain untouched.

## Plan

Compute comment counts from stored rows on read, share count values across
serializers, and consistently compute Git-derived counters on PR responses.
Test two creates and one deletion for issues and PRs, including listings/search,
review comment counts and Git counter consistency. Run full existing suite.

## Implementation and focused validation

- Issue.comments_count and PullRequest.review_comments_count are computed SQL
  properties over their source tables. Existing rows and all comment writers
  are covered without counter columns, backfills or mutation bookkeeping.
- REST serializers and schema from_db helpers use these counts; issue/search
  comment sorting and PR popularity sorting also use actual issue-comment counts.
- Added source-key indexes in models and Alembic 0012 for efficient count reads.
- PR list/create/update now attach the same Git stats as detail. Merged PRs use
  stored comparison SHAs; no-repository fallbacks no longer fabricate one commit.
- Five new counter tests pass, covering create/edit/delete counts, independent
  issues/PRs, search, lists, mutation responses, separate review-comment counts,
  multi-commit/addition/deletion/file stats, and merged/deleted-branch stats.
- Three migration tests pass; fresh DB test asserts both count indexes exist.
- Before the fix, the new regression failed after the first comment (0 vs 1).
- Compile and diff checks pass. Full suite passed: 762 tests in 302.83s (including five new counter regressions).


## Additional audit finding

GraphQL's separate additions/deletions/changedFiles resolvers return zero. Tracked
as bugs/open/github-emulator-graphql-pr-diff-stat-placeholders.md; the requested
REST API repair leaves those resolvers unchanged. GraphQL comment connections
already query stored rows.

## Publishing note

pulls.py contains unrelated, pre-existing diff-download changes as well as this
repair. Preserve those changes when staging. The pre-merge SHA snapshot hunk is
also needed to preserve accurate summaries when branch tips move before merge.


## Deployment and live verification

make host-rebuild-github completed and the deployment rolled out successfully.
A unique temporary admin-owned repository was created using the seeded token
read from the pod environment. For an issue, all three views (detail/list/search)
reported [2,2,2], then [1,1,1] after deletion. For a PR, those plus PR detail/list
reported [2,2,2,2,2], then [1,1,1,1,1]. Inline review-comment counts went 1 -> 2 -> 1
without changing the PR issue-comment count. Git counters matched the known
single-file, single-commit probe diff. The temporary repository was deleted with
HTTP 204 in finally. No credentials were printed and no existing issues mutated.

Full suite: 762 passed in 302.83s. Compile and both repository diff checks pass.
Changes remain uncommitted.
