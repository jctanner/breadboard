# Task: Revisit Bash false positives in Fullsend's injection scanner

## Goal

Distinguish ordinary Bash argument counts, background process IDs and array
lengths from environment enumeration without weakening genuine detections.

## Evidence

Job4017 logged at 2026-10-07T04:00:31Z that strategy-entrypoint.sh had8
injection findings. At source774cf10, the env_exfil_printenv regex matches:

- `$#` twice (lines11/13): argument count.
- `$!` once (line134): telemetry collector PID.
- `${#array[@]}` five times (lines163/183/184): candidate/strategy/owned counts.

Rule in Fullsend internal/security/injection.go:

```text
(?:printenv|env\s*\||\$\{?(?:!|#))
```

It classifies all matches as high severity, credential_exfil. Bootstrap scanning
prints only a count for noncritical findings and continues. Eight matches were
reproduced from the pinned script using the rule's regex; the actual Go pipeline
should be exercised in the implementation regression. No secrets are read or
exfiltrated by these eight expressions.

## Approach

Review the intended detection coverage, refine matching for shell syntax, and
add positive/negative cases. Preserve detection of real environment enumeration
such as printenv, env piped to another command, and Bash variable-name expansions
where appropriate. Evaluate whether matching needs context beyond a regex.
Consider making noncritical bootstrap diagnostics identify rule/severity/location
so operators can understand a finding without exposing sensitive source text.

## Acceptance criteria

- [ ] Real Fullsend scanner reproduces and explains all8 baseline findings.
- [ ] Argument count, background PID, string length and array length cases are not flagged as environment exfiltration.
- [ ] Genuine enumeration/exfiltration cases retain detection with regression coverage.
- [ ] Critical blocking behavior, fail mode and security hooks remain unchanged.
- [ ] Strategy entrypoint scans without these false positives, without rewriting valid Bash to evade the scanner.
- [ ] Required component checks and git diff --check pass; findings/limitations recorded.
- [ ] Published source and caller pins updated if the fix is adopted for this POC.

## Files likely involved

- `checkouts.fullsend_prototype/jctanner.fullsend/internal/security/injection.go`
- `checkouts.fullsend_prototype/jctanner.fullsend/internal/security/scanner_test.go`
- `checkouts.fullsend_prototype/jctanner.fullsend/internal/cli/bootstrap_scan.go`
- `checkouts.fullsend_prototype/jctanner.fullsend/internal/cli/bootstrap_scan_test.go`
- Strat-creator strategy-entrypoint.sh (reproduction fixture)
- Breadboard/strat-creator immutable Fullsend pins if publishing

## Status

Pending. Task creation makes no scanner, entrypoint or runtime changes.
