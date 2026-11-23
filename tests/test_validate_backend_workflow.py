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
        self.write("backend/app/main.py", "value = 2\n")
        verified, _ = workflow.workflow.verify(self.package / "backend.input.yaml", self.consumer, self.root, receipt, anchor_path, self.evidence, workflow.verify_input, workflow.scope_guard)
        self.assertEqual("PASS", verified.status, verified.payload())

        self.write("frontend/app.js", "value = 2\n")
        blocked, _ = workflow.workflow.verify(self.package / "backend.input.yaml", self.consumer, self.root, receipt, anchor_path, self.evidence, workflow.verify_input, workflow.scope_guard)
        self.assertEqual("FAIL", blocked.status)


if __name__ == "__main__":
    unittest.main()
