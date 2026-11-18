#!/usr/bin/env python3
"""Render the CC-75 synthetic Initiative catalogue into Jira import JSON.

Outputs (deterministic; reruns are byte-identical):
  generated/issues.json   Jira-REST-shaped issues for POST /api/admin/import
  expected.yaml           oracle: discovery sets, skips, child counts, links

All text comes from fixed templates and fictional vocabulary in this file and
catalogue.yaml. No LLM, no real Jira content. The lint at the end refuses to
write output that contains real-looking issue keys in text, people outside the
synthetic roster, or summaries without the [SYNTH] prefix.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]

STATUS_CATEGORY = {
    "New": "new", "Backlog": "new", "To Do": "new",
    "Refinement": "indeterminate", "In Progress": "indeterminate",
    "Review": "indeterminate", "Release Pending": "indeterminate",
    "Closed": "done",
}
OPEN_EXCLUDED = {"Closed", "Resolved"}

VARIANT_LABELS = {
    None: [],
    "opted-in": ["initiative-autofix-opt-in"],
    "rubric-pass": ["initiative-autofix-opt-in", "initiative-autofix-rubric-pass"],
    "needs-attn": ["initiative-autofix-opt-in", "initiative-needs-attention"],
}

# strat-creator initiative-strategy contract (types/initiative-strategy/type.yaml,
# read 2026-11-15 from the #124 head). Mirrored here for the oracle.
STRAT_REQUIRED = {"initiative-autofix-opt-in", "initiative-autofix-rubric-pass"}
STRAT_JQL_EXCLUDED = {"strat-creator-processing", "initiative-needs-attention",
                      "strat-creator-ignore", "initiative-ignore"}
STRAT_TOOL_SKIP = {"strat-creator-rubric-pass", "strat-creator-needs-attention",
                   "strat-creator-processing"}
DECOMP_REQUIRED = {"strat-creator-rubric-pass", "strat-creator-human-sign-off"}
DECOMP_DONE = "epic-creator-auto-decomposed"

STRAT_JQL = (
    'project = RHAISTRAT AND issuetype = "Initiative" AND labels = "initiative-autofix-opt-in" '
    'AND (labels = "initiative-autofix-rubric-pass") AND (labels NOT IN ("strat-creator-processing",'
    '"initiative-needs-attention","strat-creator-ignore","initiative-ignore") OR labels IS EMPTY) '
    'AND status NOT IN ("Closed","Resolved") ORDER BY key ASC'
)

LINK_TYPES = {
    "Blocks": ("is blocked by", "blocks"),
    "Relates": ("relates to", "relates to"),
    "Cloners": ("is cloned by", "clones"),
    "Depend": ("is depended on by", "depends on"),
    "Duplicate": ("is duplicated by", "duplicates"),
    "Incorporates": ("is incorporated by", "incorporates"),
}

WORKSTREAMS = [
    "API contract and design", "Core implementation", "Observability and alerts",
    "Documentation and enablement", "Performance and scale testing", "Security review",
    "Upgrade and migration path", "CI coverage", "Console integration",
    "Rollout behind a feature flag", "Packaging and distribution", "Usage telemetry",
]
PERSONAS = ["platform administrators", "model builders", "release owners",
            "SRE teams", "data scientists", "security reviewers"]
CAPABILITIES = [
    "a documented API with versioned schemas", "per-team quotas and limits",
    "dashboards for the key health signals", "an upgrade path with no manual steps",
    "audit events for every administrative action", "offline and disconnected operation",
    "role-based access aligned with existing groups", "self-service configuration",
    "alerting thresholds that teams can tune", "a rollback path within one release",
]
RISKS = ["dependency on an unreleased upstream component", "capacity on shared CI runners",
         "unclear ownership between two teams", "migration of existing user data",
         "performance on the smallest supported cluster size"]


def pick(seed: str, pool: list[str], n: int) -> list[str]:
    """Deterministic selection of n distinct items from pool."""
    order = sorted(pool, key=lambda item: hashlib.sha256(f"{seed}:{item}".encode()).hexdigest())
    return order[:n]


def iso(anchor: datetime, days_ago: int) -> str:
    return (anchor - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S.000+0000")


def render_description(item: dict) -> str:
    tmpl = item["template"]
    area = item.get("area", "")
    sid = item["id"]
    if tmpl == "empty":
        return ""
    if tmpl == "short":
        return f"TBD; scope for {area} to follow."
    who = pick(sid + "who", PERSONAS, 2)
    caps = pick(sid + "cap", CAPABILITIES, 5)
    risks = pick(sid + "risk", RISKS, 2)
    out: list[str] = []
    benefit = [
        "## Who benefits",
        f"{who[0][0].upper() + who[0][1:]} get a predictable, supported workflow for {area}, with "
        "fewer hand-offs and less time spent on one-off fixes. "
        f"{who[1][0].upper() + who[1][1:]} gain visibility into how {area} behaves across teams, "
        "which today requires asking around or reading logs.",
        f"Today, teams that need {area} assemble it themselves from scripts and internal notes; "
        "the result differs per team, is hard to support, and breaks on upgrade.",
        "",
    ]
    if tmpl in ("fpdor", "freehand", "strategy"):
        out += benefit
    if tmpl == "fpdor":
        out += [
            "## Feature Overview (mandatory - complete while in New status)",
            f"{area} gives {who[0]} and {who[1]} a supported way to work with this capability "
            "without bespoke scripts. This Initiative tracks the product bet end to end.",
            "",
            "## Goals (mandatory - New)",
            *[f"- Provide {c}." for c in caps[:3]],
            "",
            "## Requirements (mandatory - Refinement)",
            "| Requirement | Notes | isMVP? |",
            "| --- | --- | --- |",
            *[f"| {c[0].upper() + c[1:]} | Synthetic requirement {i + 1} | {'Yes' if i < 3 else 'No'} |"
              for i, c in enumerate(caps)],
            "",
            "## Out of Scope",
            f"- Replacing existing tooling outside {area}.",
        ]
    elif tmpl == "freehand":
        out += [
            "## Goal",
            f"Make {area} usable by {who[0]} in day-to-day work, so that {who[1]} no longer "
            "depend on manual workarounds.",
            "",
            "## Scope",
            *[f"- {c[0].upper() + c[1:]}" for c in caps[:4]],
            "",
            "## Success criteria",
            "- Median setup time below 15 minutes for a new team.",
            "- At least 3 internal teams onboarded within one release.",
        ]
        if item.get("table"):
            out += ["", "| Signal | Current | Target |", "| --- | --- | --- |",
                    "| Scale-up latency | 4 min | 60 s |", "| Idle replicas | 30% | 10% |"]
        if item.get("dod"):
            out += ["", "## Definition of Ready", "- Owner and component agreed.",
                    "", "## Definition of Done", "- Shipped behind a flag and documented."]
        if item.get("long"):
            for i in range(1, 31):
                out += ["", f"### Requirement area {i}",
                        f"{area} must handle area {i} for {who[i % 2]}: " +
                        "; ".join(pick(f"{sid}long{i}", CAPABILITIES, 6)) + ".",
                        "Open questions: " + "; ".join(pick(f"{sid}q{i}", RISKS, 3)) + "."]
    elif tmpl == "strategy":
        out += [
            "## Summary",
            f"Establish {area} as the default for every supported deployment.",
            "",
            "## Background",
            f"- Drivers: compliance expectations from {who[0]}, and support load reported by {who[1]}.",
            "- Positioning: closes a gap that customers currently fill with custom tooling.",
            "",
            "## Action items",
            *[f"{i + 1}. Deliver {c}." for i, c in enumerate(caps[:4])],
            "",
            "## Risks & Assumptions",
            *[f"- {r[0].upper() + r[1:]}." for r in risks],
        ]
    elif tmpl == "phased":
        out += [
            "## Problem statement",
            f"{area} decisions are made inconsistently across teams.",
            "1. Decisions are not recorded in one place.",
            "2. Reviews happen too late to change direction.",
            "3. Nobody owns follow-up actions.",
            "",
            "## Refinement Phase", "- Agree the template and the decision owners.",
            "", "## Design and Development Phase", "- Pilot with two teams for one release.",
            "", "## Finalization Phase", "- Publish the process and retire the old checklist.",
        ]
    elif tmpl == "exemplar":
        # Written to pass strategy review. Revised after the first check run (5/8 REVISE): one
        # runtime, REST only, no agent hop or proxy rewiring, export to the existing collector,
        # a defined benchmark, and every boundary the reviewers questioned stated explicitly.
        out = [
            "## Problem",
            "Operators of predictive model-serving endpoints cannot connect a slow client request to what "
            "happened inside the model server. MLServer already creates a server span for each REST "
            "request (its bundled FastAPI OpenTelemetry instrumentation), but on the platform those spans "
            "go nowhere: the exporter is hard-coded to an insecure connection, nothing configures it, and "
            "incoming trace context from the caller is not joined.",
            "",
            "## Who benefits",
            "- Platform operators diagnosing slow requests on predictive InferenceServices served by MLServer.",
            "- Application teams that already trace their own services and want the model call in the same trace.",
            "",
            "## Goal",
            "For an InferenceService that opts in, each sampled REST inference request served by the MLServer "
            "runtime produces an MLServer server span that joins the caller's W3C trace context and is exported "
            "over TLS to the platform's existing data-science-collector, which already forwards traces to Tempo. "
            "One trace then shows the caller's spans and the time spent inside the model server.",
            "",
            "## Scope",
            "- Runtime: MLServer only, the supported MLServer ServingRuntime image, RawDeployment mode.",
            "- Protocol: REST (KServe v2 HTTP) only.",
            "- Workers: spans from the main MLServer process; with parallel workers enabled, inference inside "
            "a worker process is covered by the server span only (see P1 below).",
            "",
            "## Requirements",
            "| ID | Requirement | Acceptance | Priority |",
            "| --- | --- | --- | --- |",
            "| R1 | Opt in per InferenceService with an annotation; odh-model-controller sets the OTEL_* "
            "environment (endpoint, sampler, resource attributes) on the predictor only when it is present | "
            "Without the annotation the predictor pod spec is byte-for-byte unchanged | P0 |",
            "| R2 | MLServer exports spans over TLS, trusting the OpenShift service CA from the namespace's "
            "injected service-CA ConfigMap (downstream patch to the hard-coded insecure exporter) | Spans reach "
            "the collector on 4317 with TLS verification on; a wrong CA produces no export and no request errors "
            "| P0 |",
            "| R3 | The server span joins an incoming W3C traceparent | A request sent with a traceparent "
            "appears in Tempo as a child of the caller's span | P0 |",
            "| R4 | Parent-based ratio sampling, default 1 percent, set per InferenceService by the annotation "
            "value | Measured export rate within 0.5 percentage points of the configured ratio over 10,000 "
            "requests | P0 |",
            "| R5 | The collector NetworkPolicy admits OTLP only from predictor pods (KServe predictor pod "
            "label), and the existing k8sattributes and identity-sanitizing processors set the namespace "
            "attribute | A pod without the label cannot export; a span claiming another namespace is "
            "rewritten to its real one | P0 |",
            "| R6 | Separate inference span inside parallel-worker processes (trace context across MLServer's "
            "worker IPC) | Server span minus inference span equals codec and queue time within 1 ms | P1 |",
            "",
            "## Non-functional requirements",
            "- Overhead: at 1 percent sampling, added p95 latency below 2 ms in the benchmark below.",
            "- Privacy: no request or response payload, header value or token in any span attribute.",
            "- Availability: if the collector is unreachable or the CA is wrong, requests succeed unchanged "
            "and spans are dropped.",
            "",
            "## Benchmark",
            "The scikit-learn iris model on the MLServer runtime, one replica, 100 requests per second of "
            "KServe v2 REST for 10 minutes, measured with and without the annotation at 1 percent sampling and "
            "at 100 percent sampling. The p95 difference at 1 percent is the overhead figure. Owned by the model "
            "serving team; the harness is a small addition to the existing runtime performance tests.",
            "",
            "## Out of scope",
            "- Spans for the OpenShift router and the kube-rbac-proxy (or Authorino) authentication hop: that "
            "time appears only as the gap between the caller's span and the server span.",
            "- gRPC: it is not externally routable on the predictive Route path today.",
            "- LLMInferenceService, vLLM, OpenVINO Model Server, Triton and AutoGluon: each would be its own "
            "Initiative.",
            "- The KServe agent sidecar and any proxy or Service rewiring.",
            "- Installing or configuring the OpenTelemetry or Tempo operators: RHOAI does not install external "
            "operators; without the collector, nothing is exported.",
            "- Per-namespace trace access for model owners: traces land in the shared Tempo, and access is "
            "arranged by administrators. Self-service access is a follow-on.",
            "",
            "## Dependencies",
            "- The existing data-science-collector deployment (OTLP over TLS on 4317) and its Tempo export.",
            "- MLServer's bundled OpenTelemetry SDK and FastAPI instrumentation (already in the shipped image).",
            "- One downstream MLServer patch (R2); no upstream change is needed for the P0 scope.",
            "",
            "## Effort and rollout",
            "- Size M: model serving team (odh-model-controller annotation and env injection, MLServer patch, "
            "benchmark) and platform observability team (NetworkPolicy, sanitization tests). About three "
            "sprints for both teams in parallel.",
            "- Technology preview behind the annotation in one release; general availability after one release "
            "of preview feedback, with R6 considered for GA.",
            "",
            "## Acceptance Criteria",
            "- [ ] R1-R5 pass on a cluster with the collector installed; R6 is tracked separately.",
            "- [ ] The benchmark shows added p95 latency below 2 ms at 1 percent sampling.",
            "- [ ] An InferenceService without the annotation is unchanged (pod spec diff and benchmark).",
            "- [ ] With the collector absent or the CA wrong, all requests succeed and no errors are logged per request.",
        ]
    elif tmpl == "tracker":
        out += [
            "## Scope",
            f"Track onboarding of new members to the {area}.",
            "",
            "## Success criteria",
            "- Each new member lands a change within 10 working days.",
            "- Onboarding guide updated after every cohort.",
        ]
    else:
        raise SystemExit(f"{sid}: unknown template {tmpl}")
    if item.get("ac") and tmpl != "tracker":
        out += ["", "## Acceptance Criteria", *[f"- [ ] {c[0].upper() + c[1:]} is verified."
                                               for c in caps[:3]]]
    return "\n".join(out)


class Keys:
    def __init__(self, base: int):
        self.base = base
        self.next: dict[str, int] = {}

    def take(self, project: str) -> str:
        n = self.next.get(project, self.base)
        self.next[project] = n + 1
        return f"{project}-{n}"


def build(cat: dict) -> tuple[list[dict], dict]:
    anchor = datetime.strptime(cat["anchor_date"], "%Y-%m-%dT%H:%M:%S.000+0000")
    fx = cat["fixture_label"]
    keys = Keys(cat["key_base"])
    issues: list[dict] = []
    key_of: dict[str, str] = {}

    def issue(fid, project, itype, summary, *, desc="", status="New", resolution=None,
              reporter=None, assignee=None, labels=(), components=(), parent=None,
              created=0, updated=None, extra=None):
        key = keys.take(project)
        key_of[fid] = key
        fields = {
            "project": {"key": project},
            "issuetype": {"name": itype},
            "summary": f"[SYNTH] {summary}",
            "description": desc,
            "status": {"name": status, "statusCategory": {"key": STATUS_CATEGORY[status]}},
            "priority": {"name": "Major"},
            "labels": sorted({fx, f"cc75-fx-{fid.lower()}", *labels}),
            "components": [{"name": c} for c in components],
            "created": iso(anchor, created),
            "updated": iso(anchor, updated if updated is not None else max(created - 3, 0)),
        }
        if resolution:
            fields["resolution"] = {"name": resolution}
        if reporter:
            fields["reporter"] = {"displayName": reporter}
        if assignee:
            fields["assignee"] = {"displayName": assignee}
        if parent:
            fields["parent"] = {"key": parent}
        fields.update(extra or {})
        rec = {"key": key, "fields": fields, "_fid": fid, "_links": []}
        issues.append(rec)
        return rec

    for o in cat["outcomes"]:
        issue(o["id"], "RHAISTRAT", "Outcome", o["summary"], status=o["status"],
              reporter=o["reporter"], assignee=o["assignee"], created=o["created_days_ago"],
              desc=f"Synthetic Outcome grouping related Initiatives: {o['summary'].lower()}.")
    for r in cat["rfes"]:
        issue(r["id"], "RHAIRFE", "Feature Request", r["summary"], reporter=r["reporter"],
              created=50, desc="Synthetic request used only as a Cloners link source.")

    oracle_items = {}
    children_plan = []
    for it in cat["initiatives"]:
        labels = set(VARIANT_LABELS[it.get("variant")]) | set(it.get("pipeline_labels_extra", []))
        labels |= set(it.get("noise_labels", []))
        extra = {}
        if it.get("target_version"):
            extra["customfield_10855"] = it["target_version"]
        if it.get("rice"):
            extra["customfield_75001"] = it["rice"]["score"]
            extra["customfield_75002"] = it["rice"]["effort"]
        if it.get("fix_version"):
            extra["fixVersions"] = [{"name": it["fix_version"]}]
        summary = it.get("summary_raw") or it["summary"]
        created = it["created_days_ago"]
        updated = it.get("resolved_days_ago", max(created - 5, 1))
        rec = issue(it["id"], "RHAISTRAT", "Initiative", summary, desc=render_description(it),
                    status=it["status"], resolution=it.get("resolution"),
                    reporter=it["reporter"], assignee=it.get("assignee"), labels=labels,
                    components=it.get("components", []), created=created, updated=updated,
                    parent=key_of.get(it.get("outcome")) if it.get("outcome") else None,
                    extra=extra)
        children_plan.append((it, rec))

    for it, rec in children_plan:
        epic_keys, epic_projects = [], []
        for group in it.get("epics", []):
            group_keys = []
            for n in range(1, group["count"] + 1):
                ws = WORKSTREAMS[(n - 1) % len(WORKSTREAMS)]
                status = group.get("status", "In Progress" if n == 1 else "New")
                e = issue(f"{it['id']}-{group['project']}-E{n}", group["project"], "Epic",
                          f"{it.get('area', 'Initiative')}: {ws}", status=status,
                          resolution="Done" if status == "Closed" else None,
                          reporter=it["reporter"], assignee=it.get("assignee"),
                          parent=rec["key"], created=max(it["created_days_ago"] - 10, 1),
                          desc=f"Synthetic Epic: {ws.lower()} for {it.get('area', 'this Initiative')}.")
                group_keys.append(e)
                epic_keys.append(e["key"])
                epic_projects.append(group["project"])
            for a, b in group.get("blocks", []):
                group_keys[a - 1]["_links"].append(("Blocks", "outward", group_keys[b - 1]["key"]))
        story = it.get("stories")
        story_keys = []
        if story:
            for n in range(1, story["count"] + 1):
                s = issue(f"{it['id']}-S{n}", story["project"], "Story",
                          f"{it['area']}: onboarding cohort {n}", status=story["status"],
                          resolution="Done" if story["status"] == "Closed" else None,
                          reporter=it["reporter"], assignee=it.get("assignee"),
                          parent=rec["key"], created=max(it["created_days_ago"] - 5, 1),
                          desc="Synthetic onboarding Story delivered without an Epic layer.")
                story_keys.append(s["key"])
        legacy = it.get("legacy_incorporates_epic")
        legacy_key = None
        if legacy:
            e = issue(f"{it['id']}-LEGACY", legacy["project"], "Epic",
                      f"{it['area']}: legacy decomposition", status="In Progress",
                      reporter=it["reporter"], assignee=it.get("assignee"),
                      created=max(it["created_days_ago"] - 20, 1),
                      desc="Synthetic Epic linked by a legacy Incorporates link, with no parent.")
            rec["_links"].append(("Incorporates", "outward", e["key"]))
            legacy_key = e["key"]
        for link in it.get("links", []):
            rec["_links"].append((link["type"], "outward", None, link["to"]))

        labels = set(rec["fields"]["labels"])
        status = rec["fields"]["status"]["name"]
        jql_selected = (STRAT_REQUIRED <= labels and not (labels & STRAT_JQL_EXCLUDED)
                        and status not in OPEN_EXCLUDED)
        oracle_items[it["id"]] = {
            "key": rec["key"],
            "archetype": it["archetype"],
            "status": status,
            "labels": sorted(l for l in labels if not l.startswith("cc75-") and l != fx),
            "epic_children": epic_keys,
            "epic_child_projects": sorted(set(epic_projects)),
            "story_children": story_keys,
            "legacy_incorporates": legacy_key,
            "strat_jql_selected": jql_selected,
            "strat_tool_skip": sorted(labels & STRAT_TOOL_SKIP) if jql_selected else [],
            "description_chars": len(rec["fields"]["description"]),
        }

    # Resolve deferred links (targets named by fixture id) and serialise.
    for rec in issues:
        links = []
        for entry in rec.pop("_links"):
            ltype = entry[0]
            target = entry[2] if entry[2] else key_of[entry[3]]
            inward, outward = LINK_TYPES[ltype]
            links.append({"type": {"name": ltype, "inward": inward, "outward": outward},
                          "outwardIssue": {"key": target}})
        if links:
            rec["fields"]["issuelinks"] = links
        rec.pop("_fid")

    oracle = build_oracle(cat, oracle_items, key_of, issues)
    return issues, oracle


def build_oracle(cat, items, key_of, issues) -> dict:
    by_key = sorted(items.values(), key=lambda x: int(x["key"].split("-")[1]))
    jql = [x["key"] for x in by_key if x["strat_jql_selected"]]
    tool = [x["key"] for x in by_key if x["strat_jql_selected"] and not x["strat_tool_skip"]]
    optin = [x["key"] for x in by_key if "initiative-autofix-opt-in" in x["labels"]]
    pending = [x["key"] for x in by_key if "initiative-autofix-opt-in" in x["labels"]
               and not ({"initiative-autofix-rubric-pass", "initiative-needs-attention"} & set(x["labels"]))
               and x["status"] not in OPEN_EXCLUDED]
    decomp = {}
    for x in by_key:
        if DECOMP_REQUIRED <= set(x["labels"]) and DECOMP_DONE not in x["labels"]:
            if x["epic_children"]:
                decomp[x["key"]] = {"action": "skip", "reason": "existing Epic children"}
            elif x["legacy_incorporates"]:
                decomp[x["key"]] = {"action": "skip", "reason": "legacy Incorporates link to an Epic"}
            else:
                decomp[x["key"]] = {"action": "decompose", "epic_count_min": 2, "epic_count_max": 8,
                                    "outlier_at": 15, "target_project": "RHAI",
                                    "sibling_link": "Blocks", "parent_label": DECOMP_DONE}
    counts = {}
    for rec in issues:
        t = rec["fields"]["issuetype"]["name"]
        p = rec["fields"]["project"]["key"]
        counts.setdefault(p, {}).setdefault(t, 0)
        counts[p][t] += 1
    return {
        "version": 1,
        "generated_from": "catalogue.yaml",
        "issue_counts": counts,
        "fixture_ids": {k: key_of[k] for k in sorted(key_of) if re.fullmatch(r"[OIR]\d+", k)},
        "strat_creator": {
            "discovery_jql": STRAT_JQL,
            "jql_selected": jql,
            "tool_selected_after_skip_labels": tool,
            "canary_batch_size_1": tool[:1],
        },
        "rfe_autofixer": {
            "note": "Provisional: the exact upstream JQL and project (RHAISTRAT vs RHOAIENG) are plan Q4.",
            "opted_in": optin,
            "pending_review": pending,
        },
        "epic_creator": {"candidates": decomp},
        "initiatives": {k: items[k] for k in sorted(items)},
    }


KEY_IN_TEXT = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")


def lint(cat: dict, issues: list[dict]) -> list[str]:
    roster = set(cat["roster"]["pms"]) | set(cat["roster"]["engineers"])
    errors = []
    for rec in issues:
        f = rec["fields"]
        key = rec["key"]
        if not f["summary"].startswith("[SYNTH] "):
            errors.append(f"{key}: summary lacks [SYNTH] prefix")
        for text in (f["summary"], f["description"]):
            for m in KEY_IN_TEXT.findall(text):
                errors.append(f"{key}: issue-key-like token in text: {m}")
        for role in ("reporter", "assignee"):
            name = (f.get(role) or {}).get("displayName")
            if name and name not in roster:
                errors.append(f"{key}: {role} {name!r} not in synthetic roster")
        if int(key.split("-")[1]) < cat["key_base"]:
            errors.append(f"{key}: key outside the synthetic block")
        if cat["fixture_label"] not in f["labels"]:
            errors.append(f"{key}: missing fixture label")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--catalogue", default=ROOT / "catalogue.yaml", type=Path)
    ap.add_argument("--out-issues", default=ROOT / "generated" / "issues.json", type=Path)
    ap.add_argument("--out-expected", default=ROOT / "expected.yaml", type=Path)
    ap.add_argument("--check", action="store_true", help="fail if outputs would change")
    args = ap.parse_args()

    cat = yaml.safe_load(args.catalogue.read_text())
    issues, oracle = build(cat)
    errors = lint(cat, issues)
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    issues_text = json.dumps({"issues": issues}, indent=1, sort_keys=True) + "\n"
    oracle_text = ("# Generated by scripts/generate_initiatives.py from catalogue.yaml. Do not edit.\n"
                   + yaml.safe_dump(oracle, sort_keys=False, width=100))
    if args.check:
        stale = [p for p, t in ((args.out_issues, issues_text), (args.out_expected, oracle_text))
                 if not p.exists() or p.read_text() != t]
        if stale:
            print("stale: " + ", ".join(map(str, stale)), file=sys.stderr)
            return 1
        return 0
    args.out_issues.parent.mkdir(parents=True, exist_ok=True)
    args.out_issues.write_text(issues_text)
    args.out_expected.write_text(oracle_text)
    total = sum(sum(v.values()) for v in oracle["issue_counts"].values())
    print(f"{total} issues; strat jql={len(oracle['strat_creator']['jql_selected'])} "
          f"tool={len(oracle['strat_creator']['tool_selected_after_skip_labels'])}; "
          f"decomposition candidates={len(oracle['epic_creator']['candidates'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
