# markov-feature-check

A Markov directory workflow that exercises markovd and Markov features without
any model calls. Run it from markovd (git project sync, import
`var/demos/markov-feature-check`) and drive it through three attempts:

1. **Start:** fails at `fan_out`. Item `b` asserts `allow_b`. Items `a` and
   `c` complete; `skip-me` is filtered out by `for_each_when`.
2. **Resume with `allow_b=true`:** only `b` runs. `collect` must still see
   three results, so the registered results of items finished before the
   resume come back. Then the run pauses at the `approval` gate.
3. **Resume with `approved=true`:** the gate passes and the run completes.

It also checks:

- `workflow_source_commit`, which markovd passes to git-imported workflows;
- a chained subscript (`groups[group_name].limit`);
- `failed_when` together with `ignore_errors`;
- `pluck` and `script_exec` `stdin`;
- `vars/*.yaml`;
- step descriptions.
