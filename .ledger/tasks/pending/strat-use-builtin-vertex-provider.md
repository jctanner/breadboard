# Task: Migrate strategy CI to Fullsend's built-in Vertex provider

## Goal

Remove the reserved provider-profile warning while preserving functional Vertex
inference and credential refresh with the existing Breadboard credentials.

## Context

Job 4017 logged at 2026-10-07T04:00:24Z:

> provider profile "fullsend-vertex-ai" will be rejected in a future release:
> the id is reserved for the copy built into fullsend. Your copy is still used
> for now. Remove it from openshell.profiles and declare the bare provider name
> "vertex-ai" instead

The strategy harness already declares `providers: [vertex-ai]` but also imports
`.fullsend/profiles/fullsend-vertex-ai.yaml` through `openshell.profiles`.
The custom profile defines Google OAuth refresh-token credentials and refresh
material. Fullsend's embedded profile supplies endpoints/binaries; its credential
setup may be provided elsewhere in the runtime. Equivalence has not yet been
verified. The pinned Fullsend bdedebeaf still accepts our custom copy.

## Approach

1. Read component instructions and compare custom profile with the built-in
   provider's complete credential/bootstrap/refresh path at the pinned revision.
2. Verify existing Breadboard Vertex credentials remain supported, including
   token renewal during long runs. Document any required version or setup change.
3. Remove the reserved profile import from all affected harnesses and fixtures;
   retain the bare `vertex-ai` provider. Remove the copied profile if unused.
4. Update tests/provenance, push component changes, update immutable caller pins,
   and publish future CI configuration without replaying processed issues.
5. Use a bounded diagnostic to verify inference, refresh behavior, warning
   absence, credential masking and cleanup. Record limits of the refresh proof.

## Acceptance criteria

- [ ] Built-in credential/bootstrap/refresh compatibility established with evidence.
- [ ] No reserved `fullsend-vertex-ai` profile import remains in affected callers.
- [ ] Vertex remains the provider; existing credentials and exact Opus 4.6 pin retained.
- [ ] Fullsend security hooks and workflow gates remain enabled.
- [ ] Required component tests and `git diff --check` pass.
- [ ] Source/pins published and diagnostic evidence recorded; warning absent.
- [ ] Plan and ledger updated with findings and remaining limitations.

## Files likely involved

- `checkouts.fullsend_prototype/jctanner.strat-creator/.fullsend/harness/*.yaml`
- `checkouts.fullsend_prototype/jctanner.strat-creator/.fullsend/profiles/fullsend-vertex-ai.yaml`
- Strat-creator entrypoint tests and CI provenance documentation
- `checkouts.fullsend_prototype/jctanner.fullsend/internal/cli/run.go`
- Fullsend embedded Vertex provider/profile and credential refresh implementation
- `var/demos/fullsend-entrypoint-poc/` caller pins and diagnostic fixtures

## Constraints

Preserve the user's overriding Vertex requirement and existing Breadboard
credential path. Do not switch provider, silently change models, expose secrets,
reset service data or replay processed RFEs. Coordinate deployment with active
CI runs. This task records future work; no migration or diagnostic is performed
when creating it.

## Status

Pending.
