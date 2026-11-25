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

JAVA_SKILL = ".github/skills/java-spring-development/SKILL.md"
DDD_SKILL = ".github/skills/backend-ddd-architecture/SKILL.md"
BACKEND_PROFILES = frozenset({"java-spring", "python-fastapi", "backend"})


class ProfileTest(unittest.TestCase):
    def test_stack_profiles_share_governance_without_java_for_non_java(self):
        for profile in ("angular", "react", "python-fastapi", "backend"):
            resolved, _ = installer.resolve_capabilities(
                (profile,), base_capability=installer.UNIVERSAL_CAPABILITY
            )
            self.assertIn(installer.UNIVERSAL_CAPABILITY, resolved)
            self.assertNotIn(installer.BASE_CAPABILITY, resolved)

    def test_multistack_profiles_deduplicate_and_do_not_pull_java(self):
        resolved, files = installer.resolve_capabilities(
            ("angular", "python-fastapi"), base_capability=installer.UNIVERSAL_CAPABILITY
        )
        self.assertGreaterEqual(len(files), 15)
        self.assertNotIn(installer.BASE_CAPABILITY, resolved)
        self.assertEqual(1, resolved.count("security-validation"))

    def test_profile_and_capability_union_uses_universal_base(self):
        resolved, _ = installer.resolve_capabilities(
            ("angular", "fastapi-development"), base_capability=installer.UNIVERSAL_CAPABILITY
        )
        self.assertIn("fastapi-development", resolved)
        self.assertNotIn(installer.BASE_CAPABILITY, resolved)

    def test_profile_installations_are_idempotent_and_isolated(self):
        fixture_root = ROOT / ".bootstrap-test-tmp"
        fixture_root.mkdir(exist_ok=True)
        for profile in ("java-spring", "angular", "react", "python-fastapi", "backend"):
            with tempfile.TemporaryDirectory(dir=fixture_root) as directory:
                target = Path(directory) / "consumer"
                target.mkdir()
                subprocess.run(["git", "init", "-q", str(target)], check=True)
                installer.install(target, profile=profile)
                installer.install(target, profile=profile)
                lock = json.loads((target / installer.LOCK_NAME).read_text())
                self.assertEqual(lock["capabilities"][0], installer.UNIVERSAL_CAPABILITY)
                has_java = (target / JAVA_SKILL).exists()
                self.assertEqual(has_java, profile == "java-spring")
                has_ddd = (target / DDD_SKILL).exists()
                self.assertEqual(has_ddd, profile in BACKEND_PROFILES)
                self.assertFalse((target / ".github/instructions/java.instructions.md").exists())

    def test_backend_profiles_install_contract_first_capabilities_without_java(self):
        for profile in ("python-fastapi", "backend"):
            resolved, files = installer.resolve_capabilities(
                (profile,), base_capability=installer.UNIVERSAL_CAPABILITY
            )
            self.assertTrue({"api-contract-first", "liquibase-versioning", "gatling-performance", "security-validation"}.issubset(resolved))
            self.assertIn("backend-ddd-architecture", resolved)
            self.assertIn(DDD_SKILL, files)
            self.assertNotIn(JAVA_SKILL, files)
            self.assertNotIn(".github/skills/java-spring-development/references/ddd-layout.md", files)

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
            self.assertFalse((target / JAVA_SKILL).exists())

    def test_every_backend_profile_resolves_ddd_and_its_stack_layout(self):
        layouts = {
            "java-spring": ".github/skills/java-spring-development/references/ddd-layout.md",
            "python-fastapi": ".github/skills/fastapi-development/references/ddd-layout.md",
        }
        for profile in sorted(BACKEND_PROFILES):
            with self.subTest(profile=profile):
                resolved, files = installer.resolve_capabilities(
                    (profile,), base_capability=installer.UNIVERSAL_CAPABILITY
                )
                self.assertIn("backend-ddd-architecture", resolved)
                self.assertIn(DDD_SKILL, files)
                if profile in layouts:
                    self.assertIn(layouts[profile], files)
        for profile in ("angular", "react"):
            with self.subTest(profile=profile):
                resolved, _ = installer.resolve_capabilities(
                    (profile,), base_capability=installer.UNIVERSAL_CAPABILITY
                )
                self.assertNotIn("backend-ddd-architecture", resolved)

    def _run(self, target, *arguments):
        return subprocess.run([
            "python3", str(ROOT / "tools" / "install.py"), "--target", str(target), *arguments
        ], cwd=ROOT, capture_output=True, text=True)
