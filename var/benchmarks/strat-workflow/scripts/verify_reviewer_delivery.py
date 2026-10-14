#!/usr/bin/env python3
"""Check one focused S1 repair from archived request bodies and native state.

This checks assessment delivery and schema isolation, not independent accuracy
or final strategy publication. Input is one unpacked jobs/<job>/ directory.
"""
import argparse
import json
from pathlib import Path
from review_assessment import classify

MODEL = "rits/zai-org/glm-5-3"
TARGET = "RHAISTRAT-9001"
ROLES = {"strategy-feasibility-review": "Feasibility",
         "strategy-testability-review": "Testability",
         "strategy-scope-review": "Scope assessment",
         "strategy-architecture-review": "Architecture assessment"}


def objects(value):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from objects(item)
    elif isinstance(value, list):
        for item in value:
            yield from objects(item)


def texts(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(texts(item) for item in value)
    if isinstance(value, dict):
        return texts(value.get("text", value.get("content", "")))
    return ""


def verify(root):
    requests = [json.loads(path.read_text()) for path in sorted((root / "api-dumps").glob("*.request.json"))]
    responses = [json.loads(path.read_text()) for path in sorted((root / "api-dumps").glob("*.response.json"))]
    calls, results, output_calls = {}, {}, {}
    errors = []
    if not requests or not responses:
        errors.append("missing API request/response bodies")
    models = sorted({request.get("model", "") for request in requests})
    if models != [MODEL]:
        errors.append("unexpected request model")
    for document in requests + responses:
        for item in objects(document.get("messages", document.get("content", []))):
            if item.get("type") == "tool_use" and item.get("name") == "Skill":
                role = item.get("input", {}).get("skill", "").split(":")[-1]
                if role in ROLES:
                    calls[item["id"]] = item
            if item.get("type") == "tool_result":
                results[item["tool_use_id"]] = item
            if item.get("type") == "tool_use" and item.get("name") == "StructuredOutput":
                output_calls[item["id"]] = item.get("input", {})
    reports = []
    for role, heading in ROLES.items():
        matches = [(identity, call) for identity, call in calls.items()
                   if call["input"]["skill"].split(":")[-1] == role]
        if len(matches) != 1:
            errors.append(f"{role}: expected one launch, found {len(matches)}")
        for identity, call in matches:
            report = results.get(identity, {})
            body = texts(report.get("content", ""))
            assessment = classify(body, TARGET, role.removeprefix("strategy-").removesuffix("-review"),
                                  is_error=report.get("is_error", False))
            valid = call["input"].get("args", "").strip() == TARGET and assessment["assessment_present"]
            if not valid:
                errors.append(role + ": no complete targeted assessment in receiving request")
            reports.append({"role": role, "tool_id": identity, "characters": len(body),
                            "delivered": bool(valid), "assessment": assessment})
    leaves = [request for request in requests if "return its complete assessment" in texts(request.get("system", ""))]
    leaf_tools = sorted({tool["name"] for request in leaves for tool in request.get("tools", [])})
    if len(leaves) < 4 or "StructuredOutput" in leaf_tools or not {"Read", "Grep", "Glob"}.issubset(leaf_tools):
        errors.append("reviewer agent tool isolation not established")
    outer = [value for value in output_calls.values() if value.get("key") == TARGET
             and value.get("recommendation") in ["approve", "revise", "reject"]
             and isinstance(value.get("needs_attention"), bool)]
    if not outer:
        errors.append("missing valid outer structured status")
    states = []
    for path in (root / "artifacts" / "native-projects").rglob("workflows/wf_*.json"):
        state = json.loads(path.read_text())
        states.append({"path": str(path.relative_to(root)), "state": state.get("state", state.get("status")), "result": state.get("result")})
    if not any(state["state"] == "completed" for state in states):
        errors.append("no completed persisted workflow state")
    if (root / "artifacts" / "claude-exit.txt").read_text().strip() != "0":
        errors.append("CLI did not exit successfully")
    return {"passed": not errors, "errors": errors, "request_models": models,
            "api_requests": len(requests), "api_responses": len(responses), "reports": reports,
            "reviewer_requests": len(leaves), "reviewer_tools": leaf_tools,
            "outer_status": outer, "workflow_states": states,
            "claim": "single-scenario assessment delivery; scope, fidelity and technical accuracy remain separate"}


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
