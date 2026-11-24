"""Focused tests for M2 onboarding helpers and custody-anchor generation."""

import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANCHOR = ROOT / "tools" / "make_anchor.py"
SCAFFOLD = ROOT / "tools" / "new_feature.py"


class M2HelperTest(unittest.TestCase):
    def test_java_apply_globs_do_not_cover_python_paths(self):
        for file in (".github/instructions/openapi-ddd.instructions.md", ".github/instructions/liquibase.instructions.md"):
            header = (ROOT / file).read_text(encoding="utf-8").split("---", 2)[1]
            self.assertNotIn("**/api/**", header)
            self.assertNotIn("**/db/**", header)
            self.assertIn("**/*.java", header)

    def test_make_anchor_matches_receipt_and_rejects_receipt_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            consumer = root / "consumer"; consumer.mkdir()
            receipt = root / "evidence" / "receipt.json"; receipt.parent.mkdir()
            value = {
                "receiptVersion": "frontend-workflow-receipt/v1", "executionId": "00000000-0000-4000-8000-000000000001",
                "manifest": {"path": str(root / "input.yaml"), "sha256": "sha256:" + "a" * 64},
                "inputs": {"specification.md": "sha256:" + "b" * 64},
                "consumer": {"id": "consumer", "root": str(consumer), "stack": "angular"},
                "baseCommit": "c" * 40,
                "snapshot": {"path": str(root / "evidence" / "snapshot.json"), "sha256": "sha256:" + "d" * 64},
            }
            receipt.write_text(json.dumps(value), encoding="utf-8")
            output = root / "custody" / "anchor.json"
            result = subprocess.run(["python3", str(ANCHOR), "--receipt", str(receipt), "--output", str(output)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            anchor = json.loads(output.read_text())
            self.assertEqual("sha256:" + hashlib.sha256(receipt.read_bytes()).hexdigest(), anchor["receiptSha256"])
            blocked = subprocess.run(["python3", str(ANCHOR), "--receipt", str(receipt), "--output", str(receipt.parent / "bad.json")], capture_output=True, text=True)
            self.assertNotEqual(0, blocked.returncode)

    def test_new_feature_creates_illustrative_structural_templates(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); consumer = root / "consumer"; consumer.mkdir(); subprocess.run(["git", "-C", str(consumer), "init", "-q"], check=True)
            output = root / "feature"
            result = subprocess.run(["python3", str(SCAFFOLD), "--feature-id", "FEAT-SAMPLE-001", "--stack", "angular", "--consumer", str(consumer), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = (output / "angular.input.yaml").read_text(encoding="utf-8")
            self.assertIn("illustrative-not-ready-for-execution", manifest)
            self.assertIn("FEAT-SAMPLE-001", manifest)

    def test_new_backend_feature_records_relative_consumer_without_mutating_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            consumer = root / "consumer"
            consumer.mkdir(); subprocess.run(["git", "-C", str(consumer), "init", "-q"], check=True)
            output = root / "feature"
            result = subprocess.run(["python3", str(SCAFFOLD), "--feature-id", "FEAT-SAMPLE-001", "--stack", "python-fastapi", "--consumer", str(consumer), "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = (output / "backend.input.yaml").read_text(encoding="utf-8")
            self.assertIn("repositoryRoot: ../consumer", manifest)
            self.assertFalse((consumer / "backend/db/changelog/db.changelog-master.xml").exists())
            self.assertIn("TC-SAMPLE-001-01", (output / "test-cases.yaml").read_text())

    def test_new_feature_reports_missing_consumer(self):
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(["python3", str(SCAFFOLD), "--feature-id", "FEAT-SAMPLE-001", "--stack", "angular", "--consumer", str(Path(directory) / "missing"), "--out", str(Path(directory) / "out")], capture_output=True, text=True)
            self.assertEqual(1, result.returncode)
            self.assertIn("NF-CONSUMER-001", result.stderr)

    def test_new_feature_prefixes_monorepo_frontend_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); consumer = root / "consumer"; consumer.mkdir()
            subprocess.run(["git", "-C", str(consumer), "init", "-q"], check=True)
            (consumer / "frontend").mkdir(); (consumer / "backend").mkdir()
            output = root / "feature"
            result = subprocess.run(["python3", str(SCAFFOLD), "--feature-id", "FEAT-SAMPLE-001", "--stack", "angular", "--consumer", str(consumer), "--frontend-root", "frontend", "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = (output / "angular.input.yaml").read_text()
            self.assertIn("manifestPath: frontend/package.json", manifest)
            self.assertIn("lockfilePath: frontend/package-lock.json", manifest)
            self.assertIn("path: frontend/src/app/features/customer-profile", manifest)
            self.assertIn("path: backend, kind: directory", manifest)

    def test_scaffolds_include_detected_monorepo_ignored_paths_and_contract_dir_removes_copies(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); consumer = root / "consumer"; consumer.mkdir()
            subprocess.run(["git", "-C", str(consumer), "init", "-q"], check=True)
            for relative in ("frontend/package.json", "backend/pyproject.toml", "performance/gatling/pom.xml"):
                path = consumer / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_text("{}")
            output = root / "backend-feature"
            result = subprocess.run(["python3", str(SCAFFOLD), "--feature-id", "FEAT-SAMPLE-001", "--stack", "python-fastapi", "--consumer", str(consumer), "--contract-dir", "backend/contract", "--out", str(output)], capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            manifest = (output / "backend.input.yaml").read_text()
            for pattern in ("**/node_modules/**", "**/.hypothesis/**", "**/target/**", "performance/gatling/target/**"):
                self.assertIn(pattern, manifest)
            self.assertFalse((output / "openapi.yaml").exists())
            self.assertTrue((consumer / "backend/contract/openapi.yaml").is_file())
