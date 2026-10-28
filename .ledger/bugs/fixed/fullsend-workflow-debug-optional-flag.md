# Bug: Workflow adapter passes the Fullsend debug filter as a positional argument

## Reproduction and impact

Pipeline 2096/job 4060 on `7b93d35a` stopped before host preparation or Claude:
`fullsend run strat-single ... --debug api,hooks` reports
`accepts 1 arg(s), received 2`. The gateway/image setup consumed 3m48s; no
RFE claim was acquired, no sandbox was created, and no inference was started.

Fullsend 0.47.1 declares the debug string as optional. A bare `--debug` selects
its implicit `*`, leaving `api,hooks` as a second positional argument.

## Fix and verification

Use `--debug=api,hooks`. A model-free regression extracts the actual launch
arguments and invokes the checksum-verified released binary with a nonexistent
configuration. It must reach the expected configuration error, rather than
argument rejection, without creating a sandbox or invoking a model.

The failed attempt is archived independently from the subsequent actual smoke.
The same RHAIRFE-19 is retained for the authorized smoke; no replacement seed
or paid retry is needed because this adapter failure preceded all inference.

Related: [single-RFE integration smoke](../../tasks/done/fullsend-claude-workflow-opus-single-smoke.md).
