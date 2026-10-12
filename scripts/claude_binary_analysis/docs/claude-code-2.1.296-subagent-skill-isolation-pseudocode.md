# Subagent skill discovery and primary context: reconstructed pseudocode

Original reconstruction from the
[exact symbol ranges](claude-code-2.1.296-subagent-skill-isolation-correspondences.json).
Names below explain roles rather than claiming original source identifiers.

```text
make_subagent_context(parent):
    child.session = parent.session or a supplied session view
    child.agentId = new or supplied agent ID
    child.readFileState = clone(parent.readFileState)
    child.dynamicSkillDirTriggers = []
    # No separate extension-registry copy is created here.

read_file(context, file_path):
    if normal local mode:
        discover_for_file(context.session.host, file_path,
                          context.dynamicSkillDirTriggers)
    return the permitted file contents

discover_for_file(host, path, triggers):
    dirs = walk ancestors below cwd looking for .claude/skills
    skip visited, ignored, restricted and sync-owned paths
    append discovered directories to this context's triggers
    start load_directories(dirs) in the background

dynamic_state():
    registry = extension_registry_for(current_session.host)
    key = registry.dynamicSkillStateKey()  # default "cli", not agentId
    return registry.dynamicSkillStates.get_or_create(key)

load_directories(dirs):
    require project settings and allowed skill policy
    commands = load and parse each skills directory
    for command in commands:
        dynamic_state().skills[(command.root, command.name)] = command
    emit shared skills-loaded signal
    # Its registered listener invalidates shared command caches.

available_commands(cwd):
    return merge(base_commands(cwd), dynamic_state().skills)
    # Qualify collisions and annotate nested-directory applicability.
    # No filter for which agent discovered a dynamic command.

assemble_skill_listing(context):
    if no Skill tool: return []
    commands = available_commands(project_root)
    apply command eligibility and session/primary allowlist filters
    sent = listing_state.sent_names[context.agentId or MAIN]
    new_commands = commands whose names are absent from sent
    mark new names as sent for this agent
    format names, descriptions and whenToUse within listing budget
    emit skill_listing attachment

serialize_skill_listing(attachment):
    create meta user message wrapped in system-reminder
    include formatted availability metadata in the current API request

invoke_skill(context, name):
    resolve name in available commands and apply ordinary invocation checks
    expand that command's full markdown instructions for this context
    record invoked content with this agent ID
    return/load skill instructions into this agent's turn
```

The registry's shared scope permits the cross-agent announcement. The listing
state's per-agent scope prevents deduplication from hiding that announcement
from the primary. Full invoked content uses agent-specific bookkeeping and
is a separate stage from availability metadata.
