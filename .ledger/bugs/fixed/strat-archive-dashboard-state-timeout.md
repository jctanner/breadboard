# Dashboard state archive exceeds the fixed command timeout

The scheduled Opus run `markov-run-dd4a838118bd23d18c693b01` completed at
2026-10-15T05:06:48Z. Its detached collector timed out after 600 seconds while
streaming all dashboard artifacts/logs/issues/workspace. Collection continued for
other sources, but the final capture is correctly marked incomplete and no final
reset-authorizing receipt was published. The observer stopped before business
verification because archival did not pass.

Investigate the source size and recover a complete capture without resetting
services or repeating model work. Preserve the original incomplete capture.

## Resolution

The retained dashboard source was 29 GiB. Added configurable per-source stream
timeouts (default 1,800 seconds, explicit recovery 2,400) and fast lossless gzip.
The gzip wrapper is separate from tarfile so Python 3.10/3.11 service containers
work too. Capture scope, inventory and checksum checks are retained.

Sixteen focused archive tests pass; full benchmark tests report 72 tests with
seven skipped. Actual dashboard, MLflow (Python 3.10), Observatory (Python 3.11)
and other sources now verify in the final recovery capture. It contains 3,599
files / 8,998,503,549 bytes with no source errors and a published verified receipt.
Recovery reuses only checksum-verified successful files and records the later
retried source intervals. Both incomplete captures remain unchanged. No model
work or destructive reset was repeated.

[Result and capture](../../notes/s1-hardening-scheduled-opus-20261015.md).
