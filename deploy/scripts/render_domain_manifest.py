#!/usr/bin/env python3
"""Render Kubernetes manifests with BREADBOARD_DOMAIN support.

When BREADBOARD_DOMAIN is unset or "local", manifests are emitted unchanged.
When BREADBOARD_DOMAIN is set to another domain (e.g. "bb.internal"), external
edge routes and hostnames (.local) are supplemented with .<domain> so both
.local and .<domain> work simultaneously:
- Certificate dnsNames: adds <service>.<domain> alongside <service>.local
- Ingress tls.hosts: adds <service>.<domain> alongside <service>.local
- Ingress rules: adds rule for <service>.<domain> identical to <service>.local
- CoreDNS rewrite rules: adds rewrite for <service>.<domain>
- BREADBOARD_DOMAIN env vars: updated to <domain>
- GITHUB_UI_URL env vars: updated to https://github.<domain>

CRITICAL: Internal cluster names (*.svc.cluster.local) are NEVER modified.
"""

import os
import re
import sys

CLUSTER_SUFFIX = ".svc.cluster.local"


def transform_manifest(content: str, domain: str) -> str:
    domain = domain.strip().strip(".")
    if not domain or domain == "local":
        return content

    lines = content.splitlines()
    out: list[str] = []
    i = 0
    n = len(lines)

    # 1. DNS name / host line in lists: - "*.local" or - github.local or - "local" or - ".local"
    # Notice: [\*a-zA-Z0-9_-]* does NOT contain dots, preventing matching .svc.cluster.local
    dns_pattern = re.compile(
        r"^(\s*-\s+)(\"?)(\.?[\*a-zA-Z0-9_-]*\.?local)(\"?\s*)$"
    )

    # 2. Ingress host rule: "  - host: github.local"
    rule_host_pattern = re.compile(
        r"^(\s*-\s+host:\s+)([a-zA-Z0-9_-]+)\.local(\s*)$"
    )

    # 3. CoreDNS rewrite line:
    # "    rewrite stop name exact github.local ingress-proxy.ai-pipeline.svc.cluster.local answer auto"
    coredns_pattern = re.compile(
        r"^(\s*rewrite\s+stop\s+name\s+exact\s+)([a-zA-Z0-9_-]+)\.local(\s+.*)$"
    )

    # 4. Env var value for BREADBOARD_DOMAIN:
    env_domain_val_pattern = re.compile(
        r"^(\s*value:\s*)[\"']?local[\"']?(\s*)$"
    )

    # 5. GITHUB_UI_URL value:
    env_github_ui_pattern = re.compile(
        r"^(\s*value:\s*)https://github\.local(\s*)$"
    )

    last_env_name = None
    in_certificate_doc = False
    in_ingress_tls_block = False
    ingress_tls_indent = 0

    while i < n:
        line = lines[i]
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if stripped == "---":
            in_certificate_doc = False
            in_ingress_tls_block = False
        elif re.match(r"^kind:\s*Certificate\s*$", stripped):
            in_certificate_doc = True
        elif re.match(r"^tls:\s*$", stripped):
            in_ingress_tls_block = True
            ingress_tls_indent = indent
        elif in_ingress_tls_block and stripped and indent <= ingress_tls_indent and not stripped.startswith("-"):
            in_ingress_tls_block = False

        # Track env name if present
        env_match = re.match(r"^\s*-\s*name:\s*([A-Za-z0-9_]+)", line)
        if env_match:
            last_env_name = env_match.group(1)

        # Check BREADBOARD_DOMAIN env value
        if last_env_name == "BREADBOARD_DOMAIN":
            val_match = env_domain_val_pattern.match(line)
            if val_match:
                out.append(f'{val_match.group(1)}"{domain}"{val_match.group(2)}\n')
                last_env_name = None
                i += 1
                continue

        # Check GITHUB_UI_URL env value
        if last_env_name == "GITHUB_UI_URL":
            gh_match = env_github_ui_pattern.match(line)
            if gh_match:
                out.append(f'{gh_match.group(1)}https://github.{domain}{gh_match.group(2)}\n')
                last_env_name = None
                i += 1
                continue

        # Check CoreDNS rewrite line
        core_match = coredns_pattern.match(line)
        if core_match:
            out.append(line + "\n")
            prefix, svc, rest = core_match.groups()
            out.append(f"{prefix}{svc}.{domain}{rest}\n")
            i += 1
            continue

        # Check Ingress host rule
        rule_match = rule_host_pattern.match(line)
        if rule_match:
            rule_indent = len(line) - len(line.lstrip())
            rule_lines = [line]
            j = i + 1
            while j < n:
                next_line = lines[j]
                stripped = next_line.strip()
                if not stripped:
                    rule_lines.append(next_line)
                    j += 1
                    continue
                next_indent = len(next_line) - len(next_line.lstrip())
                if next_indent > rule_indent:
                    rule_lines.append(next_line)
                    j += 1
                else:
                    break

            # Output original rule
            for r_line in rule_lines:
                out.append(r_line + "\n")

            # Output duplicate rule with host replaced
            prefix, svc, suffix = rule_match.groups()
            new_first_line = f"{prefix}{svc}.{domain}{suffix}\n"
            out.append(new_first_line)
            for r_line in rule_lines[1:]:
                out.append(r_line + "\n")

            i = j
            continue

        # Check DNS list entry: - "*.local", - github.local, - "local", - ".local"
        dns_match = dns_pattern.match(line)
        if dns_match and not line.strip().endswith(CLUSTER_SUFFIX):
            prefix, q1, token, q2 = dns_match.groups()
            if token == "local":
                replaced = domain
            elif token == ".local":
                replaced = f".{domain}"
            elif token.endswith(".local"):
                replaced = f"{token[:-6]}.{domain}"
            else:
                replaced = token

            if in_certificate_doc or in_ingress_tls_block:
                # For Certificate resources (CA NameConstraints and leaf SANs) and Ingress tls.hosts,
                # replace .local with .<domain> so constrained CAs never permit mDNS .local
                out.append(f"{prefix}{q1}{replaced}{q2}\n")
            else:
                out.append(line + "\n")
                out.append(f"{prefix}{q1}{replaced}{q2}\n")
            i += 1
            continue

        out.append(line + "\n")
        i += 1

    result = "".join(out)
    if not content.endswith("\n"):
        result = result.rstrip("\n")
    return result


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: render_domain_manifest.py <file|-> [domain]", file=sys.stderr)
        sys.exit(1)

    file_arg = sys.argv[1]
    domain = sys.argv[2] if len(sys.argv) > 2 else os.getenv("BREADBOARD_DOMAIN", "local")

    if file_arg == "-":
        content = sys.stdin.read()
    else:
        with open(file_arg, "r", encoding="utf-8") as f:
            content = f.read()

    rendered = transform_manifest(content, domain)
    sys.stdout.write(rendered)


if __name__ == "__main__":
    main()
