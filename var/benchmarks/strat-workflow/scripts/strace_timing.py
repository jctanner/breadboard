#!/usr/bin/env python3
# Timing from a job's strace -ff files and API dumps. Run inside the dashboard pod:
#   python3 - <job> [<job> ...] < strace_timing.py
# For each process: start/end (first/last traced line), command (its last execve), parent
# (from clone/fork/vfork return values in the parent's file). Prints the process tree's long-
# running branches, and for each claude process: wall time, time with at least one model call
# in flight (API dumps: +1 per request file, -1 per response file, by mtime, counting only the
# requests index.jsonl pairs with a response), and time with at least one tool process alive
# (its child processes). strace times carry no date; a job that runs past midnight UTC has
# times after it moved forward a day.
import glob, os, re, sys, datetime, json
from collections import defaultdict

T = re.compile(r"^(\d\d):(\d\d):(\d\d)\.(\d+) ")
EXEC = re.compile(r'execve\("([^"]*)", \[(.*?)\]')
CHILD = re.compile(r"^\S+ (?:(?:clone3?|fork|vfork)\(.*|<\.\.\. (?:clone3?|fork|vfork) resumed>.*)\)\s+=\s+(\d+)$")

def secs(m): return int(m[1]) * 3600 + int(m[2]) * 60 + int(m[3]) + int(m[4]) / 1e6

def union(intervals):
    total, cur_s, cur_e = 0.0, None, None
    for s, e in sorted(intervals):
        if cur_e is None or s > cur_e:
            if cur_e is not None: total += cur_e - cur_s
            cur_s, cur_e = s, e
        else: cur_e = max(cur_e, e)
    if cur_e is not None: total += cur_e - cur_s
    return total

def fmt(s): return f"{s/60:5.1f}m" if s >= 90 else f"{s:5.1f}s"

for job in sys.argv[1:]:
    dumps = glob.glob(f"/app/artifacts/apibodies/{job}/*.json")
    try: ok = {json.loads(l).get("request_file") for l in open(f"/app/artifacts/apibodies/{job}/index.jsonl") if l.strip()}
    except OSError: ok = None
    dumps = [f for f in dumps if ok is None or not f.endswith(".request.json") or os.path.basename(f) in ok]
    # Time of day of the job's first model request; anything 12 h or more before it is the next day.
    first = datetime.datetime.utcfromtimestamp(min(map(os.path.getmtime, dumps))) if dumps else None
    ref = first.hour * 3600 + first.minute * 60 + first.second if first else None
    def unwrap(t): return t + 86400 if ref is not None and t < ref - 43200 else t
    procs, children = {}, defaultdict(list)
    for f in glob.glob(f"/app/artifacts/strace/{job}/*"):
        pid = int(f.rsplit(".", 1)[1]); start = end = None; cmd = None; exe = None
        with open(f, errors="replace") as fh:
            for line in fh:
                m = T.match(line)
                if not m: continue
                t = unwrap(secs(m))
                if start is None: start = t
                end = t
                e = EXEC.search(line)
                if e and " = 0" in line[-6:]:
                    exe = e[1]; cmd = re.sub(r'", "', " ", e[2]).strip('"')[:160]
                c = CHILD.match(line.rstrip())
                if c: children[pid].append(int(c[1]))
        procs[pid] = dict(start=start, end=end, cmd=cmd, exe=exe)
    parent = {c: p for p, cs in children.items() for c in cs}
    def label(pid):
        p = procs.get(pid, {}); return p.get("cmd") or f"(pid {pid}, no exec)"
    # inherit command from parent for threads/forks that never exec'd
    def cmd_of(pid):
        while pid in procs and not procs[pid]["cmd"] and pid in parent: pid = parent[pid]
        return procs.get(pid, {}).get("cmd") or ""
    roots = [p for p in procs if p not in parent]
    root = min(roots, key=lambda p: procs[p]["start"] or 1e12)
    t0 = procs[root]["start"]; wall = procs[root]["end"] - t0
    print(f"\n=== {job}: {len(procs)} processes, wall {fmt(wall)}")

    def descendants(pid):
        out, stack = [], list(children.get(pid, []))
        while stack:
            c = stack.pop(); out.append(c); stack.extend(children.get(c, []))
        return out

    # The script's own steps: processes that exec'd, are not inside a claude, last >= 3s.
    def in_claude(pid):
        while pid in parent:
            pid = parent[pid]
            if "claude" in (procs[pid].get("exe") or "") and procs[pid]["cmd"] and not procs[pid]["cmd"].startswith("bash"): return True
        return False
    steps = []
    for pid, p in procs.items():
        if not p["cmd"] or p["start"] is None: continue
        dur = p["end"] - p["start"]
        if dur < 3 or in_claude(pid): continue
        steps.append((p["start"] - t0, dur, pid, p["cmd"]))
    print("  script steps (>= 3s, outside claude), offset / duration / command:")
    for off, dur, pid, cmd in sorted(steps)[:40]:
        print(f"    +{fmt(off)} {fmt(dur)}  {cmd[:120]}")

    # API in-flight intervals from the dumps.
    events = []
    for f in dumps:
        events.append((os.path.getmtime(f), 1 if f.endswith(".request.json") else -1))
    events.sort()
    api_iv, inflight, since = [], 0, None
    tz = datetime.datetime.fromtimestamp(0).astimezone().utcoffset()
    for ts, d in events:
        dt = datetime.datetime.utcfromtimestamp(ts); t = dt.hour * 3600 + dt.minute * 60 + dt.second + dt.microsecond / 1e6
        t = unwrap(t)
        if inflight == 0 and d > 0: since = t
        inflight = max(0, inflight + d)
        if inflight == 0 and since is not None: api_iv.append((since, t)); since = None

    # Each claude process: wall, model in flight, tools alive.
    claude = [pid for pid, p in procs.items() if p["cmd"] and re.search(r"(^|/)claude(\s|$)", p["cmd"].split(" ")[0] + " ") ]
    print("  claude processes: wall / model in flight / tools alive / neither (overhead)")
    for pid in sorted(claude, key=lambda x: procs[x]["start"]):
        p = procs[pid]; s, e = p["start"], p["end"]
        tools = []
        for d in descendants(pid):
            q = procs.get(d)
            if q and q["cmd"] and q["start"] is not None and not re.search(r"(^|/)claude(\s|$)", q["cmd"].split(" ")[0] + " "):
                tools.append((q["start"], q["end"]))
        model = [(max(a, s), min(b, e)) for a, b in api_iv if b > s and a < e]
        both = union(model + tools)
        args = p["cmd"].split(" ")
        prompt = next((a for a in args if a.startswith("/")), " ".join(args[1:4]))
        print(f"    +{fmt(s - t0)} wall {fmt(e - s)}  model {fmt(union(model))}  tools {fmt(union(tools))}  neither {fmt((e - s) - both)}  {prompt[:70]}")
