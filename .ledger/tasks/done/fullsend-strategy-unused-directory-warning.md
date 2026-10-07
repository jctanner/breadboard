# Task: Remove unused Claude directory permission in strategy CI

## Goal

Stop repeated untrusted-workspace warnings for the local assessment directory.

## Findings

Job 4000 warns that `.claude/settings.json` grants `/tmp/strat-assess` through
`permissions.additionalDirectories`. This directory supports local evaluation,
not the single-RFE or batch strategy workflow. Claude workspace trust resides
in `$CLAUDE_CONFIG_DIR/.claude.json`, separate from project settings.

## Implementation

The strategy entrypoint runs `prepare-claude-settings.py` on its disposable
checkout before starting Claude. Remove only `/tmp/strat-assess`, preserve
other directories, permission rules and hooks, and leave trust acceptance alone.
Missing settings are allowed; malformed JSON stops setup. Other additional
permissions, if later added, can still produce warnings until configured.

## Acceptance

- [x] Narrow settings preparation and regression checks implemented.
- [x] Unit suite: 525 passed; Bash syntax passed.
- [x] Full suite: 789 passed, 1 skipped. Source 78bc04cdc6c57e271217fc6083d0b7876609faee pushed.
- [x] Both CI pins published without starting strategy work.

## Verification limits

No model run or strategy replay is required for this settings-only adjustment.
Removal is tested directly; warning absence has not been checked in a new live
Claude invocation.

## Publication

Normal branch commit: `72eb952529c8d2a4c7105e2a62eb6800240ad090`.
Diagnostic branch commit: `1d9c25c94ee6efcf2887cc5d2ee89db045a32e98`.
Native main remained `14d81319af44973d592e4197b14b680684f35813`.
Diagnostic publishing encountered transient API errors during an externally
initiated GitLab pod replacement; retry succeeded. The retry omitted
`--publish-only` and created capability pipeline 2060. Canceled it immediately:
ordinary-ci 4005 succeeded; build 4004 and capability jobs 4006–4009 canceled.
No model diagnostic or RFE strategy job was selected. No new strategy run was
started. Component and root diff checks passed; component working tree clean.

## Status

Done.
