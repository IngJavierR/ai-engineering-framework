"""Regression tests: RC4 receipts/manifests still validate; java-spring list unchanged."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/rc4"
BASELINE = ROOT / "tests/fixtures/v0.8.0"
VALIDATOR = ROOT / "tools/validate_backend_contracts.py"
EXAMPLE = ROOT / "docs/backend/examples/customer-api"


class RegressionRc4Test(unittest.TestCase):
    def test_rc4_receipts_still_validate_without_traceback(self):
        """RC4 receipts that have ignoredWorkPaths must load, not traceback."""
        receipt_path = FIXTURES / "receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        sys.path.insert(0, str(ROOT / "tools"))
        import validate_frontend_workflow as wf  # noqa: E402
        value, error = wf.load_json(receipt_path)
        self.assertIsNone(error, f"RC4 receipt load error: {error}")
        self.assertIsNotNone(value)
        result = wf.validate_receipt(value)
        self.assertIsNone(result, f"RC4 receipt validation error: {result}")

    def test_java_spring_install_list_unchanged(self):
        """java-spring profile must install the 0.8.0 baseline file list.

        The RC4 baseline (tests/fixtures/rc4) is kept for history; 0.8.0
        replaced java.instructions.md and ddd-structure.md with the
        java-spring-development and backend-ddd-architecture skills.
        """
        expected = sorted((BASELINE / "install-java-spring-files.txt").read_text(encoding="utf-8").splitlines())
        sys.path.insert(0, str(ROOT / "tools"))
        import install as i  # noqa: E402
        _, files = i.resolve_capabilities(["java-spring"], base_capability=i.UNIVERSAL_CAPABILITY)
        self.assertEqual(expected, sorted(files), "java-spring file list changed from the 0.8.0 baseline")

    def test_examples_validate(self):
        """Backend and M2 examples must pass preflight validation."""
        import tempfile, hashlib, yaml  # noqa: E402
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ("backend.input.yaml", "openapi.yaml", "test-cases.yaml"):
                (root / name).write_bytes((EXAMPLE / name).read_bytes())
            # update hashes
            doc = yaml.safe_load((root / "backend.input.yaml").read_text())
            for key in ("openapi", "testCases"):
                path = root / doc[key]["path"]
                doc[key]["sha256"] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            (root / "backend.input.yaml").write_text(yaml.safe_dump(doc, sort_keys=False))
            result = subprocess.run(
                [sys.executable, str(VALIDATOR), "--input", str(root / "backend.input.yaml"),
                 "--workspace-root", str(root), "--phase", "preflight"],
                capture_output=True, text=True,
            )
            self.assertEqual(0, result.returncode, f"Example failed: {result.stderr}")


if __name__ == "__main__":
    unittest.main()
