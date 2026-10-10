#!/usr/bin/env python3
# Architecture-context requests per agent, from a job's API dumps. Run inside the dashboard pod:
#   python3 - <job> [...] < arch_requests.py
# Conversations (agents) are rebuilt as in conv_breakdown.py; each response's tool calls are
# attributed to its conversation, and architecture docs are taken from Read file_paths, Bash
# commands naming them (bare names resolved against the directory the command cd's into) and
# Grep/Glob calls over the context.
import json, os, glob, hashlib, re, sys
from collections import defaultdict, Counter

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

AC = "architecture-context/"
def docs_in(tool, inp):
    """Architecture docs a tool call requests, as paths under architecture-context/."""
    out = []
    if tool == "Read":
        p = inp.get("file_path", "")
        if AC in p: out.append(p.split(AC, 1)[1])
    elif tool in ("Grep", "Glob"):
        p = inp.get("path", "") or ""
        pat = inp.get("pattern", "") or ""
        if AC in p or AC in pat:
            where = (p.split(AC, 1)[1] if AC in p else "") or "."
            out.append(f"[{tool} sweep] {where.rstrip('/')}" + (f" {pat}" if tool == "Glob" else ""))
    elif tool == "Bash":
        cmd = inp.get("command", "") or ""
        if "architecture" not in cmd and "overlays" not in cmd: return out
        cwd = ""
        m = re.search(r"cd \S*?" + re.escape(AC) + r"(\S*?)(?:\s|&&|;|$)", cmd)
        if m: cwd = m.group(1).rstrip("/")
        for tok in re.findall(r"[\w./*{}-]+\.md\b|LATEST_VERSION", cmd):
            if AC in tok: out.append(tok.split(AC, 1)[1])
            elif tok.startswith(("architecture/", "overlays/")): out.append(tok)
            elif "/" not in tok and (cwd or "architecture-context" in cmd): out.append((cwd + "/" if cwd else "") + tok)
            elif cwd and not tok.startswith("/"): out.append(cwd + "/" + tok)
    return [re.sub(r"^\./", "", d) for d in out]

DESIGNS = {}
KINDS = defaultdict(lambda: defaultdict(Counter))
for job in sys.argv[1:]:
    design = "S1 Workflow" if "run-workflow" in job else "S2 bash"
    d = f"/app/artifacts/apibodies/{job}"
    reqs, resps = [], []
    for f in glob.glob(d + "/*.json"):
        try: body = json.load(open(f))
        except Exception: continue
        (reqs if f.endswith(".request.json") else resps).append((os.path.getmtime(f), body))
    reqs.sort(key=lambda x: x[0]); resps.sort(key=lambda x: x[0])
    convs, by_tool = {}, {}
    for t, q in reqs:
        sysp = q.get("system"); sys_text = text_of(sysp) if isinstance(sysp, list) else (sysp or "")
        msgs = q.get("messages", []); first = text_of(msgs[0]["content"]) if msgs else ""
        key = hashlib.sha1((sys_text[:3000] + "|" + first[-1500:]).encode()).hexdigest()[:10]
        c = convs.setdefault(key, {"first": first, "t0": t, "last_t": t, "calls": []}); c["last_t"] = t
        for m in msgs:
            if m.get("role") == "assistant" and isinstance(m.get("content"), list):
                for b in m["content"]:
                    if b.get("type") == "tool_use": by_tool[b["id"]] = key
    for t, r in resps:
        if not isinstance(r, dict): continue
        uses = [b for b in r.get("content", []) if b.get("type") == "tool_use"]
        key = next((by_tool[b["id"]] for b in uses if b["id"] in by_tool), None)
        if key is None and uses:
            before = [(c["last_t"], k) for k, c in convs.items() if c["last_t"] <= t]
            key = max(before)[1] if before else None
        if key: convs[key]["calls"].extend(uses)
    n = 0
    run = defaultdict(lambda: defaultdict(Counter))   # role -> conversation -> doc counts
    for key, c in sorted(convs.items(), key=lambda kv: kv[1]["t0"]):
        role = role_of(c["first"], n)
        if "documented completion marker" in c["first"][-600:]: n += 1
        for b in c["calls"]:
            for doc in docs_in(b["name"], b.get("input") or {}):
                run[role][key][doc] += 1
                cmd = (b.get("input") or {}).get("command", "") or ""
                kind = b["name"] if b["name"] != "Bash" else ("Bash grep" if re.search(r"\b(grep|rg)\b", cmd) else "Bash sed/head" if re.search(r"\b(sed|head|tail|awk)\b", cmd) else "Bash cat" if re.search(r"\bcat\b", cmd) else "Bash other")
                KINDS[design][role][kind] += 1
    DESIGNS.setdefault(design, []).append((job, run))

for design, runs in DESIGNS.items():
    print(f"\n######## {design}: {len(runs)} runs")
    roles = sorted({r for _, run in runs for r in run})
    for role in roles:
        total = Counter(); max_one = Counter(); runs_with = Counter()
        for _, run in runs:
            seen = set()
            for conv, docs in run.get(role, {}).items():
                for doc, k in docs.items():
                    total[doc] += k; max_one[doc] = max(max_one[doc], k); seen.add(doc)
            for doc in seen: runs_with[doc] += 1
        if not total: continue
        reps = sum(v for v in total.values()) - sum(1 for _ in total)  # beyond first request per doc (across runs: approx)
        print(f"\n  {role}: {sum(total.values())} requests for {len(total)} docs across {len(runs)} runs")
        print(f"    {'requests':>8} {'max in one agent':>16} {'runs':>4}  doc")
        for doc, k in total.most_common(10):
            print(f"    {k:8} {max_one[doc]:16} {runs_with[doc]:4}  {doc[:100]}")
    # Same doc fetched independently by several agents in one run.
    print(f"\n  docs fetched by 3+ different agents in the same run (agents, runs where that happened):")
    multi = Counter(); agents_n = defaultdict(list)
    for _, run in runs:
        holders = defaultdict(set)
        for role, convs_ in run.items():
            for conv, docs in convs_.items():
                for doc in docs:
                    if not doc.startswith("["): holders[doc].add(conv)
        for doc, cs in holders.items():
            if len(cs) >= 3: multi[doc] += 1; agents_n[doc].append(len(cs))
    for doc, k in multi.most_common(12):
        print(f"    {doc[:90]:90} agents {agents_n[doc]}  ({k}/{len(runs)} runs)")

print("\n######## how the requests were made (per design and agent, all runs)")
for design, roles in KINDS.items():
    for role, kinds in sorted(roles.items()):
        print(f"  {design:12} {role:24} " + ", ".join(f"{k} {v}" for k, v in kinds.most_common()))
