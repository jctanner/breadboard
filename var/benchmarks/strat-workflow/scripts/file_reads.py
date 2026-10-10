#!/usr/bin/env python3
# Which project files a job opened, how often, and by whom, from its strace -ff files.
# Run inside the dashboard pod:  python3 - <job> [...] < file_reads.py
# Reader of an open: "claude" when the process (or thread) belongs to a claude process (its
# Read/Grep/Glob tools run in-process), else the command that opened it (cat, grep, python3 ...).
import glob, re, sys, os
from collections import Counter, defaultdict

T = re.compile(r"^(\d\d:\d\d:\d\d\.\d+) ")
EXEC = re.compile(r'execve\("([^"]*)", \[(.*?)\]')
CHILD = re.compile(r"^\S+ (?:(?:clone3?|fork|vfork)\(.*|<\.\.\. (?:clone3?|fork|vfork) resumed>.*)\)\s+=\s+(\d+)$")
OPEN = re.compile(r'open(?:at)?\((?:AT_FDCWD|\d+), "([^"]+)", (O_[A-Z_|]+)')
OPEN_RES = re.compile(r"\) = (\d+)$")

def category(p):
    if p.startswith(("./architecture", "./.discovery", "./overlays")) or "/.analyzer/" in p or p.startswith("./") and ".analyzer" in p: return "architecture context (Grep sweeps)"
    if "/.context/architecture-context/" in p or p.startswith(".context/architecture-context"): return "architecture context"
    if "/.claude/skills/" in p or p.startswith(".claude/skills"): return "skills"
    if "/.claude/agents/" in p or "/plugins/" in p: return "agents/plugins"
    if "/artifacts/" in p or p.startswith("artifacts/"): return "artifacts (strategy, reviews)"
    if "/scripts/" in p or p.startswith("scripts/"): return "scripts"
    if p.endswith("CLAUDE.md"): return "CLAUDE.md"
    if "/tmp/strat-assess" in p: return "scorer run dir"
    return "other project"

def normalise(p, roots):
    for r in roots:
        if p.startswith(r): return "<repo>/" + p[len(r):].lstrip("/")
    return p

SKIP = re.compile(r"^/(proc|sys|dev|usr|lib|lib64|etc|bin|sbin|run|var/lib|opt|nix|home/pipelineagent/\.(cache|npm|local|claude|config))\b|/node_modules/|/\.git/|/site-packages/|/\.venv/|__pycache__|\.pyc$|\.so(\.\d+)*$|^/app/\.venv|^/app/artifacts/(apibodies|strace)|/mlflow/|/tmp/claude-|\.jsonl$|^/tmp/[^/]*\.(sock|tmp)$")

COMPACT = "--compact" in sys.argv
SUMMARY = []
for job in [a for a in sys.argv[1:] if not a.startswith("--")]:
    files = glob.glob(f"/app/artifacts/strace/{job}/*")
    cmd, parent, children = {}, {}, defaultdict(list)
    opens = []  # (pid, path, flags)
    for f in files:
        pid = int(f.rsplit(".", 1)[1])
        with open(f, errors="replace") as fh:
            for line in fh:
                if "execve(" in line and line.rstrip().endswith("= 0"):
                    e = EXEC.search(line)
                    if e: cmd[pid] = (e[1], re.sub(r'", "', " ", e[2]).strip('"')[:120])
                    continue
                c = CHILD.match(line.rstrip())
                if c: children[pid].append(int(c[1])); continue
                if "open" in line and "O_RDONLY" in line and not "ENOENT" in line and "O_DIRECTORY" not in line:
                    o = OPEN.search(line); r = OPEN_RES.search(line.rstrip())
                    if o and r: opens.append((pid, o[1], o[2]))
    for p, cs in children.items():
        for c in cs: parent[c] = p
    def owner(pid):
        q = pid
        while q not in cmd and q in parent: q = parent[q]
        return q
    def reader(pid):
        o = owner(pid); exe, line = cmd.get(o, ("?", "?"))
        if re.search(r"(^|/)claude(\.exe)?$", exe): return "claude"
        base = os.path.basename(exe)
        if base.startswith("python"):
            script = next((a for a in line.split(" ")[1:] if a.endswith(".py")), "python3 -c")
            return "python3 " + os.path.basename(script)
        return base
    roots = sorted({m.group(0) for _, p, _ in opens for m in [re.match(r"^/app/tmp/(?:script-src/[^/]+|strat-workflow/[^/]+/(?:repo|state/strat-creator))", p)] if m}, key=len, reverse=True)
    per_file = defaultdict(Counter)
    for pid, p, flags in opens:
        if SKIP.search(p) or not p.startswith(("/app/tmp", "/tmp/strat", ".", "artifacts", "scripts", "/app/artifacts/scripts")) and not p.startswith("/app/tmp"):
            if not (p.startswith(".") or p.startswith("artifacts") or p.startswith("scripts")): continue
        np = normalise(p, roots)
        if re.search(r"(^|/)(\.git|node_modules)(/|$)", np): continue
        leaf = np.rstrip("/").rsplit("/", 1)[-1]
        if "." not in leaf and leaf not in ("LATEST_VERSION", "Makefile", "SKILL"): continue  # directories
        per_file[np][reader(pid)] += 1
    # What the model asked for: Read tool calls (file_path) and Bash commands naming the file.
    asked = Counter()
    import json
    for f in glob.glob(f"/app/artifacts/apibodies/{job}/*.response.json"):
        try: body = json.load(open(f))
        except Exception: continue
        for b in (body.get("content") or []) if isinstance(body, dict) else []:
            if b.get("type") != "tool_use": continue
            i = b.get("input") or {}
            if b["name"] == "Read" and i.get("file_path"):
                asked[normalise(i["file_path"], roots)] += 1
            elif b["name"] == "Bash":
                for tok in re.findall(r"[\w./-]+\.(?:md|py|yaml|yml|json|sh|txt)", i.get("command") or ""):
                    key = normalise(tok, roots) if tok.startswith("/") else "<repo>/" + tok.lstrip("./")
                    asked[key] += 1
    # A path that prefixes another opened path is a directory (scanned, not read).
    paths = sorted(per_file)
    dirs = {a for a, b in zip(paths, paths[1:]) if b.startswith(a.rstrip("/") + "/")}
    for d_ in dirs: per_file.pop(d_, None)
    other_dirs = Counter()
    for p_, rc in per_file.items():
        if category(p_) == "other project":
            parts = p_.split("/")
            other_dirs["/".join(parts[:3])] += sum(rc.values())
    cats = defaultdict(lambda: [0, 0, 0])
    for p, rc in per_file.items():
        c = category(p); cats[c][0] += 1; cats[c][1] += sum(rc.values()); cats[c][2] += asked.get(p, 0)
    total_opens = sum(sum(rc.values()) for rc in per_file.values())
    by_reader = Counter()
    for rc in per_file.values(): by_reader.update(rc)
    calls = len(glob.glob(f"/app/artifacts/apibodies/{job}/*.response.json"))
    claude_opens = sum(rc.get("claude", 0) for rc in per_file.values())
    asked_total = sum(asked.get(p_, 0) for p_ in per_file)
    SUMMARY.append((job, calls, asked_total, claude_opens, cats))
    if COMPACT: continue
    print(f"\n=== {job}: {len(per_file)} project files, {total_opens} opens; by reader: " + ", ".join(f"{k} {v}" for k, v in by_reader.most_common(6)))
    print(f"  {'category':32} files  opens  model asked  opens/file")
    for c, (n, o, a) in sorted(cats.items(), key=lambda x: -x[1][1]):
        print(f"  {c:32} {n:5} {o:6} {a:11} {o/n:9.1f}")
    print("  'other project' by folder (opens): " + ", ".join(f"{k} {v}" for k, v in other_dirs.most_common(6)))
    print("  most re-opened files: opens (claude / other) | times the model asked for it")
    for p, rc in sorted(per_file.items(), key=lambda x: -sum(x[1].values()))[:18]:
        cl = rc.get("claude", 0); other = sum(rc.values()) - cl
        print(f"    {sum(rc.values()):4} ({cl:3} / {other:3}) | {asked.get(p, 0):3}  {p[-95:]}")

if COMPACT:
    print(f"{'job':58} {'model calls':>11} {'file asks':>9} {'opens by claude':>15} {'opens per ask':>13}  arch-docs opens/asks  artifacts opens/asks")
    for job, calls, asked_total, claude_opens, cats in SUMMARY:
        a = cats.get("architecture context", [0, 0, 0]); r = cats.get("artifacts (strategy, reviews)", [0, 0, 0])
        print(f"{job[:58]:58} {calls:11} {asked_total:9} {claude_opens:15} {claude_opens/max(asked_total,1):13.1f}  {a[1]:>9}/{a[2]:<9}  {r[1]:>9}/{r[2]}")
