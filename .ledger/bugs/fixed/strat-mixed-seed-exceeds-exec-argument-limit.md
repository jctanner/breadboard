# Mixed-state checker passes a seed report larger than an exec argument allows

Status: fixed in the benchmark checker/orchestration; live Opus validation pending. Observed after stopping markov-run-eaf92e4d.

The rich-text mixed seed report is 306,233 bytes. workflows/run-test.yaml
passes seed | to_json as one argument to check_run.py. Markov fails before
the checker starts with "fork/exec /usr/bin/python3: argument list too long".
The failure is recorded on the check step and its parent iteration steps at
2026-10-16T01:20:18Z. The native Workflow's business-validation failure is
separate; do not report the missing independent evaluation as a pipeline pass.

Pass the report through a file or standard input, or keep a small seed identity
and load its stored report from the dashboard. Cover a realistic rich-text
fixture larger than 128 KiB in the offline orchestration test. Current fake
seed reports are too small to exercise the operating-system argument limit.
No model inference is needed to reproduce or repair this benchmark defect.

The job's model-free finish checker did run and saved per-ticket checks. It
reported preserved controls/deferred work, four fresh clones, expected STRAT
identities, nine review publications and released owned claims. Its repeat was
skipped because the original invocation failed; that is not a live repeat pass.

## Repair and verification

The Markov check step now sends seed JSON through stdin, with a dash argument
telling check_run.py to read it there. Small direct JSON arguments still work.
A real offline Markov executor test sends a 350 KB seed and confirms this
contract without model inference. All 96 benchmark tests pass (one optional
local-emulator case skipped there and run separately: nine passed).
