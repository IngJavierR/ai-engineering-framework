"""Regression test for non-JVM PostgreSQL Liquibase guidance."""

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REFERENCE = ROOT / ".github/skills/liquibase-versioning/references/xml-conventions.md"


class LiquibasePostgresqlReferenceTest(unittest.TestCase):
    def test_documents_docker_lpm_for_liquibase_five(self):
        content = REFERENCE.read_text(encoding="utf-8")
        self.assertIn("Liquibase 5.x", content)
        self.assertIn("liquibase/liquibase:5.0", content)
        self.assertIn("lpm add postgresql", content)


if __name__ == "__main__":
    unittest.main()
