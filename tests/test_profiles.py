"""M5 profile composition and Java-artifact migration tests."""

import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("installer", ROOT / "tools" / "install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class ProfileTest(unittest.TestCase):
    def test_stack_profiles_share_governance_without_java_for_non_java(self):
        for profile in ("angular", "react", "python-fastapi"):
            resolved, _ = installer.resolve_capabilities(
                (profile,), base_capability=installer.UNIVERSAL_CAPABILITY
            )
            self.assertIn(installer.UNIVERSAL_CAPABILITY, resolved)
            self.assertNotIn(installer.BASE_CAPABILITY, resolved)

    def test_migration_requires_explicit_flag_and_removes_verified_java_files(self):
        fixture_root = ROOT / ".bootstrap-test-tmp"
        fixture_root.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=fixture_root) as directory:
            target = Path(directory) / "consumer"
            target.mkdir()
            subprocess.run(["git", "init", "-q", str(target)], check=True)
            installer.install(target, capabilities=("angular-ui-implementation",))
            blocked = self._run(target, "--profile", "angular", "--upgrade")
            self.assertNotEqual(blocked.returncode, 0)
            migrated = self._run(target, "--profile", "angular", "--upgrade", "--migrate-stack")
            self.assertEqual(migrated.returncode, 0, migrated.stderr)
            lock = json.loads((target / installer.LOCK_NAME).read_text())
            self.assertEqual(lock["capabilities"][0], installer.UNIVERSAL_CAPABILITY)
            self.assertFalse((target / ".github/instructions/java.instructions.md").exists())

    def _run(self, target, *arguments):
        return subprocess.run([
            "python3", str(ROOT / "tools" / "install.py"), "--target", str(target), *arguments
        ], cwd=ROOT, capture_output=True, text=True)
