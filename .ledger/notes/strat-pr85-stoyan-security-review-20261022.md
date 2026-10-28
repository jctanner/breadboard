# Stoyan's PR #85 security review

## Bottom line

Stoyan's central finding is valid. Our sandbox has a Jira write token and can
change the code and inputs used by its guards. Those guards catch mistakes;
they are not a security boundary against a compromised agent. The trusted host
validator can reject a run, but Jira writes can already have happened.

The proposed host-only Jira writer fits the existing Claude Workflow and
Fullsend entrypoint. It does not require bringing back the scripted executor or
obtaining the rejected custom-entrypoint feature. It is a significant change to
where data is read and published, rather than another hook repair.

The initial assessment involved no implementation, paid model call, reviewer
reply, thread resolution or production cutover. The owner subsequently approved
the scope comment recorded below; it has now been posted and verified.

**Scope correction after discussion:** the user wants this migration balanced
against rfe-autofixer's existing deployment, without making strat-creator the
first adopter of an entire new security architecture. The host-only writer
below remains an unapproved option. Verification of a finding is not acceptance
of every proposed remedy. Keep independent fixes small and identify shared
platform risks separately from strategy-specific differences.

## Review and source

- [Stoyan's comment](https://github.com/fullsend-ai/strat-creator/pull/85#issuecomment-6341322570),
  author `stoniko`, ID `6341322570`, October 22, 2026 at 12:57:49 UTC.
- Complete current discussion fetched: 131 entries, consisting of 15 regular
  comments, 33 reviews and 83 inline comments. Stoyan has one architectural
  comment in that inventory. Fifteen entries are new relative to our previous
  116-entry export; the others include bot follow-ups.
- Assessed fork branch `feat/s1-workflow-hardening`, clean local checkout and
  verified remote PR head `85e830713e21fbea74518e87e6d62df0355c7234`.
- Harness pins Fullsend 0.47.1, Claude Code 2.1.296 and, in the current CI path,
  OpenShell 0.0.112-rhaiv.0. Stoyan's dynamic sandbox tests used Claude Code
  2.1.306 and OpenShell 0.1.2. Keep that distinction when citing his tests.

Evidence, including the full export, original comment, offline reproduction,
code extracts and SHA-256 manifest:
`var/run-data/20261022-strat-pr85-stoyan-security-review/`.

## Comparison with current rfe-autofixer

Read current real GitLab main on October 22, commit
`efc285d7b3f69a8aac668e03adb81fdb0026b536`, rather than relying on our older local
clone. Its config points to rfe-creator `83cbc27`; verified the registered
harness and base-policy hashes. Also checked current rfe-creator main
`36ef1a0`. No agent or CI job was launched.

| Aspect | rfe-autofixer Fullsend path | Current strat-creator Fullsend path |
| --- | --- | --- |
| Writable workspace | Shared base policy allows `/sandbox` and `/tmp`, with `include_workdir: true` | Same filesystem permissions |
| Google credential | Raw service-account file copied to `/tmp/.gcp-credentials.json` | Same pattern |
| Vertex egress | Pinned harness uses the same shared Vertex profile with `*.googleapis.com` | Same pinned shared profile |
| Jira authority | Declares a read-only Jira profile; supplies Jira token through a provider, not `env.sandbox` | Raw token in `env.sandbox`; Python uses opaque TLS egress and performs writes |
| Jira publication | Outer CI calls host `scripts/submit.py` after Fullsend; this Fullsend job uses `--dry-run` | Workflow helpers write during execution, before final host validation |
| Qualification | Fullsend 0.43.0, manual dry-run job; all ten Fullsend jobs in latest 100 project jobs are unstarted | Fullsend 0.47.1; actual real-runner live smoke and publication verified |

Sources: [pipeline at inspected commit](https://gitlab.com/redhat/rhel-ai/agentic-ci/rfe-autofixer/-/blob/efc285d7b3f69a8aac668e03adb81fdb0026b536/.gitlab-ci.yml),
[pinned harness](https://github.com/fullsend-ai/rfe-creator/blob/83cbc27e23a99bf6cb5b8a7984a17f882b61bfb1/.fullsend/rfe-creator/rfe-creator.yaml),
[Jira profile](https://github.com/fullsend-ai/rfe-creator/blob/83cbc27e23a99bf6cb5b8a7984a17f882b61bfb1/.fullsend/rfe-creator/jira-profile.yaml),
[shared filesystem policy](https://github.com/fullsend-ai/agents/blob/11dd3ad15ab5033fd04661d7faf6f7af45548d2f/policies/base.yaml).

The legacy non-Fullsend rfe-autofixer path is different: `runner.py` explicitly
passes `JIRA_TOKEN` through `extra_env` and `.agentic-ci/openshell-policy.yml`
adds read-write Jira egress. Those are valid comparisons for the existing
operational risk model, but not evidence that its Fullsend path permits the
same writes as ours. Conversely, the Fullsend read-only declaration is not
proof of runtime enforcement or successful production use. We inspected
configuration, not the actual contents/scopes of deployed credentials.

This comparison supports keeping a writable working directory and separating
shared GCP/profile risks from this migration's business behavior. It also
shows a real Jira authority difference to discuss explicitly. rfe-autofixer
does not establish a precedent for the full immutable-plugin/interpreter or
effects-plan architecture described in the review. The owner has chosen to
keep this PR focused on the Workflow migration, concrete defects and accurate
documentation of its trust assumptions. Host-only publication remains a
separate proposal; this scope decision does not depend on reviewer agreement.

Comparison evidence is separately archived at
`var/run-data/20261022-rfe-autofixer-security-comparison/`; the earlier sealed
review archive remains unchanged and contains the initial assessment.

## Owner scope comment posted

The user approved the drafted owner response and explicitly authorized posting
it. Posted once as `jctanner` on October 22, 2026 at 16:04:01 UTC:
[comment 6345317940](https://github.com/fullsend-ai/strat-creator/pull/85#issuecomment-6345317940).
Authenticated API read-back verifies the exact approved wording, author and
target PR. SHA-256 of the posted body:
`9c548f8e6822237364bc34c44b37bc9b360285e29fc80da6fbbadabdb1e5018d`.

The comment acknowledges the finding, states the owner's migration scope,
distinguishes rfe-autofixer's Jira path, and leaves host-only publication as a
follow-up proposal. No implementation, review dismissal, thread resolution,
paid run or production change accompanied the comment.

## Findings checked against current code

| Finding | Assessment | Evidence and implication |
| --- | --- | --- |
| Hooks import agent-editable workspace code | Confirmed in source | The plugin freshness, completion and refinement adapters prepend workspace `scripts/` to `sys.path`. The completion adapter delegates its decision to `strat_pipeline_outcome.guard`. |
| Removing run input bypasses safeguards | Reproduced locally | `strat_side_effects.context()` returns no run context when `tmp/strat-input.json` is absent and `STRAT_EFFECTS_DIR` is unset. The harness does not set that fallback. Dry-run refusal, ownership checks and journaling then disappear. The freshness hook also returns success without the file. |
| Moving helpers into the plugin establishes an immutable boundary | Rejected as a sufficient fix | Fullsend 0.47.1 launches Claude with `--plugin-dir` and `--dangerously-skip-permissions`. Our policy grants writes under `/sandbox`, including uploaded plugins. A raw Jira token would still permit direct API calls even if all hooks were immutable. |
| Plugin/interpreter/settings tampering works in the deployed versions | Partially verified, not fully reproduced | The source and policy support the architectural concern. The detailed plugin upload, Python `sitecustomize` and mid-session settings demonstrations are Stoyan's tests on the versions above. We did not reproduce that entire chain in our pinned image. |
| Host checks occur too late to prevent unexpected Jira writes | Confirmed | `validate_result.py` checks final input, artifacts, progress and expected Jira state after execution. Restoring an input file hides its temporary absence. Expected-state readback is not an audit of every write the token permitted. |
| Sandbox holds useful external credentials | Confirmed | All three harnesses place Jira credentials in `env.sandbox` and copy the raw GCP credential to `/tmp/.gcp-credentials.json`. Jira Python egress is an opaque TLS tunnel. The pinned Vertex profile allows `*.googleapis.com`. |
| Results-repo publication has the same redaction as CI export | False | `post-strategy.sh` hands off artifacts and prepares/pushes the bundle without the CI export's redaction step. Arbitrary generated output needs its own publication controls. This is a potential leak path, not evidence of an observed secret leak. |
| Existing dry-run support is already a complete offline mode | False | `strat_freshness.jira_rfe()` requires live Jira access and prepared runs use live freshness. Synthetic STRAT handling solves only part of the problem. Host snapshots, skill reads, resume state and placeholder mapping need explicit changes. |

The existing host boundary does provide useful protection: validation imports
trusted host code, compares against host-only run state, and handoff accepts
allowlisted regular data files rather than executing downloaded workspace
scripts. Preserve those protections. They do not make earlier Jira mutations
safe or prove that the reported specialist agents actually ran.

### Offline reproduction

Ran the actual `strat_side_effects.py` and plugin freshness hook from the
reviewed revision in a temporary directory, using an in-memory fake write:

1. With dry-run input present, the helper refused the write; zero writes.
2. Renamed the input file, leaving `STRAT_EFFECTS_DIR` unset.
3. The helper accepted a simulated write to a ticket outside the acquired set.
   `check_owner()` returned without checking and no ledger was created.
4. The real freshness hook returned exit 0 for a replay request with no input.
5. Restored the input and verified that its bytes matched the original.

No Jira, Google Cloud, model service or other remote API was called by the
reproduction. This demonstrates the control-path bypass, not an observed attack
or a paid Claude prompt-injection test. The normal missing-input behavior also
supports interactive local use, so globally rejecting every missing file would
need a reliable way to distinguish local use from a managed run. An editable
flag alone would not provide the missing security boundary.

## Unapproved architectural option: host-only Jira writer

This is a dependency order if that architecture is selected, not an instruction
to implement it as part of the current review fixes. First resolve the scope
against the rfe-autofixer comparison and the user's incremental-change preference.

1. **Define the host publishing contract and fixtures.** Keep immutable host
   selection/ownership/freshness state. Specify a small effects plan for allowed
   business operations, labels, targets and artifact files. Targets come from
   the acquired run, not arbitrary URLs or raw HTTP supplied by the model.
   Reject unsupported actions, changed inputs and invalid output before any
   strategy publication. Host pre-script lock writes remain intentional.
2. **Prepare offline inputs and adapt the Workflow.** Host-fetch RFEs, comments,
   existing STRAT descriptions, attachments and SME context. Sandbox skills
   read that snapshot and write artifacts plus the plan. Separate offline
   generation from the user's dry-run setting; do not mislabel a live request
   as dry-run to obtain placeholder behavior. Preserve interactive local skills.
3. **Implement and test host-only apply.** Recheck freshness and ownership;
   clone/update/comment/attach/label through trusted helpers and a host-only
   idempotence ledger. Map local placeholders to real keys consistently across
   artifacts, reviews, progress and publication. A lost write response must
   stop for reconciliation, not cause a duplicate. Preserve recovery evidence
   when CI fails; retrying publication should not require another model run.
4. **Remove sandbox Jira authority and narrow inference egress.** Remove Jira
   credentials and endpoints in all three harnesses once the offline path and
   host writer are ready. Add the proposed runtime read privilege and an
   explicitly named custom Vertex profile. Then test denial of direct Jira
   requests, unexpected targets and unused Google hosts without model inference.
5. **Simplify guards and qualify the complete path.** Retain cheap checks that
   improve agent work and explain their quality/recovery role honestly. Redact
   or reject known credentials before building/sealing published bundles. Run
   local adversarial/failure fixtures first, then qualify the changed inference
   and real CI publication path in an explicitly authorized smoke run. No cutover
   is implied by this assessment.

Do not remove the current guards before the host replacement exists. Keep the
numeric scores as the sole approval gate and preserve reviewer dissent. This
review does not authorize a change to those business rules.

## Details to retain or qualify in Stoyan's proposal

- **Runtime read privilege is useful but separate.** Fullsend's
  `privilege_levels: {runtime: read}` controls the minted repository credential.
  It does not downgrade `JIRA_TOKEN` or the uploaded Google service-account key.
- **Narrow model egress is feasible, but needs qualification.** Stoyan tested
  custom profiles through Fullsend's dummy runtime and OpenShell 0.1.2. For our
  global Vertex configuration he proposes `aiplatform.googleapis.com` and
  `oauth2.googleapis.com`, restricted to Claude/Node. He did not make a real
  Vertex model call. Check the exact pinned stack and any future regional
  endpoint before declaring the replacement qualified. Avoid Fullsend's reserved
  profile/provider names and record the upstream derivation for version bumps.
- **GCP credentials still remain.** Removing Jira authority materially reduces
  risk; it does not make the sandbox credential-free. Google IAM permissions
  and allowed inference calls still matter even with a hostname allowlist.
- **Fail-open hooks are not an automatic requirement.** Once trusted host
  validation is authoritative, optional quality-hook infrastructure failures
  may be tolerable. Missing required evidence or invalid business outputs must
  still stop host apply. Decide per check rather than making all checks fail open.
- **Hashes still have an audit role.** They can detect accidental corruption
  and bind validated outputs to published bytes. Sandbox-produced hashes cannot
  establish specialist authenticity against a malicious sandbox. Dropping every
  hash is not necessary to move Jira authority to the host.
- **Output is still untrusted content.** A validated plan must not become an
  arbitrary write proxy. Mentions, links, attachments and secret-bearing content
  need publication policy. A known-secret scanner alone does not prove that no
  data can leak. Prefer removing credentials over relying on redaction alone.
- **Freshness is conflict detection, not a transaction.** Jira has no general
  compare-and-swap for these writes. Host freshness checks reduce stale updates
  but leave a check-to-write window; do not claim otherwise.

## Separate new bot comments

The full fetch also surfaced these pending items, separate from Stoyan's
architecture review. They were not fixed during the initial assessment.
**Follow-up:** the owner-authorized bounded repairs are now implemented locally
with 1,230 tests passing; see [implementation notes](strat-pr85-scoped-review-fixes-20261022.md).
The parser, SME boundary, ownership export and default-mode defects below are
repaired. Org Pulse URL/redirect forwarding is repaired while the explicitly
approved certificate exception remains. The user then authorized commit/push:
signed-off `32700ec` is verified as PR #85 head, with clean worktree and zero
staged credential findings. No thread resolution is implied.

- [4344160882](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4344160882):
  skipped-ticket table parser does not recognize the `RFE Key` header.
- [4344160887](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4344160887):
  missing Strategy heading can place SME input inside a section that later gets dropped.
- [4344160895](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4344160895):
  failed-run export omits the lock ownership sidecar needed for later cleanup.
- [4344160899](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4344160899):
  direct shared-harness invocation defaults to live mode when dry-run is unset,
  unlike the safer CI wrapper default.
- [4344160878](https://github.com/fullsend-ai/strat-creator/pull/85#discussion_r4344160878):
  Org Pulse TLS bypass and credential forwarding. The temporary certificate
  exception was explicitly requested by the user. Keep that decision distinct
  from hardening URL scheme/origin and redirect handling; do not silently reverse
  the approved exception.

Protected-path/human-approval requirements remain external review requirements.
Passing earlier smoke tests does not resolve the newly raised security claims.
