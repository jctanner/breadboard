# Task: Identify skill placeholders and expansion stages

## Goal

Trace all author-facing skill/command prompt substitutions in the pinned Claude
Code 2.1.296 binary, including argument, directory, session, effort and plugin
configuration placeholders. Identify resolution sources, timing and differences
between local skills, plugin skills and remote skills.

## Acceptance criteria

- [x] Trace exact substitutions and field-specific invocation/load timing.
- [x] Trace positional/named argument parsing, missing values and escaping.
- [x] Inspect shell preprocessing and distinguish it from prompt expansion.
- [x] Verify selected substitutions through isolated mock-API controls.
- [x] Save report and exact evidence under the analysis documentation home.
- [x] Validate outcomes, evidence hashes, links, compilation and whitespace.

## Status

Done. [Report](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-skill-variable-expansion.md)
catalogs all inspected prompt-body placeholder families, exact resolution
sources, local/plugin pass order, argument edge cases and field-specific
frontmatter/hook/remote differences. Recorded forty-one exact symbol ranges,
ten evidence-labeled claims and nine verified mock API controls.

Runtime confirms local/plugin directory/session/effort values, positional/named
arguments, empty/missing values, escaped arguments and appended fallback text.
Plugin options redact sensitive values and leave unset/default-only values
literal. Supported placeholders inserted by arguments resolve in later passes;
placeholders emitted by bundled scripts do not re-expand. Script cwd remains
the session cwd. Incorrect variable spellings and arbitrary environment names
stay literal in prose. Hook and remote policy branches are static-only.

Nine outcome checks, ten claim/path checks, forty-one payload hash checks,
thirty-five local documentation links, JSON, Python compilation and whitespace
passed. Fresh configs, deterministic Git fixture provenance and exact runner
snapshots retained. Earlier incomplete fixture revisions are excluded from
selected controls. No real credentials, paid inference or plugin installation.
