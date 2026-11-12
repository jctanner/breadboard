---
name: breadboard-ops
description: Operate the Breadboard K3s cluster, emulators, and Fullsend agent execution stack on the selected cluster. Use when checking cluster health, emulator tickets, GitHub Actions workflow runs or job logs, resetting OpenShell state, or running conformance seeders.
---

# breadboard-ops

The `scripts/bb` CLI is the authoritative, version-matched source of truth for Breadboard operations.

Before executing operational tasks, load the full guide and live state:

1. **Load version-matched operational guide:**
   ```bash
   ./scripts/bb --skill
   ```
   This outputs the complete, up-to-date guide covering all CLI subcommands, the 3 Fullsend patch layers, example hardware and thermal rules, and OpenShell 0.1.4 architecture.

2. **Inspect live cluster and emulator state:**
   ```bash
   ./scripts/bb
   ```
   This prints the content-first home view with K3s pod health, physical host thermal status, emulator ticket totals, runner statuses, and recent workflow runs.

If `./scripts/bb` is missing, not executable, or fails to execute, report the exact error and stop — do not guess cluster configuration or bypass safety checks.
All CLI runtime and usage errors follow the AXI TOON structured error contract (`error{code,message,hint}:` on stdout); follow the provided hints to resolve errors.
