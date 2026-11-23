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
        document = self.manifest()
        for key in ("openapi", "testCases"):
            path = self.root / document[key]["path"]
            document[key]["sha256"] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        self.write_manifest(document)

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self):
        return yaml.safe_load((self.root / "backend.input.yaml").read_text())

    def write_manifest(self, document):
        (self.root / "backend.input.yaml").write_text(yaml.safe_dump(document, sort_keys=False))

    def run_validator(self, *extra):
        return subprocess.run([sys.executable, str(VALIDATOR), "--input", str(self.root / "backend.input.yaml"), *extra], text=True, capture_output=True)

    def test_valid_example(self):
        result = self.run_validator("--workspace-root", str(self.root), "--phase", "preflight")
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
        result = self.run_validator("--workspace-root", str(self.root), "--phase", "preflight")
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
        self.assertEqual(0, self.run_validator("--phase", "preflight").returncode)
        overridden = self.run_validator("--workspace-root", str(self.root))
        self.assertEqual(1, overridden.returncode)
        self.assertIn("BE-DB-001", overridden.stderr)

    def test_preflight_allows_absent_changelog_but_verify_requires_it(self):
        (self.root / "backend/db/changelog/db.changelog-master.xml").unlink()
        self.assertEqual(0, self.run_validator("--phase", "preflight").returncode)
        verified = self.run_validator("--phase", "verify")
        self.assertEqual(1, verified.returncode)
        self.assertIn("BE-DB-001", verified.stderr)

    def test_negative_case_requires_4xx_status(self):
        cases = yaml.safe_load((self.root / "test-cases.yaml").read_text())
        cases["cases"][1]["expected"]["status"] = 200
        cases["cases"][1]["expected"]["responseSchema"] = "#/components/schemas/Customer"
        path = self.root / "test-cases.yaml"; path.write_text(yaml.safe_dump(cases, sort_keys=False))
        document = self.manifest(); document["testCases"]["sha256"] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest(); self.write_manifest(document)
        self.assertIn("BE-TEST-006", self.run_validator("--phase", "preflight").stderr)

    def test_gatling_sources_report_fixed_host_but_not_pom_namespaces(self):
        gatling = self.root / "performance/gatling"; (gatling / "src/test/java").mkdir(parents=True)
        (gatling / "pom.xml").write_text('<project xmlns="http://maven.apache.org/POM/4.0.0"/>')
        source = gatling / "src/test/java/Simulation.java"
        source.write_text('String url = "https://example.com"; // getCustomer')
        result = self.run_validator("--workspace-root", str(self.root), "--phase", "preflight")
        self.assertIn("BE-PERF-002", result.stderr)
        self.assertIn("Simulation.java:1", result.stderr)
        source.write_text('String url = System.getenv("TARGET_BASE_URL"); // getCustomer')
        self.assertEqual(0, self.run_validator("--workspace-root", str(self.root), "--phase", "preflight").returncode)

    def test_verify_requires_changeset_and_simulation_references(self):
        result = self.run_validator("--workspace-root", str(self.root), "--phase", "verify")
        self.assertIn("BE-DB-005", result.stderr)
        self.assertIn("BE-PERF-003", result.stderr)
        changes = self.root / "backend/db/changelog/changes"; changes.mkdir()
        (changes / "001.xml").write_text('<databaseChangeLog><changeSet id="1" author="test"/></databaseChangeLog>')
        (self.root / "backend/db/changelog/db.changelog-master.xml").write_text('<databaseChangeLog><include file="changes/001.xml" relativeToChangelogFile="true"/></databaseChangeLog>')
        source = self.root / "performance/gatling/src/Simulation.scala"; source.parent.mkdir(parents=True); source.write_text('// getCustomer')
        self.assertEqual(0, self.run_validator("--workspace-root", str(self.root), "--phase", "verify").returncode)
