# Redact managed credentials from retained strategy transcripts

## Finding

Real job 3955's native Claude transcript retained one Jira password value.
It was detected by an exact-value credential scan of the final archive.
The value was never printed in agent commentary or committed to the ledger.
Current-run report/strategy/review/OTEL artifact files had no credential hits.

## Resolution and evidence

Added CI artifact redaction of known job credential values (including Google
refresh/client secrets, JSON escaping, URL encoding and Basic-auth values).
The CI after-script erases generated artifact directories if redaction fails,
preventing an unsafe upload. Hooks remain enabled; this additional step
protects retained native audit transcripts.

Replaced only the affected archive with its sanitized copy using cluster
administration access, preserved the evidence and updated artifact size
metadata. Verified the downloaded archive matched and scanned all 52 entries:
zero known credential hits.

Fresh pipeline 2040/job 3960 passed. Its synthetic credential fixture was
changed to `[REDACTED]`; the after-script reported one changed file. All 27
archive entries scanned clean and cleanup exit was 0. A deterministic local
check passed, including an unchanged second redaction pass.
