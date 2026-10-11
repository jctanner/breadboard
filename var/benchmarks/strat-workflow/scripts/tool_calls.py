#!/usr/bin/env python3
# Every tool call the model made in a job, from its API dumps, sub-agents included. Run inside
# the dashboard pod:
#   python3 - <job> [...] < tool_calls.py            summary tables
#   python3 - --jsonl <job> [...] < tool_calls.py    one JSON record per tool call
# Conversations (agents) are rebuilt as in conv_breakdown.py. A call's tool_use block comes from
# the assistant turns that later requests carry (or, for a conversation's last turn, its
# response); its tool_result, from the user turn after it. The time is the response dump's mtime.
import json, os, glob, hashlib, re, sys
from collections import defaultdict, Counter
from datetime import datetime, timezone

def text_of(content):
    if isinstance(content, str): return content
    out = []
    for c in content or []:
        if c.get("type") == "text": out.append(c.get("text", ""))
        elif c.get("type") == "tool_result":
            cc = c.get("content"); out.append(cc if isinstance(cc, str) else text_of(cc))
    return " ".join(out)

def role_of(first, idx_completion):
    tail = first[-600:]
    if "cite specific components, APIs" in tail: return "reviewer: architecture"
    if "Be adversarial" in tail: return "reviewer: feasibility"
    if "can't be tested" in tail: return "reviewer: testability"
    if "If scope is too large" in tail: return "reviewer: scope"
    if "Run directory: /tmp/strat-assess" in tail: return "scorer"
    if "Skipping Jira update" in tail: return "refine"
    if "documented completion marker" in tail: return ["create", "refine", "review"][min(idx_completion, 2)]
    if "record-review" in tail: return "review"
    if "record-create" in tail: return "create"
    return "workflow plumbing"

def brief(tool, inp):
    """The part of a tool's input worth reading: command, path or pattern."""
    if tool == "Bash": return " ".join((inp.get("command") or "").split())
    if tool in ("Read", "Write", "Edit"): return inp.get("file_path", "")
    if tool in ("Grep", "Glob"): return f"{inp.get('pattern', '')} in {inp.get('path') or '.'}"
    if tool == "Skill": return inp.get("skill", "") + (" " + inp["args"] if inp.get("args") else "")
    if tool == "Agent": return inp.get("description", "") or (inp.get("prompt") or "")[:120]
    return json.dumps(inp)[:200]

def verb(tool, inp):
    """A coarse kind for the call: the Bash program, or the tool name."""
    if tool != "Bash": return tool
    cmd = inp.get("command") or ""
    for part in re.split(r"&&|\|\||;|\|", cmd):
        words = [w for w in part.split() if "=" not in w or w.startswith(("-", "/"))]
        while words and words[0] in ("cd", "timeout", "env", "sudo", "time"):
            words = words[2:] if words[0] in ("cd", "timeout") else words[1:]
        if words and words[0] not in ("echo", "set", "export"):
            return "Bash " + os.path.basename(words[0])
    return "Bash (other)"

def norm(s):
    """Job-specific paths shortened, so the same call compares equal across runs and designs."""
    s = re.sub(r"\S*/\.context/architecture-context/", "<ctx>/", s)
    return re.sub(r"/app/tmp/(?:strat-workflow|script-src)/script-[\w.-]+?(?:/repo)?/", "<repo>/", s)

def iso(t): return datetime.fromtimestamp(t, timezone.utc).strftime("%H:%M:%S") if t else None

def request_key(q):
    sysp = q.get("system"); sys_text = text_of(sysp) if isinstance(sysp, list) else (sysp or "")
    msgs = q.get("messages", []); first = text_of(msgs[0]["content"]) if msgs else ""
    return hashlib.sha1((sys_text[:3000] + "|" + first[-1500:]).encode()).hexdigest()[:10]

def job_calls(job):
    design = "S1" if "run-workflow" in job else "S2"
    reqs, resps = [], []
    for f in glob.glob(f"/app/artifacts/apibodies/{job}/*.json"):
        try: body = json.load(open(f))
        except Exception: continue
        (reqs if f.endswith(".request.json") else resps).append((os.path.getmtime(f), body))
    reqs.sort(key=lambda x: x[0]); resps.sort(key=lambda x: x[0])
    convs = {}
    for t, q in reqs:
        msgs = q.get("messages", []); first = text_of(msgs[0]["content"]) if msgs else ""
        key = request_key(q)
        c = convs.setdefault(key, {"first": first, "t0": t, "last_t": t, "uses": {}, "order": [], "results": {}})
        c["last_t"] = t
        for m in msgs:
            if not isinstance(m.get("content"), list): continue
            for b in m["content"]:
                if m.get("role") == "assistant" and b.get("type") == "tool_use" and b["id"] not in c["uses"]:
                    c["uses"][b["id"]] = b; c["order"].append(b["id"])
                elif m.get("role") == "user" and b.get("type") == "tool_result":
                    c["results"][b["tool_use_id"]] = b
    owner = {i: k for k, c in convs.items() for i in c["uses"]}
    by_text = {}
    for t, q in reqs:
        key = request_key(q)
        for m in q.get("messages", []):
            if m.get("role") == "assistant" and isinstance(m.get("content"), list):
                for b in m["content"]:
                    if b.get("type") == "text" and b.get("text"): by_text[hashlib.sha1(b["text"].encode()).hexdigest()] = key
    # Every request gets one response, written after it. Walk both in time order, keeping the
    # requests not yet answered. A response a later request carries (by tool_use ID or text) answers
    # its own conversation's request; a conversation's last response, which nothing carries, answers
    # the latest open request. Assigning it to whoever asked last instead misplaces it whenever
    # another agent sends its first request in between.
    events = sorted([(t, 0, request_key(q), None) for t, q in reqs] + [(t, 1, None, r) for t, r in resps], key=lambda e: (e[0], e[1]))
    open_reqs, resp_time = [], {}
    for t, kind, key, r in events:
        if kind == 0: open_reqs.append(key); continue
        if not isinstance(r, dict): continue
        uses = [b for b in r.get("content", []) if b.get("type") == "tool_use"]
        for b in uses: resp_time.setdefault(b["id"], t)
        known = next((owner[b["id"]] for b in uses if b["id"] in owner), None) or next(
            (by_text.get(hashlib.sha1(b["text"].encode()).hexdigest()) for b in r.get("content", [])
             if b.get("type") == "text" and b.get("text") and hashlib.sha1(b["text"].encode()).hexdigest() in by_text), None)
        k = known if known in open_reqs else (open_reqs[-1] if open_reqs else known)
        if k in open_reqs: del open_reqs[len(open_reqs) - 1 - open_reqs[::-1].index(k)]
        if k is None: continue
        for b in uses:
            if b["id"] not in owner:
                convs[k]["uses"][b["id"]] = b; convs[k]["order"].append(b["id"]); owner[b["id"]] = k
    out, completions = [], 0
    for k, c in sorted(convs.items(), key=lambda kv: kv[1]["t0"]):
        if not c["order"]: continue
        role = role_of(c["first"], completions)
        if "documented completion marker" in c["first"][-600:]: completions += 1
        for n, i in enumerate(c["order"], 1):
            b, res = c["uses"][i], c["results"].get(i)
            # Claude Code appends <system-reminder> blocks to some results; they aren't the tool's.
            text = re.sub(r"<system-reminder>.*?</system-reminder>", "", text_of(res.get("content")) if res else "", flags=re.S)
            out.append({"job": job, "design": design, "agent": role, "conversation": k, "n": n,
                        "time": iso(resp_time.get(i)), "tool": b["name"], "kind": verb(b["name"], b.get("input") or {}),
                        "input": norm(brief(b["name"], b.get("input") or {})),
                        "error": bool(res and res.get("is_error")), "answered": res is not None,
                        "result_chars": len(text), "result_head": " ".join(text.split())[:160]})
    return out

args = sys.argv[1:]
jsonl = "--jsonl" in args
jobs = [a for a in args if not a.startswith("--")]
calls = [c for j in jobs for c in job_calls(j)]
if jsonl:
    for c in calls: print(json.dumps(c))
    sys.exit()

runs = {d: len({c["job"] for c in calls if c["design"] == d}) for d in ("S1", "S2")}
print("Tool calls per run, by job")
for j in jobs:
    cs = [c for c in calls if c["job"] == j]
    tools = Counter(c["tool"] for c in cs)
    print(f"  {j[-40:]:40} {len(cs):4} calls, {sum(c['error'] for c in cs):3} errors   " + ", ".join(f"{t} {n}" for t, n in tools.most_common()))

print("\nMean per run, by agent (S1 vs S2): calls, errors, top kinds")
agents = sorted({c["agent"] for c in calls})
for a in agents:
    for d in ("S1", "S2"):
        cs = [c for c in calls if c["agent"] == a and c["design"] == d]
        if not cs or not runs[d]: continue
        kinds = Counter(c["kind"] for c in cs)
        print(f"  {a:24} {d}  {len(cs)/runs[d]:6.1f} calls  {sum(c['error'] for c in cs)/runs[d]:4.1f} err   "
              + ", ".join(f"{k} {n/runs[d]:.1f}" for k, n in kinds.most_common(6)))

print("\nErrors (tool_result is_error), by design and kind")
for d in ("S1", "S2"):
    errs = [c for c in calls if c["design"] == d and c["error"]]
    print(f"  {d}: {len(errs)} in {runs[d]} runs   " + ", ".join(f"{k} {n}" for k, n in Counter(c["kind"] for c in errs).most_common(8)))
    for head, n in Counter(re.sub(r"\d+", "N", c["result_head"][:90]) for c in errs).most_common(6):
        print(f"      {n:3}x  {head}")

print("\nForked skills that returned no text (\"Skill execution completed\" only), and reruns of the same skill")
for d in ("S1", "S2"):
    sk = [c for c in calls if c["design"] == d and c["tool"] == "Skill"]
    empty = [c for c in sk if c["result_head"].rstrip().endswith("Result: Skill execution completed")]
    reruns = sum(n - 1 for n in Counter((c["job"], c["input"]) for c in sk).values())
    print(f"  {d}: {len(sk)} skill calls, {len(empty)} empty results, {reruns} reruns in {runs[d]} runs   "
          + ", ".join(f"{k.split()[0]} {n}" for k, n in Counter(c["input"] for c in empty).most_common()))
    so = Counter(c["agent"] for c in calls if c["design"] == d and c["tool"] == "StructuredOutput" and c["agent"].startswith("reviewer"))
    print(f"      reviewer StructuredOutput calls: " + (", ".join(f"{a.split(': ')[1]} {n}" for a, n in so.most_common()) or "none"))

print("\nSame call repeated within one agent (identical input), top 12")
rep = Counter((c["job"], c["agent"], c["tool"], c["input"]) for c in calls)
for (j, a, t, i), n in [x for x in rep.most_common() if x[1] > 1][:12]:
    print(f"  {n:3}x  {'S1' if 'run-workflow' in j else 'S2'} {j[-6:]} {a:24} {t:5} {i[:150]}")
print("\nRepeated identical calls per run (calls beyond the first of each input), by design and agent")
for d in ("S1", "S2"):
    extra = Counter()
    for (j, a, t, i), n in rep.items():
        if ("run-workflow" in j) == (d == "S1"): extra[a] += n - 1
    print(f"  {d}: " + ", ".join(f"{a} {n/runs[d]:.1f}" for a, n in extra.most_common() if n))
