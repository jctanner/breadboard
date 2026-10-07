# Task: Publish and verify architecture Git fetch policy fix

## Goal

Complete handoff: publish strat-creator3fd1563 pins and run a no-model sandbox
fetch diagnostic, preserving denied push and other repositories' POST fetches.

## Acceptance

- [x] Normal and validation pins published.
- [x] No-model architecture-fetch diagnostic passes actual sandbox fetch and document checks.
- [x] Denial probes, source provenance, artifacts and cleanup checked.
- [x] Bug/plan receipts updated with live evidence and limitations.

## Status

Done. Uses existing local admin bootstrap; no transcript credential search.
No Jira or model work is selected. Previous4021 review results remain unchanged.

## First diagnostic

Normal pin published8c7f6a2; validationc2c6562a, pipeline2069/build4024success,
architecture4025failed on a diagnostic assertion, not the fetch. Fetch exit0
in4.4s, commit4df4a8a8, rhoai-3.6-ea.2,1025 docs/78,291,598 bytes and36 overlays/
418,085 bytes. Supervisor decisions allow context upload-pack and deny
receive-pack/other-repo upload-pack; both denial probes403. No model transcripts.
Artifacts scan zero managed credential hits,26 entries.

Failure: cone-mode keeps architecture/early-access, a Git symlink (120000)
pointing to rhoai-3.6-ea.2; is_dir() followed it and counted a second version.
Confirmed upstream tree/blob at fetched commit. Corrected diagnostic to count
non-symlink directories and report aliases. Offline regression still detects
an actual extra version directory.5 fixture checks pass; syntax/diff clean.
Rerunning live diagnostic with corrected assertion.

## Passing diagnostic

Final validation commit0964954537811fa8bfd0c39d8467e3780c40590e;
pipeline2070/build4026/architecture4027 success. Fetch3.7s, source3fd1563,
HEAD4df4a8a8, rhoai-3.6-ea.2,1025 docs,36 overlays, shallow/blob:none;
actual directories exactly selected version, aliases separately reported.
Supervisor confirms both denial probes and allowed context fetch. Source
artifact hooks enabled; no transcripts. Cleanup exit0, no containers/job network
or pod.27 archive entries zero managed credential hits.5 focused fixture checks
passed; syntax and diff checks pass. No models/RFEs/reviews rerun or edited.
