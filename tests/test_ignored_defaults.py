"""Tests for C1 (git ls-files), C2 (.env patterns), C3 (java stack detection)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import ignored_defaults as ig  # noqa: E402


def _git_init(path: Path) -> None:
    for cmd in (
        ["git", "-C", str(path), "init", "-q"],
        ["git", "-C", str(path), "config", "user.email", "t@t.invalid"],
        ["git", "-C", str(path), "config", "user.name", "T"],
    ):
        subprocess.run(cmd, check=True, capture_output=True)


def _commit(path: Path, *files: str) -> None:
    subprocess.run(["git", "-C", str(path), "add", *files], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(path), "commit", "-qm", "c"], check=True, capture_output=True)


class TestC1GitLsFiles(unittest.TestCase):
    def test_defaults_kept_when_only_on_disk(self):
        """C1: disk-only files (.venv, node_modules, egg-info) must NOT discard defaults."""
        with tempfile.TemporaryDirectory() as d:
            consumer = Path(d) / "consumer"
            consumer.mkdir()
            _git_init(consumer)
            (consumer / ".gitignore").write_text(".venv/\nnode_modules/\n*.egg-info/\n")
            _commit(consumer, ".gitignore")
            # Create disk-only ignored files (not versionados)
            (consumer / "frontend/node_modules/a").mkdir(parents=True)
            (consumer / "frontend/node_modules/a/b.js").write_text("x")
            (consumer / "backend/.venv/bin").mkdir(parents=True)
            (consumer / "backend/.venv/bin/python").write_text("x")
            (consumer / "backend/x.egg-info").mkdir()
            (consumer / "backend/x.egg-info/PKG-INFO").write_text("x")
            (consumer / "frontend/package.json").write_text("{}")
            (consumer / "backend/pyproject.toml").write_text("[project]")
            _commit(consumer, "frontend/package.json", "backend/pyproject.toml")
            accepted, skipped = ig.safe_patterns_for(consumer, set())
            self.assertEqual([], skipped, f"Unexpected skipped: {skipped}")
            self.assertIn("**/node_modules/**", accepted)
            self.assertIn("**/.venv/**", accepted)
            self.assertIn("**/*.egg-info/**", accepted)

    def test_default_omitted_only_when_tracked(self):
        """C1: a pattern is omitted only when it matches a versioned file, naming that file."""
        with tempfile.TemporaryDirectory() as d:
            consumer = Path(d) / "consumer"
            consumer.mkdir()
            _git_init(consumer)
            # Add package.json to trigger node stack (which includes **/dist/**)
            (consumer / "package.json").write_text("{}")
            (consumer / "dist").mkdir()
            (consumer / "dist/app.js").write_text("x")
            _commit(consumer, "package.json", "dist/app.js")
            accepted, skipped = ig.safe_patterns_for(consumer, set())
            self.assertTrue(any("**/dist/**" in s for s in skipped), f"dist pattern not skipped: {skipped}")
            skipped_str = " ".join(skipped)
            self.assertIn("dist/app.js", skipped_str)
            self.assertNotIn("**/dist/**", accepted)

    @pytest.mark.slow
    def test_scaffold_fast_with_large_node_modules(self):
        """C1: safe_patterns_for must complete < 3s even with 50k disk-only files."""
        with tempfile.TemporaryDirectory() as d:
            consumer = Path(d) / "consumer"
            consumer.mkdir()
            _git_init(consumer)
            (consumer / ".gitignore").write_text("node_modules/\n")
            (consumer / "package.json").write_text("{}")
            _commit(consumer, ".gitignore", "package.json")
            nm = consumer / "frontend/node_modules"
            nm.mkdir(parents=True)
            for i in range(50_000):
                (nm / f"{i}.js").write_text(f"{i}")
            start = time.monotonic()
            accepted, _ = ig.safe_patterns_for(consumer, set())
            elapsed = time.monotonic() - start
            self.assertIn("**/node_modules/**", accepted)
            self.assertLess(elapsed, 3.0, f"safe_patterns_for took {elapsed:.1f}s (limit 3s)")


class TestC2DotEnvPatterns(unittest.TestCase):
    def test_universal_patterns_always_present(self):
        """C2: .env and .env.local patterns appear regardless of stack."""
        with tempfile.TemporaryDirectory() as d:
            consumer = Path(d) / "consumer"
            consumer.mkdir()
            _git_init(consumer)
            (consumer / ".gitignore").write_text(".env\n")
            _commit(consumer, ".gitignore")
            patterns = ig.patterns_for(consumer, set())
            self.assertIn("**/.env", patterns)
            self.assertIn("**/.env.local", patterns)

    def test_env_example_not_in_defaults(self):
        """C2: .env.example, .env.sample and .env.template must not match .env patterns."""
        with tempfile.TemporaryDirectory() as d:
            consumer = Path(d) / "consumer"
            consumer.mkdir()
            _git_init(consumer)
            for name in (".env.example", ".env.sample", ".env.template"):
                (consumer / name).write_text("x")
            _commit(consumer, ".env.example", ".env.sample", ".env.template")
            accepted, skipped = ig.safe_patterns_for(consumer, set())
            self.assertIn("**/.env", accepted, f"**/.env incorrectly skipped by {skipped}")
            self.assertIn("**/.env.local", accepted)


class TestC3JavaStackDetection(unittest.TestCase):
    def test_gatling_pom_does_not_enable_java(self):
        """C3: pom.xml under performance/gatling must not activate java stack."""
        with tempfile.TemporaryDirectory() as d:
            consumer = Path(d) / "consumer"
            consumer.mkdir()
            _git_init(consumer)
            (consumer / "performance/gatling").mkdir(parents=True)
            (consumer / "performance/gatling/pom.xml").write_text("<project/>")
            _commit(consumer, "performance/gatling/pom.xml")
            patterns = ig.patterns_for(consumer, set())
            self.assertIn("performance/gatling/target/**", patterns)
            self.assertNotIn("**/target/**", patterns)
            self.assertNotIn("**/build/**", patterns)

    def test_pom_outside_gatling_enables_java(self):
        """C3: pom.xml outside performance/gatling should activate java stack."""
        with tempfile.TemporaryDirectory() as d:
            consumer = Path(d) / "consumer"
            consumer.mkdir()
            _git_init(consumer)
            (consumer / "pom.xml").write_text("<project/>")
            _commit(consumer, "pom.xml")
            patterns = ig.patterns_for(consumer, set())
            self.assertIn("**/target/**", patterns)


if __name__ == "__main__":
    unittest.main()
