# Claude Code 2.1.296: skill variables and expansion timing

Investigated against the unmodified Linux x64 binary in the
[binary manifest](claude-code-2.1.296-workflow-binary-manifest.json).
This is a catalog of skill/command **prompt-body** substitutions, with separate
notes for frontmatter and hook execution. These contexts use different expanders.

## Prompt-body variables

| Exact spelling | Value / resolution | Availability |
| --- | --- | --- |
| `$ARGUMENTS` | Entire invocation argument string, preserving its original quotes and spacing | Local and plugin skills/commands |
| `$ARGUMENTS[n]`, `$n` | Zero-based parsed argument n; `$0` is the first argument, not a script name | Local and plugin skills/commands |
| `$name` | Positional alias declared by frontmatter `arguments: [name, ...]`; each alias uses its list position | Local and plugin skills/commands |
| `${CLAUDE_SKILL_DIR}` | Directory containing the skill file, supplied as its base directory | Local skills with a directory; plugin skills loaded in skill mode |
| `${CLAUDE_PROJECT_DIR}` | Explicit host project-config root if set, otherwise the current session/project-view project root | Local trusted skills and plugin prompts |
| `${CLAUDE_SESSION_ID}` | Current session-context ID from `K()`: a context override if present, otherwise the session object's ID | Local trusted skills and plugin prompts |
| `${CLAUDE_EFFORT}` | Effective effort label computed for the selected model, current effort and skill effort override | Both prompt factories, including remote skill factory paths |
| `${CLAUDE_PLUGIN_ROOT}` | Loader-provided plugin directory; installed plugins generally use their materialized/cache directory | Plugin prompts |
| `${CLAUDE_PLUGIN_DATA}` | Persistent plugin data directory derived from the plugin source/storage ID; resolution ensures it exists | Plugin prompts with a source ID |
| `${user_config.KEY}` | Exact own-property lookup of KEY in that plugin's configured option values, converted with `String(value)` | Plugin prompts when the manifest declares `userConfig` |

The first three entries are argument syntax, rather than environment-variable
lookup. The directory/session/effort entries require the exact **braced**
spelling shown. There is no universal `${ENV_VAR}` expansion in skill prose.

Verified literal forms include `${SKILL_DIR}`, `$SKILL_DIR`,
`$CLAUDE_SKILL_DIR`, `${ARGUMENTS}`, `${HOME}` and a custom `${VARIABLE_FIXTURE_ENV}`
whose environment value was deliberately set. Plugin placeholders likewise stay
literal in a local skill body. Authors can define argument aliases; the built-in
context values are supplied by the harness.

## Argument parsing, missing arguments and escaping

`nHe` applies argument substitution using `I6r`, which first tries a literal
shell-word parser (`_v`). If that cannot produce words, it falls back to splitting
on whitespace. It does not execute the argument string. The runtime fixture
`alpha "two words" third` yields `$0 = alpha`, `$1 = two words`, and
`$ARGUMENTS[1] = two words`; `$ARGUMENTS` retains the original string.

`arguments:` accepts an array of names or a whitespace-separated string. Empty
and purely numeric names are dropped. `argument-hint:` describes usage; it does
not declare aliases. Aliases are substituted longest-name first and require a
boundary: a following word character or `[` prevents a match.

- Missing `$ARGUMENTS[n]` and `$n` remain literal.
- A declared alias with no corresponding argument becomes an empty string.
- `$ARGUMENTS` becomes empty when the invocation supplies an empty string.
- If no argument placeholder was consumed and the argument string is nonempty,
  the helper appends a blank line and `ARGUMENTS: <raw arguments>`.
- A missing named alias still counts as a consumed placeholder, so it can
  suppress that fallback footer even though its expansion is empty.
- A single backslash before a recognized argument dollar sign preserves it
  literally and removes that backslash, for example `\$ARGUMENTS` and `\$0`.
  This is not a universal escape mechanism for the braced built-ins.
- If the helper receives null/undefined arguments, it returns before the
  argument substitution pass; that differs from an explicitly empty string.

Internally, inserted argument text is protected with sentinel characters so it
does not recursively expand as another argument placeholder in the same pass.
`bx` also neutralizes inline-shell directive syntax introduced by argument or
plugin-option values. These transformations are not general shell quoting.

## Resolution sources

**Skill directory:** the local factory `aYt` captures `baseDir`; plugin factory
`y6` uses the parent of the skill file. A plugin's overall root and a skill's own
directory can differ. In this Linux build `_x` is an identity function. The older
source's Windows path normalization is not runtime evidence for this binary.
The factories can also prepend a “Base directory for this skill” line; that line
is added by the harness, independently of placeholder replacement.

**Project directory:** `Kr()` reads the host's explicit project-config root.
The fallback `cr()` reads the session/project-view project root. This is not
simply a textual substitution of whichever directory a shell most recently
changed to, nor a nearest-Git-root search at each occurrence.

**Session:** `K()` returns `h()?.sessionId ?? n().id`, allowing a host context
override before falling back to the current session object's ID. It does not
read `toolUseContext.agentId`. The runtime verifier
checks it against the CLI's actual init event. Forked skill preparation calls
the prompt factory before launching its agent, so this is not a newly allocated
child ID.

**Effort:** `GA` computes an effective effort for the skill's model override or
the current main-loop model, using current effort and the skill effort override
(or permission-layer override). `Ev` also accounts for higher-priority settings,
model defaults and supported effort levels. `GA` defaults to `high` if there is
no effective value; numeric/non-label results are converted to `high` by `$B`.
This is an effective label, not necessarily the literal frontmatter value.
The fixtures' `effort: low` resolves to `low`.

**Plugin data:** `uNe` ensures the directory computed by `wh` exists. Its layout
is `<plugin base>/data/<encoded source ID>`, where the plugin base is normally
`<CLAUDE_CONFIG_DIR>/plugins` and can be overridden by the plugin-cache setting.
The encoding function distinguishes source/storage identities; do not derive
the path from only the plugin display name. The direct-loader control's source
is `variable-fixture@inline` and its directory is
`config/plugins/data/variable-fixture-inline`.

**Plugin options:** `Ox` uses a per-plugin cached option-loading promise. `At`
merges the settings-backed options with values from secure plugin storage,
including applicable source aliases. Secure-store values take precedence.
`epr` performs an exact own-property lookup; dots in KEY do not traverse objects.
A missing value remains literal, rather than throwing in the skill-body path.
A schema option marked `sensitive: true` becomes
`[sensitive option 'KEY' not available in skill content]`, even if a value exists.

The prompt-body expander does **not** merge manifest defaults through `Dqe`.
An option having only a schema default and no stored value stayed literal in the
runtime control. Defaults can be materialized by other configuration flows;
their presence in the manifest alone is insufficient at this expansion stage.

## When expansion runs

Discovery reads and parses markdown/frontmatter into a command object. It stores
the body and invocation callbacks; ordinary availability listing does not run
body substitution. Relevant `allowed-tools` path placeholders are resolved at
this **load** stage, as described below.

The following pipelines run when the harness asks `getPromptForCommand` for the
actual prompt. That includes explicit Skill/slash-command invocation and
subagent `skills:` preloading. `SA` calls the factory with empty arguments and
`isSkillPreload: true` for those preloads. A `context: fork` skill is expanded
before its child is launched. Expansion is not repeated before every later
model request that happens to contain the already-expanded skill text.

```text
local skill factory:
    prepend base-directory or resource-root information, if available
    substitute arguments and declared aliases
    replace CLAUDE_SKILL_DIR if baseDir exists
    for trusted/local expansion: replace PROJECT_DIR, then SESSION_ID
    replace EFFORT
    apply shell-execution policy, or execute permitted inline shell directives
    return text blocks

plugin skill/command factory:
    prepend skill-directory information in skill mode
    apply optional host prompt transform, if registered
    substitute arguments and declared aliases
    replace PLUGIN_ROOT, PROJECT_DIR, PLUGIN_DATA
    substitute user_config options if the manifest declares them
    replace SKILL_DIR in skill mode
    replace SESSION_ID, then EFFORT
    apply shell-execution policy, or execute permitted inline shell directives
    return text blocks
```

Each stage is a string pass over the whole body, including code blocks. This is
not a recursive general template engine. However, a later pass can expand a
placeholder introduced by an earlier pass: an argument containing
`${CLAUDE_SESSION_ID}` was substituted and then resolved by the session pass in
the runtime control. Shell output arrives after these passes and is not sent
through them again.

Plugin legacy commands share most substitutions, but their factory does not
apply SKILL_DIR unless the loader passed skill mode. Presence of a similarly
named shell environment variable does not change that condition.

## Frontmatter and hooks use different rules

| Field/context | Expansion in the inspected paths |
| --- | --- |
| Local `allowed-tools` | SKILL_DIR and PROJECT_DIR at command construction; rules naming either directory without the required directory context are dropped |
| Plugin `allowed-tools` | PLUGIN_ROOT, PROJECT_DIR, PLUGIN_DATA; additionally SKILL_DIR in skill mode, before parsing tool grants |
| `description`, `name`, `argument-hint`, model/effort values, `disallowed-tools` | No general prompt-body substitution pass; the factories parse them as metadata |
| Hook executable/args in exec form | Hook-specific PROJECT_DIR, PLUGIN_ROOT, PLUGIN_DATA and plugin-option handling at execution |
| Hook shell-form commands | Shell environment rules; plugin-option interpolation is rejected where it would be reparsed by the shell |

The hook runner `i$` injects `CLAUDE_PROJECT_DIR`. It supplies
`CLAUDE_PLUGIN_ROOT` for plugin hooks or a skill-associated root, and
`CLAUDE_PLUGIN_DATA` only for plugin hooks. Configured plugin options are exposed
as `CLAUDE_PLUGIN_OPTION_<KEY>`, with names uppercased and non-alphanumeric
characters replaced by underscores. These are hook environment variables,
not extra body-template variables. A local skill hook can therefore use the
hook runner's PLUGIN_ROOT convention even though its prose does not expand that
placeholder through the local prompt factory. Hook behavior was traced
statically, not exercised by these controls.

Remote policy also matters. `F4e` treats MCP, memory-store and attached-folder
skills as remote, and ordinary synced skills as remote unless the hosting mode
relaxes that classification. The local factory suppresses project/session
substitutions and inline shell execution on these remote paths. It still applies
arguments, any supplied skill directory and effort. Remote arguments receive
additional text sanitization. These branches were inspected statically.

## Inline shell preprocessing

The shell extractor recognizes an exclamation-prefixed backtick command at a
line start or after whitespace, and exclamation-mark fenced blocks. Its syntax
is distinct from variables. For example:

```markdown
!`python "${CLAUDE_SKILL_DIR}/scripts/context.py"`
```

Directory variables resolve before that command is checked/executed. Execution
uses the relevant Bash/PowerShell tool, permission checks and applicable skill
tool grants. A shell-execution policy can replace the directive with a disabled
notice; read-only/coordinator paths can disable or hand off execution. Directory
substitutions are plain text, so quote paths in shell commands when needed.

Both local and plugin controls run a harmless bundled script by its expanded
SKILL_DIR path. Its `pwd` is the session working directory, not the script's
directory. Its stdout contains literal `${CLAUDE_SKILL_DIR}`, which remains
literal in the final model request, proving the ordering. Shell environment
expansion inside a command/script is a separate operation; it does not make
`${HOME}` or arbitrary environment names expand in ordinary skill prose.

## Evidence and reproduction

- [Nine verified API controls](claude-code-2.1.296-skill-variable-controls.json)
- [Forty-one exact symbol ranges/hashes](claude-code-2.1.296-skill-variable-symbols.json)
- [Evidence-labeled claims](claude-code-2.1.296-skill-variable-claims.json)
- [Mock probe runner](../run_skill_variable_experiments.py) and
  [outcome verifier](../verify_skill_variable_controls.py)

The controls cover local/plugin arguments, empty and missing arguments, named
aliases and escaping, fallback argument delivery, ordered substitutions,
configured/sensitive/missing/default-only plugin options and inline scripts.
Each run has a fresh config, deterministic fixture Git commit/tree hashes,
exact runner snapshot and scoped captures of authored fixture text. The verifier
checks actual invocation results and model request text, not only CLI exit code.
Earlier fixture revisions are ignored artifacts and excluded from selected
controls. No paid model, real credentials or external plugin installation was
used. Raw extracted code and full generated transcripts remain ignored.
