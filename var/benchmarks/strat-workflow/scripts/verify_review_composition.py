#!/usr/bin/env python3
"""Join final role sections to actual delivered Skills and check the numeric gate."""
import argparse
import hashlib
import json
from pathlib import Path
import re

import yaml

from verify_reviewer_delivery import MODEL, objects, texts

ROLES = ("feasibility", "testability", "scope", "architecture")
CASES = {
    "STRAT-9501": {"score": 8, "recommendation": "approve", "needs_attention": False,
                   "roles": ("approve", "revise", "approve", "revise")},
    "STRAT-9502": {"score": 4, "recommendation": "revise", "needs_attention": True,
                   "roles": ("approve", "revise", "approve", "approve")},
}


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def inspect(root):
    native = (root / "fixture/artifacts").exists()
    artifacts = root / "fixture/artifacts" if native else root / "artifacts/fixture-artifacts"
    progress_path = root / "fixture/tmp/strat-progress.json" if native else root / "artifacts/fixture-state/strat-progress.json"
    native_path = root / "config/projects" if native else root / "artifacts/native-projects"
    requests = [json.loads(path.read_text()) for path in (root / "api-dumps").glob("*.request.json")]
    responses = [json.loads(path.read_text()) for path in (root / "api-dumps").glob("*.response.json")]
    errors, calls, results, reports = [], {}, {}, []
    models = sorted({request.get("model", "") for request in requests})
    if models != [MODEL] or not responses:
        errors.append("missing API captures or an unexpected model")
    for document in requests + responses:
        for item in objects(document.get("messages", document.get("content", []))):
            if item.get("type") == "tool_use":
                calls[item["id"]] = item
            if item.get("type") == "tool_result":
                results[item["tool_use_id"]] = item
    progress = json.loads(progress_path.read_text())

    def artifact(relative):
        if not isinstance(relative, str) or not relative.startswith("artifacts/") or ".." in Path(relative).parts:
            raise ValueError("unsafe provenance path")
        return artifacts / relative.removeprefix("artifacts/")

    for key, expected in CASES.items():
        manifest = json.loads((artifacts / "strat-reviews" / f"{key}-review-provenance.json").read_text())
        review = artifact(manifest["review"]["path"]).read_text()
        metadata = yaml.safe_load(review.split("---", 2)[1])
        if (manifest.get("policy") != "numeric-only-v1" or manifest.get("key") != key
                or manifest.get("workflow_run_id") != progress.get("run_id")
                or manifest["review"]["sha256"] != sha(review)):
            errors.append(key + ": missing or inconsistent composition provenance")
        if (metadata.get("recommendation") != expected["recommendation"]
                or metadata.get("needs_attention") is not expected["needs_attention"]
                or metadata.get("scores", {}).get("total") != expected["score"]
                or any(metadata.get("scores", {}).get(role) != expected["score"] // 4 for role in ROLES)
                or manifest.get("decision") != {field: expected[field] for field in ("recommendation", "needs_attention")}):
            errors.append(key + ": numeric policy was overridden or its flag disagrees")
        saved = progress.get("review", {}).get(key, {})
        if (saved.get("composition_session") != manifest.get("session_id")
                or any(saved.get(field) != expected[field] for field in ("recommendation", "needs_attention"))):
            errors.append(key + ": persisted review does not agree with this composition")
        for role, verdict in zip(ROLES, expected["roles"]):
            source = manifest.get("reports", {}).get(role, {})
            body = artifact(source["path"]).read_text()
            identity = source.get("tool_use_id")
            call = calls.get(identity, {})
            receipt = results.get(identity, {})
            canonical = role.upper() + "_" + key.split("-")[-1]
            matches = [call for call in calls.values() if call.get("name") == "Skill"
                       and call.get("input", {}).get("skill", "").split(":")[-1] == f"strategy-{role}-review"
                       and call["input"].get("args", "").strip() == key]
            if (len(matches) != 1 or call.get("name") != "Skill"
                    or call.get("input", {}).get("skill", "").split(":")[-1] != f"strategy-{role}-review"
                    or call.get("input", {}).get("args", "").strip() != key
                    or receipt.get("is_error") or body not in texts(receipt.get("content"))):
                errors.append(key + ": " + role + " has no unique matching delivered Skill result")
            if (canonical not in body or body not in review or source.get("sha256") != sha(body)
                    or source.get("key") != key or source.get("role") != role
                    or source.get("session_id") != manifest.get("session_id")
                    or source.get("caller") != manifest.get("caller") or not source.get("agent_id")
                    or source.get("recommendation") != verdict or metadata.get("reviewers", {}).get(role) != verdict):
                errors.append(key + ": " + role + " finding, dissent or attribution was lost")
            child_paths = list(native_path.rglob("agent-" + str(source.get("agent_id")) + ".jsonl"))
            child_text = ""
            if len(child_paths) == 1:
                for line in child_paths[0].read_text().splitlines():
                    item = json.loads(line)
                    if item.get("type") == "assistant":
                        child_text = texts(item.get("message", {}).get("content"))
            if len(child_paths) != 1 or body not in child_text:
                errors.append(key + ": " + role + " producer identity does not match its native final response")
            reports.append({"key": key, "role": role, "tool_id": identity, "sha256": sha(body), "recommendation": verdict})
            if verdict != expected["recommendation"] and f"{role}: {verdict} (numeric: {expected['recommendation']})" not in review:
                errors.append(key + ": dissent not explicitly listed")
        for entry in [manifest["scorer"], *manifest["inputs"].values()]:
            if sha(artifact(entry["path"]).read_text()) != entry["sha256"]:
                errors.append(key + ": exported input/scorer provenance disagrees")
        if "separate numeric assessor" not in review:
            errors.append(key + ": scorer feedback lacks separate attribution")
        parents = [call for call in calls.values() if call.get("name") == "Skill"
                   and call.get("input", {}).get("skill", "").split(":")[-1] == "strategy-review"
                   and call["input"].get("args", "").split()[:1] == [key]]
        composers = [call for call in calls.values() if call.get("name") == "Bash"
                     and re.search(r"review_composition.py\s+compose\s+" + re.escape(key) + r"\b",
                                   call.get("input", {}).get("command", ""))]
        if len(parents) != 1 or len(composers) != 1:
            errors.append(key + ": expected one actual review Skill and composition call")
    expected_result = [{"key": key, **{field: value[field] for field in ("recommendation", "needs_attention")}}
                       for key, value in CASES.items()]
    outcomes = [json.loads(path.read_text()) for path in native_path.rglob("workflows/wf_*.json")]
    if not any(state.get("status", state.get("state")) == "completed" and state.get("result") == expected_result for state in outcomes):
        errors.append("no completed native Workflow with matching numeric decisions")
    if not native and (root / "artifacts/claude-exit.txt").read_text().strip() != "0":
        errors.append("CLI exit was not successful")
    return {"passed": not errors, "errors": errors, "models": models, "requests": len(requests),
            "responses": len(responses), "reports": reports, "expected_result": expected_result,
            "claim": "authored findings and dissent preserved from actual delivered Skills; numeric-only gate unchanged; not strategy accuracy"}


def verify(root):
    try:
        return inspect(root)
    except (OSError, ValueError, KeyError, TypeError) as error:
        return {"passed": False, "errors": [f"missing or invalid archive evidence: {error}"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.root)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
