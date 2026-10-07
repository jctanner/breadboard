# Fullsend strategy entrypoint omits Claude progress from CI trace

## Reproduction

Open project 7/job 3993 raw trace. Claude inference occurred, but assistant
stdout is absent; stderr warnings dominate the trace.

## Findings

- Batch harness `entrypoint.stream_format: none` is correct for a shell
  orchestrator emitting human-readable output.
- Fullsend `internal/runtime/entrypoint.go` RunEntrypoint sends that stdout
  only to its output artifact (`io.Copy(out, stdout)`); stderr reaches CI.
- Our `stream-claude.py` renders stream_event deltas and ignores completed
  assistant messages. Fullsend ClaudeEntrypointHelper requests stream-json
  without --include-partial-messages, so the expected deltas are absent.
- Job archive output.jsonl: 3,705 bytes / 67 lines. Persisted trace: ~3.4 MB /
  22,497 lines, no truncation warning. Transcripts retain 355 assistant records
  across 17 files, all using claude-opus-4-6.

## Expected fix

Render completed assistant messages (or explicitly request and correctly
handle partial messages), and safely forward orchestrator stdout to CI while
retaining the output artifact. Preserve redaction, exact model pin, hooks,
exit codes, and completion marker behavior. Do not change shell output to
stream_format claude: it is not a single Claude JSON stream.

## Status

Fixed in source and published CI pins. Browser raw trace route returns stored text unchanged.
No evidence currently identifies OpenShell or GitLab per-line truncation.

## Implementation and evidence

Fullsend bdedebeaf96cbfabf298472397321a946af621c9 forwards `none` stdout to
both host stdout and its retained artifact. Strat-creator
7244097a7dce233cb283947fc8f4381b0197cba8 renders completed assistant text/tool
messages and avoids duplicates when partial events are present. Both pushed.
Normal emulator branch final 456a78653f93e2ae56889e04e19f611c9110683b;
validation branch 7e79ef1386cabdcda1eff1281e3cf32194141e1e. Both use new pins.
Live caller stdout/stderr is masked before runner capture, including fields
from the private credential file after the raw credential variable is removed.

787 strategy tests passed / 1 skipped; all Fullsend make go-test variants passed
with race detector, vet and staged lint passed. Complete runtime package 90.6%
coverage; RunEntrypoint 82.5%, changed expression covered. Four caller regression
tests passed. Replayed 17 actual archived transcripts / 355 assistant records
into 97,108 rendered bytes. Long 100,000-character line and credential-field
masking tests passed. Existing completion exit marker preserved.

Optional live pipeline 2056 (3997 build, 3998 connectivity) was canceled before
sandbox execution because the GitHub source fetch advanced extremely slowly.
Thus live CI forwarding is covered by runtime regression, but not a completed
new deployed sandbox run. Historical job 3993 trace remains unchanged.
