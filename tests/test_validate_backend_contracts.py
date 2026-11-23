"""Tests for backend contract-first validation."""

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools/validate_backend_contracts.py"
EXAMPLE = ROOT / "docs/backend/examples/customer-api"


class BackendContractValidatorTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for name in ("backend.input.yaml", "openapi.yaml", "test-cases.yaml"):
            (self.root / name).write_bytes((EXAMPLE / name).read_bytes())
        changelog = self.root / "backend/db/changelog"
        changelog.mkdir(parents=True)
        (changelog / "db.changelog-master.xml").write_bytes((EXAMPLE / "backend/db/changelog/db.changelog-master.xml").read_bytes())

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self):
        return yaml.safe_load((self.root / "backend.input.yaml").read_text())

    def write_manifest(self, document):
        (self.root / "backend.input.yaml").write_text(yaml.safe_dump(document, sort_keys=False))

    def run_validator(self, *extra):
        return subprocess.run([sys.executable, str(VALIDATOR), "--input", str(self.root / "backend.input.yaml"), *extra], text=True, capture_output=True)

    def test_valid_example(self):
        result = self.run_validator("--workspace-root", str(self.root))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("VALID", result.stdout)

    def test_missing_negative_case_is_invalid(self):
        cases = yaml.safe_load((self.root / "test-cases.yaml").read_text())
        cases["cases"] = [case for case in cases["cases"] if case["id"] != "TC-CUSTOMER-API-001-04"]
        (self.root / "test-cases.yaml").write_text(yaml.safe_dump(cases, sort_keys=False))
        manifest = self.manifest()
        manifest["testCases"]["sha256"] = "sha256:" + hashlib.sha256((self.root / "test-cases.yaml").read_bytes()).hexdigest()
        self.write_manifest(manifest)
        result = self.run_validator("--workspace-root", str(self.root))
        self.assertEqual(1, result.returncode)
        self.assertIn("BE-TEST-002", result.stderr)

    def test_non_liquibase_is_blocked(self):
        manifest = self.manifest()
        manifest["database"]["migrationTool"] = "alembic"
        self.write_manifest(manifest)
        result = self.run_validator("--workspace-root", str(self.root))
        self.assertEqual(2, result.returncode)
        self.assertIn("BE-DB-003", result.stderr)

    def test_consumer_root_is_default_and_workspace_root_is_explicit_override(self):
        consumer = self.root / "consumer"
        (consumer / "backend/db/changelog").mkdir(parents=True)
        (consumer / "backend/db/changelog/db.changelog-master.xml").write_bytes((EXAMPLE / "backend/db/changelog/db.changelog-master.xml").read_bytes())
        manifest = self.manifest()
        manifest["consumer"]["repositoryRoot"] = "consumer"
        self.write_manifest(manifest)
        (self.root / "backend/db/changelog/db.changelog-master.xml").unlink()
        self.assertEqual(0, self.run_validator().returncode)
        overridden = self.run_validator("--workspace-root", str(self.root))
        self.assertEqual(1, overridden.returncode)
        self.assertIn("BE-DB-001", overridden.stderr)

    def test_preflight_allows_absent_changelog_but_verify_requires_it(self):
        (self.root / "backend/db/changelog/db.changelog-master.xml").unlink()
        self.assertEqual(0, self.run_validator("--phase", "preflight").returncode)
        verified = self.run_validator("--phase", "verify")
        self.assertEqual(1, verified.returncode)
        self.assertIn("BE-DB-001", verified.stderr)
