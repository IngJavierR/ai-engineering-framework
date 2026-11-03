"""Integration tests for the fail-closed M2 PREPARE/VERIFY workflow."""

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
TOOL = ROOT / "tools" / "validate_frontend_workflow.py"
EXAMPLES = ROOT / "docs" / "m2" / "examples" / "customer-profile"
SPEC = importlib.util.spec_from_file_location("frontend_workflow", TOOL)
workflow = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = workflow
assert SPEC.loader is not None
SPEC.loader.exec_module(workflow)


class FrontendWorkflowTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.package = self.root / "package"
        shutil.copytree(EXAMPLES, self.package)
        self.consumer = self.root / "consumer"
        self.consumer.mkdir()
        self.evidence = self.root / "evidence"
        self.custody = self.root / "custody"
        self.manifest = self.package / "angular.input.yaml"
        self.git("init")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        self.write_consumer("package.json", '{"dependencies":{"@angular/core":"^20.0.0"},"devDependencies":{"typescript":"^5.0.0"}}')
        self.write_consumer("package-lock.json", '{"lockfileVersion":3,"packages":{"node_modules/@angular/core":{"version":"20.0.2"}}}')
        self.write_consumer("src/app/features/customer-profile/original.ts", "export const x = 1;\n")
        self.write_consumer("src/app/core/auth.ts", "export const auth = 1;\n")
        self.git("add", ".")
        self.git("commit", "-m", "initial")
        self.ready_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.consumer), *args], check=True, capture_output=True, text=True)

    def write_consumer(self, relative, content):
        path = self.consumer / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def document(self):
        return yaml.safe_load(self.manifest.read_text(encoding="utf-8"))

    def save(self, document):
        self.manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    def refresh_hashes(self, document):
        hashes = {
            item: "sha256:" + hashlib.sha256((self.package / item).read_bytes()).hexdigest()
            for item in ("specification.md", "mockup.html", "unit-tests.yaml")
        }
        document["functionalSpecification"]["sha256"] = hashes["specification.md"]
        document["mockups"][0]["sha256"] = hashes["mockup.html"]
        document["unitTests"]["sha256"] = hashes["unit-tests.yaml"]
        for item in document["files"]:
            item["sha256"] = hashes[item["path"]]

    def ready_manifest(self):
        document = self.document()
        document["templateStatus"] = "ready-for-execution"
        document["consumer"]["repositoryRoot"] = "../consumer"
        document["consumer"]["verificationStatus"] = "verified"
        document["consumer"]["detection"]["declaredVersions"]["angularCore"] = "^20.0.0"
        document["consumer"]["detection"]["resolvedVersions"]["angularCore"] = "20.0.2"
        document["consumer"]["detection"]["declaredVersions"]["typescript"] = "^5.0.0"
        document["consumer"]["detection"]["resolvedVersions"]["typescript"] = "5.0.0"
        document["consumer"]["detection"]["detectionMethod"] = "package.json and package-lock.json inspected in temporary consumer"
        document["consumer"]["detection"]["reason"] = "Temporary consumer metadata is available for semantic verification."
        document["baseline"]["commit"] = self.git("rev-parse", "HEAD").stdout.strip()
        document["baseline"]["verificationStatus"] = "verified"
        document["requirements"]["ambiguities"] = []
        document["requirements"]["authorizedDecisions"] = []
        unit = yaml.safe_load((self.package / "unit-tests.yaml").read_text(encoding="utf-8"))
        for case in unit["cases"]:
            for precondition in case["preconditions"]:
                precondition.pop("decisionId", None)
        (self.package / "unit-tests.yaml").write_text(yaml.safe_dump(unit, sort_keys=False), encoding="utf-8")
        self.refresh_hashes(document)
        self.save(document)

    def prepare(self):
        return workflow.prepare(self.manifest, self.consumer, self.root, self.evidence)

    def anchor(self, receipt_path):
        self.assertIsNotNone(receipt_path, "PREPARE must PASS before creating an external anchor")
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        anchor = {
            "anchorVersion": workflow.ANCHOR_VERSION,
            "executionId": receipt["executionId"],
            "receiptSha256": workflow.digest(receipt_path),
            "manifestSha256": receipt["manifest"]["sha256"],
            "inputs": receipt["inputs"],
            "consumer": receipt["consumer"],
            "baseCommit": receipt["baseCommit"],
            "snapshotSha256": receipt["snapshot"]["sha256"],
        }
        path = self.custody / f"{receipt['executionId']}.anchor.json"
        workflow.atomic_json(path, anchor)
        return path

    def verify(self, receipt, anchor):
        return workflow.verify(self.manifest, self.consumer, self.root, receipt, anchor, self.evidence)[0]

    def test_t01_prepare_and_verify_valid_consumer_without_modifying_it(self):
        before = {path.relative_to(self.consumer): path.read_bytes() for path in self.consumer.rglob("*") if path.is_file() and ".git" not in path.parts}
        prepared, receipt = self.prepare()
        self.assertEqual("PASS", prepared.status, f"{prepared.code}: {prepared.message}; phases={prepared.phases}")
        self.assertIsNotNone(receipt, f"{prepared.code}: {prepared.message}; phases={prepared.phases}")
        self.assertEqual("BLOCKED", prepared.workflow_status)
        self.assertIsNotNone(receipt)
        self.assertNotEqual(self.consumer, receipt.parent)
        anchor = self.anchor(receipt)
        verified = self.verify(receipt, anchor)
        self.assertEqual("PASS", verified.status)
        self.assertEqual("NOT_RUN", verified.frontend_evidence)
        self.assertEqual("BLOCKED", verified.workflow_status)
        self.assertEqual(before, {path.relative_to(self.consumer): path.read_bytes() for path in self.consumer.rglob("*") if path.is_file() and ".git" not in path.parts})

    def test_t02_blocks_illustrative_and_structural_before_snapshot(self):
        document = self.document()
        document["templateStatus"] = "illustrative-not-ready-for-execution"
        self.save(document)
        result, receipt = self.prepare()
        self.assertEqual("WF-SEMANTIC-001", result.code)
        self.assertIsNone(receipt)
        self.assertFalse(self.evidence.exists())

        self.ready_manifest()
        document = self.document()
        del document["featureId"]
        self.save(document)
        result, receipt = self.prepare()
        self.assertEqual("WF-STRUCTURAL-001", result.code)
        self.assertIsNone(receipt)
        self.assertFalse(self.evidence.exists())

    def test_t03_blocks_semantic_error_before_snapshot(self):
        document = self.document()
        structural_errors = workflow.structural.validate_document(self.manifest, "frontend-ui-input/v1")
        self.assertEqual([], structural_errors, structural_errors)
        document["functionalSpecification"]["sha256"] = "sha256:" + "0" * 64
        self.save(document)
        structural_errors = workflow.structural.validate_document(self.manifest, "frontend-ui-input/v1")
        self.assertEqual([], structural_errors, structural_errors)
        result, receipt = self.prepare()
        self.assertEqual("WF-SEMANTIC-001", result.code)
        self.assertIsNone(receipt)
        self.assertFalse(self.evidence.exists())

    def test_t04_blocks_manifest_scope_and_protected_path_changes(self):
        prepared, receipt = self.prepare()
        self.assertEqual("PASS", prepared.status, f"{prepared.code}: {prepared.message}; phases={prepared.phases}")
        self.assertIsNotNone(receipt, f"{prepared.code}: {prepared.message}; phases={prepared.phases}")
        anchor = self.anchor(receipt)
        document = self.document()
        document["scope"]["allowedPaths"] = [{"path": "src/app", "kind": "directory"}]
        self.save(document)
        self.assertEqual("WF-IDENTITY-001", self.verify(receipt, anchor).code)

        self.ready_manifest()
        document = self.document()
        document["scope"]["protectedPaths"] = []
        self.save(document)
        self.assertEqual("WF-IDENTITY-001", self.verify(receipt, anchor).code)

    def test_t05_blocks_referenced_inputs_and_consumer_metadata_changes(self):
        for input_name in ("specification.md", "mockup.html", "unit-tests.yaml"):
            with self.subTest(input_name=input_name):
                _prepared, receipt = self.prepare()
                anchor = self.anchor(receipt)
                path = self.package / input_name
                original = path.read_bytes()
                path.write_bytes(original + b"\nchanged")
                self.assertEqual("WF-SEMANTIC-001", self.verify(receipt, anchor).code)
                path.write_bytes(original)

        _prepared, receipt = self.prepare()
        anchor = self.anchor(receipt)
        self.write_consumer("package-lock.json", '{"lockfileVersion":3,"packages":{"node_modules/@angular/core":{"version":"20.0.3"}}}')
        self.assertEqual("WF-SEMANTIC-001", self.verify(receipt, anchor).code)

    def test_t06_blocks_snapshot_receipt_and_anchor_tampering(self):
        _, receipt = self.prepare()
        anchor = self.anchor(receipt)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        Path(data["snapshot"]["path"]).write_text("{}", encoding="utf-8")
        self.assertEqual("WF-SNAPSHOT-002", self.verify(receipt, anchor).code)

        self.ready_manifest()
        _, receipt = self.prepare()
        anchor = self.anchor(receipt)
        receipt.write_text("{}", encoding="utf-8")
        self.assertEqual("WF-RECEIPT-003", self.verify(receipt, anchor).code)

        self.ready_manifest()
        _, receipt = self.prepare()
        anchor = self.anchor(receipt)
        data = json.loads(anchor.read_text(encoding="utf-8"))
        data["snapshotSha256"] = "sha256:" + "0" * 64
        workflow.atomic_json(anchor, data)
        self.assertEqual("WF-ANCHOR-003", self.verify(receipt, anchor).code)

    def test_t07_rejects_malformed_receipts_anchors_and_snapshot_paths(self):
        receipt_mutations = {
            "manifest-null": ("manifest", None, "WF-RECEIPT-003"),
            "snapshot-list": ("snapshot", [], "WF-RECEIPT-003"),
            "inputs-list": ("inputs", [], "WF-RECEIPT-003"),
            "execution-id": ("executionId", "invalid", "WF-RECEIPT-003"),
        }
        for label, (field, value, expected_code) in receipt_mutations.items():
            with self.subTest(label=label):
                _prepared, receipt = self.prepare()
                anchor = self.anchor(receipt)
                data = json.loads(receipt.read_text(encoding="utf-8"))
                data[field] = value
                workflow.atomic_json(receipt, data)
                self.assertEqual(expected_code, self.verify(receipt, anchor).code)

        _prepared, receipt = self.prepare()
        anchor = self.anchor(receipt)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["snapshot"]["path"] = None
        workflow.atomic_json(receipt, data)
        self.assertEqual("WF-RECEIPT-003", self.verify(receipt, anchor).code)

        _prepared, receipt = self.prepare()
        anchor = self.anchor(receipt)
        data = json.loads(anchor.read_text(encoding="utf-8"))
        data["consumer"] = None
        workflow.atomic_json(anchor, data)
        self.assertEqual("WF-ANCHOR-004", self.verify(receipt, anchor).code)

        _prepared, receipt = self.prepare()
        anchor = self.anchor(receipt)
        data = json.loads(anchor.read_text(encoding="utf-8"))
        data["receiptSha256"] = "sha256:not-a-digest"
        workflow.atomic_json(anchor, data)
        self.assertEqual("WF-ANCHOR-004", self.verify(receipt, anchor).code)

        _prepared, receipt = self.prepare()
        anchor = self.anchor(receipt)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["snapshot"]["path"] = str(self.evidence / "other-execution.snapshot.json")
        data["snapshot"]["sha256"] = "sha256:" + "0" * 64
        workflow.atomic_json(receipt, data)
        anchor_data = json.loads(anchor.read_text(encoding="utf-8"))
        anchor_data["receiptSha256"] = workflow.digest(receipt)
        anchor_data["snapshotSha256"] = data["snapshot"]["sha256"]
        workflow.atomic_json(anchor, anchor_data)
        self.assertEqual("WF-SNAPSHOT-003", self.verify(receipt, anchor).code)

        _prepared, receipt = self.prepare()
        anchor = self.anchor(receipt)
        data = json.loads(receipt.read_text(encoding="utf-8"))
        data["snapshot"]["path"] = str(self.custody / "outside.snapshot.json")
        data["snapshot"]["sha256"] = "sha256:" + "0" * 64
        workflow.atomic_json(receipt, data)
        anchor_data = json.loads(anchor.read_text(encoding="utf-8"))
        anchor_data["receiptSha256"] = workflow.digest(receipt)
        anchor_data["snapshotSha256"] = data["snapshot"]["sha256"]
        workflow.atomic_json(anchor, anchor_data)
        self.assertEqual("WF-SNAPSHOT-003", self.verify(receipt, anchor).code)

    def test_t08_blocks_missing_anchor_and_receipt_reuse_for_other_consumer(self):
        _, receipt = self.prepare()
        missing = self.custody / "missing.json"
        self.assertEqual("WF-ANCHOR-002", self.verify(receipt, missing).code)
        anchor = self.anchor(receipt)
        other = self.root / "other"
        other.mkdir()
        self.git("worktree", "add", "--detach", str(other), "HEAD")
        result, _ = workflow.verify(self.manifest, other, self.root, receipt, anchor, self.evidence)
        self.assertEqual("WF-CONSUMER-002", result.code)

    def test_t09_propagates_head_index_scope_fail_and_permitted_change(self):
        _, receipt = self.prepare()
        anchor = self.anchor(receipt)
        self.write_consumer("src/app/features/customer-profile/original.ts", "export const x = 2;\n")
        self.assertEqual("PASS", self.verify(receipt, anchor).status)

        self.write_consumer("src/app/features/customer-profile/original.ts", "export const x = 1;\n")
        self.ready_manifest()
        _, receipt = self.prepare()
        anchor = self.anchor(receipt)
        self.write_consumer("src/app/core/auth.ts", "export const auth = 2;\n")
        result = self.verify(receipt, anchor)
        self.assertEqual("FAIL", result.status)
        self.assertEqual("WF-VERIFY-FAIL", result.code)

        self.write_consumer("src/app/core/auth.ts", "export const auth = 1;\n")
        self.write_consumer("src/app/features/customer-profile/original.ts", "export const x = 3;\n")
        self.git("add", "src/app/features/customer-profile/original.ts")
        result = self.verify(receipt, anchor)
        self.assertEqual("BLOCKED", result.status)
        self.assertEqual("GIT-004", result.phases[-1].code)

    def test_t10_cli_reports_custody_limitations_and_never_validates_frontend(self):
        result = subprocess.run([
            sys.executable, str(TOOL), "prepare", "--manifest", str(self.manifest),
            "--consumer-repository", str(self.consumer), "--workspace-root", str(self.root),
            "--evidence-directory", str(self.evidence),
        ], capture_output=True, text=True, check=False)
        self.assertEqual(0, result.returncode, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual("PASS", payload["status"])
        self.assertEqual("BLOCKED", payload["workflowStatus"])
        self.assertEqual("NOT_RUN", payload["frontendEvidence"])
        limitations = " ".join(payload["limitations"])
        self.assertIn("reverted", limitations)
        self.assertIn("does not authenticate", limitations)
        self.assertIn("invoker is responsible", limitations)


if __name__ == "__main__":
    unittest.main()
