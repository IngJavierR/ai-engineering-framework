"""Ensure neutral backend instruction scopes do not imply Java."""

import fnmatch
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def applies(pattern: str, path: str) -> bool:
    return any(fnmatch.fnmatch(path, item.strip()) for item in pattern.split(","))


class InstructionScopeTest(unittest.TestCase):
    def scope(self, name: str) -> str:
        return (ROOT / ".github/instructions" / name).read_text(encoding="utf-8").split('applyTo: "', 1)[1].split('"', 1)[0]

    def test_java_rules_do_not_apply_to_python_paths(self):
        scope = self.scope("java.instructions.md")
        self.assertFalse(applies(scope, "app/api/main.py"))
        self.assertFalse(applies(scope, "app/db/session.py"))

    def test_neutral_rules_apply_to_python_contract_and_changelog(self):
        self.assertTrue(applies(self.scope("openapi-ddd.instructions.md"), "openapi/openapi.yaml"))
        self.assertTrue(applies(self.scope("liquibase.instructions.md"), "db/changelog/db.changelog-master.xml"))
