"""Regression coverage for backend PREPARE/VERIFY scope enforcement."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/validate_backend_workflow.py"
SPEC = importlib.util.spec_from_file_location("backend_workflow", TOOL)
workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow
assert SPEC.loader is not None
SPEC.loader.exec_module(workflow)
EXAMPLE = ROOT / "docs/backend/examples/customer-api"


class BackendWorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.package = self.root / "package"
        shutil.copytree(EXAMPLE, self.package)
        self.consumer = self.root / "consumer"
        self.consumer.mkdir()
        self.evidence = self.root / "evidence"
        self.custody = self.root / "custody"
        self.git("init")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        self.write("backend/app/main.py", "value = 1\n")
        self.write("frontend/app.js", "value = 1\n")
        shutil.copytree(self.package / "backend/db", self.consumer / "backend/db")
        self.git("add", ".")
        self.git("commit", "-m", "initial")
        document = yaml.safe_load((self.package / "backend.input.yaml").read_text())
        document["consumer"]["repositoryRoot"] = "../consumer"
        document["consumer"]["baseline"]["commit"] = self.git("rev-parse", "HEAD").stdout.strip()
        for key in ("openapi", "testCases"):
            path = self.package / document[key]["path"]
            document[key]["sha256"] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        (self.package / "backend.input.yaml").write_text(yaml.safe_dump(document, sort_keys=False))

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.consumer), *args], check=True, capture_output=True, text=True)

    def write(self, relative, content):
        path = self.consumer / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)

    def test_prepare_and_verify_enforce_backend_scope(self):
        prepared, receipt = workflow.workflow.prepare(self.package / "backend.input.yaml", self.consumer, self.root, self.evidence, workflow.validate_input)
        self.assertEqual("PASS", prepared.status, prepared.payload())
        data = json.loads(receipt.read_text())
        anchor = {
            "anchorVersion": workflow.workflow.ANCHOR_VERSION, "executionId": data["executionId"],
            "receiptSha256": workflow.workflow.digest(receipt), "manifestSha256": data["manifest"]["sha256"],
            "inputs": data["inputs"], "consumer": data["consumer"], "baseCommit": data["baseCommit"],
            "snapshotSha256": data["snapshot"]["sha256"],
        }
        anchor_path = self.custody / "anchor.json"
        workflow.workflow.atomic_json(anchor_path, anchor)
        changes = self.consumer / "backend/db/changelog/changes"; changes.mkdir(parents=True)
        (changes / "001.xml").write_text('<databaseChangeLog><changeSet id="1" author="test"/></databaseChangeLog>')
        (self.consumer / "backend/db/changelog/db.changelog-master.xml").write_text('<databaseChangeLog><include file="changes/001.xml" relativeToChangelogFile="true"/></databaseChangeLog>')
        simulation = self.consumer / "performance/gatling/src/Simulation.scala"; simulation.parent.mkdir(parents=True); simulation.write_text("// getCustomer")
        self.write("backend/app/main.py", "value = 2\n")
        verified, _ = workflow.workflow.verify(self.package / "backend.input.yaml", self.consumer, self.root, receipt, anchor_path, self.evidence, workflow.verify_input, workflow.scope_guard)
        self.assertEqual("PASS", verified.status, verified.payload())

        self.write("frontend/app.js", "value = 2\n")
        blocked, _ = workflow.workflow.verify(self.package / "backend.input.yaml", self.consumer, self.root, receipt, anchor_path, self.evidence, workflow.verify_input, workflow.scope_guard)
        self.assertEqual("FAIL", blocked.status)

    def test_backend_verify_branch_change_reports_git003_before_content(self):
        """C4: branch change must surface GIT-003 before any content error (BE-DB-*, BE-PERF-*)."""
        self.git("switch", "-c", "feat/x")
        prepared, receipt = workflow.workflow.prepare(self.package / "backend.input.yaml", self.consumer, self.root, self.evidence, workflow.validate_input)
        self.assertEqual("PASS", prepared.status, prepared.payload())
        data = json.loads(receipt.read_text())
        anchor = {
            "anchorVersion": workflow.workflow.ANCHOR_VERSION, "executionId": data["executionId"],
            "receiptSha256": workflow.workflow.digest(receipt), "manifestSha256": data["manifest"]["sha256"],
            "inputs": data["inputs"], "consumer": data["consumer"], "baseCommit": data["baseCommit"],
            "snapshotSha256": data["snapshot"]["sha256"],
        }
        anchor_path = self.custody / "anchor.json"
        workflow.workflow.atomic_json(anchor_path, anchor)
        self.git("switch", "main")
        result, _ = workflow.workflow.verify(self.package / "backend.input.yaml", self.consumer, self.root, receipt, anchor_path, self.evidence, workflow.verify_input, workflow.scope_guard)
        self.assertEqual("BLOCKED", result.status)
        payload = result.payload()
        dump = json.dumps(payload)
        self.assertIn("GIT-003", dump, f"Expected GIT-003: {payload}")
        self.assertIn("feat/x", dump, f"Expected branch name feat/x: {payload}")
        self.assertIn("main", dump, f"Expected branch name main: {payload}")
        self.assertNotIn("BE-DB-", dump, f"Content errors must not appear before GIT-003: {payload}")

    def test_backend_workflow_output_has_no_frontend_vocabulary(self):
        """C5: PREPARE CLI output must not contain 'frontend' anywhere."""
        result = subprocess.run(
            [sys.executable, str(ROOT / "tools/validate_backend_workflow.py"), "prepare",
             "--manifest", str(self.package / "backend.input.yaml"),
             "--consumer-repository", str(self.consumer),
             "--workspace-root", str(self.root),
             "--evidence-directory", str(self.evidence)],
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertNotIn("frontend", json.dumps(payload).lower(),
                         f"Frontend vocabulary in CLI output: {result.stdout}")
        self.assertIn("backendEvidence", payload)


if __name__ == "__main__":
    unittest.main()
