#!/usr/bin/env python3
# Group a job's API dumps into conversations and report each one's calls and tokens.
# Requests and responses are saved under unrelated IDs, so a response is matched to its
# conversation through the next request that carries it as an assistant turn (by tool_use IDs
# or text); a conversation's final response, which no request carries, goes to the conversation
# whose latest request came just before it. Run inside the dashboard pod.
import json, os, glob, hashlib, sys
from collections import defaultdict

def text_of(content):
    if isinstance(content, str): return content
    out = []
    for c in content or []:
        if c.get("type") == "text": out.append(c.get("text", ""))
        elif c.get("type") == "tool_result":
            cc = c.get("content")
            out.append(cc if isinstance(cc, str) else text_of(cc))
    return " ".join(out)

def conv_key(q):
    sysp = q.get("system")
    sys_text = text_of(sysp) if isinstance(sysp, list) else (sysp or "")
    msgs = q.get("messages", [])
    first = text_of(msgs[0]["content"]) if msgs else ""
    # The first user message carries reminders that can vary; key on its task-specific tail.
    return hashlib.sha1((sys_text[:3000] + "|" + first[-1500:]).encode()).hexdigest()[:10], sys_text, first, msgs

for job in sys.argv[1:]:
    d = f"/app/artifacts/apibodies/{job}"
    reqs, resps = [], []
    for f in glob.glob(d + "/*.json"):
        try: body = json.load(open(f))
        except Exception: continue
        (reqs if f.endswith(".request.json") else resps).append((os.path.getmtime(f), body))
    reqs.sort(key=lambda x: x[0]); resps.sort(key=lambda x: x[0])

    convs = {}
    by_tool, by_text = {}, {}
    for t, q in reqs:
        key, sys_text, first, msgs = conv_key(q)
        c = convs.setdefault(key, {"reqs": 0, "first": first, "sys": len(sys_text), "tools_avail": len(q.get("tools", [])),
                                   "max_msgs": 0, "last_t": 0, "t0": t, "resp": []})
        c["reqs"] += 1; c["max_msgs"] = max(c["max_msgs"], len(msgs)); c["last_t"] = t
        for m in msgs:
            if m.get("role") != "assistant" or not isinstance(m.get("content"), list): continue
            for b in m["content"]:
                if b.get("type") == "tool_use": by_tool[b["id"]] = key
                elif b.get("type") == "text" and b.get("text"): by_text[hashlib.sha1(b["text"].encode()).hexdigest()] = key

    unmatched = 0
    for t, r in resps:
        if not isinstance(r, dict) or "usage" not in r: continue
        key = None
        for b in r.get("content", []):
            if b.get("type") == "tool_use" and b["id"] in by_tool: key = by_tool[b["id"]]; break
            if b.get("type") == "text" and b.get("text"):
                key = by_text.get(hashlib.sha1(b["text"].encode()).hexdigest())
                if key: break
        if key is None:
            unmatched += 1
            before = [(c["last_t"], k) for k, c in convs.items() if c["last_t"] <= t]
            key = max(before)[1] if before else None
        if key: convs[key]["resp"].append(r)

    def u(r, f): return (r.get("usage") or {}).get(f, 0) or 0
    rows = []
    for k, c in convs.items():
        rs = c["resp"]
        tools = defaultdict(int)
        for r in rs:
            for b in r.get("content", []):
                if b.get("type") == "tool_use": tools[b["name"]] += 1
        peak = max([u(r, "input_tokens") + u(r, "cache_read_input_tokens") + u(r, "cache_creation_input_tokens") for r in rs] or [0])
        rows.append(dict(k=k, calls=len(rs), peak=peak, sys=c["sys"], tools_avail=c["tools_avail"],
                         out=sum(u(r, "output_tokens") for r in rs),
                         think=sum(((r.get("usage") or {}).get("output_tokens_details") or {}).get("thinking_tokens", 0) or 0 for r in rs),
                         cr=sum(u(r, "cache_read_input_tokens") for r in rs), cw=sum(u(r, "cache_creation_input_tokens") for r in rs),
                         first=c["first"], tools=tools, t0=c["t0"], models={r.get("model") for r in rs}))
    rows.sort(key=lambda x: x["t0"])
    tot = {k: sum(x[k] for x in rows) for k in ("calls", "out", "think", "cr", "cw")}
    print(f"\n=== {job}\n{len(rows)} conversations, {tot['calls']} calls ({unmatched} final responses matched by time); "
          f"output {tot['out']/1e3:.0f}k (thinking {tot['think']/1e3:.0f}k), cache read {tot['cr']/1e6:.2f}M, cache write {tot['cw']/1e3:.0f}k")
    print(f"{'calls':>5} {'peakctx':>7} {'sys':>5} {'out':>5} {'think':>5} {'c.read':>7} {'c.write':>7}  conversation (task tail)")
    for x in rows:
        if x["calls"] == 0: continue
        task = " ".join(x["first"].split())[-120:]
        top = ", ".join(f"{n} {t}" for t, n in sorted(x["tools"].items(), key=lambda y: -y[1])[:5])
        print(f"{x['calls']:>5} {x['peak']/1e3:>6.0f}k {x['sys']/1e3:>4.0f}k {x['out']/1e3:>4.0f}k {x['think']/1e3:>4.0f}k {x['cr']/1e6:>6.2f}M {x['cw']/1e3:>6.0f}k  …{task}")
        print(f"{'':>45}tools: {top or '-'}")
