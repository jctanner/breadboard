# Review scope parser splits a valid frontmatter title

On strat-creator 73c454b, `review_scope.inputs` splits frontmatter using any
`---` substring. A valid quoted or unquoted title containing those characters
truncates the metadata, hiding source_rfe or raising a YAML parser error. Both
root and bundled reviewer hooks reject the assigned strategy.

Review comment: 4354198483. Repair: use the shared frontmatter parser, which
recognizes delimiter lines. Cover artifact/local inputs and actual root/bundled
hook subprocesses with vendored helpers. Preserve ticket scope and path guards;
trusted host imports must not import code from the downloaded repository.

[Implementation task](../../tasks/done/strat-pr85-three-review-fixes.md).

## Resolution

Both scope copies use the shared frontmatter reader. Six regression cases fail
before repair and pass afterward, including actual hook subprocesses with
vendored helpers. Mandatory root/bundled parity remains covered by the full
1,261-pass suite (six optional skips). Lint/types/diff pass. Published as
signed-off 0707b5b; exact PR #85 head verified and component clean.
No model run.
[Evidence and limits](../../notes/strat-pr85-three-review-fixes-20261022.md).
