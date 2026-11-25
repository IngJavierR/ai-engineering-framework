"""Locks created before a capability gained artifacts must remain upgradable."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LOCK_NAME = ".ai-framework.lock.json"


class InventoryEvolutionTest(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.source = self.root / "framework"
        self.target = self.root / "consumer"
        subprocess.run(["git", "clone", "-q", str(ROOT), str(self.source)], check=True)
        subprocess.run(["git", "init", "-q", str(self.target)], check=True)

    def tearDown(self):
        self.temporary_directory.cleanup()

    def git(self, *args):
        subprocess.run(
            ["git", "-C", str(self.source),
             "-c", "user.email=test@example.com", "-c", "user.name=test", *args],
            check=True, capture_output=True,
        )

    def run_installer(self, *args):
        return subprocess.run(
            [sys.executable, str(self.source / "tools/install.py"),
             "--target", str(self.target), *args],
            capture_output=True, text=True,
        )

    def test_additive_capability_change_upgrades_existing_lock(self):
        first = self.run_installer("--profile", "python-fastapi")
        self.assertEqual(0, first.returncode, first.stderr)

        added = ".github/skills/fastapi-development/references/extra-guidance.md"
        (self.source / added).write_text("# Extra guidance\n", encoding="utf-8")
        config = self.source / "framework.yaml"
        anchor = '".github/skills/fastapi-development/references/ddd-layout.md"'
        content = config.read_text(encoding="utf-8")
        self.assertEqual(1, content.count(anchor))
        config.write_text(
            content.replace(anchor, anchor + ",\n            \"" + added + "\""),
            encoding="utf-8",
        )
        self.git("add", "-A")
        self.git("commit", "-q", "-m", "inventory: add fastapi reference")

        blocked = self.run_installer("--profile", "python-fastapi")
        self.assertNotEqual(0, blocked.returncode)
        self.assertIn("use --upgrade", blocked.stderr)

        upgraded = self.run_installer("--profile", "python-fastapi", "--upgrade")
        self.assertEqual(0, upgraded.returncode, upgraded.stderr)
        lock = json.loads((self.target / LOCK_NAME).read_text(encoding="utf-8"))
        self.assertIn(added, lock["files"])
        self.assertTrue((self.target / added).is_file())


if __name__ == "__main__":
    unittest.main()
