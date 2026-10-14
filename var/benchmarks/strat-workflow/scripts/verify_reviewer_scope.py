#!/usr/bin/env python3
"""Verify scope and delivery for the authored three-ticket GLM scenario."""
import argparse
import json
from pathlib import Path
import re

from verify_reviewer_delivery import MODEL, ROLES, objects, texts
from review_assessment import classify

TARGETS = {"RHAISTRAT-9101": "TIMEOUT_SCOPE_CANARY",
           "RHAISTRAT-9102": "RETENTION_SCOPE_CANARY",
           "RHAISTRAT-9103": "ROTATION_SCOPE_CANARY"}


def outcome_issues(statuses):
    return [{"key": value.get("key"), "recommendation": value["recommendation"],
             "needs_attention": False, "issue": "revision/rejection without attention flag"}
            for value in statuses if isinstance(value, dict)
            and value.get("recommendation") in {"revise", "reject"}
            and value.get("needs_attention") is False]


def inspect(requests, responses, audits, transcripts):
    errors = []
    calls, receipts = {}, {}
    models = sorted({request.get("model", "") for request in requests})
    if models != [MODEL] or not responses:
        errors.append("missing captures or unexpected request model")
    for document in requests + responses:
        for item in objects(document.get("messages", document.get("content", []))):
            if item.get("type") == "tool_use" and item.get("name") == "Skill":
                role = item.get("input", {}).get("skill", "").split(":")[-1]
                if role in ROLES:
                    calls[item["id"]] = item
            elif item.get("type") == "tool_result":
                receipts[item["tool_use_id"]] = item
    reports = []
    for key in TARGETS:
        for role, heading in ROLES.items():
            matches = [(identity, call) for identity, call in calls.items()
                       if call["input"]["skill"].split(":")[-1] == role
                       and call["input"].get("args", "").strip() == key]
            if len(matches) != 1:
                errors.append(f"{key}/{role}: expected one launch, found {len(matches)}")
            for identity, _ in matches:
                receipt = receipts.get(identity, {})
                body = texts(receipt.get("content", ""))
                headings = re.findall(r"^###\s+((?:RHAISTRAT|STRAT)-[0-9]+):", body, re.M)
                assessment = classify(body, key, role.removeprefix("strategy-").removesuffix("-review"),
                                      is_error=receipt.get("is_error", False))
                valid = (headings == [key] and set(re.findall(r"(?:RHAISTRAT|STRAT)-[0-9]+", body)) == {key}
                         and not set(re.findall(r"(?:RHAIRFE|RFE)-[0-9]+", body)) - {key.replace("STRAT", "RFE")}
                         and assessment["assessment_present"] and "REVIEW_SCOPE_ERROR:" not in body)
                if not valid:
                    errors.append(f"{key}/{role}: missing or out-of-scope delivered assessment")
                reports.append({"key": key, "role": role, "characters": len(body), "valid": bool(valid),
                                "assessment": assessment})
    actors = {}
    for agent, prompt in transcripts.items():
        assignment = re.search(r"^REVIEW_SCOPE_TARGET: (RHAISTRAT-[0-9]+)$", prompt, re.M)
        if assignment:
            roles = [role for role in ROLES if role in prompt.split("\n", 1)[0]]
            if len(roles) == 1 and assignment[1] in TARGETS:
                actors[agent] = (assignment[1], roles[0])
    expected = {(key, role) for key in TARGETS for role in ROLES}
    if len(actors) != 12 or set(actors.values()) != expected:
        errors.append("reviewer transcripts do not establish 12 unique role/target identities")
    for agent, (key, role) in actors.items():
        events = audits.get(agent, [])
        allowed = [event for event in events if event.get("allowed")]
        if not any(event["event"] == "SubagentStop" and event.get("key") == key for event in allowed):
            errors.append(f"{key}/{role}: no validated completion hook")
        source = key.replace('STRAT', 'RFE')
        for required in ((f"/strat-tasks/{key}.md",), (f"/rfe-tasks/{source}.md", f"/strat-originals/{source}.md")):
            if not any(event.get("tool") == "Read" and (event.get("input") or {}).get("file_path", "").endswith(required)
                       and event.get("key") == key for event in allowed):
                errors.append(f"{key}/{role}: assigned input read was not verified: {required}")
    leaves = []
    for request in requests:
        prompt = "\n".join(texts(message.get("content")) for message in request.get("messages", [])
                           if message.get("role") == "user")
        assignment = re.search(r"^REVIEW_SCOPE_TARGET: (RHAISTRAT-[0-9]+)$", prompt, re.M)
        if not assignment:
            continue
        key = assignment[1]
        if key not in TARGETS:
            errors.append("unexpected reviewer target")
            continue
        leaves.append(request)
        tools = {tool["name"] for tool in request.get("tools", [])}
        if tools != {"Read", "Grep", "Glob"}:
            errors.append(f"{key}: reviewer tools changed")
        messages = json.dumps(request.get("messages", []))
        if any(canary in messages for peer, canary in TARGETS.items() if peer != key):
            errors.append(f"{key}: another ticket's content reached the reviewer")
    if not leaves:
        errors.append("no reviewer API requests identified")
    return {"passed": not errors, "errors": sorted(set(errors)), "reports": reports,
            "api_requests": len(requests), "api_responses": len(responses),
            "request_models": models, "reviewer_requests": len(leaves),
            "reviewer_agents": len(actors), "hook_events": sum(map(len, audits.values())),
            "blocked_actions": sum(not event.get("allowed") for events in audits.values() for event in events),
            "claim": "single three-ticket scenario: report target, captured input isolation and hook execution; accuracy remains separate"}


def verify(root):
    requests = [json.loads(path.read_text()) for path in (root / "api-dumps").glob("*.request.json")]
    responses = [json.loads(path.read_text()) for path in (root / "api-dumps").glob("*.response.json")]
    audits = {path.stem: [json.loads(line) for line in path.read_text().splitlines()]
              for path in (root / "artifacts/review-scope").glob("*.jsonl")}
    transcripts = {}
    for path in (root / "artifacts/native-projects").rglob("agent-*.jsonl"):
        for line in path.read_text().splitlines():
            item = json.loads(line)
            if item.get("type") == "user":
                transcripts[path.stem.removeprefix("agent-")] = texts(item.get("message", {}).get("content"))
                break
    result = inspect(requests, responses, audits, transcripts)
    completed = []
    for path in (root / "artifacts/native-projects").rglob("workflows/wf_*.json"):
        state = json.loads(path.read_text())
        if state.get("state", state.get("status")) == "completed":
            completed.append(state.get("result"))
    result["workflow_results"] = completed
    statuses = [value for values in completed if isinstance(values, list) for value in values]
    # Keep the scope result distinct from the later business-outcome gate.
    result["outcome_consistency_issues"] = outcome_issues(statuses)
    if {value.get("key") for value in statuses if isinstance(value, dict)} != set(TARGETS):
        result["errors"].append("missing completed workflow with all three receiver statuses")
    if (root / "artifacts/claude-exit.txt").read_text().strip() != "0":
        result["errors"].append("CLI did not exit successfully")
    result["passed"] = not result["errors"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("job", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.job)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
