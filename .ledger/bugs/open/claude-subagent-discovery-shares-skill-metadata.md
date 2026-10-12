# Bug: Child file discovery exposes nested skills in the primary context

## Summary

Claude Code 2.1.296 registers skills discovered by subagent file operations in
a host-shared registry. The primary consumes that registry and receives new
names/descriptions even when it never reads the checkout and the child
returns no skill details. Whether upstream intends this sharing is unknown;
it violates the assumption that exploring a checkout in a child confines
that checkout's skill metadata to the child.

## Evidence

[Analysis and code path](../../../scripts/claude_binary_analysis/docs/claude-code-2.1.296-subagent-skill-isolation-analysis.md)
and ten verified controls against the unmodified binary. Explore,
general-purpose and Workflow agents reproduce it after Read; no read, Bash
cat alone, gitignored checkout and disabled project settings do not.

## Reproduction

Create an unignored nested checkout with README.md and
`.claude/skills/<name>/SKILL.md`, launch a child that Reads only README.md,
and have it return a fixed answer without skill details. Inspect the primary's
next API messages: the skill appears in a skill_listing system-reminder.

## Impact and boundary

The primary's context and callable skill set change due to work delegated
to a child. Automatic discovery injects metadata; it does not automatically
inject the full instruction body in these controls. Explicit primary Skill
invocation loads that body. No file/tool privilege bypass was investigated.

## Status

Open; investigated and documented, no harness changes or upstream report.
Potential fix requires an agent-scoped registry or ownership filter in the
command view, rather than changing per-agent listing deduplication alone.
