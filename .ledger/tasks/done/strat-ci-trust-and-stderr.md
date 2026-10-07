# Task: Configure Claude workspace trust and isolate invocation stderr

## Goal

Honor project permissions in authorized strategy CI and stop replaying prior
run/phase warnings in current console output.

## Implementation

Settings helper merges the resolved project's hasTrustDialogAccepted into
CLAUDE_CONFIG_DIR/.claude.json, preserving config and writing atomically with
0600 permissions. Missing config is created; malformed JSON fails setup.
Clear historical working stderr after results clone. Each Claude invocation
captures and prints its own stderr file; cleanup exports invocation logs even
on failure. Fullsend hook settings and model pin remain unchanged.

## Acceptance

- [x] Trust/config preservation and repeated setup regressions pass.
- [x] Invocation stderr isolation and full component suite pass.
- [x] Source pushed and both future CI pins published without new model run.

## Status

Done. Existing job4017 is not modified.

## Evidence

Source3343f23f477434c49a036c64f959ad4e0564dd1f pushed. Full component suite:
792 passed,1 skipped (113.40s). Normal CI commit a2ca86ecead5fa08b00dfc3cc909410db7fe8c8f;
diagnostic commit68a16b166f90ae44b6b48322ffacf09a0c7b983d. Both publish-only,
native main preserved. Source working tree clean; root/component diff checks
passed. Active sandbox config directory owned by sandbox UID998, mode0755;
state file0600. No runtime mutation or new model invocation for this fix.
Live absence of warnings awaits a future job using this new pin.
