#!/usr/bin/env python3
"""Archive run evidence to host var/run-data and publish verified receipts.

  archive_run.py --run markov-run-02336f23
  archive_run.py --verify var/run-data/strat-workflow/<run>/<capture>

An active run needs --allow-running and always produces a provisional capture.
Repeat after completion to create a separate final capture. Failed runs count
as terminal and must be archived too. Never overwrites an earlier capture.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tarfile
import time
from urllib.parse import urlencode, quote

BENCH = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = BENCH.parents[2] / "var/run-data/strat-workflow"
REMOTE = Path(__file__).with_name("archive_remote.py").read_bytes()
TERMINAL = {"completed", "failed", "cancelled", "canceled"}


def terminal(info):
    return (info["run"]["status"] in TERMINAL and bool(info["jobs"])
            and all(job["status"] in TERMINAL for job in info["jobs"].values()))


def wait_for_terminal(collector, run_id, seconds):
    """Bounded read-only polling for use by a detached host collector."""
    deadline = time.monotonic() + seconds
    while True:
        info = json.loads(collector.remote("pipeline-dashboard", "info", run_id))
        if terminal(info):
            return info
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"run/jobs not terminal within {seconds}s; no final receipt published")
        print(f"Waiting for {run_id}: {info['run']['status']}, {len(info['jobs'])} jobs", flush=True)
        time.sleep(min(30, remaining))


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def unpack_job(directory, name):
    """Expose job evidence without following links or trusting tar paths."""
    if not re.fullmatch(r"script-[a-zA-Z0-9_-]+", name):
        raise ValueError("unsafe job name")
    root = Path(directory) / "jobs" / name
    prefixes = {f"app/artifacts/{kind}/{name}/": label for kind, label in
                (("scripts", "artifacts"), ("apibodies", "api-dumps"), ("strace", "strace"))}
    counts = {label: 0 for label in prefixes.values()}
    with tarfile.open(root / "files.tar.gz", "r|gz") as archive:
        for member in archive:
            if member.isdir() or member.name == "capture-inventory.json":
                continue
            if not member.isfile():
                raise ValueError(f"unsupported archive member: {member.name}")
            for prefix, label in prefixes.items():
                if member.name.startswith(prefix):
                    relative = Path(member.name[len(prefix):])
                    if relative.is_absolute() or ".." in relative.parts:
                        raise ValueError(f"unsafe archive path: {member.name}")
                    target = root / label / relative
                    if not target.resolve().is_relative_to(root.resolve()) or target.is_symlink():
                        raise ValueError(f"unsafe extraction target: {member.name}")
                    target.parent.mkdir(parents=True, exist_ok=True)
                    content = archive.extractfile(member)
                    if target.exists():
                        # Repeatable unpacking must never overwrite edited evidence.
                        digest = hashlib.sha256()
                        for block in iter(lambda: content.read(1024 * 1024), b""):
                            digest.update(block)
                        if target.stat().st_size != member.size or sha256(target) != digest.hexdigest():
                            raise ValueError(f"existing evidence differs: {target}")
                    else:
                        with target.open("xb") as output:
                            for block in iter(lambda: content.read(1024 * 1024), b""):
                                output.write(block)
                    counts[label] += 1
                    break
            else:
                raise ValueError(f"unexpected archive member: {member.name}")
    return counts


def manifest_files(root):
    return [{"path": str(path.relative_to(root)), "bytes": path.stat().st_size, "sha256": sha256(path)}
            for path in sorted(root.rglob("*")) if path.is_file()
            and not (path.parent == root and (path.name == "manifest.json" or path.name.startswith("receipt-")))]


def verify(directory):
    root = Path(directory)
    manifest = json.loads((root / "manifest.json").read_text())
    problems = []
    for record in manifest["files"]:
        path = root / record["path"]
        if Path(record["path"]).is_absolute() or not path.resolve().is_relative_to(root.resolve()):
            problems.append(f"unsafe manifest path: {record['path']}")
        elif not path.is_file() or path.stat().st_size != record["bytes"] or sha256(path) != record["sha256"]:
            problems.append(f"missing or changed file: {record['path']}")
    if not manifest["files"]:
        problems.append("capture has no files")
    if not manifest.get("complete") or not manifest.get("final"):
        problems.append("capture is incomplete or provisional; it does not authorize a reset")
    if manifest.get("errors"):
        problems.append("capture contains source errors")
    return {"ok": not problems, "run_id": manifest["run_id"], "archive": str(root), "problems": problems}


def scrub_k8s(value):
    """Retain resource identity/spec/status without credential environment values."""
    if isinstance(value, list):
        return [scrub_k8s(item) for item in value]
    if isinstance(value, dict):
        result = {key: scrub_k8s(item) for key, item in value.items() if key != "managedFields"}
        if isinstance(result.get("name"), str) and "value" in result and re.search("TOKEN|SECRET|PASSWORD|API.?KEY|CREDENTIAL", result["name"], re.I):
            result["value"] = "<redacted>"
        return result
    return value


class Collector:
    def __init__(self, root, namespace):
        self.root, self.namespace = root, namespace
        self.errors, self.sources = [], []

    def kubectl(self, *args):
        return ["kubectl", "-n", self.namespace, *args]

    def command(self, args, relative=None, input=None):
        if relative:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("wb") as output:
                result = subprocess.run(args, input=input, stdout=output, stderr=subprocess.PIPE, timeout=600)
        else:
            result = subprocess.run(args, input=input, capture_output=True, timeout=120)
        if result.returncode:
            # Errors never include request headers or the relay key.
            raise RuntimeError(result.stderr.decode(errors="replace")[-1000:])
        return result.stdout if not relative else target

    def remote(self, deployment, mode, *args, relative=None):
        return self.command(self.kubectl("exec", "-i", "deploy/" + deployment, "--", "python3", "-", mode, *args),
                            relative=relative, input=REMOTE)

    def save(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, indent=2) + "\n")

    def source(self, name, operation):
        print(f"Collecting {name}...", flush=True)
        started = datetime.now(timezone.utc).isoformat()
        try:
            operation()
            self.sources.append({"name": name, "ok": True, "started": started,
                                 "completed": datetime.now(timezone.utc).isoformat()})
        except Exception as error:
            self.errors.append({"source": name, "error": str(error)})
            self.sources.append({"name": name, "ok": False, "started": started})
            print(f"Incomplete source: {name}", flush=True)

    def tar(self, deployment, mode, args, relative, required=()):
        target = self.remote(deployment, mode, *args, relative=relative)
        # Consume every member to detect truncation, not just the gzip header.
        with tarfile.open(target, "r|gz") as archive:
            inventory = None
            for member in archive:
                if member.isfile():
                    content = archive.extractfile(member)
                    if member.name == "capture-inventory.json":
                        inventory = json.load(content)
                    else:
                        while content.read(1024 * 1024):
                            pass
            if inventory is None:
                raise RuntimeError("archive has no completion inventory")
            missing = [path for path in required if not inventory["paths"].get(path)]
            if missing:
                raise RuntimeError(f"required paths absent: {missing}")
            self.save(relative + ".inventory.json", inventory)

    def job(self, name, metadata):
        self.save(f"jobs/{name}/metadata.json", metadata)
        paths = [f"/app/artifacts/{kind}/{name}" for kind in ("scripts", "apibodies", "strace")]
        required = [paths[0]] if name.startswith("script-seed-") else paths
        self.tar("pipeline-dashboard", "files", [json.dumps(paths)], f"jobs/{name}/files.tar.gz", required)
        unpack_job(self.root, name)
        self.resources(name, f"jobs/{name}/kubernetes")

    def resources(self, name, relative):
        resource = json.loads(self.command(self.kubectl("get", "job", name, "-o", "json")))
        self.save(relative + "/job.json", scrub_k8s(resource))
        pods = json.loads(self.command(self.kubectl("get", "pods", "-l", "job-name=" + name, "-o", "json")))
        self.save(relative + "/pods.json", scrub_k8s(pods))
        if not pods["items"]:
            raise RuntimeError("job pods absent; pod logs cannot be collected")
        for pod in pods["items"]:
            pod_name = pod["metadata"]["name"]
            events = json.loads(self.command(self.kubectl("get", "events", "--field-selector", "involvedObject.name=" + pod_name, "-o", "json")))
            self.save(relative + f"/{pod_name}-events.json", events)
            for container in [*pod["spec"].get("initContainers", []), *pod["spec"]["containers"]]:
                self.command(self.kubectl("logs", pod_name, "-c", container["name"], "--timestamps"),
                             relative + f"/{pod_name}-{container['name']}.log")

    def relay(self, start):
        # Authentication stays inside the relay container, never in host files,
        # argv, stdout, or the archive. Export all pages, including usage events.
        shell = 'relay_archive_key=$(cat /run/secrets/model-relay/admin-api-key); exec curl -fsS -H "Authorization: Bearer $relay_archive_key" "http://127.0.0.1:8081/api/private/v1/$1"'
        def get(path):
            return json.loads(self.command(self.kubectl("exec", "deploy/model-relay", "--", "sh", "-c", shell, "sh", path)))
        def pages(path, query):
            cursor, seen = None, set()
            while True:
                params = {**query, **({"cursor": cursor} if cursor is not None else {})}
                page = get(path + "?" + urlencode(params))
                yield from page["items"]
                cursor = page.get("next_cursor")
                if cursor is None:
                    break
                if cursor in seen:
                    raise RuntimeError("relay pagination cursor repeated")
                seen.add(cursor)
        self.save("relay/health.json", get("health"))
        requests = list(pages("telemetry/requests", {"from": start, "limit": 500, "order": "asc"}))
        self.save("relay/requests.json", {"scope": "all system requests since run start", "items": requests})
        for index, row in enumerate(requests):
            request_id = row["request_id"]
            self.save(f"relay/events/{request_id}.json", list(pages(
                "telemetry/requests/" + quote(request_id, safe="") + "/events", {"limit": 500})))
            if index % 50 == 0:
                print(f"Relay events: {index + 1}/{len(requests)}", flush=True)

    def publish_receipts(self, info):
        """Publish only after host checksums verify. Receipts survive artifact wipes."""
        manifest_hash = sha256(self.root / "manifest.json")
        code = ('import json,pathlib,sys; r=json.load(sys.stdin); '
                'p=pathlib.Path("/app/logs/strat-workflow-archive-receipts")/(r["job"]+".json"); '
                'p.parent.mkdir(parents=True,exist_ok=True); t=p.with_suffix(".tmp"); '
                't.write_text(json.dumps(r,indent=2)+"\\n"); t.replace(p)')
        for name in info["jobs"]:
            if not name.startswith(("script-run-workflow-", "script-strategy-entrypoint-")):
                continue
            receipt = {"job": name, "run_id": info["run"]["run_id"], "archive": str(self.root.resolve()),
                       "verified": True, "final": True, "manifest_sha256": manifest_hash,
                       "verified_at": datetime.now(timezone.utc).isoformat()}
            self.command(self.kubectl("exec", "-i", "deploy/pipeline-dashboard", "--", "python3", "-c", code),
                         input=json.dumps(receipt).encode())
            self.save("receipt-" + name + ".json", receipt)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--run")
    source.add_argument("--verify", type=Path)
    parser.add_argument("--publish-receipts", action="store_true", help="publish receipts after verifying an existing final archive")
    parser.add_argument("--unpack", action="store_true", help="with --verify, expose job files and update manifest checksums")
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--namespace", default="ai-pipeline")
    parser.add_argument("--allow-running", action="store_true")
    parser.add_argument("--wait", type=int, default=0, metavar="SECONDS",
                        help="wait for terminal run/jobs before final collection; suitable for a detached host process")
    args = parser.parse_args(argv)
    if args.unpack and not args.verify:
        parser.error("--unpack requires --verify")
    if args.wait < 0 or (args.wait and args.verify):
        parser.error("--wait requires --run and nonnegative seconds")
    os.umask(0o077)
    if args.verify:
        report = verify(args.verify)
        if report["ok"] and args.unpack:
            manifest = json.loads((args.verify / "manifest.json").read_text())
            report["unpacked"] = {name: unpack_job(args.verify, name) for name in manifest["jobs"]}
            manifest["files"] = manifest_files(args.verify)
            manifest["unpacked_at"] = datetime.now(timezone.utc).isoformat()
            Collector(args.verify, args.namespace).save("manifest.json", manifest)
            report.update(verify(args.verify))
        if report["ok"] and args.publish_receipts:
            collector = Collector(args.verify, args.namespace)
            info = {"run": json.loads((args.verify / "markov/run.json").read_text()),
                    "jobs": {name: json.loads((args.verify / "jobs" / name / "metadata.json").read_text())
                             for name in json.loads((args.verify / "manifest.json").read_text())["jobs"]}}
            collector.publish_receipts(info)
            report["receipts_published"] = True
        print(json.dumps(report))
        return 0 if report["ok"] else 1
    if not re.fullmatch(r"markov-run-[a-z0-9-]+", args.run):
        parser.error("invalid Markov run ID")
    started = datetime.now(timezone.utc)
    root = args.root / args.run / started.strftime("%Y%m%dT%H%M%S%fZ")
    # Resolve run identity before creating a local capture.
    collector = Collector(root, args.namespace)
    info = (wait_for_terminal(collector, args.run, args.wait) if args.wait else
            json.loads(collector.remote("pipeline-dashboard", "info", args.run)))
    is_terminal = terminal(info)
    if not is_terminal and not args.allow_running:
        parser.error("run/jobs still active; use --allow-running for a provisional capture")
    if not info["jobs"]:
        parser.error("no benchmark jobs discovered; cannot establish capture scope")
    # The capture interval excludes time spent waiting for the run.
    started = datetime.now(timezone.utc)
    root = args.root / args.run / started.strftime("%Y%m%dT%H%M%S%fZ")
    collector.root = root
    root.mkdir(parents=True, exist_ok=False)
    collector.save("markov/run.json", info["run"])
    collector.save("markov/workflow.json", info["workflow"])
    collector.source("pinned benchmark source", lambda: collector.command([
        "git", "-C", str(BENCH.parents[2]), "archive", "--format=tar.gz",
        info["run"].get("workflow_source_commit") or info["workflow"]["source_commit"],
        "var/benchmarks/strat-workflow"], "context/benchmark-source.tar.gz"))
    collector.source("Markov runner", lambda: collector.resources(args.run, "markov/kubernetes"))
    for name, job in info["jobs"].items():
        collector.source(name, lambda name=name, job=job: collector.job(name, job))
    collector.source("benchmark results", lambda: collector.tar("pipeline-dashboard", "files", [json.dumps([
        "/app/artifacts/benchmarks/strat-workflow/" + args.run])], "markov/results.tar.gz",
        required=["/app/artifacts/benchmarks/strat-workflow/" + args.run] if info["run"]["status"] == "completed" else []))
    collector.source("dashboard stored state", lambda: collector.tar("pipeline-dashboard", "files", [json.dumps([
        "/app/artifacts", "/app/logs", "/app/issues", "/app/workspace"])], "system-state/dashboard-files.tar.gz",
        required=["/app/artifacts", "/app/logs", "/app/issues", "/app/workspace"]))
    for deployment, database in (("jira-emulator", "/data/jira.db"), ("mlflow", "/data/mlflow.db"),
                                  ("observatory", "/data/observatory.db")):
        collector.source(deployment + " database/files", lambda deployment=deployment, database=database:
                         collector.tar(deployment, "database", [database, json.dumps(["/data"])],
                                       f"system-state/{deployment}.tar.gz", required=["/data"]))
    collector.source("Jira readable export", lambda: collector.remote("pipeline-dashboard", "jira", relative="jira/issues.json"))
    architecture = "/app/.context/snapshots/architecture-context/7d61f097a9220aeb1280837b66b532177ec558b6"
    collector.source("architecture snapshot", lambda: collector.tar("pipeline-dashboard", "files", [json.dumps([architecture])],
                                                                    "context/architecture.tar.gz", required=[architecture]))
    for deployment in ("pipeline-dashboard", "markovd", "jira-emulator", "mlflow", "observatory", "model-relay", "github-emulator"):
        collector.source(deployment + " logs", lambda deployment=deployment: collector.command(collector.kubectl(
            "logs", "deploy/" + deployment, "--all-containers=true", "--timestamps", "--since-time=" + info["run"]["created_at"]),
            f"logs/{deployment}.log"))
    collector.source("relay telemetry", lambda: collector.relay(info["run"]["created_at"]))
    collector.source("final run identity", lambda: collector.save("markov/run-at-capture-end.json", json.loads(
        collector.remote("pipeline-dashboard", "info", args.run))["run"]))
    files = manifest_files(root)
    manifest = {"schema_version": 1, "run_id": args.run,
                "workflow_source_commit": info["run"].get("workflow_source_commit") or info["workflow"].get("source_commit"),
                "jobs": list(info["jobs"]), "started": started.isoformat(), "completed": datetime.now(timezone.utc).isoformat(),
                "final": is_terminal, "complete": not collector.errors, "sources": collector.sources,
                "errors": collector.errors, "files": files,
                "scope": "per-run job files/logs and workflow; full retained dashboard volume data and shared-service database/file snapshots; service logs and relay telemetry since run start",
                "consistency": "SQLite online backups are individually consistent; services are captured over the recorded time interval",
                "limitations": ["Historical Jira states already reset cannot be recovered from today's snapshot",
                                "Kubernetes events/logs expired before capture cannot be reconstructed",
                                "Symlinks in stored data are listed but not followed"]}
    collector.save("manifest.json", manifest)
    report = verify(root)
    if report["ok"]:
        try:
            collector.publish_receipts(info)
            report["receipts_published"] = True
        except Exception as error:
            report["receipts_published"] = False
            report["receipt_error"] = str(error)
            report["ok"] = False
    print(json.dumps(report))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
