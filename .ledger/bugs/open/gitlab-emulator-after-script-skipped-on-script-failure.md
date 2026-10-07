# Bug: Emulator after_script is skipped after a failing step_script

## Summary

M7 native job 3963 and OpenShell job 3966 failed before the default artifact
redaction command ran. Successful jobs execute it at the end of step_script,
rather than in the official runner's independent after_script stage.
This means after_script alone cannot guarantee artifact sanitization on failure.

## Required resolution

Keep emulator behavior documented; register an EXIT sanitizer before CI work
so failure paths redact retained artifacts or remove them if sanitization fails.
Verify with a synthetic credential and an intentional nonzero job exit.
Do not use real credentials in a failure fixture.

## Related task

[M7](../../tasks/done/consolidate-gitlab-runner-capabilities.md).

## Workflow mitigation verified — 2026-10-06

An inherited before_script now registers an EXIT sanitizer in both the strategy
and M7 CI fixtures. Pipeline **2044**, job **3975**, deliberately exited **37**
after writing a synthetic credential. It remained failed with exit 37, uploaded
its artifact with `[REDACTED]`, and contained no synthetic value. Sanitizer
failure removes generated output directories. This closes the workflow safety
gap; the emulator after_script semantics remain an open upstream behavior bug.
