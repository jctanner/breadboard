#!/usr/bin/env python3
"""Mixed-state fixture setup and mechanical checks. Never calls a model.

Seed review-only work using the pinned host preparation and push helpers,
before creating the remaining RFEs. Guard the actual preparation before
Claude starts. After cleanup, check Jira and prepare once more without Claude.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import urlparse

KIND = "mixed-state-v1"
PROCESSING = "strat-creator-processing"
OWNER_PREFIX = "strat-creator-owner-"
FINAL_LABELS = {"strat-creator-rubric-pass", "strat-creator-needs-attention"}
REVIEW = re.compile(r"^\*?\[Strat Creator\]\*?\s+Strategy Review\s+[—-]\s+(\w+)\s+\(Score:\s*([\d.]+)/(\d+)\)")
FIELDS = "summary,description,priority,status,labels,issuelinks,comment,attachment"


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate(scenario):
    rows = scenario["rfes"]
    if scenario.get("kind") != KIND or scenario.get("batch_size") != 10:
        raise ValueError("mixed fixture needs its explicit kind and a ten-candidate cap")
    if len(rows) + sum(bool(row.get("strat")) for row in rows) != scenario["expected_initial_issues"]:
        raise ValueError("mixed fixture issue count disagrees with inventory")
    review = [row for row in rows if row["action"] == "review"]
    if len(review) != 2 or rows[:2] != review:
        raise ValueError("two review fixtures must precede all other work for genuine preparation")
    if any(not row["strat"].get("strategy", "").strip() for row in review):
        raise ValueError("review-only fixtures need authored strategy content")
    active = [r for r in rows if r["action"] in {"create", "refine", "review"}]
    if len(active) != 10 or len({r["template"] for r in active}) != 10:
        raise ValueError("mixed scenario needs ten distinct actionable capabilities")
    if scenario.get("require_distinct_templates") and len({r["template"] for r in rows}) != len(rows):
        raise ValueError("mixed scenario controls must also have distinct templates")
    return scenario


def connection():
    # Only the job-side seed/guard/finish paths need httpx. Runner-side
    # check_run imports this module using the standard library alone.
    import httpx
    from seed_scenario import EMULATOR_HOSTS
    server = os.environ["JIRA_SERVER"].rstrip("/")
    if urlparse(server).hostname not in EMULATOR_HOSTS:
        raise ValueError("mixed fixtures may only access the Jira emulator")
    client = httpx.Client(base_url=server,
                          auth=(os.environ["JIRA_USER"], os.environ["JIRA_TOKEN"]),
                          verify=os.environ.get("JIRA_CA_FILE") or os.environ.get("REQUESTS_CA_BUNDLE") or True,
                          timeout=60)

    def api(method, path, **kwargs):
        response = client.request(method, path, **kwargs)
        response.raise_for_status()
        return response.json() if response.content else None
    return client, api


def normalize(issue):
    fields = issue["fields"]
    links = [{"id": str(link.get("id", "")), "type": link.get("type", {}).get("name"),
              **{side: link[side]["key"] for side in ("inwardIssue", "outwardIssue") if side in link}}
             for link in fields.get("issuelinks", [])]
    comments = fields.get("comment", {})
    if comments.get("total", len(comments.get("comments", []))) != len(comments.get("comments", [])):
        raise ValueError("truncated comment snapshot")
    return {
        "summary": fields.get("summary"), "description": fields.get("description"),
        "priority": fields.get("priority"), "status": fields.get("status", {}).get("name"),
        "labels": sorted(fields.get("labels", [])), "links": sorted(links, key=digest),
        "comments": sorted([{"id": str(c["id"]), "body": c["body"]}
                            for c in comments.get("comments", [])], key=lambda c: c["id"]),
        "attachments": sorted([{k: a.get(k) for k in ("id", "filename", "size", "mimeType")}
                               for a in fields.get("attachment", [])], key=digest),
    }


def snapshot(api):
    search = api("GET", "/rest/api/2/search", params={
        "jql": "project in (RHAIRFE, RHAISTRAT) ORDER BY key ASC", "maxResults": 200, "fields": "key"})
    if search.get("total", len(search["issues"])) != len(search["issues"]):
        raise ValueError("truncated issue inventory")
    return {row["key"]: normalize(api("GET", f"/rest/api/3/issue/{row['key']}", params={"fields": FIELDS}))
            for row in search["issues"]}


def discover(checkout, env, limit):
    proc = subprocess.run([sys.executable, str(checkout / "scripts/list-rfe-ids.py"),
                           "--jql-default", "--batch-size", str(limit)], cwd=checkout,
                          env={**env, "BATCH_OFFSET": "0"}, capture_output=True, text=True, check=False)
    if proc.returncode:
        raise RuntimeError("discovery failed: " + proc.stderr[-1500:])
    return proc.stdout.split()


def command(args, checkout, env, log, expected=(0,)):
    proc = subprocess.run(args, cwd=checkout, env=env, capture_output=True, text=True, timeout=600, check=False)
    with Path(log).open("a") as out:
        out.write(json.dumps({"argv": args, "exit": proc.returncode}) + "\n" + proc.stdout + proc.stderr + "\n")
    if proc.returncode not in expected:
        raise RuntimeError(f"{Path(args[0]).name} failed ({proc.returncode}); see {log}: {proc.stderr[-1600:]}")
    return proc.returncode


def prove_push(checkout, rows, out, ref, repo):
    """Produce an actual earlier run's proof, with only these two RFEs present."""
    state = out / "fixture-state"
    env = {**os.environ, "TARGET_REPO_DIR": str(checkout), "STRAT_STATE_DIR": str(state),
           "STRAT_CREATOR_REF": ref, "STRAT_CREATOR_REPO": repo,
           "STRAT_MODE": "batch", "STRAT_RUN_ID": "mixed-fixture-push",
           "STRAT_DRY_RUN": "", "BATCH_SIZE": "10", "BATCH_OFFSET": "0",
           "BATCH_EXPECTED_KEYS": " ".join(discover(checkout, os.environ.copy(), 10)),
           "STRAT_PREVIOUS_PROGRESS": "", "STRAT_ARCHITECTURE_CONTEXT_PATH": os.environ.get(
               "STRAT_ARCHITECTURE_CONTEXT_PATH", "/app/.context/snapshots/architecture-context/7d61f097a9220aeb1280837b66b532177ec558b6")}
    log = out / "fixture-preparation.log"
    shared = state / "strat-creator/.fullsend/shared"
    try:
        command(["bash", str(checkout / ".fullsend/shared/pre-strategy.sh")], checkout, env, log)
        for row in rows:
            key = row["strat_key"]
            path = checkout / f"artifacts/strat-tasks/{key}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("## Strategy (AI Generated by Agentic SDLC Pipeline)\n\n" + row["strategy"])
            # Author the fixture in Jira's round-trip Markdown form. This
            # avoids inventing a cache mismatch from our own line wrapping.
            command([sys.executable, "-c",
                     ("from pathlib import Path; import sys; sys.path.insert(0, 'scripts'); "
                     "from jira_utils import adf_to_markdown, markdown_to_adf; "
                     "from push_strategy import STAFF_INPUT_TEMPLATE; "
                     "p=Path(sys.argv[1]); p.write_text(adf_to_markdown(markdown_to_adf(p.read_text()+'\\n\\n'+STAFF_INPUT_TEMPLATE)))"),
                     str(path)], checkout, env, log)
            command([sys.executable, "scripts/frontmatter.py", "set", str(path),
                     f"strat_id={key}", f"source_rfe={row['key']}", f"jira_key={key}",
                     f"title={row['summary']}", "priority=Major", "status=Refined"], checkout, env, log)
        command([sys.executable, "scripts/strat_pipeline_state.py", "record-create"], checkout, env, log)
        for row in rows:
            command([sys.executable, "scripts/strat_pipeline_state.py", "mark", "refine", row["strat_key"]],
                    checkout, env, log)
        command([sys.executable, "scripts/push_refined_strategies.py"], checkout, env, log)
        command([sys.executable, "scripts/strat_pipeline_state.py", "mark", "push"], checkout, env, log)
        previous = out / "previous-progress.json"
        shutil.copyfile(checkout / "tmp/strat-progress.json", previous)
        shutil.copytree(checkout / "artifacts", out / "prior-artifacts")
        return str(previous)
    finally:
        if (shared / "release-locks.sh").exists():
            command(["bash", str(shared / "release-locks.sh"), str(state)], checkout, env, log)


def seed(args, scenario, templates):
    import yaml
    from require_archive import DEFAULT_SINCE, check_archives
    from seed_scenario import (
        BENCH_LABEL,
        EXTRA_ELIGIBLE_LABELS,
        RELEASE_LABEL,
        clone_strat_creator,
    )
    validate(scenario)
    client, api = connection()
    out = Path(os.environ["JOB_ARTIFACT_DIR"]).resolve()
    fixture = out / "mixed-fixture"
    fixture.mkdir(parents=True, exist_ok=True)
    with client, tempfile.TemporaryDirectory() as temporary:
        checkout = args.strat_creator.resolve() if args.strat_creator else clone_strat_creator(
            args.strat_creator_ref, Path(temporary) / "strat-creator", args.strat_creator_repo)
        ref = subprocess.check_output(["git", "-C", str(checkout), "rev-parse", "HEAD"], text=True).strip()
        settings = yaml.safe_load((checkout / "config/pipeline-settings.yaml").read_text())
        eligible = [RELEASE_LABEL, *settings["jql"]["quality_labels"][:1], *EXTRA_ELIGIBLE_LABELS]
        if RELEASE_LABEL not in settings["jql"]["required_labels"]:
            raise ValueError("fixture release label is outside candidate scope")
        for project in ("RHAIRFE", "RHAISTRAT"):
            api("GET", f"/rest/api/2/project/{project}")
        if args.dry_run:
            print(json.dumps({"dry_run": True, "kind": KIND, "rfes": len(scenario["rfes"]),
                              "issues": scenario["expected_initial_issues"], "candidate": ref}, indent=2))
            return 0
        archives = check_archives(os.environ.get("STRAT_ARCHIVE_REQUIRED_SINCE", DEFAULT_SINCE))
        if not archives["ok"]:
            raise ValueError("previous runs require verified archives before mixed seeding")
        reset = scenario.get("reset", True) and not args.no_reset
        if reset and api("POST", "/api/admin/reset").get("message") != "Database reset successfully":
            raise ValueError("unexpected Jira reset reply")
        created, previous = [], None
        for index, row in enumerate(scenario["rfes"]):
            template = templates[row["template"]]
            summary = template["summary"]
            if row["action"] in {"untouched", "late-skip"}:
                summary = f"[Control: {row['id']}] {summary}"
            labels = [BENCH_LABEL, f"swe-{args.scenario}", f"swe-id-{row['id']}", *row.get("labels", [])]
            if row["eligible"]:
                labels += eligible
            issue = api("POST", "/rest/api/2/issue", json={"fields": {
                "project": {"key": "RHAIRFE"}, "issuetype": {"name": "Feature Request"},
                "summary": summary, "description": template["description"],
                "priority": {"name": "Major"}, "labels": list(dict.fromkeys(labels))}})
            record = {**row, "key": issue["key"], "summary": summary}
            if row.get("strat"):
                strat = row["strat"]
                labels = [BENCH_LABEL, "strat-creator-auto-created", *strat.get("labels", [])]
                if strat["state"] in {"missing-proof", "human-cleared"}:
                    labels.append("strat-creator-auto-refined")
                new = api("POST", "/rest/api/2/issue", json={"fields": {
                    "project": {"key": "RHAISTRAT"}, "issuetype": {"name": "Feature"},
                    "summary": summary, "description": "## Strategy\n\n" + strat.get(
                        "strategy", f"Existing draft for {summary}.\n\n{template['description']}"),
                    "priority": {"name": "Major"}, "labels": labels}})
                record["strat_key"] = new["key"]
                record["strategy"] = strat.get("strategy", "")
                api("POST", "/rest/api/2/issueLink", json={"type": {"name": "Cloners"},
                    "inwardIssue": {"key": new["key"]}, "outwardIssue": {"key": issue["key"]}})
                desired = strat.get("status")
                if desired:
                    # Emulator import supports the complete status inventory,
                    # including Draft/Refinement which need not be workflow transitions.
                    api("POST", "/api/admin/import", json={"issues": [{
                        "key": new["key"], "project": "RHAISTRAT", "issue_type": "Feature",
                        "summary": summary, "description": "## Strategy\n\n" + strat.get(
                            "strategy", f"Existing draft for {summary}.\n\n{template['description']}"),
                        "status": desired, "priority": "Major", "labels": labels}]})
                    actual = api("GET", f"/rest/api/2/issue/{new['key']}")["fields"]["status"]["name"]
                    if actual != desired:
                        raise ValueError(f"cannot seed {desired} status (got {actual})")
                api("POST", f"/rest/api/2/issue/{new['key']}/attachments",
                    headers={"X-Atlassian-Token": "no-check"},
                    files={"file": ("fixture-sentinel.txt", f"Preserve attachment for {row['id']}.\n".encode(), "text/plain")})
                if strat["state"] == "human-cleared":
                    api("POST", f"/rest/api/2/issue/{new['key']}/comment", json={
                        "body": "[Fixture history] Human cleared the previous needs-attention gate; refinement is still required."})
            # Sentinels make accidental rewrites of ignored comments visible.
            api("POST", f"/rest/api/2/issue/{issue['key']}/comment", json={
                "body": f"[Fixture sentinel] {row['id']}; preserve this input."})
            created.append(record)
            if index == 1:
                previous = prove_push(checkout, created, fixture, ref, args.strat_creator_repo)
        pool = discover(checkout, os.environ.copy(), 200)
        selected = discover(checkout, os.environ.copy(), scenario["batch_size"])
        expected_pool = {r["key"] for r in created if r["action"] != "untouched"}
        if set(pool) != expected_pool or len(pool) != len(expected_pool):
            raise ValueError(f"candidate discovery differs from manifest: {pool}, expected {sorted(expected_pool)}")
        by_key = {r["key"]: r for r in created}
        acquired = [key for key in selected if by_key[key]["action"] != "late-skip"]
        points = {key: by_key[key]["action"] for key in acquired}
        if len(acquired) != scenario["expected_acquired"]:
            raise ValueError(f"expected {scenario['expected_acquired']} acquired, got {acquired}")
        before = snapshot(api)
        if len(before) != scenario["expected_initial_issues"]:
            raise ValueError("unexpected Jira issue inventory")
        report = {"kind": KIND, "scenario": args.scenario, "description": scenario["description"],
                  "server": os.environ["JIRA_SERVER"].rstrip("/"), "strat_creator_ref": ref,
                  "strat_creator_repo": args.strat_creator_repo, "reset": reset, "rfes": created,
                  "pool_in_order": pool, "discovered": sorted(selected), "discovered_in_order": selected,
                  "expected_acquired_keys": acquired, "expected_resume_points": points,
                  "expected_preparation_skips": [k for k in selected if k not in acquired],
                  "deferred_keys": [k for k in pool if k not in selected and by_key[k]["action"] != "late-skip"],
                  "previous_progress_path": previous, "before": before, "ok": True, "problems": []}
        write(out / "seed.json", report)
        write(fixture / "jira-before.json", before)
        print(json.dumps({k: v for k, v in report.items() if k not in {"before", "rfes"}}, indent=2))
    return 0


def preparation_checks(seed, prepared):
    expected = seed["expected_acquired_keys"]
    return {
        "candidate_pin": prepared.get("freshness", {}).get("contract") == "strat-freshness-v1",
        "discovery_order": prepared.get("input_keys") == seed["discovered_in_order"],
        "acquisition": prepared.get("acquired_keys") == expected,
        "resume_points": prepared.get("resume_points") == seed["expected_resume_points"],
        "late_gate": [row["key"] for row in prepared.get("skipped", [])] == seed["expected_preparation_skips"],
        "no_create_skips": prepared.get("expected_skips") == [],
        "verified_reuse": set(prepared.get("reused_push", {})) == {
            k for k, point in seed["expected_resume_points"].items() if point == "review"},
    }


def linked(issue):
    return sorted({link[side] for link in issue["links"] for side in ("inwardIssue", "outwardIssue")
                   if side in link and link[side].startswith("RHAISTRAT-") and link["type"] == "Cloners"})


def comment_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "".join(comment_text(node) for node in value)
    if isinstance(value, dict):
        text = value.get("text", "") + comment_text(value.get("content", []))
        return text + ("\n" if value.get("type") in {"paragraph", "heading", "hardBreak"} else "")
    return ""


def assess(seed, after, prepared, progress):
    """Return independently reproducible checks, without model judgment."""
    before = seed["before"]
    acquired = seed["expected_acquired_keys"]
    rows = {r["key"]: r for r in seed["rfes"]}
    checks = {"preparation": all(preparation_checks(seed, prepared).values())}
    controls = [k for key, row in rows.items() if key not in acquired
                for k in (key, row.get("strat_key")) if k]
    checks["untouched_controls_and_deferred"] = all(after.get(k) == before[k] for k in controls)
    expected_new = sum(rows[k]["action"] == "create" for k in acquired)
    new_keys = set(after) - set(before)
    checks["clone_count"] = (len(new_keys) == expected_new and all(k.startswith("RHAISTRAT-") for k in new_keys)
                              and set(before) <= set(after))
    pairs, items = [], []
    for rfe in acquired:
        targets = linked(after.get(rfe, {"links": []}))
        item = {"rfe": rfe, "action": rows[rfe]["action"], "strategies": targets}
        identity = len(targets) == 1 and (not rows[rfe].get("strat_key") or targets == [rows[rfe]["strat_key"]])
        item["identity_ok"] = identity
        if identity:
            key = targets[0]
            pairs.append(key)
            current = after[key]
            reviews = [match for c in current["comments"] if (match := REVIEW.match(comment_text(c["body"]).strip()))]
            labels = set(current["labels"])
            expected_label = "strat-creator-rubric-pass" if reviews and reviews[0][1].lower() == "approve" else "strat-creator-needs-attention"
            item["completed"] = (len(reviews) == 1 and labels & FINAL_LABELS == {expected_label}
                                 and {"strat-creator-auto-created", "strat-creator-auto-refined"} <= labels)
            review_files = [a for a in current["attachments"] if a["filename"] == f"{key}-review.md"]
            item["one_review_attachment"] = len(review_files) == 1
            old = before.get(key, {"comments": [], "attachments": []})
            item["existing_effects_preserved"] = (all(c in current["comments"] for c in old["comments"])
                                                   and all(a in current["attachments"] for a in old["attachments"]))
            if rows[rfe]["action"] == "review":
                old_strategy = [a for a in old["attachments"] if a["filename"] == f"{key}-strategy.md"]
                new_strategy = [a for a in current["attachments"] if a["filename"] == f"{key}-strategy.md"]
                item["review_only_preserved"] = (old["description"] == current["description"]
                                                  and old_strategy == new_strategy
                                                  and key not in progress.get("refine", {})
                                                  and key not in (progress.get("push") or {}).get("strategies", []))
            else:
                item["refined_and_pushed"] = (key in progress.get("refine", {})
                                                and key in (progress.get("push") or {}).get("strategies", []))
        items.append(item)
    checks["per_ticket_completion"] = all(all(v for k, v in item.items() if k.endswith(("_ok", "_preserved"))
                                                       or k in {"completed", "one_review_attachment", "refined_and_pushed"})
                                           and item["identity_ok"] for item in items)
    checks["distinct_strategies"] = len(pairs) == len(acquired) == len(set(pairs))
    checks["owned_locks_released"] = all(
        PROCESSING not in after[k]["labels"] and not any(x.startswith(OWNER_PREFIX) for x in after[k]["labels"])
        for rfe in acquired for k in (rfe, *linked(after[rfe])))
    return {"checks": checks, "ok": all(checks.values()), "items": items, "strategies": pairs,
            "acquired_count": len(acquired), "candidate_count": len(seed["discovered_in_order"]),
            "deferred_keys": seed["deferred_keys"], "new_strategies": sorted(new_keys)}


def repeat(checkout, seed, out):
    """Use a clean preparation and release its claims. No Claude invocation."""
    target = out / "repeat-repo"
    state = out / "repeat-state"
    log = out / "repeat-preparation.log"
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", str(checkout), str(target)], check=True)
    env = {**os.environ, "TARGET_REPO_DIR": str(target), "REPO_DIR": str(target),
           "STRAT_STATE_DIR": str(state), "STRAT_RUN_ID": "repeat-" + os.environ["STRAT_RUN_ID"],
           "BATCH_EXPECTED_KEYS": "", "STRAT_PREVIOUS_PROGRESS": "", "BATCH_OFFSET": "0"}
    shared = state / "strat-creator/.fullsend/shared"
    client, api = connection()
    try:
        with client:
            before = snapshot(api)
            code = command(["bash", str(target / ".fullsend/shared/pre-strategy.sh")], target, env, log, (0, 78))
            run = json.loads((state / "run.json").read_text())
            command(["bash", str(shared / "release-locks.sh"), str(state)], target, env, log)
            after = snapshot(api)
            expected_pool = {r["key"] for r in seed["rfes"] if r["action"] == "late-skip"} | set(seed["deferred_keys"])
            checks = {"completed_work_excluded": set(run["input_keys"]) == expected_pool,
                      "only_deferred_work_acquired": run["acquired_keys"] == seed["deferred_keys"],
                      "no_duplicate_side_effects": before == after,
                      "no_model_call": not (target / "artifacts/strat-tasks").exists(),
                      "expected_exit": code == (0 if seed["deferred_keys"] else 78)}
            result = {"ok": all(checks.values()), "checks": checks, "exit": code, "run": run,
                      "model_invocations": 0, "note": "Deferred work stays pending; this is not global queue exhaustion."}
            write(out / "mixed-repeat.json", result)
            return result
    finally:
        if (state / "owned-rfe-ids.txt").exists():
            command(["bash", str(shared / "release-locks.sh"), str(state)], target, env, log)


def main(argv):
    mode, seed_path, target_path, state_path, out_path = argv[:5]
    seed_report = json.loads(Path(seed_path).read_text())
    target, state, out = map(Path, (target_path, state_path, out_path))
    if seed_report["kind"] != KIND or not seed_report["ok"]:
        raise ValueError("invalid mixed-state seed report")
    actual = subprocess.check_output(["git", "-C", str(target), "rev-parse", "HEAD"], text=True).strip()
    if actual != seed_report["strat_creator_ref"]:
        raise ValueError("mixed seed and workflow candidate differ")
    prepared = json.loads((state / "run.json").read_text())
    if mode == "guard":
        checks = preparation_checks(seed_report, prepared)
        result = {"ok": all(checks.values()), "checks": checks, "prepared": prepared,
                  "acquired_count": len(prepared["acquired_keys"]),
                  "candidate_count": len(prepared["input_keys"])}
        write(out / "mixed-preflight.json", result)
        shutil.copyfile(seed_path, out / "mixed-seed.json")
        print(json.dumps({k: v for k, v in result.items() if k != "prepared"}))
        return 0 if result["ok"] else 1
    if mode != "finish":
        raise ValueError("expected guard or finish")
    client, api = connection()
    with client:
        after = snapshot(api)
    write(out / "mixed-jira-after.json", after)
    progress_path = target / "tmp/strat-progress.json"
    progress = json.loads(progress_path.read_text()) if progress_path.exists() else {}
    result = assess(seed_report, after, prepared, progress)
    if argv[5:] == ["0"] and result["ok"]:
        result["repeat"] = repeat(target, seed_report, out)
        result["ok"] = result["repeat"]["ok"]
    else:
        result["repeat"] = {"ok": False, "skipped": "original run or mixed-state checks failed; no repeat claims taken"}
        result["ok"] = False
    write(out / "mixed-state-result.json", result)
    print(json.dumps(result))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
