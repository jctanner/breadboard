#!/usr/bin/env python3
"""Measure each conversation's input context using exact API-dump index pairs.

Run inside the dashboard pod:
  python3 - <job> ... < context_growth.py
  python3 - --json <job> ... < context_growth.py

Input context = input_tokens + cache_read_input_tokens + cache_creation_input_tokens.
These are per-request sizes, not cumulative usage or the model's window capacity.
The final response's output is reported separately from the last observed input.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def text_of(content):
    if isinstance(content, str):
        return content
    return " ".join(
        block.get("text", "") if block.get("type") == "text"
        else text_of(block.get("content")) if block.get("type") == "tool_result"
        else ""
        for block in content or []
    )


def role_of(first):
    tail = first[-1500:]
    if 'Workflow({ name: "strat-pipeline:strat-pipeline" })' in first:
        return "primary"
    for marker, role in (
        ("cite specific components, APIs", "reviewer: architecture"),
        ("Be adversarial", "reviewer: feasibility"),
        ("can't be tested", "reviewer: testability"),
        ("If scope is too large", "reviewer: scope"),
        ("Run directory: /tmp/strat-assess", "scorer"),
        ("Skipping Jira update", "refine skill (fork)"),
        ("record-review", "review helper"),
        ("record-create", "create helper"),
        ("mark refine", "refine helper"),
        ("push_refined_strategies.py", "push helper"),
        ("strat_pipeline_state.py read", "read helper"),
        ("strat_pipeline_state.py result", "result helper"),
    ):
        if marker in tail:
            return role
    return "other"


def history_ids(messages):
    return {
        b["id"] for m in messages if m.get("role") == "assistant"
        for b in m.get("content", []) if isinstance(b, dict)
        and b.get("type") == "tool_use"
    }


def analyze(job, root):
    directory = root / job
    indexed = [json.loads(line) for line in (directory / "index.jsonl").read_text().splitlines() if line.strip()]
    # Request mtimes describe when the input was submitted; index timestamps are
    # recorded at response completion. No attribution by nearest response time.
    indexed.sort(key=lambda x: (directory / Path(x["request_file"]).name).stat().st_mtime)
    groups, families, seen = [], {}, set()
    for entry in indexed:
        request_name = Path(entry["request_file"]).name
        if request_name in seen:
            raise ValueError(f"Duplicate indexed request: {request_name}")
        seen.add(request_name)
        request_path = directory / request_name
        request = json.loads(request_path.read_text())
        response = json.loads((directory / Path(entry["response_file"]).name).read_text())
        if response.get("id") != entry.get("message_id"):
            raise ValueError(f"Response ID mismatch: {request_name}")
        usage = response["usage"]
        fields = ("input_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")
        if any(field not in usage for field in fields):
            raise ValueError(f"Incomplete input usage: {request_name}")
        messages = request.get("messages", [])
        first = text_of(messages[0]["content"]) if messages else ""
        system = text_of(request.get("system"))
        fingerprint = hashlib.sha256((system[:3000] + "|" + first[-1500:]).encode()).hexdigest()[:12]
        ids = history_ids(messages)
        candidates = families.setdefault(fingerprint, [])
        # Identical skill prompts can be relaunched. Shared tool-use IDs link
        # continuation calls; a shorter, disjoint history begins another launch.
        group = next((g for g in reversed(candidates) if ids & g["history_ids"]), None)
        if group is None and candidates and len(messages) > candidates[-1]["last_messages"]:
            group = candidates[-1]
        if group is None:
            group = {"conversation": f"{fingerprint}/{len(candidates) + 1}",
                     "role": role_of(first), "history_ids": set(), "last_messages": 0,
                     "session_ids": set(), "calls": []}
            groups.append(group)
            candidates.append(group)
        group["history_ids"].update(ids)
        group["last_messages"] = len(messages)
        group["session_ids"].add(entry.get("session_id"))
        previous = group["calls"][-1] if group["calls"] else None
        context = sum(usage[field] for field in fields)
        timestamp = request_path.stat().st_mtime
        blocks = [b for m in messages for b in m.get("content", []) if isinstance(b, dict)]
        tool_names = {b["id"]: b["name"] for b in blocks if b.get("type") == "tool_use"}
        new_results = []
        for b in blocks:
            if b.get("type") != "tool_result":
                continue
            if previous and b.get("tool_use_id") in previous["result_ids"]:
                continue
            value = text_of(b.get("content"))
            new_results.append({"tool": tool_names.get(b.get("tool_use_id"), "unknown"),
                                "chars": len(value),
                                "head": " ".join(value.split())[:180]})
        outputs = [b for b in response.get("content", []) if b.get("type") == "tool_use"]
        call = {"n": len(group["calls"]) + 1, "request_file": request_name,
                "response_file": Path(entry["response_file"]).name,
                "timestamp": datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
                "elapsed_seconds": timestamp - (group["calls"][0]["request_epoch"] if previous else timestamp),
                "request_epoch": timestamp, "messages": len(messages),
                "input_context_tokens": context,
                "growth_tokens": context - previous["input_context_tokens"] if previous else None,
                "usage": {field: usage[field] for field in fields},
                "output_tokens": usage.get("output_tokens", 0),
                "response_tools": [b["name"] for b in outputs],
                "new_tool_results": new_results,
                "result_ids": {b.get("tool_use_id") for b in blocks if b.get("type") == "tool_result"},
                "block_counts": dict(Counter(b.get("type") for b in blocks)),
                "compaction_marker": any(marker in text_of(messages[-1].get("content", ""))
                                         for marker in ("continued from a previous conversation", "<compaction>")) if messages else False}
        group["calls"].append(call)
    conversations = []
    for group in groups:
        calls = group.pop("calls")
        group.pop("history_ids")
        group.pop("last_messages")
        group["session_ids"] = sorted(group["session_ids"], key=str)
        sizes = [c["input_context_tokens"] for c in calls]
        duration = calls[-1]["elapsed_seconds"]
        delta = sizes[-1] - sizes[0]
        group.update(calls=len(calls), first_tokens=sizes[0], last_tokens=sizes[-1],
                     peak_tokens=max(sizes), growth_tokens=delta,
                     request_span_seconds=duration,
                     net_tokens_per_minute=delta / (duration / 60) if duration else None,
                     net_tokens_per_transition=delta / (len(calls) - 1) if len(calls) > 1 else None,
                     input_drops=sum(b < a for a, b in zip(sizes, sizes[1:])),
                     compaction_markers=sum(c["compaction_marker"] for c in calls))
        for call in calls:
            call.pop("result_ids")
            call.pop("request_epoch")
        group["snapshots"] = calls
        conversations.append(group)
    unindexed_roles = Counter()
    for path in directory.glob("*.request.json"):
        if path.name not in seen:
            request = json.loads(path.read_text())
            messages = request.get("messages", [])
            unindexed_roles[role_of(text_of(messages[0]["content"]) if messages else "")] += 1
    return {"job": job, "indexed_pairs": len(indexed),
            "unindexed_requests": sum(unindexed_roles.values()),
            "unindexed_requests_by_role": dict(unindexed_roles),
            "conversations": conversations}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--root", type=Path, default=Path("/app/artifacts/apibodies"))
    parser.add_argument("jobs", nargs="+")
    args = parser.parse_args()
    results = [analyze(job, args.root) for job in args.jobs]
    if args.json:
        print(json.dumps(results, indent=2))
        return
    for result in results:
        print(f"\n{result['job']}: {result['indexed_pairs']} exact pairs, "
              f"{result['unindexed_requests']} requests without indexed responses")
        for group in result["conversations"]:
            print(f"{group['role']:24} {group['calls']:3} calls  "
                  f"{group['first_tokens']:7,} -> {group['last_tokens']:7,} tokens  "
                  f"peak {group['peak_tokens']:7,}  drops {group['input_drops']}")
            if group["role"] == "primary":
                for call in group["snapshots"]:
                    print(f"  {call['n']:2} +{call['elapsed_seconds']/60:5.2f}m "
                          f"{call['input_context_tokens']:7,} tokens  "
                          f"response tools: {','.join(call['response_tools']) or '-'}")


if __name__ == "__main__":
    main()
