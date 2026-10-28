# Bug: GraphQL PR diff-stat fields are placeholders

## Summary

The counter audit found that additions, deletions and changed_files in
checkouts/github-emulator/src/app/graphql/types/pull_request.py return literal
zero. This is separate from the REST serializers repaired in
[tasks/done/github-emulator-comment-counters.md](../../tasks/done/github-emulator-comment-counters.md).
GraphQL comment connections already query stored comment rows.

## Expected

GraphQL additions/deletions/changedFiles should reflect the real Git comparison.

## Status

Open. The requested REST counter repair does not change GraphQL field resolvers.
