"""Tests for structural validation of M2 frontend YAML contracts."""

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from jsonschema.exceptions import SchemaError

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPOSITORY_ROOT / "tools" / "validate_frontend_contracts.py"
EXAMPLE_DIRECTORY = (
    REPOSITORY_ROOT / "docs" / "m2" / "examples" / "customer-profile"
)
SPEC = importlib.util.spec_from_file_location(
    "frontend_contract_validator", VALIDATOR_PATH
)
validator = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = validator
SPEC.loader.exec_module(validator)


class FrontendContractValidatorTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temporary_root = Path(self.temporary_directory.name)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def example(self, name):
        return yaml.safe_load((EXAMPLE_DIRECTORY / name).read_text("utf-8"))

    def write_yaml(self, name, document):
        path = self.temporary_root / name
        path.write_text(
            yaml.safe_dump(document, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        return path

    def authorization_trust(self):
        return {
            "schemaVersion": "authorization-trust/v1",
            "repositoryRoot": "/workspace/angular-customer-profile-consumer",
            "authorizedSigners": [{
                "principal": "functional-owner@example.invalid",
                "publicKey": "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIFixtureKey",
                "featureIds": ["FEAT-CUSTOMER-PROFILE-001"],
                "decisionIds": ["DEC-CUSTOMER-PROFILE-001-01"],
                "requirementIds": ["REQ-CUSTOMER-PROFILE-001-02"],
            }],
            "revokedKeyFingerprints": ["SHA256:FixtureFingerprint"],
        }

    def run_cli(self, *arguments):
        return subprocess.run(
            [sys.executable, str(VALIDATOR_PATH), *map(str, arguments)],
            cwd=REPOSITORY_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_t01_validates_all_example_contracts_without_modifying_them(self):
        paths = [
            EXAMPLE_DIRECTORY / "angular.input.yaml",
            EXAMPLE_DIRECTORY / "react.input.yaml",
            EXAMPLE_DIRECTORY / "unit-tests.yaml",
            EXAMPLE_DIRECTORY / "angular.output.yaml",
            EXAMPLE_DIRECTORY / "react.output.yaml",
        ]
        before = {path: path.read_bytes() for path in paths}

        result = self.run_cli(
            "--input", paths[0],
            "--input", paths[1],
            "--unit-tests", paths[2],
            "--output", paths[3],
            "--output", paths[4],
        )

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, {path: path.read_bytes() for path in paths})
        self.assertEqual(5, result.stdout.count("VALID "))

    def test_t02_rejects_unknown_contract_version(self):
        document = self.example("angular.input.yaml")
        document["schemaVersion"] = "frontend-ui-input/v99"

        result = self.run_cli("--input", self.write_yaml("unknown.yaml", document))

        self.assertEqual(1, result.returncode)
        self.assertIn("CONTRACT-002", result.stderr)

    def test_t03_rejects_invalid_yaml(self):
        path = self.temporary_root / "invalid.yaml"
        path.write_text("schemaVersion: [unterminated\n", encoding="utf-8")

        result = self.run_cli("--input", path)

        self.assertEqual(1, result.returncode)
        self.assertIn("YAML-001", result.stderr)

    def test_t04_rejects_duplicate_yaml_keys(self):
        path = self.temporary_root / "duplicate.yaml"
        path.write_text(
            "schemaVersion: frontend-ui-input/v1\n"
            "schemaVersion: frontend-ui-input/v1\n",
            encoding="utf-8",
        )

        result = self.run_cli("--input", path)

        self.assertEqual(1, result.returncode)
        self.assertIn("YAML-002", result.stderr)
        self.assertIn("duplicate key", result.stderr)

    def test_t05_rejects_unhashable_yaml_mapping_key(self):
        path = self.temporary_root / "complex-key.yaml"
        path.write_text("? [complex, key]\n: value\n", encoding="utf-8")

        result = self.run_cli("--input", path)

        self.assertEqual(1, result.returncode)
        self.assertIn("YAML-004", result.stderr)
        self.assertNotIn("Traceback", result.stderr)

    def test_t06_reports_invalid_json_schema_as_controlled_error(self):
        document = self.example("angular.input.yaml")
        path = self.write_yaml("schema-error.yaml", document)

        with mock.patch.object(
            validator.Draft202012Validator,
            "check_schema",
            side_effect=SchemaError("invalid test schema"),
        ):
            errors = validator.validate_document(
                path, "frontend-ui-input/v1"
            )

        self.assertEqual(["SCHEMA-002"], [error.code for error in errors])

    def test_t07_rejects_missing_required_field(self):
        document = self.example("angular.input.yaml")
        del document["featureId"]

        result = self.run_cli("--input", self.write_yaml("missing.yaml", document))

        self.assertEqual(1, result.returncode)
        self.assertIn("SCHEMA-003", result.stderr)
        self.assertIn("featureId", result.stderr)

    def test_t08_rejects_invalid_identifier(self):
        document = self.example("unit-tests.yaml")
        document["cases"][0]["id"] = "invalid-id"

        result = self.run_cli(
            "--unit-tests", self.write_yaml("invalid-id.yaml", document)
        )

        self.assertEqual(1, result.returncode)
        self.assertIn("SCHEMA-003", result.stderr)
        self.assertIn("invalid-id", result.stderr)

    def test_t09_rejects_traversal_and_absolute_paths(self):
        for label, path_value in (
            ("traversal", "foo/../bar"),
            ("absolute", "/tmp/customer-profile.md"),
        ):
            with self.subTest(label=label):
                document = self.example("angular.input.yaml")
                document["functionalSpecification"]["path"] = path_value
                result = self.run_cli(
                    "--input", self.write_yaml(f"{label}.yaml", document)
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("SCHEMA-003", result.stderr)

    def test_t10_rejects_real_browser_or_external_http(self):
        for label, field in (
            ("browser", "realBrowserAllowed"),
            ("http", "externalHttpAllowed"),
        ):
            with self.subTest(label=label):
                document = self.example("unit-tests.yaml")
                document["cases"][0]["isolation"][field] = True
                result = self.run_cli(
                    "--unit-tests", self.write_yaml(f"{label}.yaml", document)
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("SCHEMA-003", result.stderr)

    def test_t11_accepts_manual_test_with_required_declarations(self):
        document = self.example("unit-tests.yaml")
        document["cases"][0]["async"] = {
            "isAsync": True,
            "mechanism": "callback",
            "timerControl": "manual",
            "completionCondition": "await controlled signal",
            "cleanup": "release callback",
            "manualJustification": "The project controls the callback.",
        }

        result = self.run_cli(
            "--unit-tests", self.write_yaml("manual-valid.yaml", document)
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_t12_accepts_pure_unit_test_without_dom_simulation(self):
        document = self.example("unit-tests.yaml")
        document["cases"][1]["isolation"]["domSimulationAllowed"] = False

        result = self.run_cli(
            "--unit-tests", self.write_yaml("pure-unit.yaml", document)
        )

        self.assertEqual(0, result.returncode, result.stderr)

    def test_t13_rejects_manual_test_without_required_declarations(self):
        for label, removed in (
            ("justification", "manualJustification"),
            ("completion", "completionCondition"),
        ):
            with self.subTest(label=label):
                document = self.example("unit-tests.yaml")
                async_config = {
                    "isAsync": True,
                    "mechanism": "callback",
                    "timerControl": "manual",
                    "completionCondition": "controlled callback completes",
                    "cleanup": "release callback",
                    "manualJustification": "The project controls the callback.",
                }
                del async_config[removed]
                document["cases"][0]["async"] = async_config
                result = self.run_cli(
                    "--unit-tests", self.write_yaml(f"manual-{label}.yaml", document)
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("SCHEMA-003", result.stderr)

    def test_t14_rejects_tested_output_without_execution_evidence(self):
        document = self.example("angular.output.yaml")
        document["validation"]["unitTests"].update(
            {
                "status": "TESTED",
                "runner": None,
                "command": None,
                "exitCode": None,
                "resultFiles": [],
            }
        )

        result = self.run_cli("--output", self.write_yaml("tested.yaml", document))

        self.assertEqual(1, result.returncode)
        self.assertIn("SCHEMA-003", result.stderr)

    def test_t15_rejects_scope_failure_without_blocked_workflow(self):
        document = self.example("angular.output.yaml")
        document["scopeValidation"]["result"] = "FAIL"
        document["workflowStatus"] = "READY_FOR_VALIDATION"

        result = self.run_cli("--output", self.write_yaml("scope-fail.yaml", document))

        self.assertEqual(1, result.returncode)
        self.assertIn("SCHEMA-003", result.stderr)

    def test_t16_reports_read_errors_and_requires_an_argument(self):
        missing = self.run_cli("--input", self.temporary_root / "missing.yaml")
        no_arguments = self.run_cli()

        self.assertEqual(1, missing.returncode)
        self.assertIn("READ-001", missing.stderr)
        self.assertEqual(2, no_arguments.returncode)
        self.assertIn("CLI-001", no_arguments.stderr)

    def test_t17_accepts_valid_authorization_trust_policy(self):
        for label, repository_root in (
            ("workspace", "/workspace/angular-customer-profile-consumer"),
            ("users", "/Users/example/labs/angular-customer-profile-consumer"),
        ):
            with self.subTest(label=label):
                document = self.authorization_trust()
                document["repositoryRoot"] = repository_root
                result = self.run_cli(
                    "--authorization-trust",
                    self.write_yaml(f"authorization-trust-{label}.yaml", document),
                )

                self.assertEqual(0, result.returncode, result.stderr)
                self.assertIn("VALID", result.stdout)

    def test_t18_rejects_invalid_authorization_trust_policy_fields(self):
        cases = {
            "missing": lambda document: document.pop("repositoryRoot"),
            "extra": lambda document: document.update({"approvedBy": "name"}),
            "empty-signers": lambda document: document.update({"authorizedSigners": []}),
            "invalid-feature": lambda document: document["authorizedSigners"][0].update({"featureIds": ["*"]}),
            "invalid-decision": lambda document: document["authorizedSigners"][0].update({"decisionIds": ["DEC-*"]}),
            "invalid-requirement": lambda document: document["authorizedSigners"][0].update({"requirementIds": ["REQ-*"]}),
            "wildcard-root": lambda document: document.update({"repositoryRoot": "/workspace/*"}),
            "relative-root": lambda document: document.update({"repositoryRoot": "workspace/consumer"}),
            "current-directory-root": lambda document: document.update({"repositoryRoot": "/workspace/./consumer"}),
            "parent-directory-root": lambda document: document.update({"repositoryRoot": "/workspace/consumer/../other"}),
            "duplicate-separator-root": lambda document: document.update({"repositoryRoot": "/workspace//consumer"}),
            "private-key": lambda document: document["authorizedSigners"][0].update({"publicKey": "-----BEGIN OPENSSH PRIVATE KEY-----"}),
            "invalid-version": lambda document: document.update({"schemaVersion": "authorization-trust/v2"}),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                document = self.authorization_trust()
                mutate(document)
                result = self.run_cli(
                    "--authorization-trust",
                    self.write_yaml(f"trust-{label}.yaml", document),
                )
                self.assertEqual(1, result.returncode)
                expected_code = (
                    "CONTRACT-002" if label == "invalid-version" else "SCHEMA-003"
                )
                self.assertIn(expected_code, result.stderr)

    def test_t19_rejects_invalid_authorization_trust_principals(self):
        cases = {
            "empty": "",
            "whitespace": " \t ",
            "line-feed": "principal\nother",
            "carriage-return": "principal\rother",
            "control": "principal\x01other",
            "wildcard": "principal-*",
        }
        for label, principal in cases.items():
            with self.subTest(label=label):
                document = self.authorization_trust()
                document["authorizedSigners"][0]["principal"] = principal
                result = self.run_cli(
                    "--authorization-trust",
                    self.write_yaml(f"trust-principal-{label}.yaml", document),
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("SCHEMA-003", result.stderr)

    def test_t20_rejects_duplicate_authorization_trust_values(self):
        cases = {
            "feature": lambda document: document["authorizedSigners"][0].update({"featureIds": ["FEAT-CUSTOMER-PROFILE-001", "FEAT-CUSTOMER-PROFILE-001"]}),
            "decision": lambda document: document["authorizedSigners"][0].update({"decisionIds": ["DEC-CUSTOMER-PROFILE-001-01", "DEC-CUSTOMER-PROFILE-001-01"]}),
            "requirement": lambda document: document["authorizedSigners"][0].update({"requirementIds": ["REQ-CUSTOMER-PROFILE-001-02", "REQ-CUSTOMER-PROFILE-001-02"]}),
            "fingerprint": lambda document: document.update({"revokedKeyFingerprints": ["SHA256:FixtureFingerprint", "SHA256:FixtureFingerprint"]}),
            "principal": lambda document: document.update({"authorizedSigners": document["authorizedSigners"] * 2}),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                document = self.authorization_trust()
                mutate(document)
                result = self.run_cli(
                    "--authorization-trust",
                    self.write_yaml(f"trust-duplicate-{label}.yaml", document),
                )
                self.assertEqual(1, result.returncode)
                self.assertIn("SCHEMA-003", result.stderr)


if __name__ == "__main__":
    unittest.main()
