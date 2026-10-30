# Task: Lima VM and Tailnet DMZ Environment

## Status

Done, 2026-10-30.

## Context

Implement the plan defined in [lima-tailnet-environment-plan.md](../../plans/lima-tailnet-environment-plan.md) and [ADR-0014](../../decisions/ADR-0014-lima-tailnet-dmz-environment.md).

## Work Packages

- [x] WP1: Lima VM definition (`deploy/lima/breadboard-vm.yaml`) with Rosetta binfmt
- [x] WP2: Ingress domain parameterization (`BREADBOARD_DOMAIN`) across reverse proxy, cert-manager, and dashboard
- [x] WP3: Full stack deployment inside Lima VM (`make host-deploy-all`)
- [x] WP4: Tailnet DMZ configuration (`tag:breadboard`), Split DNS routing, and remote browser verification

## Verification

- Breakpoint B1: Docker runs x86_64 container via Rosetta inside Lima VM.
- Breakpoint B2: Go reverse proxy & cert-manager route custom `BREADBOARD_DOMAIN`.
- Breakpoint B3: `make host-status` shows all ~15 pods running in `ai-pipeline`.
- Breakpoint B4: Remote client opens `https://dashboard.bb.internal` over Tailscale; lateral egress from VM is refused by ACL.
