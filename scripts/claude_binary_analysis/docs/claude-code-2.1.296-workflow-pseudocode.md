# Claude Code 2.1.296 workflow pseudocode

Original reconstruction from the parsed symbols recorded in
`claude-code-2.1.296-workflow-correspondences.json`. This is descriptive
pseudocode, not recovered Anthropic source or an executable replacement.

```text
invoke_workflow(input, session):
    check session/organization/managed settings availability
    reject retracted input and prohibited session input forms
    if resuming:
        require the old run to be inactive and its state recoverable
    resolve scriptPath, then named definition, then inline script
    require readable permitted regular file when reading scriptPath
    validate first statement: export a literal meta with name and description
    check deterministic-script restrictions
    request permissions, carrying the resolved script for review
    compile async script body with guarded VM boundaries
    if compilation fails: return an error; register no background execution
    allocate task ID and either new run ID or prior resume run ID
    persist script and remember its path
    launch background engine and return launch receipt

background_engine(script, task, run):
    register local_workflow task and associated abort/controller bookkeeping
    create/load journal; record launch for a fresh run
    configure token budget with total = null in this local launch path
    create VM with cloned args, logging, phase, timers and host hooks
    block dynamic imports and string/wasm code generation
    block nondeterministic current-time/random generation
    execute the script and sanitize its return value
    batch progress, retaining most recent phase/agent entries by index
    if aborted: mark killed
    else if an uncaught error escaped: mark failed
    else: mark completed, even if individual branches recorded failures
    persist final result/progress/usage snapshot
    notify parent of result plus failures and artifact locations

agent(prompt, options):
    check lifetime-call and configured token budget gates
    validate/canonicalize options, record phase and display label
    key = hash(previous_key, prompt, canonical result-relevant options)
    advance previous_key
    if journal has successful cached result and no prior divergence:
        emit cached progress; return cloned cached result
    update prefix-replay state after a miss/failure
    enqueue under live-agent concurrency limit
    run subagent spawn checks, custom type/model/tool restrictions
    validate schema and install StructuredOutput tool when schema supplied
    create agent conversation and transcript under workflow run directory
    record started entry and controller; emit progress
    retry according to stall/throttle/rate-limit policies
    if user skipped or terminal API error: return null
    if schema supplied but no valid structured output: throw
    result = structured object or normalized last assistant text
    journal non-null results; journal failures without a usable cached result
    return result

parallel(thunks):
    validate bounded array of functions
    settle all concurrently
    return positional values, replacing rejected branches with null
    record branch failures separately

pipeline(items, stages):
    validate bounded input and stage arrays
    for each item concurrently:
        value = item
        for each stage:
            if value is null: stop this item's stages
            value = await stage(value, original_item, index)
        on error: record failure and return null for this item
    return positional results after all item chains settle

child_workflow(reference, args):
    resolve/parse child definition with the same registry/read restrictions
    create a separate VM and clone args into it
    share parent agent hooks, budget, journal and abort/concurrency gates
    place child agents in a child progress group
    prohibit another child_workflow call inside this child
    return sanitized child script result
```

The canonical journal options include schema/model/effort/isolation/agent
type/tool denials/Bash clamp. Display label and phase do not invalidate a
cached result. A successful result's content is not semantically validated
unless the caller separately enforces a schema or task-specific contract.
