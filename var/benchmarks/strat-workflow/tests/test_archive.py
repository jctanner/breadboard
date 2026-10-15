import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import archive_remote
import archive_run
import require_archive


class ArchiveTests(unittest.TestCase):
    def test_stream_timeout_is_configurable_and_small_reads_remain_bounded(self):
        with tempfile.TemporaryDirectory() as scratch:
            collector = archive_run.Collector(Path(scratch), "ai-pipeline", stream_timeout=2400)
            with patch.object(archive_run.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b"ok", b"")) as run:
                collector.command(["test"], "large.tar.gz")
                self.assertEqual(run.call_args.kwargs["timeout"], 2400)
                collector.command(["test"])
                self.assertEqual(run.call_args.kwargs["timeout"], 120)
            with self.assertRaises(ValueError):
                archive_run.Collector(Path(scratch), "ai-pipeline", stream_timeout=0)

    def test_fast_stream_preserves_file_bytes_and_completion_inventory(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            source = root / "evidence.bin"
            data = b"unchanged binary evidence\x00\xff" * 1000
            source.write_bytes(data)
            capture = root / "capture.tar.gz"
            with capture.open("wb") as output:
                subprocess.run([sys.executable, str(SCRIPTS / "archive_remote.py"), "files", json.dumps([str(source)])], stdout=output, check=True)
            with tarfile.open(capture) as archive:
                self.assertEqual(archive.extractfile(str(source).lstrip("/")).read(), data)
                inventory = json.load(archive.extractfile("capture-inventory.json"))
                self.assertTrue(inventory["paths"][str(source)])

    def test_stream_does_not_require_new_tarfile_compression_options(self):
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "evidence.txt"
            path.write_text("old Python compatibility")
            output = io.BytesIO()
            real_open = tarfile.open
            def old_python_open(*args, **kwargs):
                self.assertNotIn("compresslevel", kwargs)
                self.assertEqual(kwargs["mode"], "w|")
                return real_open(*args, **kwargs)
            with patch.object(archive_remote.sys, "stdout", SimpleNamespace(buffer=output)), \
                    patch.object(archive_remote.tarfile, "open", side_effect=old_python_open):
                archive_remote.stream_paths([str(path)])
            with real_open(fileobj=io.BytesIO(output.getvalue()), mode="r:gz") as archive:
                self.assertEqual(archive.extractfile(str(path).lstrip("/")).read(), b"old Python compatibility")

    def test_deleted_job_requires_explicit_cancellation_evidence(self):
        with tempfile.TemporaryDirectory() as scratch:
            path = Path(scratch) / "stopped.json"
            record = {"name": "script-run-stopped", "created": "2026-10-14T00:30:34Z",
                      "status": "cancelled", "script": {"ref": "candidate-commit"},
                      "stop": {"response": {"status": "stopped"}, "job_absent": True}}
            path.write_text(json.dumps(record))
            info = archive_run.stopped_job_record(path, record["name"])
            self.assertTrue(archive_run.terminal(info))
            self.assertEqual(info["run"]["source_commit"], "candidate-commit")
            record["stop"]["job_absent"] = False
            path.write_text(json.dumps(record))
            with self.assertRaises(ValueError):
                archive_run.stopped_job_record(path, record["name"])

    def test_cancelled_job_records_confirmed_absence_instead_of_inventing_logs(self):
        with tempfile.TemporaryDirectory() as scratch:
            collector = archive_run.Collector(Path(scratch), "ai-pipeline")
            with patch.object(collector, "command", side_effect=[b"", b'{"items":[]}']):
                collector.resources("script-run-stopped", "jobs/script-run-stopped/kubernetes", stopped=True)
            absence = json.loads((Path(scratch) / "jobs/script-run-stopped/kubernetes/absence.json").read_text())
            self.assertTrue(absence["job_absent"])
            self.assertFalse((Path(scratch) / "jobs/script-run-stopped/kubernetes/job.json").exists())

    def test_direct_job_identity_preserves_source_and_does_not_invent_markov_run(self):
        job = {"name": "script-run-focused", "created": "2026-10-13T22:00:00Z", "status": "failed",
               "script": {"ref": "candidate-commit", "path": "tests/reviewer-delivery/run.sh"}}
        with patch.object(archive_remote, "http", return_value=job):
            info = archive_remote.job_info(job["name"])
        self.assertEqual(info["run"]["run_id"], job["name"])
        self.assertEqual(info["run"]["execution"], "dashboard-direct")
        self.assertEqual(info["run"]["source_commit"], "candidate-commit")
        self.assertTrue(archive_run.terminal(info))

    def test_reset_gate_includes_focused_hardening_jobs(self):
        jobs = [{"name": "script-run-focused", "created": "2026-10-13T22:00:00Z", "status": "completed",
                 "mlflow_experiment": "strat-workflow-hardening/01-reviewer-delivery/glm"},
                {"name": "script-run-other", "created": "2026-10-13T22:00:00Z", "status": "completed",
                 "mlflow_experiment": None}]
        with patch.object(require_archive, "dashboard", return_value=(200, jobs)), \
                patch.object(require_archive, "read_file", return_value=None):
            result = require_archive.check_archives("2026-10-11T00:00:00Z")
        self.assertEqual([item["job"] for item in result["pending"]], ["script-run-focused"])

    def test_wait_requires_terminal_jobs_and_run(self):
        info = {"run": {"status": "running"}, "jobs": {"script-run-workflow-test": {"status": "running"}}}
        final = {"run": {"status": "completed"}, "jobs": {"script-run-workflow-test": {"status": "failed"}}}
        collector = archive_run.Collector(Path("/unused"), "ai-pipeline")
        with patch.object(collector, "remote", side_effect=[json.dumps(info), json.dumps(final)]), \
                patch.object(archive_run.time, "sleep"):
            self.assertEqual(archive_run.wait_for_terminal(collector, "markov-run-test", 100), final)
        self.assertFalse(archive_run.terminal({"run": {"status": "completed"}, "jobs": {}}))
        with patch.object(collector, "remote", return_value=json.dumps(info)), \
                patch.object(archive_run.time, "monotonic", side_effect=[0, 101]):
            with self.assertRaises(TimeoutError):
                archive_run.wait_for_terminal(collector, "markov-run-test", 100)

    def test_job_evidence_is_browsable_checked_and_repeatable(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            job = "script-run-workflow-test"
            folder = root / "jobs" / job
            folder.mkdir(parents=True)
            with tarfile.open(folder / "files.tar.gz", "w:gz") as archive:
                for kind, filename, data in (("strace", "trace.123", b"execve evidence"),
                                             ("apibodies", "nested/request.json", b'{"messages":[]}'),
                                             ("scripts", "manifest.json", b'{"job":"test"}')):
                    member = tarfile.TarInfo(f"app/artifacts/{kind}/{job}/{filename}")
                    member.size = len(data)
                    archive.addfile(member, io.BytesIO(data))
            expected = {"artifacts": 1, "api-dumps": 1, "strace": 1}
            self.assertEqual(archive_run.unpack_job(root, job), expected)
            self.assertEqual(archive_run.unpack_job(root, job), expected)
            self.assertEqual((folder / "api-dumps/nested/request.json").read_text(), '{"messages":[]}')
            manifest = {"run_id": "markov-run-test", "complete": True, "final": True, "errors": [],
                        "files": archive_run.manifest_files(root)}
            (root / "manifest.json").write_text(json.dumps(manifest))
            self.assertTrue(archive_run.verify(root)["ok"])
            self.assertIn(f"jobs/{job}/artifacts/manifest.json", [r["path"] for r in manifest["files"]])
            (folder / "strace/trace.123").write_text("edited")
            self.assertFalse(archive_run.verify(root)["ok"])
            with self.assertRaisesRegex(ValueError, "existing evidence differs"):
                archive_run.unpack_job(root, job)

    def test_job_unpack_rejects_traversal_and_links(self):
        for suffix, link in (("../../../escaped", False), ("linked", True)):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as scratch:
                root = Path(scratch)
                job = "script-run-workflow-test"
                folder = root / "jobs" / job
                folder.mkdir(parents=True)
                with tarfile.open(folder / "files.tar.gz", "w:gz") as archive:
                    member = tarfile.TarInfo(f"app/artifacts/strace/{job}/{suffix}")
                    if link:
                        member.type = tarfile.SYMTYPE
                        member.linkname = "/tmp"
                    archive.addfile(member)
                with self.assertRaises(ValueError):
                    archive_run.unpack_job(root, job)

    def test_nested_job_discovery_in_saved_step_outputs(self):
        value = {"steps": [{"output_json": json.dumps({"body": {"job_name": "script-seed-one"}})},
                            {"output_json": json.dumps({"job_name": "script-run-workflow-one"})}]}
        self.assertEqual(archive_remote.job_names(value), {"script-seed-one", "script-run-workflow-one"})

    def test_sqlite_online_backup_retains_committed_wal_data(self):
        with tempfile.TemporaryDirectory() as scratch:
            source = Path(scratch) / "source.db"
            with sqlite3.connect(source) as connection:
                connection.execute("PRAGMA journal_mode=WAL")
                connection.execute("CREATE TABLE evidence (body TEXT)")
                connection.execute("INSERT INTO evidence VALUES ('committed WAL evidence')")
                connection.commit()
                capture = Path(scratch) / "capture.tar.gz"
                with capture.open("wb") as output:
                    subprocess.run([sys.executable, str(SCRIPTS / "archive_remote.py"), "database", str(source), "[]"],
                                   stdout=output, check=True)
                with tarfile.open(capture) as archive:
                    backup = Path(scratch) / "backup.db"
                    backup.write_bytes(archive.extractfile("database.sqlite").read())
                with sqlite3.connect(backup) as restored:
                    self.assertEqual(restored.execute("SELECT body FROM evidence").fetchone()[0], "committed WAL evidence")

    def test_verify_rejects_missing_changed_and_provisional_captures(self):
        with tempfile.TemporaryDirectory() as scratch:
            root = Path(scratch)
            data = root / "evidence.json"
            data.write_text('{"preserved":true}')
            manifest = {"run_id": "markov-run-test", "final": True, "complete": True, "errors": [],
                        "files": [{"path": data.name, "bytes": data.stat().st_size, "sha256": archive_run.sha256(data)}]}
            path = root / "manifest.json"
            path.write_text(json.dumps(manifest))
            self.assertTrue(archive_run.verify(root)["ok"])
            data.write_text("changed")
            self.assertFalse(archive_run.verify(root)["ok"])
            data.unlink()
            self.assertFalse(archive_run.verify(root)["ok"])
            manifest["final"] = False
            manifest["files"] = []
            path.write_text(json.dumps(manifest))
            self.assertFalse(archive_run.verify(root)["ok"])

    def test_kubernetes_credentials_are_not_copied_into_metadata(self):
        metadata = {"spec": {"containers": [{"env": [{"name": "API_TOKEN", "value": "private"},
                                                        {"name": "BATCH_SIZE", "value": "3"}]}]}}
        cleaned = archive_run.scrub_k8s(metadata)
        self.assertNotIn("private", json.dumps(cleaned))
        self.assertEqual(cleaned["spec"]["containers"][0]["env"][1]["value"], "3")

    def test_archive_gate_requires_final_verified_receipt(self):
        jobs = [{"name": "script-run-workflow-test", "created": "2026-10-11T13:48:02+00:00", "status": "failed"},
                {"name": "script-run-workflow-old", "created": "2026-10-10T13:48:02+00:00", "status": "completed"},
                {"name": "script-seed-test", "created": "2026-10-11T13:48:02+00:00", "status": "completed"}]
        since = "2026-10-11T13:47:49+00:00"
        with patch.object(require_archive, "dashboard", return_value=(200, jobs)), \
                patch.object(require_archive, "read_file", return_value=None):
            result = require_archive.check_archives(since)
            self.assertFalse(result["ok"])
            self.assertEqual(len(result["pending"]), 1)
        receipt = {"job": jobs[0]["name"], "verified": True, "final": True, "archive": "/data/archive", "manifest_sha256": "a" * 64}
        with patch.object(require_archive, "dashboard", return_value=(200, jobs)), \
                patch.object(require_archive, "read_file", return_value=json.dumps(receipt)):
            self.assertTrue(require_archive.check_archives(since)["ok"])
        receipt["final"] = False
        with patch.object(require_archive, "dashboard", return_value=(200, jobs)), \
                patch.object(require_archive, "read_file", return_value=json.dumps(receipt)):
            self.assertFalse(require_archive.check_archives(since)["ok"])

    def test_gate_is_before_both_destructive_paths(self):
        import yaml
        root = SCRIPTS.parent / "workflows"
        for workflow, gate, action in (("main", "require_archives_before_wipe", "wipe"),
                                       ("run-test", "require_archives_before_seed", "submit_seed")):
            names = [step["name"] for step in yaml.safe_load((root / f"{workflow}.yaml").read_text())["steps"]]
            self.assertLess(names.index(gate), names.index(action))


if __name__ == "__main__":
    unittest.main()
