# CI recovery artifact redaction misses pathnames

On strat-creator 73c454b, failed-run capture retains filenames and manifest keys
from sandbox tmp/artifacts. The outer CI cleanup copies recovery into its export
and `scrub_tree` redacts only contents. A known credential in a file/directory
name survives. Binary scrub errors also echo an unsanitized filename.

Review comment: 4354198490. Repair: check all relative pathnames, including
empty directories, and reject unsafe export with a generic credential-free
error. The existing outer cleanup must remove unsafe generated CI artifacts,
preserve private recovery and release owned claims. Test actual capture and CI
wrapper with synthetic secrets; no real credentials or external services.

[Implementation task](../../tasks/done/strat-pr85-three-review-fixes.md).

## Resolution

The scrubber checks all relative names before redacting contents and returns
generic errors without filenames or tracebacks. Seven new regressions fail
before repair and pass afterward; actual capture/wrapper tests prove removal
of unsafe generated export, preservation of private recovery, owned cleanup
and failure-code handling. Full suite: 1,261 pass/six optional skips;
lint/types/diff pass. Published as signed-off 0707b5b; exact PR #85 head verified
and component clean. No real credentials or external exports were used.
[Evidence and limits](../../notes/strat-pr85-three-review-fixes-20261022.md).
