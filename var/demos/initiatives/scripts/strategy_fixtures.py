#!/usr/bin/env python3
"""Write synthetic strategy attachments for the signed-off Initiatives (S8 fixture).

epic-creator's rhai-initiative workload (PR #40) reads an Initiative's strategy
only from its `{key}-strategy.md` attachment (description_fallback: false). The
catalogue's signed-off Initiatives (archetypes S-signed*) model strategies that
already went through strat-creator and human sign-off, so their attachments are
fixture data, not model output. The format is the one strat-creator #124's
push_strategy.py writes on a same-ticket Initiative: the Strategy section, a blank
line, then the Staff Engineer / SME Input section; no frontmatter. Headings follow
the strategy S7 produced. Every name and fact here is synthetic.

Writes generated/strategies/<KEY>-strategy.md for each signed-off Initiative.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

# Synthetic technical content per catalogue area (codenames are fictional).
CONTENT = {
    "I22": {
        "tldr": "Ship a default-deny network policy baseline for every workload namespace the platform "
                "creates, with an allow list generated from each component's declared service graph, and "
                "an audit-only rollout mode before enforcement.",
        "approach": [
            ("Baseline policy set", "The platform operator installs a default-deny ingress and egress "
             "NetworkPolicy plus DNS and API-server allowances into each managed namespace."),
            ("Generated allow lists", "Each component declares its peers in a manifest annotation; a "
             "controller renders allow policies from those declarations and reconciles drift."),
            ("Audit-only mode", "A per-namespace mode label switches the baseline to log-only so teams "
             "can review would-be denials before enforcement."),
            ("Dashboard and alerts", "Denied-flow counters are exported as metrics and surfaced on the "
             "existing platform dashboard, with an alert for sustained denials after enforcement."),
        ],
        "components": ["synth-networking (controller, policy templates)", "synth-security (review of the "
                       "baseline set)", "synth-dashboard (denial panels)"],
        "hlrs": ["Install the default-deny baseline into every managed namespace on creation and upgrade.",
                 "Render allow policies from component peer declarations and reconcile drift within 5 minutes.",
                 "Provide an audit-only mode per namespace, with denials logged but not enforced.",
                 "Export denied-flow metrics and add dashboard panels and one alert rule.",
                 "Document the peer declaration format and the migration from audit-only to enforce."],
        "deps": ["The cluster CNI must support NetworkPolicy logging (verified on the reference CNI)."],
        "risks": ["Undeclared peers in older components cause denials at enforcement; mitigated by the "
                  "audit-only phase and a pre-enforcement report."],
    },
    "I23": {
        "tldr": "Rotate platform service credentials automatically on a schedule and on demand, with "
                "dual-validity windows so services never see a hard cut-over.",
        "approach": [
            ("Rotation controller", "A controller owns rotation for secrets labelled for management and "
             "writes the new version alongside the old one."),
            ("Dual-validity window", "Consumers accept both versions for a configurable window; the old "
             "version is revoked when every consumer reports the new one."),
            ("On-demand rotation", "Operators trigger an immediate rotation through a custom resource, "
             "for incident response."),
        ],
        "components": ["synth-security (rotation controller)", "platform services consuming managed secrets"],
        "hlrs": ["Rotate managed secrets on a schedule with a configurable period.",
                 "Keep the previous version valid until every consumer reports the new one.",
                 "Support on-demand rotation through a custom resource.",
                 "Record every rotation in the audit log."],
        "deps": ["Consumers must reload credentials without a restart, or tolerate a rolling restart."],
        "risks": ["A consumer that never reports the new version blocks revocation; a maximum window "
                  "forces revocation and raises an alert."],
    },
    "I24": {
        "tldr": "Generate and publish an SBOM for every shipped image at build time, attach it to the "
                "image as a signed attestation, and expose it through the product's documentation index.",
        "approach": [
            ("Build-time generation", "The image build pipeline generates an SPDX SBOM per image and "
             "stores it next to the build record."),
            ("Signed attestation", "The SBOM is attached to the image digest as a signed attestation, "
             "verifiable with the published public key."),
            ("Publication index", "A per-release index lists every image digest with a link to its SBOM."),
        ],
        "components": ["synth-images (build pipeline, attestation)", "release documentation index"],
        "hlrs": ["Generate an SPDX SBOM for every shipped image at build time.",
                 "Attach the SBOM to the image digest as a signed attestation.",
                 "Publish a per-release index of digests and SBOM links.",
                 "Fail the release gate when an image lacks a verified SBOM."],
        "deps": ["The build system must expose the final image digest to the generation step."],
        "risks": ["SBOM generation adds build time; generation runs in parallel with image scanning."],
    },
}

STAFF_INPUT = """## Staff Engineer / SME Input

*Add technical corrections, architectural direction, component preferences, or domain expertise below. \
Write in declarative, cumulative form — statements that remain valid across refinement iterations. \
This input takes priority over architecture context when they conflict. \
After review: address findings, then remove the needs-attention label from Jira.*"""


def strategy(item: dict) -> str:
    c = CONTENT[item["id"]]
    parts = ["## Strategy (AI Generated by Agentic SDLC Pipeline)", "", "### TL;DR", "", c["tldr"], "",
             "### Technical Approach", ""]
    for n, (title, text) in enumerate(c["approach"], 1):
        parts += [f"#### {n}. {title}", "", text, ""]
    parts += ["### Affected Components", ""] + [f"- {x}" for x in c["components"]] + [""]
    parts += ["### High Level Requirements", ""] + [f"- HLR-{n}: {x}" for n, x in enumerate(c["hlrs"], 1)] + [""]
    parts += ["### Dependencies", ""] + [f"- {x}" for x in c["deps"]] + [""]
    parts += ["### Non-Functional Requirements", "", "- No measurable latency regression on the "
              "platform's reference workloads.", ""]
    parts += ["### Acceptance Criteria (Proposed — requires PM/Engineering validation)", ""]
    parts += [f"- HLR-{n} is demonstrated in the release candidate." for n in range(1, len(c["hlrs"]) + 1)] + [""]
    parts += ["### Effort Estimate", "", "M (one to two sprints for two teams).", ""]
    parts += ["### Risks", ""] + [f"- {x}" for x in c["risks"]] + [""]
    parts += ["### Open Questions", "", "- None blocking.", ""]
    return "\n".join(parts).rstrip() + "\n\n" + STAFF_INPUT + "\n"


def main() -> int:
    catalogue = yaml.safe_load((ROOT / "catalogue.yaml").read_text())
    issues = json.loads((ROOT / "generated" / "issues.json").read_text())["issues"]
    by_label = {lbl: i["key"] for i in issues for lbl in i["fields"]["labels"] if lbl.startswith("cc75-fx-")}
    out = ROOT / "generated" / "strategies"
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for item in catalogue["initiatives"]:
        if not str(item.get("archetype", "")).startswith("S-signed"):
            continue
        key = by_label[f"cc75-fx-{item['id'].lower()}"]
        path = out / f"{key}-strategy.md"
        path.write_text(strategy(item))
        written.append((item["id"], key))
    for item_id, key in written:
        print(f"{item_id} -> {key}-strategy.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
