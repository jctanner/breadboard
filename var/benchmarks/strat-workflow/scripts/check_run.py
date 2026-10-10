#!/usr/bin/env python3
"""Check one finished test run and print its eval-result.

    check_run.py '<run json>' <job name> <RFE key>

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


def jira_checks(rfe_key: str) -> tuple[dict, dict]:
    rfe = jira(f"/rest/api/2/issue/{rfe_key}?fields=labels,issuelinks")
    strat_keys = linked_strategies(rfe)
    all_strats = [i["key"] for i in jira("/rest/api/2/search?jql=project%3DRHAISTRAT&fields=key&maxResults=100")["issues"]]
    strats = [jira(f"/rest/api/2/issue/{k}?fields=labels,description,comment") for k in strat_keys]

    checks = {"one_strategy": check(len(strat_keys) == 1 and len(all_strats) == 1,
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


def api_usage(job: str) -> dict:
    """Sum usage over the job's API dumps (one response file per model call)."""
    base = f"/app/artifacts/apibodies/{job}"
    entries = [e["name"] for e in list_dir(base)]
    requests = sum(1 for n in entries if n.endswith(".request.json"))
    totals = {"calls": 0, "input": 0, "output": 0, "thinking": 0, "cache_read": 0, "cache_write": 0}
    by_model, errors, unreadable = {}, {}, 0
    for name in entries:
        if not name.endswith(".response.json"):
            continue
        text = read_file(f"{base}/{name}")
        try:
            body = json.loads(text) if text else None
        except json.JSONDecodeError:
            body = None
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
            "rate_limited": errors.get("rate_limit_error", 0), "unreadable": unreadable}


def seconds_between(start: str | None, end: str | None):
    if not start or not end:
        return None
    return int((datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds())


def main(argv: list[str]) -> int:
    run, job_name, rfe_key = json.loads(argv[0]), argv[1], argv[2]
    status, job = dashboard(f"/api/jobs/{job_name}")
    if status != 200:
        emit({"run": run["id"], "error": f"job lookup failed: HTTP {status}", "response": job})
        return 1

    result = {
        "run": run["id"], "tier": run["tier"], "test": run["test"], "arm": run["arm"],
        "variant": run["variant"], "model": run["model"], "repeat": run["repeat"],
        "scenario": run["scenario"], "rfe": rfe_key, "job": job_name,
        "strat_creator_ref": run["strat_creator_ref"], "script": run["script"],
        "mlflow_experiment": run["mlflow_experiment"],
        "job_status": job.get("status"),
        "started": job.get("created"), "completed": job.get("completed"),
        "wall_seconds": seconds_between(job.get("created"), job.get("completed")),
    }
    checks = {"finished": check(job.get("status") == "completed", {"job_status": job.get("status")})}
    try:
        jira_result, facts = jira_checks(rfe_key)
        checks.update(jira_result)
        result.update(facts)
    except Exception as err:  # Jira unreachable: record, don't guess
        checks["jira"] = check(False, f"Jira checks failed: {err}")
    result["checks"] = checks
    result["pass"] = all(c["ok"] for c in checks.values())
    result["failed_checks"] = [name for name, c in checks.items() if not c["ok"]]
    result["usage"] = api_usage(job_name)
    emit(result)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
