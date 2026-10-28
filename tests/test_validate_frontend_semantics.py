"""Tests for semantic validation of M2 frontend input contracts."""

import hashlib
import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SEMANTIC_PATH = REPOSITORY_ROOT / "tools" / "validate_frontend_semantics.py"
EXAMPLES = REPOSITORY_ROOT / "docs" / "m2" / "examples" / "customer-profile"
SPEC = importlib.util.spec_from_file_location("frontend_semantics", SEMANTIC_PATH)
semantics = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = semantics
assert SPEC.loader is not None
SPEC.loader.exec_module(semantics)


class FrontendSemanticsTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.package = self.root / "package"
        shutil.copytree(EXAMPLES, self.package)
        self.manifest = self.package / "angular.input.yaml"

    def tearDown(self):
        self.temporary_directory.cleanup()

    def document(self):
        return yaml.safe_load(self.manifest.read_text(encoding="utf-8"))

    def save(self, document):
        self.manifest.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")

    def update_hashes(self, document):
        hashes = {
            name: "sha256:" + hashlib.sha256((self.package / name).read_bytes()).hexdigest()
            for name in ("specification.md", "mockup.html", "unit-tests.yaml")
        }
        document["functionalSpecification"]["sha256"] = hashes["specification.md"]
        document["mockups"][0]["sha256"] = hashes["mockup.html"]
        document["unitTests"]["sha256"] = hashes["unit-tests.yaml"]
        for item in document["files"]:
            item["sha256"] = hashes[item["path"]]

    def codes(self, workspace_root=None):
        return [
            item.code
            for item in semantics.validate_manifest(self.manifest, workspace_root)
        ]

    def test_t01_verifies_hashes_then_blocks_illustrative_template_without_mutating_inputs(self):
        before = {path: path.read_bytes() for path in self.package.iterdir() if path.is_file()}
        codes = self.codes(self.root)
        self.assertNotIn("SEM-HASH-001", codes)
        self.assertIn("SEM-AUTH-001", codes)
        self.assertIn("SEM-CONSUMER-002", codes)
        self.assertIn("SEM-TEMPLATE-001", codes)
        self.assertEqual(before, {path: path.read_bytes() for path in self.package.iterdir() if path.is_file()})

    def test_t02_detects_incorrect_hash_and_missing_file(self):
        document = self.document()
        document["functionalSpecification"]["sha256"] = "sha256:" + "0" * 64
        self.save(document)
        self.assertIn("SEM-HASH-001", self.codes())
        (self.package / "mockup.html").unlink()
        self.assertIn("SEM-FILE-001", self.codes())

    def test_t03_rejects_input_symlink(self):
        target = self.root / "outside.md"
        target.write_text("outside", encoding="utf-8")
        (self.package / "specification.md").unlink()
        (self.package / "specification.md").symlink_to(target)
        self.assertIn("SEM-PATH-002", self.codes())

    def test_t04_detects_duplicate_and_orphan_identifiers(self):
        document = self.document()
        duplicate = dict(document["requirements"]["confirmed"][0])
        duplicate["statement"] = "Duplicado deliberado con contenido distinto."
        document["requirements"]["confirmed"].append(duplicate)
        document["conceptualComponents"][0]["requirementIds"].append("REQ-MISSING-001-01")
        self.save(document)
        codes = self.codes()
        self.assertIn("SEM-ID-001", codes)
        self.assertIn("SEM-REF-001", codes)

    def test_t05_detects_feature_case_and_test_coverage_errors(self):
        unit_path = self.package / "unit-tests.yaml"
        unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
        unit["featureId"] = "FEAT-OTHER-001"
        unit["cases"] = unit["cases"][:1]
        unit_path.write_text(yaml.safe_dump(unit, sort_keys=False), encoding="utf-8")
        document = self.document()
        self.update_hashes(document)
        self.save(document)
        codes = self.codes()
        self.assertIn("SEM-FEATURE-001", codes)
        self.assertIn("SEM-CASE-001", codes)
        self.assertIn("SEM-TEST-001", codes)

    def test_t06_stops_on_structural_error_before_semantic_validation(self):
        document = self.document()
        del document["featureId"]
        self.save(document)
        codes = self.codes()
        self.assertEqual(["SEM-STRUCTURAL"], codes)

    def test_t07_rejects_declared_verified_authorization_without_external_verification(self):
        document = self.document()
        document["requirements"]["authorizedDecisions"][0]["authorizationEvidence"] = {
            "status": "verified",
            "type": "signed-commit",
            "reference": "example",
            "approvedCommit": "a" * 40,
        }
        self.save(document)
        self.assertIn("SEM-AUTH-001", self.codes())

    def test_t08_reports_unavailable_consumer_versions(self):
        codes = self.codes()
        self.assertIn("SEM-WORKSPACE-001", codes)

    def test_t09_rejects_consumer_symlink_and_workspace_escape(self):
        outside = self.root / "outside"
        outside.mkdir()
        link = self.package / "consumer-link"
        link.symlink_to(outside, target_is_directory=True)
        document = self.document()
        document["consumer"]["repositoryRoot"] = "consumer-link"
        self.save(document)
        self.assertIn("SEM-CONSUMER-001", self.codes(self.root))

        document["consumer"]["repositoryRoot"] = "../.."
        self.save(document)
        self.assertIn("SEM-CONSUMER-003", self.codes(self.package))

    def test_t10_rejects_intermediate_input_symlink(self):
        outside = self.root / "outside"
        outside.mkdir()
        (outside / "specification.md").write_text("outside", encoding="utf-8")
        link = self.package / "linked"
        link.symlink_to(outside, target_is_directory=True)
        document = self.document()
        document["functionalSpecification"]["path"] = "linked/specification.md"
        self.save(document)
        self.assertIn("SEM-PATH-002", self.codes())

    def test_t11_detects_cross_reference_and_inventory_errors(self):
        document = self.document()
        document["mockups"][0]["conceptualComponentIds"] = ["CMP-MISSING-001-01"]
        document["requirements"]["confirmed"][0]["sourceId"] = "SPEC-MISSING-001"
        document["files"] = document["files"][:1]
        self.save(document)
        codes = self.codes()
        self.assertIn("SEM-REF-003", codes)
        self.assertIn("SEM-REF-004", codes)
        self.assertIn("SEM-INVENTORY-003", codes)

    def test_t12_detects_target_decision_and_traceability_errors(self):
        unit_path = self.package / "unit-tests.yaml"
        unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
        unit["cases"][0]["target"]["conceptualUnitId"] = "CMP-MISSING-001-01"
        unit["cases"][1]["preconditions"][0]["decisionId"] = "DEC-MISSING-001-01"
        unit["cases"][1]["requirementIds"] = ["REQ-CUSTOMER-PROFILE-001-01"]
        unit_path.write_text(yaml.safe_dump(unit, sort_keys=False), encoding="utf-8")
        document = self.document()
        document["conceptualComponents"][1]["requirementIds"] = ["REQ-CUSTOMER-PROFILE-001-02"]
        self.update_hashes(document)
        self.save(document)
        codes = self.codes()
        self.assertIn("SEM-REF-003", codes)
        self.assertIn("SEM-REF-005", codes)
        self.assertIn("SEM-TRACE-001", codes)

    def test_t13_reports_invalid_consumer_metadata_and_versions(self):
        consumer = self.root / "consumer"
        consumer.mkdir()
        (consumer / "package.json").write_text("{}", encoding="utf-8")
        (consumer / "package-lock.json").write_text("{}", encoding="utf-8")
        document = self.document()
        document["consumer"]["repositoryRoot"] = "../consumer"
        document["consumer"]["verificationStatus"] = "verified"
        document["consumer"]["detection"]["declaredVersions"]["angularCore"] = "^20.0.0"
        document["consumer"]["detection"]["resolvedVersions"]["angularCore"] = "20.0.0"
        self.save(document)
        codes = self.codes(self.root)
        self.assertIn("SEM-VERSION-003", codes)
        self.assertIn("SEM-VERSION-005", codes)

    def test_t14_validates_npm_lockfile_and_detects_resolved_version_conflict(self):
        consumer = self.root / "consumer"
        consumer.mkdir()
        (consumer / "package.json").write_text('{"dependencies":{"@angular/core":"^20.0.0"}}', encoding="utf-8")
        (consumer / "package-lock.json").write_text('{"lockfileVersion":3,"packages":{"node_modules/@angular/core":{"version":"20.0.2"}}}', encoding="utf-8")
        document = self.document()
        document["consumer"]["repositoryRoot"] = "../consumer"
        document["consumer"]["verificationStatus"] = "verified"
        document["consumer"]["detection"]["declaredVersions"]["angularCore"] = "^20.0.0"
        document["consumer"]["detection"]["resolvedVersions"]["angularCore"] = "20.0.2"
        self.save(document)
        codes = self.codes(self.root)
        self.assertNotIn("SEM-VERSION-003", codes)
        self.assertNotIn("SEM-VERSION-004", codes)
        self.assertNotIn("SEM-VERSION-005", codes)
        self.assertNotIn("SEM-VERSION-006", codes)
        document["consumer"]["detection"]["resolvedVersions"]["angularCore"] = "20.0.1"
        self.save(document)
        self.assertIn("SEM-VERSION-006", self.codes(self.root))

    def test_t15_detects_conflicting_reference_inventory_and_traceability(self):
        document = self.document()
        document["unitTests"]["path"] = document["functionalSpecification"]["path"]
        document["unitTests"]["sha256"] = "sha256:" + "0" * 64
        self.save(document)
        self.assertIn("SEM-INVENTORY-001", self.codes())

        unit_path = self.package / "unit-tests.yaml"
        unit = yaml.safe_load(unit_path.read_text(encoding="utf-8"))
        unit["cases"][0]["componentIds"] = ["CMP-CUSTOMER-PROFILE-001-02"]
        unit["cases"][1]["requirementIds"] = ["REQ-CUSTOMER-PROFILE-001-01"]
        unit_path.write_text(yaml.safe_dump(unit, sort_keys=False), encoding="utf-8")
        document = self.document()
        document["unitTests"]["path"] = "unit-tests.yaml"
        self.update_hashes(document)
        self.save(document)
        codes = self.codes()
        self.assertIn("SEM-TRACE-002", codes)
        self.assertIn("SEM-TRACE-003", codes)

    def test_t16_reports_controlled_hash_read_error(self):
        original = Path.read_bytes
        specification = self.package / "specification.md"

        def fail_read_bytes(path):
            if path.name == specification.name:
                raise OSError("simulated read failure")
            return original(path)

        with mock.patch.object(Path, "read_bytes", fail_read_bytes):
            codes = self.codes()
        self.assertIn("SEM-FILE-004", codes)

    def test_t17_rejects_manifest_and_workspace_symlink_ancestors(self):
        linked_parent = self.root / "linked-parent"
        linked_parent.symlink_to(self.root, target_is_directory=True)
        linked_manifest = linked_parent / "package" / "angular.input.yaml"
        self.assertIn(
            "SEM-PATH-002",
            [item.code for item in semantics.validate_manifest(linked_manifest)],
        )

        workspace = self.root / "workspace"
        workspace.mkdir()
        linked_workspace_parent = self.root / "workspace-link"
        linked_workspace_parent.symlink_to(self.root, target_is_directory=True)
        linked_workspace = linked_workspace_parent / "workspace"
        self.assertIn("SEM-WORKSPACE-002", self.codes(linked_workspace))

    def test_t18_rejects_non_object_npm_metadata(self):
        consumer = self.root / "consumer"
        consumer.mkdir()
        document = self.document()
        document["consumer"]["repositoryRoot"] = "../consumer"
        document["consumer"]["verificationStatus"] = "verified"
        self.save(document)
        for label, package_contents, lock_contents in (
            ("dependencies-list", '{"dependencies":[]}', '{"lockfileVersion":3,"packages":{}}'),
            ("packages-list", '{"dependencies":{"@angular/core":"^20.0.0"}}', '{"lockfileVersion":3,"packages":[]}'),
            ("package-root-list", '[]', '{"lockfileVersion":3,"packages":{}}'),
            ("lock-root-list", '{"dependencies":{"@angular/core":"^20.0.0"}}', '[]'),
            ("package-root-null", 'null', '{"lockfileVersion":3,"packages":{}}'),
            ("lock-root-null", '{"dependencies":{"@angular/core":"^20.0.0"}}', 'null'),
        ):
            with self.subTest(label=label):
                (consumer / "package.json").write_text(package_contents, encoding="utf-8")
                (consumer / "package-lock.json").write_text(lock_contents, encoding="utf-8")
                codes = self.codes(self.root)
                if label in ("dependencies-list", "package-root-list", "package-root-null"):
                    self.assertIn("SEM-VERSION-002", codes)
                if label in ("packages-list", "lock-root-list", "lock-root-null"):
                    self.assertIn("SEM-VERSION-005", codes)

    def test_t19_reports_controlled_read_error(self):
        self.manifest.unlink()
        codes = self.codes()
        self.assertEqual(["SEM-STRUCTURAL"], codes)


if __name__ == "__main__":
    unittest.main()
