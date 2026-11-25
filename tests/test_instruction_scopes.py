"""Ensure installable instructions stay stack-neutral; stack standards are skills."""

import fnmatch
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTRUCTIONS = ROOT / ".github/instructions"
SOURCE_LANGUAGE_GLOBS = ("*.java", "*.kt", "*.py", "*.cs", "*.ts", "*.js", "*.go")


def applies(pattern: str, path: str) -> bool:
    return any(fnmatch.fnmatch(path, item.strip()) for item in pattern.split(","))


class InstructionScopeTest(unittest.TestCase):
    def scope(self, name: str) -> str:
        return (INSTRUCTIONS / name).read_text(encoding="utf-8").split('applyTo: "', 1)[1].split('"', 1)[0]

    def test_no_language_specific_instruction_files(self):
        self.assertFalse((INSTRUCTIONS / "java.instructions.md").exists())
        names = {path.name for path in INSTRUCTIONS.glob("*.instructions.md")}
        self.assertEqual(
            {"global-governance.instructions.md", "openapi-ddd.instructions.md", "liquibase.instructions.md"},
            names,
        )

    def test_instruction_scopes_do_not_target_source_languages(self):
        for name in ("openapi-ddd.instructions.md", "liquibase.instructions.md"):
            with self.subTest(name=name):
                scope = self.scope(name)
                for pattern in (item.strip() for item in scope.split(",")):
                    self.assertFalse(pattern.endswith(SOURCE_LANGUAGE_GLOBS), pattern)
                for path in ("src/main/java/App.java", "app/api/main.py", "src/Api/Program.cs"):
                    self.assertFalse(applies(scope, path), path)

    def test_neutral_rules_apply_to_contract_and_changelog(self):
        self.assertTrue(applies(self.scope("openapi-ddd.instructions.md"), "openapi/openapi.yaml"))
        self.assertTrue(applies(self.scope("liquibase.instructions.md"), "db/changelog/db.changelog-master.xml"))


if __name__ == "__main__":
    unittest.main()
