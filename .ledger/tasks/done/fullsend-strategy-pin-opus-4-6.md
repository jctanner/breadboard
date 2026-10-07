# Pre-M8: Pin the strategy model to claude-opus-4-6

## Goal

Use exactly `claude-opus-4-6` for the Fullsend strategy POC before proceeding
to M8 or other new workflow runs. This is the user's explicit model choice.
The previous `.fullsend/harness/strategy.yaml` used the moving alias `opus`;
M6 recorded real inference using `claude-opus-4-8`.

## Scope

Work in `checkouts.fullsend_prototype/jctanner.strat-creator` on the existing
`feat/fullsend-strategy-entrypoint` branch. Read its component instructions.
Update Breadboard's CI fixture and published POC branch to consume the new
commit. Preserve Vertex with the existing authorized Breadboard credentials,
enabled hooks, current effort, shared images, and strategy orchestration.
Do not change Fullsend's general model defaults for unrelated harnesses.

## Acceptance criteria

- [x] Replace `model: opus` in the strategy harness with
  `model: claude-opus-4-6`. Inspect effective CLI/environment settings and
  any child-agent model selection so none silently overrides this POC pin.
  Remove conflicting POC overrides; do not fall back to an alias or newer
  model if the requested model is unavailable.
- [x] Verify create, refine, and review all inherit the exact pin through
  `run-claude.sh` and `fullsend-claude`. Add a focused regression check of
  effective child invocation/model propagation; a YAML string check alone
  is insufficient. Change the Fullsend feature branch only if this exposes
  a model-propagation defect.
- [x] Run the relevant component checks and `git diff --check`, then commit
  and push the strat-creator feature branch. Update the pinned source SHA in
  Breadboard's strategy CI fixture and any dependent validation fixtures.
  Republish the POC CI branch without automatically starting a strategy run.
- [x] Run a small, non-mutating Claude smoke through the same CI image,
  Vertex path, Fullsend helper, and pinned harness model. Record the actual
  model reported by Claude/provider metadata, pipeline/job IDs, and source
  SHAs. Verify it identifies Opus 4.6, not merely a requested CLI argument.
  Document any provider-specific identifier mapping if required.
- [x] Preserve artifact redaction and job cleanup. Update invocation docs
  and the ledger handoff with the tested pin. Historical M6 evidence remains
  a 4.8 run; do not relabel it as validation of 4.6.

## Limits and sequencing

Do not reset Jira or rerun processed RHAIRFE-1 to prove model selection.
Mocked phase invocations plus the small real smoke are sufficient for this
gate; no new end-to-end strategy output is required. If the existing nested
DNS issue prevents the smoke, retain the failure evidence and leave runtime
verification incomplete; a source edit alone does not close the gate.

This task precedes M8. The existing
[nested DNS reliability bug](../../bugs/open/nested-podman-aardvark-dns-startup-intermittent.md)
remains separate; M1–M7's recorded completion is unchanged.

## Status

Complete. Exact model pin and phase propagation verified; the non-mutating
Vertex smoke passed with actual Opus 4.6 metadata. M8 has not started.

## Source implementation — 2026-10-06

Pushed strat-creator feature commit `68614f656df6598e1429cac125d634802c07e0f1`.
Harness model is exactly claude-opus-4-6; effort remains high. The strategy
wrapper sources a POC-only helper that pins the opus alias and subagent model
to 4.6, forces subagent selection, and clears ANTHROPIC_MODEL. Unrelated
Fullsend defaults and general skill frontmatter are unchanged. The CI caller
clears FULLSEND_MODEL/FULLSEND_FALLBACK_MODELS and passes the exact model
flag. No fallback alias/model is configured. Fullsend's generated helper
already propagates the selected model; no Fullsend source defect was found.

Focused regression exercises the actual FIFO run-claude wrapper and helper/
Claude argv chain for create, refine and review, including conflicting ambient
model variables. The test helper follows Fullsend's generated argv layout;
the live smoke independently verifies the real generated helper. All three
phases reached mocked Claude with the exact model, effort high, hook settings
and the forced subagent pin. **513 unit passed; 777 full passed, 1 skipped**;
component diff check passed before commit/push.

Claude Code documents subagent model defaults/force precedence in
[its primary documentation](https://code.claude.com/docs/en/sub-agents#run-every-subagent-on-one-model).
In current versions the default variable alone does not override explicit
agent/skill choices; FORCE=1 is required. ANTHROPIC_DEFAULT_OPUS_MODEL also
pins existing skill requests of the opus alias.

Breadboard strategy and runner-validation fixtures now pin the pushed source.
The smoke derives a tools-disabled, one-turn entrypoint from the same strategy
harness, retains provider/credentials/effort/policy/hooks/images, and calls
actual fullsend-claude. It cannot run strategy skills or mutate Jira/results.
Redaction and gateway cleanup remain enabled. Live verification is pending
and this gate remains current until actual model metadata is checked.

## Live verification attempt — 2026-10-06

Initial smoke pipeline 2046 (POC commit ac10cca6ff5a6adb3745fd769bcb2921b6135b67),
job 3979 failed before inference: Claude's variadic --tools option consumed the
positional prompt. This is a smoke invocation defect, not a Vertex model or
DNS failure. Changed the smoke to pass the prompt through stdin while keeping
--tools empty and max-turns 1. The generated helper is unchanged.

Failed-run artifacts: zero credential matches across 24 archive entries;
no containers or job network remained. cleanup_exit=1 preserves the original
agent failure (it does not imply leaked resources). Pipeline 2047, POC commit
9326f5c10d6f9853c799aa47074dfbfd4aa25d8a, retries the corrected smoke.
Runner-validation source was republished without a pipeline at
adc94890ba9ea45265aa67a07b4eaa26e03a6a0f. Actual model verification remains
pending; no strategy workflow was started.

## Final live acceptance — 2026-10-06

Pipeline **2047** passed: build job **3980**, model-smoke job **3981**.
Run fs-mod-fd6686424e6a used strat-creator SHA
68614f656df6598e1429cac125d634802c07e0f1 and unchanged Fullsend feature SHA
8f628aec6d113181914e2a2307fce17488e2c4b4. POC CI commit is
9326f5c10d6f9853c799aa47074dfbfd4aa25d8a. Image pins, effort high, existing
Breadboard Vertex credentials and enabled hooks are preserved.

Actual archived Claude stream, beyond the requested flag:

- init model claude-opus-4-6, Claude Code **2.1.260**, tools empty.
- assistant response model **claude-opus-4-6**.
- result success, PINNED_MODEL_SMOKE_OK, one turn.
- modelUsage key/canonicalModel **claude-opus-4-6**, provider **vertex**.
- Aggregate input 787, output 32, cache creation 8747, cost $0.05940375.
- Fullsend metrics report the same actual and requested model; tool_calls=0.

No provider identifier remapping was required in reported response metadata.
The installed Claude version supports SUBAGENT_MODEL_FORCE. Live smoke does
not spawn subagents; all three phase invocations/child environment are covered
by the focused regression, while real helper/provider inference is covered by
this smoke. This gate does not claim a new end-to-end strategy run on 4.6.

Archive scan: **zero credential matches across 26 entries**, including managed
secret values and Google refresh token/client secret. Cleanup exit 0, no
containers, removed job gateway and job network; only default Podman bridge
remains. Logs/artifacts are retained by GitLab and locally under /tmp, not
committed. Syntax checks and diff checks passed after the smoke correction.

Results main remains 05b2a813232d2b3446f30ff17fba6520d7c9215d, with the
historical run 20261006-165222 and RHAISTRAT-1 revise/5-of-8/needs-attention
unchanged. No Jira reset or processed-RFE rerun occurred. M6 remains an actual
4.8 run. No DNS failure occurred in these smoke attempts; the intermittent
nested DNS bug remains open and this is not evidence of a causal fix.

**Pre-M8 gate complete.** Next milestone work needs its own M8 scope; none
was started here.
