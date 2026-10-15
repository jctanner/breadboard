#!/usr/bin/env python3
"""Check one finished test run and print its eval-result.

    check_run.py '<run json>' <job name> <RFE key|batch-discover> <wait status> ['<seed json>']

The run JSON is the run-test workflow's `run` fact; the wait status is what
Markov's job_wait saw (completed, failed, or running at the timeout).

Every check is a script, not a model's judgement (the plan, "What counts as
a pass"). For one new eligible RFE, as in the smoke tier:

  finished         the job completed with exit 0
  one_strategy     exactly one RHAISTRAT, cloned from the RFE
  steps_done       the strategy was created, refined and pushed (labels and
                   text), and got a verdict label
  one_review       exactly one review comment on the strategy
  records_agree    the review comment's verdict matches the verdict label
  no_half_done     no review comment without a refined, pushed strategy
  locks_released   no lock label left on the RFE or the strategy

Batch runs additionally require one distinct strategy per seeded eligible
RFE, all four reviewer roles to return completed assessments to their parent for each strategy,
and only the requested Haiku model in the response dumps. Reviewer return
checks do not prove verbatim preservation in the published review.

Also recorded, without pass or fail: wall time, and model calls and tokens
from the job's API dumps (relay telemetry drops records under load; see
.ledger/bugs/open/model-relay-telemetry-drops-under-load.md).

Reads the job from the dashboard API, its files through the dashboard's file
API, and Jira directly. Exits 0 whatever the verdict, so a failed test is
recorded and the tier goes on; exits 1 only when it can't check at all.
"""
from datetime import datetime
import json
import re
import sys

from benchlib import dashboard, emit, jira, list_dir, read_file
from review_assessment import CONTRACT, classify

LOCK_LABEL = "strat-creator-processing"
REVIEW_PREFIX = re.compile(r"^\*?\[Strat Creator\]\*?\s+Strategy Review\s+[—-]\s+(\w+)\s+\(Score:\s*([\d.]+)/(\d+)\)")
VERDICT_LABELS = {"approve": "strat-creator-rubric-pass",
                  "revise": "strat-creator-needs-attention",
                  "reject": "strat-creator-needs-attention"}


def check(ok: bool, detail) -> dict:
    return {"ok": bool(ok), "detail": detail}


def linked_strategies(issue: dict) -> list[str]:
    keys = []
    for link in issue["fields"].get("issuelinks", []):
        for side in ("inwardIssue", "outwardIssue"):
            key = (link.get(side) or {}).get("key", "")
            if key.startswith("RHAISTRAT-") and key not in keys:
                keys.append(key)
    return keys


def jira_checks(rfe_key: str, expected_count: int = 1) -> tuple[dict, dict]:
    rfe = jira(f"/rest/api/2/issue/{rfe_key}?fields=labels,issuelinks")
    strat_keys = linked_strategies(rfe)
    all_strats = [i["key"] for i in jira("/rest/api/2/search?jql=project%3DRHAISTRAT&fields=key&maxResults=100")["issues"]]
    strats = [jira(f"/rest/api/2/issue/{k}?fields=labels,description,comment") for k in strat_keys]

    checks = {"one_strategy": check(len(strat_keys) == 1 and len(all_strats) == expected_count,
                                    {"linked": strat_keys, "in_project": all_strats})}
    facts = {"strategies": strat_keys}
    locked = [rfe_key] if LOCK_LABEL in rfe["fields"].get("labels", []) else []

    if not strats:
        for name in ("steps_done", "one_review", "records_agree", "no_half_done"):
            checks[name] = check(False, "no strategy")
    else:
        strat = strats[0]
        labels = strat["fields"].get("labels", [])
        text = strat["fields"].get("description") or ""
        reviews = []
        for comment in strat["fields"].get("comment", {}).get("comments", []):
            match = REVIEW_PREFIX.match(comment.get("body", "").strip())
            if match:
                reviews.append({"verdict": match.group(1).lower(),
                                "score": f"{match.group(2)}/{match.group(3)}"})
        verdict_labels = sorted(set(labels) & set(VERDICT_LABELS.values()))
        refined = "strat-creator-auto-refined" in labels and len(text) > 0
        checks["steps_done"] = check(
            "strat-creator-auto-created" in labels and refined and len(verdict_labels) == 1,
            {"labels": sorted(l for l in labels if l.startswith("strat-creator-")), "text_chars": len(text)})
        checks["one_review"] = check(len(reviews) == 1, {"reviews": reviews})
        expected = VERDICT_LABELS.get(reviews[0]["verdict"]) if reviews else None
        checks["records_agree"] = check(
            len(reviews) == 1 and verdict_labels == [expected],
            {"comment_verdict": reviews[0]["verdict"] if reviews else None, "verdict_labels": verdict_labels})
        checks["no_half_done"] = check(not reviews or refined, {"reviews": len(reviews), "refined": refined})
        if reviews:
            facts.update(reviews[0])
        for s in strats:
            if LOCK_LABEL in s["fields"].get("labels", []):
                locked.append(s["key"])

    checks["locks_released"] = check(not locked, {"locked": locked})
    return checks, facts


def batch_jira_checks(seed: dict, expected_count: int) -> tuple[dict, dict]:
    """Apply the single-item contract to every RFE and reject shared strategies."""
    keys = [rfe["key"] for rfe in seed["rfes"] if rfe["eligible"]]
    items = []
    for key in keys:
        checks, facts = jira_checks(key, expected_count)
        items.append({"rfe": key, **facts, "checks": checks})
    names = ("one_strategy", "steps_done", "one_review", "records_agree", "no_half_done", "locks_released")
    checks = {name: check(bool(items) and all(item["checks"][name]["ok"] for item in items),
                          {item["rfe"]: item["checks"][name] for item in items}) for name in names}
    strategies = [key for item in items for key in item["strategies"]]
    checks["batch_complete"] = check(
        seed.get("ok") and len(keys) == expected_count and len(set(keys)) == expected_count
        and set(keys) == set(seed.get("discovered", []))
        and len(strategies) == expected_count and len(set(strategies)) == expected_count,
        {"expected_count": expected_count, "rfes": keys, "strategies": strategies})
    return checks, {"rfes": keys, "batch_size": expected_count, "strategies": sorted(set(strategies)), "items": items}


REVIEWER_SKILLS = {f"strategy-{role}-review": role for role in
                   ("feasibility", "testability", "scope", "architecture")}


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(block.get("text", "") for block in content or [] if block.get("type") == "text")


def reviewer_returns(bodies, strategies: list[str]) -> dict:
    """Join Skill launches and parent tool results by ID, deduplicating histories.

    Check the receiving user channel, with repeated histories deduplicated and
    conflicts rejected. Scope exclusivity is reported separately and does not
    change delivery. Neither final incorporation nor accuracy is checked here.
    """
    launches, results, models, conflicts = {}, {}, set(), set()
    for body in bodies:
        if body.get("model"):
            models.add(body["model"])
        messages = body.get("messages", [])
        if body.get("type") == "message":
            messages = [*messages, {"role": "assistant", "content": body.get("content", [])}]
        for message in messages:
            content = message.get("content")
            if not isinstance(content, list):
                continue
            for block in content:
                if message.get("role") == "assistant" and block.get("type") == "tool_use" and block.get("name") == "Skill":
                    args = block.get("input") or {}
                    skill = args.get("skill", "").split(":")[-1]
                    if skill in REVIEWER_SKILLS:
                        keys = re.findall(r"\bRHAISTRAT-\d+\b", args.get("args", ""))
                        launch = {"skill": skill, "role": REVIEWER_SKILLS[skill], "strategies": sorted(set(keys))}
                        if block["id"] in launches and launches[block["id"]] != launch:
                            conflicts.add(block["id"])
                        launches[block["id"]] = launch
                elif message.get("role") == "user" and block.get("type") == "tool_result":
                    text = re.sub(r"<system-reminder>.*?</system-reminder>", "",
                                  text_of(block.get("content")), flags=re.S).strip()
                    result = {"text": text, "error": bool(block.get("is_error"))}
                    identity = block["tool_use_id"]
                    if identity in results and results[identity] != result:
                        conflicts.add(identity)
                    results[identity] = result
    records = []
    for tool_id, launch in launches.items():
        result = results.get(tool_id)
        text = result["text"] if result else ""
        # Forked Skill results have an acknowledgement followed by Result:.
        wrapper = re.match(r'^Skill "([^"\n]+)" completed \(forked execution\)\.\s*Result:\s*', text)
        output = text[wrapper.end():].strip() if wrapper else text
        key = launch["strategies"][0] if len(launch["strategies"]) == 1 else ""
        assessment = classify(output, key, launch["role"], is_error=bool(result and result["error"]))
        valid_boundary = bool(wrapper and wrapper[1].split(":")[-1] == launch["skill"] and key)
        returned = bool(result and valid_boundary and tool_id not in conflicts and assessment["assessment_present"])
        reason = ("missing receiving tool result" if result is None else
                  "conflicting launch/result history" if tool_id in conflicts else
                  "missing or mismatched single-target fork boundary" if not valid_boundary else assessment["reason"])
        records.append({"tool_use_id": tool_id, **launch, "answered": result is not None,
                        "returned": returned, "result_chars": len(output) if returned else 0,
                        "result_head": output[:160], "content_chars": len(output),
                        "valid_fork_boundary": valid_boundary, "conflicting_history": tool_id in conflicts,
                        "assessment": assessment, "delivery_reason": reason})
    by_strategy = {}
    for key in strategies:
        roles = {}
        for role in REVIEWER_SKILLS.values():
            calls = [record for record in records if record["strategies"] == [key] and record["role"] == role]
            roles[role] = {"launches": len(calls), "reruns": max(0, len(calls) - 1),
                           "empty_returns": sum(call["answered"] and not call["returned"] for call in calls),
                           "invalid_returns": sum(call["answered"] and not call["returned"] for call in calls),
                           "skipped": sum(call["assessment"]["classification"] == "skipped" for call in calls),
                           "returned": any(call["returned"] for call in calls)}
        by_strategy[key] = roles
    return check(bool(strategies) and all(role["returned"] for roles in by_strategy.values() for role in roles.values()),
                 {"contract": CONTRACT, "by_strategy": by_strategy, "launches": records, "models": sorted(models),
                  "limits": "Mechanical assessment delivery; exclusive scope, incorporation and accuracy are separate."})


def api_bodies(job: str):
    base = f"/app/artifacts/apibodies/{job}"
    for entry in list_dir(base):
        name = entry["name"]
        if not name.endswith((".request.json", ".response.json")):
            continue
        text = read_file(f"{base}/{name}")
        try:
            body = json.loads(text) if text else None
        except json.JSONDecodeError:
            body = None
        if isinstance(body, dict):
            yield body


GLM_MODEL = "rits/zai-org/glm-5-3"
# This is the verified EnMaaS response spelling, not a general fuzzy match.
GLM_RESPONSE_IDS = {GLM_MODEL, "zai-org/GLM-5.3"}

def model_identity_check(model, usage, additional_models=()):
    responses = set(usage["by_model"])
    observed = responses | set(additional_models)
    requests = set(usage.get("request_models", []))
    if model == GLM_MODEL:
        allowed = GLM_RESPONSE_IDS
        ok = bool(responses) and observed <= allowed and requests == {GLM_MODEL}
    else:
        ok = bool(responses) and observed == {model}
    return check(ok, {"expected_model": model, "observed_models": sorted(observed),
                      "request_models": sorted(requests)})


def api_usage(job: str) -> dict:
    """Sum usage over the job's API dumps (one response file per model call)."""
    base = f"/app/artifacts/apibodies/{job}"
    entries = [e["name"] for e in list_dir(base)]
    requests = sum(1 for n in entries if n.endswith(".request.json"))
    totals = {"calls": 0, "input": 0, "output": 0, "thinking": 0, "cache_read": 0, "cache_write": 0}
    by_model, errors, unreadable = {}, {}, 0
    request_models = set()
    for name in entries:
        if not name.endswith((".request.json", ".response.json")):
            continue
        text = read_file(f"{base}/{name}")
        try:
            body = json.loads(text) if text else None
        except json.JSONDecodeError:
            body = None
        if name.endswith(".request.json"):
            if isinstance(body, dict) and isinstance(body.get("model"), str):
                request_models.add(body["model"])
            continue
        if not isinstance(body, dict):
            unreadable += 1
            continue
        if body.get("type") == "error":
            kind = (body.get("error") or {}).get("type", "unknown")
            errors[kind] = errors.get(kind, 0) + 1
            continue
        usage = body.get("usage") or {}
        model = body.get("model", "unknown")
        row = {"calls": 1,
               "input": usage.get("input_tokens", 0) or 0,
               "output": usage.get("output_tokens", 0) or 0,
               "thinking": (usage.get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0,
               "cache_read": usage.get("cache_read_input_tokens", 0) or 0,
               "cache_write": usage.get("cache_creation_input_tokens", 0) or 0}
        per_model = by_model.setdefault(model, dict.fromkeys(totals, 0))
        for key, value in row.items():
            totals[key] += value
            per_model[key] += value
    return {**totals, "requests": requests, "by_model": by_model, "errors": errors,
            "rate_limited": errors.get("rate_limit_error", 0), "unreadable": unreadable,
            "request_models": sorted(request_models)}


def seconds_between(start: str | None, end: str | None):
    if not start or not end:
        return None
    return int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())


def main(argv: list[str]) -> int:
    run, job_name, rfe_key, waited = json.loads(argv[0]), argv[1], argv[2], argv[3]
    status, job = dashboard(f"/api/jobs/{job_name}")
    if status != 200:
        emit({"run": run["id"], "error": f"job lookup failed: HTTP {status}", "response": job})
        return 1

    result = {
        "run": run["id"], "tier": run["tier"], "test": run["test"], "arm": run["arm"],
        "variant": run["variant"], "model": run["model"], "repeat": run["repeat"],
        "scenario": run["scenario"], "rfe": rfe_key, "job": job_name,
        "mode": run.get("mode", "single"),
        "strat_creator_ref": run["strat_creator_ref"], "breadboard_ref": run["breadboard_ref"],
        "markov_run_id": run.get("markov_run_id"),
        "workflow_max_concurrent_agents": run.get("workflow_max_concurrent_agents") or None,
        "script": job.get("script"), "mlflow_experiment": run["mlflow_experiment"],
        "job_status": job.get("status"), "wait_status": waited,
        "started": job.get("created"), "completed": job.get("completed"),
        "wall_seconds": seconds_between(job.get("created"), job.get("completed")),
    }
    checks = {"finished": check(job.get("status") == "completed" and waited == "completed",
                                {"job_status": job.get("status"), "wait_status": waited})}
    try:
        if run.get("mode") == "batch":
            seed = json.loads(argv[4])
            jira_result, facts = batch_jira_checks(seed, int(run["batch_size"]))
        else:
            jira_result, facts = jira_checks(rfe_key)
        checks.update(jira_result)
        result.update(facts)
    except Exception as err:  # Jira unreachable: record, don't guess
        checks["jira"] = check(False, f"Jira checks failed: {err}")
    if run.get("mode") == "batch":
        try:
            checks["reviewer_outputs_returned"] = reviewer_returns(api_bodies(job_name), result.get("strategies", []))
        except Exception as err:
            checks["reviewer_outputs_returned"] = check(False, f"API dump review checks failed: {err}")
    result["usage"] = api_usage(job_name)
    if run.get("mode") == "batch" or run["variant"] == "glm":
        additional = checks.get("reviewer_outputs_returned", {}).get("detail", {})
        models = additional.get("models", []) if isinstance(additional, dict) else []
        gate = "haiku_only" if run["variant"] == "haiku" else "model_matches"
        checks[gate] = model_identity_check(run["model"], result["usage"], models)
    result["checks"] = checks
    result["pass"] = all(c["ok"] for c in checks.values())
    result["failed_checks"] = [name for name, c in checks.items() if not c["ok"]]
    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
