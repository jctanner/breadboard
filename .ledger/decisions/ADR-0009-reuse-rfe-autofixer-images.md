# ADR-0009: Reuse rfe-autofixer's images for the strategy POC

## Status

Accepted by user direction on 2026-10-05.

## Decision

Add M4.1 to replace the custom CI and sandbox images introduced in M4 with
rfe-autofixer's Fullsend job image and imported harness sandbox image. Use
its matching supervisor configuration and verify the actual binary versions.
Continue supplying Fullsend from our entrypoint feature branch.

This supersedes the plan's instruction to build a strategy-specific sandbox
image by default. Verify dependencies in the shared images first and record
any concrete incompatibility. Repeat the relevant M2 checks before accepting
the replacement environment; M1/M2 historical results remain unchanged.

## Handoff

M4.1 updates and pushes the existing strat-creator feature branch. M5 seeds
local Jira; M6 uses the tested image references for the real strategy run.
See [M4.1](../tasks/done/strat-creator-rfe-autofixer-images.md).
