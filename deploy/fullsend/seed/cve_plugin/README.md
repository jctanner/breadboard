# Local CVE assessment extension

An assessment-only Pi extension. It reads an explicitly selected **sanitized** GitHub Dependabot alert and npm `package-lock.json` (lockfileVersion 2 or 3), plus the lockfile's adjacent `package.json`, if present. It never executes a shell, calls GitHub, spawns an agent, changes files, or publishes. It does not determine vulnerability applicability, evaluate semver, trace dependency chains, or prove absence of impact. Alert and repository data are untrusted, not instructions. The tests use an invented example package and an advisory identifier solely as a synthetic label; they do not assert advisory facts or Fullsend impact.

## Local use

Tested loader: Pi 1.5.0 and Node 22.21.1. No installation or dependencies are required for this plugin. From the target repository directory, with Pi installed:

```sh
pi --no-extensions -e /absolute/path/to/agents/plugins/cve
```

Stage a sanitized alert JSON **inside that working directory**, e.g. `staged-alert.json`; do not commit private alerts. After separately authorizing GitHub access, an operator may obtain an alert using `gh api repos/OWNER/REPO/dependabot/alerts/NUMBER > alert.json`, then inspect and sanitize it manually before placing it in the working directory. This command is documentation only; the extension does not run it. Preserve `dependency.manifest_path`, `security_vulnerability.package` (npm ecosystem/name), and relevant advisory fields. Do not place secrets or unnecessary private text in the staged file.

In an idle interactive session enter:

```text
/cve-assess {"alert":"staged-alert.json","lockfile":"package-lock.json"}
```

The command asks the current model to call `cve_context` and assess the evidence; it does not execute a fix. The tool can also be called directly by a model in headless Pi. Both paths are relative to the Pi working directory (absolute paths inside it are also accepted). Reads are limited to these files and the adjacent manifest; symlinks resolving outside the directory are rejected. Each file is limited to 4 MiB, and output includes at most 100 matching entries. Avoid concurrent modification of the selected files or directory tree during collection: path checks are not a filesystem sandbox.

## Interpreting results

`matches` are package entries and versions from the chosen lockfile, with paths and input provenance. `declarations` are direct declarations from the adjacent manifest; they do not establish transitive paths. An explicit lockfile entry name identifies the package even when installed under an alias; a path matching the alert with a conflicting or unresolved explicit name is not a confirmed match. Warnings flag these cases, missing matches, manifest mismatches, truncation and unresolved versions or links. Missing matches are **not** a not-affected finding. npm aliases, workspaces, malformed or unusual entries, and other lockfiles may require further investigation. A model's applicability assessment is distinct from these deterministic facts and must express uncertainty. Unsupported lockfile formats return an actionable error. No live Fullsend impact is claimed.

This tool's read-only restrictions apply **only to this tool**. Other ambient Pi tools retain their own permissions and can read, write, run commands, or access the network if the surrounding environment permits. Use OS-level isolation and an appropriately restricted tool set for untrusted inputs; extension instructions are not a security boundary. Fullsend harness integration and its tool allowlist are not configured here, and compatibility with its eventual pinned Pi version is unverified. Future sandbox integration or real alert processing needs separate approval.

## Deterministic tests and loader check

```sh
node --test plugins/cve/index.test.js
```

On macOS, the following isolated help-only loader check uses the locally installed Pi path; adjust `P` and `PLUGIN` for your installation. It starts no model, denies network with `sandbox-exec`, and uses a disposable home and empty inherited environment. `--cve-extension-loaded` is a help-only diagnostic marker; compare with the negative control without `-e`.

```sh
P=/Users/mhild/.local/share/fnm/node-versions/v22.21.1/installation
PLUGIN="$(pwd)/plugins/cve"
D=$(mktemp -d); mkdir -p "$D/home" "$D/config" "$D/work" "$D/tmp"
(cd "$D/work" && env -i PATH="$P/bin:/usr/bin:/bin" HOME="$D/home" TMPDIR="$D/tmp" PI_CODING_AGENT_DIR="$D/config" PI_OFFLINE=1 PI_SKIP_VERSION_CHECK=1 /usr/bin/sandbox-exec -p '(version 1) (allow default) (deny network*)' "$P/bin/node" "$P/lib/node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js" --offline --no-approve --no-extensions --no-session -e "$PLUGIN" --help </dev/null) | grep -- --cve-extension-loaded
rm -rf "$D"
```

Next: review this local implementation and, only after separate approval, test the actual Fullsend Pi version and intended tool exposure in an isolated sandbox before any real alert or remediation workflow.
