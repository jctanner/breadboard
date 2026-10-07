# Bug: Strategy CI replays historical and accumulated Claude stderr

## Evidence

Live job4017 source774cf10 has 19 allow rules, no additionalDirectories, and
workspace trust false. Trace inspection counted 45 allow and39 directory
warnings. Current artifacts/claude-stderr.log had17 allow and13 directory
warnings; results-repo HEAD already had13 of each, and its contents are an
exact prefix of the current file. Therefore current invocations added4 allow
warnings and zero directory warnings at that inspection point.

The entrypoint does not remove claude-stderr.log after cloning results.
run-claude.sh appends stderr with `2>>` and cats the entire accumulated file
after each invocation. Old warnings reappear with fresh runner timestamps;
each phase also replays earlier phases' output.

## Impact

Misleading warning volume and apparent failure of the previous directory fix.
Current allow warnings are real: project trust remains false, and Claude ignores
19 project permission rules. Fullsend's helper uses --dangerously-skip-permissions;
Fullsend hooks are configured separately. No trust fix applied during inspection.

## Follow-up

Use current-invocation stderr for console output and segregate/remove historical
working logs at job startup. Configure the authorized CI project's trust before
launch if its project permission settings are intended to apply. Verify hooks
remain loaded. Do not mutate the running model session just to suppress warnings.

## Fix (2026-10-07)

Strat-creator3343f23 pushed. Entry helper configures resolved project trust in
CLAUDE_CONFIG_DIR/.claude.json with an atomic0600 write and preserved config.
Entrypoint clears historical working stderr after results clone; wrapper uses
one persistent file per invocation and prints only that file. Cleanup exports
those files on success/failure. Fullsend helper/hook settings and model pin
unchanged. Full suite792 passed/1 skipped; regression executes real wrapper
for all3 phases, confirms each console prints only its own stderr and3 files
remain. Trust preservation/repeat/missing/malformed tests pass. Future CI pins
updated; existing4017 not changed. No fresh model run claims warning absence.
