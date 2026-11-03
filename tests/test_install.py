"""Tests for the framework installer using isolated Git repositories."""

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
INSTALLER_PATH = REPOSITORY_ROOT / "tools" / "install.py"
SPEC = importlib.util.spec_from_file_location(
    "framework_installer", INSTALLER_PATH
)
installer = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = installer
SPEC.loader.exec_module(installer)


class InstallerTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.temporary_root = Path(
            self.temporary_directory.name
        ).resolve(strict=True)
        self.target = self.temporary_root / "consumer"
        self.target.mkdir()
        self.run_git("init", self.target)
        self.source_manifest = installer.source_manifest()

    def tearDown(self):
        self.assertEqual(self.source_manifest, installer.source_manifest())
        self.temporary_directory.cleanup()

    def run_git(self, command, directory):
        subprocess.run(
            ["git", "-C", str(directory), command],
            check=True,
            capture_output=True,
            text=True,
        )

    def framework_git(self, *args):
        if args == ("status", "--porcelain"):
            return ""
        return installer.git_at(installer.ROOT, *args)

    def install(self, dry_run=False, upgrade=False, capabilities=()):
        original_historical_content = installer.historical_file_content
        current_commit = installer.git_at(installer.ROOT, "rev-parse", "HEAD")

        def historical_content(commit, relative):
            if commit == current_commit:
                return self.current_historical_content(commit, relative)
            return original_historical_content(commit, relative)

        with (
            mock.patch.object(installer, "git", self.framework_git),
            mock.patch.object(
                installer,
                "historical_file_content",
                side_effect=historical_content,
            ),
        ):
            installer.install(
                self.target,
                dry_run=dry_run,
                upgrade=upgrade,
                capabilities=capabilities,
            )

    def lock_path(self):
        return self.target / installer.LOCK_NAME

    def read_lock(self):
        return json.loads(self.lock_path().read_text(encoding="utf-8"))

    def write_lock(self, lock):
        self.lock_path().write_text(
            json.dumps(lock, indent=2) + "\n", encoding="utf-8"
        )

    def destination(self, relative):
        return self.target / relative

    def current_historical_content(self, commit, relative):
        self.assertEqual(
            installer.git_at(installer.ROOT, "rev-parse", "HEAD"), commit
        )
        if relative == "framework.yaml":
            return (installer.ROOT / relative).read_bytes()
        return installer.source_path(relative).read_bytes()

    def create_historical_installation(self):
        try:
            commit = installer.git_at(
                installer.ROOT, "rev-parse", "v0.3.0^{commit}"
            )
            files = installer.MANAGED_FILES
            manifest = {}
            for relative in files:
                content = subprocess.check_output(
                    [
                        "git", "-C", str(installer.ROOT), "show",
                        f"{commit}:{relative}",
                    ]
                )
                destination = self.destination(relative)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(content)
                manifest[relative] = hashlib.sha256(content).hexdigest()
        except subprocess.CalledProcessError as exc:
            self.fail("BLOCKED: v0.3.0 historical fixture is unavailable")
        self.write_lock(
            installer.build_lock(installer.HISTORICAL_VERSION, commit, manifest)
        )
        return manifest

    def create_legacy_installation(self):
        relative = installer.LEGACY_MANAGED_FILES[0]
        try:
            commit = installer.git_at(
                installer.ROOT, "rev-parse", "v0.2.0^{commit}"
            )
            content = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(installer.ROOT),
                    "show",
                    f"{commit}:{relative}",
                ]
            )
        except subprocess.CalledProcessError as exc:
            self.fail(
                "BLOCKED: v0.2.0 must resolve to a commit containing "
                f"{relative}; historical upgrade fixtures were not invented"
            )
        destination = self.destination(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(content)
        self.write_lock(
            installer.build_lock(
                installer.LEGACY_VERSION,
                commit,
                {relative: hashlib.sha256(content).hexdigest()},
            )
        )
        return relative, content

    def assert_no_managed_files(self):
        for relative in installer.MANAGED_FILES:
            self.assertFalse(
                os.path.lexists(self.destination(relative)), relative
            )

    def test_t01_clean_install_creates_manifest_and_real_hashes(self):
        self.install()

        lock = self.read_lock()
        self.assertEqual(installer.MANAGED_FILES, list(lock["files"]))
        self.assertEqual(installer.FRAMEWORK_NAME, lock["framework"])
        self.assertEqual(installer.FRAMEWORK_SOURCE, lock["source"])
        self.assertEqual(
            installer.git_at(installer.ROOT, "rev-parse", "HEAD"),
            lock["commit"],
        )
        for relative in installer.MANAGED_FILES:
            destination = self.destination(relative)
            source = installer.source_path(relative)
            self.assertEqual(source.read_bytes(), destination.read_bytes())
            self.assertEqual(installer.sha256(destination), lock["files"][relative])

    def test_t02_repeated_install_does_not_rewrite_files_or_lock(self):
        self.install()
        tracked_paths = [
            self.destination(relative) for relative in installer.MANAGED_FILES
        ] + [self.lock_path()]
        before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in tracked_paths
        }

        self.install()

        after = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in tracked_paths
        }
        self.assertEqual(before, after)

    def test_t03_dry_run_has_no_side_effects(self):
        self.install(dry_run=True)

        self.assert_no_managed_files()
        self.assertFalse(os.path.lexists(self.lock_path()))

    def test_t04_capability_resolver_returns_base_and_frontend_profiles(self):
        cases = {
            (): (installer.BASE_CAPABILITY, tuple(installer.MANAGED_FILES)),
            (
                "frontend-ui-design",
            ): (
                "frontend-ui-design",
                (
                    *installer.MANAGED_FILES,
                    ".github/skills/frontend-ui-design/SKILL.md",
                    ".github/skills/frontend-ui-design/references/"
                    "input-interpretation.md",
                    ".github/skills/frontend-ui-design/references/"
                    "mockup-conversion.md",
                    ".github/skills/frontend-ui-design/references/"
                    "traceability-and-scope.md",
                ),
            ),
            (
                "angular-ui-implementation",
            ): (
                "angular-ui-implementation",
                (
                    *installer.MANAGED_FILES,
                    ".github/skills/frontend-ui-design/SKILL.md",
                    ".github/skills/frontend-ui-design/references/"
                    "input-interpretation.md",
                    ".github/skills/frontend-ui-design/references/"
                    "mockup-conversion.md",
                    ".github/skills/frontend-ui-design/references/"
                    "traceability-and-scope.md",
                    ".github/skills/angular-ui-implementation/SKILL.md",
                    ".github/skills/angular-ui-implementation/references/"
                    "angular-discovery.md",
                    ".github/skills/angular-ui-implementation/references/"
                    "angular-components.md",
                    ".github/skills/angular-ui-implementation/references/"
                    "angular-unit-testing.md",
                ),
            ),
            (
                "react-ui-implementation",
            ): (
                "react-ui-implementation",
                (
                    *installer.MANAGED_FILES,
                    ".github/skills/frontend-ui-design/SKILL.md",
                    ".github/skills/frontend-ui-design/references/"
                    "input-interpretation.md",
                    ".github/skills/frontend-ui-design/references/"
                    "mockup-conversion.md",
                    ".github/skills/frontend-ui-design/references/"
                    "traceability-and-scope.md",
                    ".github/skills/react-ui-implementation/SKILL.md",
                    ".github/skills/react-ui-implementation/references/"
                    "react-discovery.md",
                    ".github/skills/react-ui-implementation/references/"
                    "react-components.md",
                    ".github/skills/react-ui-implementation/references/"
                    "react-unit-testing.md",
                ),
            ),
        }
        for requested, (last_capability, expected_files) in cases.items():
            with self.subTest(requested=requested):
                resolved, files = installer.resolve_capabilities(requested)
                self.assertEqual(len(expected_files), len(files))
                self.assertEqual(expected_files, files)
                self.assertEqual(last_capability, resolved[-1])

    def test_t05_capability_resolver_deduplicates_design_dependency(self):
        resolved, files = installer.resolve_capabilities(
            ("angular-ui-implementation", "react-ui-implementation")
        )

        self.assertEqual(
            (
                installer.BASE_CAPABILITY,
                "frontend-ui-design",
                "angular-ui-implementation",
                "react-ui-implementation",
            ),
            resolved,
        )
        self.assertEqual(20, len(files))
        self.assertEqual(1, files.count(
            ".github/skills/frontend-ui-design/SKILL.md"
        ))

    def test_t06_capability_resolver_rejects_invalid_inventories(self):
        valid = installer.capability_inventory()
        cases = {
            "unknown-id": (valid, ("missing",), "Unknown capability"),
            "duplicate-id": (
                valid,
                ("frontend-ui-design", "frontend-ui-design"),
                "Duplicate requested capability",
            ),
            "missing-dependency": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "test": {
                        "dependencies": ["missing"],
                        "artifacts": [".github/skills/test/SKILL.md"],
                    },
                },
                ("test",),
                "unknown dependency",
            ),
            "cycle": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "first": {
                        "dependencies": ["second"],
                        "artifacts": [".github/skills/first/SKILL.md"],
                    },
                    "second": {
                        "dependencies": ["first"],
                        "artifacts": [".github/skills/second/SKILL.md"],
                    },
                },
                ("first",),
                "Capability dependency cycle",
            ),
            "duplicate-path": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "test": {
                        "dependencies": [],
                        "artifacts": [
                            ".github/skills/test/SKILL.md",
                            ".github/skills/test/SKILL.md",
                        ],
                    },
                },
                ("test",),
                "Duplicate capability artifact",
            ),
            "unsafe-path": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "test": {
                        "dependencies": [],
                        "artifacts": [".github/skills/test/SKILL.md", "../bad"],
                    },
                },
                ("test",),
                "Non-canonical capability artifact",
            ),
            "missing-skill-file": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "frontend-ui-design": {
                        "dependencies": [],
                        "artifacts": [
                            ".github/skills/frontend-ui-design/reference.md",
                        ],
                    },
                },
                ("frontend-ui-design",),
                "canonical SKILL.md",
            ),
            "non-canonical-path": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "test": {
                        "dependencies": [],
                        "artifacts": [
                            ".github/skills/test/SKILL.md",
                            ".github/skills/test//reference.md",
                        ],
                    },
                },
                ("test",),
                "Non-canonical capability artifact",
            ),
            "alternate-separator": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "test": {
                        "dependencies": [],
                        "artifacts": [
                            ".github/skills/test/SKILL.md",
                            ".github\\skills\\test\\reference.md",
                        ],
                    },
                },
                ("test",),
                "Unsafe capability artifact",
            ),
            "dot-segment": (
                {
                    installer.BASE_CAPABILITY: valid[installer.BASE_CAPABILITY],
                    "test": {
                        "dependencies": [],
                        "artifacts": [
                            ".github/skills/test/SKILL.md",
                            ".github/skills/test/./reference.md",
                        ],
                    },
                },
                ("test",),
                "Non-canonical capability artifact",
            ),
        }
        for label, (inventory, requested, message) in cases.items():
            with self.subTest(label=label):
                with self.assertRaisesRegex(ValueError, message):
                    installer.resolve_capabilities(requested, inventory)

    def test_t07_capability_inventory_contains_real_skill_files(self):
        installer.validate_capability_inventory()

    def test_t08_frontend_skill_inventory_rejects_invalid_ownership_and_links(self):
        valid = installer.capability_inventory()
        frontend = valid["frontend-ui-design"]
        cases = {
            "wrong-skill-file": {
                **frontend,
                "artifacts": [
                    ".github/skills/other/SKILL.md",
                    *frontend["artifacts"][1:],
                ],
            },
            "escaping-artifact": {
                **frontend,
                "artifacts": [
                    *frontend["artifacts"],
                    ".github/skills/other/reference.md",
                ],
            },
            "missing-reference": {
                **frontend,
                "artifacts": frontend["artifacts"][:-1],
            },
        }
        for label, definition in cases.items():
            with self.subTest(label=label):
                inventory = {
                    installer.BASE_CAPABILITY:
                    valid[installer.BASE_CAPABILITY],
                    "frontend-ui-design": definition,
                }
                with self.assertRaisesRegex(ValueError, "skill|SKILL|inventoried"):
                    installer.validate_capability_inventory(inventory)

    def test_t09_frontend_skill_inventory_rejects_escaping_reference(self):
        valid = installer.capability_inventory()
        with mock.patch.object(
            installer,
            "declared_local_references",
            return_value=("../outside.md",),
        ):
            with self.assertRaisesRegex(ValueError, "escapes skill directory"):
                installer.validate_capability_inventory(valid)

    def test_t10_frontend_profiles_install_exact_resolved_manifests(self):
        cases = {
            ("frontend-ui-design",): 12,
            ("angular-ui-implementation",): 16,
            ("react-ui-implementation",): 16,
            ("angular-ui-implementation", "react-ui-implementation"): 20,
        }
        for capabilities, expected_count in cases.items():
            with self.subTest(capabilities=capabilities):
                self.install(capabilities=capabilities)
                resolved, files = installer.resolve_capabilities(capabilities)
                lock = self.read_lock()
                self.assertEqual(expected_count, len(files))
                self.assertEqual(list(resolved), lock["capabilities"])
                self.assertEqual(list(files), list(lock["files"]))
                for relative in files:
                    self.assertEqual(
                        installer.sha256(installer.source_path(relative)),
                        lock["files"][relative],
                    )
                    self.assertEqual(
                        installer.source_path(relative).read_bytes(),
                        self.destination(relative).read_bytes(),
                    )
                for path in files:
                    self.destination(path).unlink()
                self.lock_path().unlink()

    def test_t11_frontend_dry_run_has_no_side_effects(self):
        self.install(
            dry_run=True,
            capabilities=("angular-ui-implementation",),
        )

        self.assert_no_managed_files()
        self.assertFalse(os.path.lexists(self.lock_path()))
        self.assertEqual([], list(self.target.glob(".ai-framework-stage-*")))

    def test_t12_frontend_reinstall_preserves_timestamps(self):
        capabilities = ("angular-ui-implementation",)
        self.install(capabilities=capabilities)
        _, files = installer.resolve_capabilities(capabilities)
        paths = [self.destination(relative) for relative in files]
        paths.append(self.lock_path())
        before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths
        }

        self.install(capabilities=capabilities)

        self.assertEqual(
            before,
            {path: (path.read_bytes(), path.stat().st_mtime_ns) for path in paths},
        )

    def test_t13_v030_upgrade_supports_base_and_frontend_addition(self):
        self.create_historical_installation()
        self.install(upgrade=True, capabilities=("angular-ui-implementation",))

        resolved, files = installer.resolve_capabilities(
            ("angular-ui-implementation",)
        )
        lock = self.read_lock()
        self.assertEqual(list(resolved), lock["capabilities"])
        self.assertEqual(list(files), list(lock["files"]))
        self.assertEqual(16, len(files))

    def test_t14_v030_upgrade_supports_base_profile(self):
        self.create_historical_installation()
        self.install(upgrade=True)

        lock = self.read_lock()
        self.assertEqual([installer.BASE_CAPABILITY], lock["capabilities"])
        self.assertEqual(installer.MANAGED_FILES, list(lock["files"]))

    def test_t15_capability_change_requires_upgrade_and_cannot_remove(self):
        self.install(capabilities=("angular-ui-implementation",))
        original_lock = self.lock_path().read_bytes()
        with self.assertRaisesRegex(ValueError, "use --upgrade"):
            self.install(capabilities=("angular-ui-implementation", "react-ui-implementation"))
        with self.assertRaisesRegex(ValueError, "Capability removal is BLOCKED"):
            self.install(upgrade=True)
        self.assertEqual(original_lock, self.lock_path().read_bytes())

    def test_t16_lock_schema_and_historical_integrity_are_rejected(self):
        self.create_historical_installation()
        historical_lock = self.read_lock()
        historical_lock["files"].pop(next(iter(historical_lock["files"])))
        self.write_lock(historical_lock)
        with self.assertRaisesRegex(ValueError, "supported format"):
            self.install(upgrade=True)

        self.lock_path().unlink()
        self.create_historical_installation()
        historical_lock = self.read_lock()
        historical_lock["commit"] = "f" * 40
        self.write_lock(historical_lock)
        with self.assertRaisesRegex(ValueError, "Cannot verify legacy source"):
            self.install(upgrade=True)

        self.lock_path().unlink()
        for relative in installer.MANAGED_FILES:
            self.destination(relative).unlink()
        self.install()
        current_lock = self.read_lock()
        current_lock["capabilities"].append("react-ui-implementation")
        self.write_lock(current_lock)
        with self.assertRaisesRegex(ValueError, "invalid capabilities|inconsistent"):
            self.install()

    def test_t17_current_lock_historical_integrity_and_capabilities_are_verified(self):
        self.install(capabilities=("angular-ui-implementation",))
        original_lock = self.lock_path().read_bytes()
        original_reference = self.destination(
            ".github/skills/frontend-ui-design/references/"
            "input-interpretation.md"
        ).read_bytes()
        cases = {
            "digest": lambda lock: lock["files"].update({
                ".github/skills/frontend-ui-design/references/"
                "input-interpretation.md": hashlib.sha256(
                    b"local lock digest match"
                ).hexdigest(),
            }),
            "commit": lambda lock: lock.update({"commit": "f" * 40}),
            "version": lambda lock: lock.update({"version": "9.9.9"}),
            "missing-artifact": lambda lock: lock["files"].update({
                ".github/skills/missing/SKILL.md": "a" * 64,
            }),
            "capabilities": lambda lock: lock.update({
                "capabilities": [installer.BASE_CAPABILITY],
            }),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                lock = json.loads(original_lock)
                mutate(lock)
                self.write_lock(lock)
                if label == "digest":
                    altered_content = b"local lock digest match"
                    altered_file = self.destination(
                        ".github/skills/frontend-ui-design/references/"
                        "input-interpretation.md"
                    )
                    altered_file.write_bytes(altered_content)
                    self.assertEqual(
                        hashlib.sha256(altered_content).hexdigest(),
                        lock["files"][
                            ".github/skills/frontend-ui-design/references/"
                            "input-interpretation.md"
                        ],
                    )
                with self.assertRaises(ValueError):
                    self.install(
                        upgrade=True,
                        capabilities=(
                            "angular-ui-implementation",
                            "react-ui-implementation",
                        ),
                    )
                self.assertEqual(
                    json.dumps(lock, indent=2).encode() + b"\n",
                    self.lock_path().read_bytes(),
                )
                if label == "digest":
                    self.assertEqual(
                        b"local lock digest match",
                        self.destination(
                            ".github/skills/frontend-ui-design/references/"
                            "input-interpretation.md"
                        ).read_bytes(),
                    )
                    self.assertEqual(
                        hashlib.sha256(
                            self.destination(
                                ".github/skills/frontend-ui-design/references/"
                                "input-interpretation.md"
                            ).read_bytes()
                        ).hexdigest(),
                        lock["files"][
                            ".github/skills/frontend-ui-design/references/"
                            "input-interpretation.md"
                        ],
                    )
                    self.destination(
                        ".github/skills/frontend-ui-design/references/"
                        "input-interpretation.md"
                    ).write_bytes(original_reference)
        self.lock_path().write_bytes(original_lock)

    def test_t18_current_lock_capability_types_reject_without_side_effects(self):
        self.install()
        original_lock = self.lock_path().read_bytes()
        cases = (["java-base", ["react-ui-implementation"]],
                 ["java-base", {"id": "react-ui-implementation"}],
                 ["java-base", None], ["java-base", 1],
                 ["java-base", "java-base"],
                 ["java-base", "unknown"])
        for capabilities in cases:
            with self.subTest(capabilities=capabilities):
                lock = json.loads(original_lock)
                lock["capabilities"] = capabilities
                self.write_lock(lock)
                with self.assertRaises(ValueError):
                    self.install()
                self.assertEqual(
                    json.dumps(lock, indent=2).encode() + b"\n",
                    self.lock_path().read_bytes(),
                )
        self.lock_path().write_bytes(original_lock)

    def test_t19_historical_framework_identity_is_rejected(self):
        self.create_historical_installation()
        original_lock = self.lock_path().read_bytes()
        original_historical_content = installer.historical_file_content
        historical_lock = self.read_lock()

        def altered_framework_config(commit, relative):
            content = original_historical_content(commit, relative)
            if (
                commit == historical_lock["commit"]
                and relative == "framework.yaml"
            ):
                return content.replace(
                    b"name: ai-engineering-framework",
                    b"name: different-framework",
                )
            return content

        with mock.patch.object(
            installer,
            "historical_file_content",
            side_effect=altered_framework_config,
        ):
            with self.assertRaisesRegex(
                ValueError, "Historical framework identity"
            ):
                self.install(upgrade=True)

        self.assertEqual(original_lock, self.lock_path().read_bytes())

    def test_t20_frontend_publication_failure_rolls_back(self):
        real_replace = installer.os.replace
        calls = 0

        def fail_second_replace(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected frontend replacement failure")
            return real_replace(source, destination)

        with mock.patch.object(
            installer.os, "replace", side_effect=fail_second_replace
        ):
            with self.assertRaisesRegex(OSError, "frontend replacement"):
                self.install(capabilities=("angular-ui-implementation",))

        _, files = installer.resolve_capabilities(("angular-ui-implementation",))
        for relative in files:
            self.assertFalse(os.path.lexists(self.destination(relative)))
        self.assertFalse(os.path.lexists(self.lock_path()))

    def test_t21_modified_frontend_file_and_upgrade_conflict_are_rejected(self):
        self.install(capabilities=("angular-ui-implementation",))
        design_reference = self.destination(
            ".github/skills/frontend-ui-design/references/"
            "input-interpretation.md"
        )
        original_lock = self.lock_path().read_bytes()
        design_reference.write_text("local modification", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "modified locally"):
            self.install(
                upgrade=True,
                capabilities=(
                    "angular-ui-implementation", "react-ui-implementation"
                ),
            )
        self.assertEqual(original_lock, self.lock_path().read_bytes())

        design_reference.write_bytes(
            installer.source_path(
                ".github/skills/frontend-ui-design/references/"
                "input-interpretation.md"
            ).read_bytes()
        )
        self.write_lock(
            installer.build_lock(
                installer.version(),
                installer.git_at(installer.ROOT, "rev-parse", "HEAD"),
                installer.source_manifest(
                    installer.resolve_capabilities(
                        ("angular-ui-implementation",)
                    )[1]
                ),
                installer.resolve_capabilities(
                    ("angular-ui-implementation",)
                )[0],
            )
        )
        conflict = self.destination(
            ".github/skills/react-ui-implementation/SKILL.md"
        )
        conflict.parent.mkdir(parents=True, exist_ok=True)
        conflict.write_text("consumer file", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "unmanaged destination"):
            self.install(
                upgrade=True,
                capabilities=(
                    "angular-ui-implementation", "react-ui-implementation"
                ),
            )
        self.assertEqual("consumer file", conflict.read_text(encoding="utf-8"))
        self.assertEqual(original_lock, self.lock_path().read_bytes())

    def test_t22_unmanaged_managed_file_conflict_is_rejected(self):
        relative = installer.MANAGED_FILES[1]
        destination = self.destination(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("consumer content", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "unmanaged destination"):
            self.install()

        self.assertEqual("consumer content", destination.read_text(encoding="utf-8"))
        self.assertFalse(os.path.lexists(self.lock_path()))

    def test_t23_invalid_unknown_corrupt_and_tampered_locks_are_rejected(self):
        cases = {
            "corrupt": "{not json",
            "unknown": json.dumps(
                {
                    "framework": "other-framework",
                    "version": "0.2.0",
                    "source": installer.FRAMEWORK_SOURCE,
                    "commit": "a" * 40,
                    "files": {},
                }
            ),
            "tampered": json.dumps(
                {
                    "framework": installer.FRAMEWORK_NAME,
                    "version": installer.LEGACY_VERSION,
                    "source": installer.FRAMEWORK_SOURCE,
                    "commit": "a" * 40,
                    "files": {
                        installer.LEGACY_MANAGED_FILES[0]: "not-a-hash"
                    },
                }
            ),
        }
        for label, contents in cases.items():
            with self.subTest(label=label):
                self.lock_path().write_text(contents, encoding="utf-8")
                with self.assertRaises(ValueError):
                    self.install(upgrade=True)
                self.assertEqual(contents, self.lock_path().read_text(encoding="utf-8"))
                self.assert_no_managed_files()
                self.lock_path().unlink()

    def test_t24_locally_modified_managed_file_is_rejected(self):
        self.install()
        destination = self.destination(installer.MANAGED_FILES[0])
        original_lock = self.lock_path().read_bytes()
        destination.write_text("consumer modification", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "modified locally"):
            self.install()

        self.assertEqual("consumer modification", destination.read_text(encoding="utf-8"))
        self.assertEqual(original_lock, self.lock_path().read_bytes())

    def test_t25_verified_v020_upgrade_preserves_consumer_files(self):
        legacy_relative, legacy_content = self.create_legacy_installation()
        consumer_file = self.target / "consumer-notes.txt"
        consumer_file.write_text("preserve me", encoding="utf-8")

        self.assertEqual(
            legacy_content,
            self.destination(legacy_relative).read_bytes(),
        )

        self.install(upgrade=True)

        self.assertEqual("preserve me", consumer_file.read_text(encoding="utf-8"))
        self.assertEqual(
            installer.source_path(legacy_relative).read_bytes(),
            self.destination(legacy_relative).read_bytes(),
        )
        lock = self.read_lock()
        self.assertEqual(installer.MANAGED_FILES, list(lock["files"]))
        for relative in installer.MANAGED_FILES:
            destination = self.destination(relative)
            self.assertTrue(destination.is_file(), relative)
            self.assertEqual(
                installer.source_path(relative).read_bytes(),
                destination.read_bytes(),
            )
            self.assertEqual(installer.sha256(destination), lock["files"][relative])
    def test_t26_upgrade_rejects_unverifiable_historical_revision(self):
        legacy_relative, legacy_content = self.create_legacy_installation()
        legacy_lock = self.read_lock()
        legacy_lock["commit"] = "f" * 40
        self.write_lock(legacy_lock)

        with self.assertRaisesRegex(ValueError, "Cannot verify legacy source"):
            self.install(upgrade=True)

        self.assertEqual(
            legacy_content, self.destination(legacy_relative).read_bytes()
        )
        self.assertEqual(legacy_lock, self.read_lock())
        for relative in installer.MANAGED_FILES[1:]:
            self.assertFalse(os.path.lexists(self.destination(relative)))

    def test_t27_managed_path_symlinks_and_broken_symlinks_are_rejected(self):
        relative = installer.MANAGED_FILES[0]
        destination = self.destination(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        outside = self.temporary_root / "outside"
        outside.write_text("outside", encoding="utf-8")

        for label, target in (
            ("normal", outside),
            ("broken", self.temporary_root / "missing-target"),
        ):
            with self.subTest(label=label):
                destination.unlink(missing_ok=True)
                destination.symlink_to(target)
                with self.assertRaisesRegex(ValueError, "Symlink"):
                    self.install()
                self.assertTrue(destination.is_symlink())
                self.assertFalse(os.path.lexists(self.lock_path()))

            destination.unlink()
        skills_directory = self.target / ".github" / "skills"
        skills_directory.parent.mkdir(parents=True, exist_ok=True)
        outside_directory = self.temporary_root / "outside-skills"
        outside_directory.mkdir()
        skills_directory.symlink_to(outside_directory, target_is_directory=True)

        with self.subTest(label="intermediate-skills-directory"):
            with self.assertRaisesRegex(ValueError, "Symlink"):
                self.install()
            self.assertTrue(skills_directory.is_symlink())
            self.assertEqual([], list(outside_directory.iterdir()))
            self.assertFalse(os.path.lexists(self.lock_path()))

    def test_t28_target_with_symlink_ancestor_is_rejected(self):
        real_parent = self.temporary_root / "real-parent"
        real_parent.mkdir()
        linked_parent = self.temporary_root / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        linked_target = linked_parent / "consumer"
        linked_target.mkdir()
        self.run_git("init", linked_target)

        with self.assertRaisesRegex(ValueError, "must not contain a symlink"):
            installer.validate_target(linked_target)

    def test_t29_file_replace_failure_rolls_back_created_files(self):
        real_replace = installer.os.replace
        calls = 0

        def fail_second_replace(source, destination):
            nonlocal calls
            calls += 1
            if calls == 2:
                raise OSError("injected file replacement failure")
            return real_replace(source, destination)

        with mock.patch.object(
            installer.os, "replace", side_effect=fail_second_replace
        ):
            with self.assertRaisesRegex(OSError, "injected file replacement"):
                self.install()

        self.assert_no_managed_files()
        self.assertFalse(os.path.lexists(self.lock_path()))

    def test_t30_lock_publication_failure_rolls_back_created_files(self):
        real_replace = installer.os.replace

        def fail_lock_publication(source, destination):
            if Path(source).name == installer.LOCK_NAME:
                raise OSError("injected lock publication failure")
            return real_replace(source, destination)

        with mock.patch.object(
            installer.os, "replace", side_effect=fail_lock_publication
        ):
            with self.assertRaisesRegex(OSError, "injected lock publication"):
                self.install()

        self.assert_no_managed_files()
        self.assertFalse(os.path.lexists(self.lock_path()))

    def test_t31_incomplete_rollback_preserves_backups_and_cause(self):
        relative = installer.MANAGED_FILES[0]
        destination = self.destination(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("legacy file", encoding="utf-8")
        self.lock_path().write_text("legacy lock", encoding="utf-8")
        staging = self.temporary_root / "stage"
        staging.mkdir()
        manifest = installer.source_manifest()
        lock = installer.build_lock("test", "a" * 40, manifest)
        staged_files, staged_lock = installer.prepare_staged_files(
            staging, manifest, lock
        )
        backup = destination.with_name(
            f".{destination.name}.ai-framework-backup"
        )
        real_replace = installer.os.replace

        def fail_write_and_restore(source, target):
            if source == staged_files[relative] and target == destination:
                raise OSError("injected install failure")
            if source == backup and target == destination:
                raise OSError("injected restore failure")
            return real_replace(source, target)

        with mock.patch.object(
            installer.os, "replace", side_effect=fail_write_and_restore):
            with self.assertRaises(installer.RecoveryError) as raised:
                installer.replace_staged_files(
                    self.target,
                    staged_files,
                    staged_lock,
                    {relative},
                    True,
                )

        self.assertIn("injected install failure", str(raised.exception))
        self.assertIn("injected restore failure", str(raised.exception))
        self.assertTrue(backup.exists())
        self.assertFalse(destination.exists())
        self.assertEqual("legacy lock", self.lock_path().read_text(encoding="utf-8"))

    def test_t32_cleanup_failure_reports_completed_install_and_keeps_backup(self):
        relative = installer.MANAGED_FILES[0]
        destination = self.destination(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("legacy file", encoding="utf-8")
        self.lock_path().write_text("legacy lock", encoding="utf-8")
        staging = self.temporary_root / "stage"
        staging.mkdir()
        manifest = installer.source_manifest()
        lock = installer.build_lock("test", "a" * 40, manifest)
        staged_files, staged_lock = installer.prepare_staged_files(
            staging, manifest, lock
        )
        real_remove = installer.remove_regular_file_or_symlink

        def fail_backup_cleanup(path):
            if ".ai-framework-backup" in path.name:
                raise OSError("injected cleanup failure")
            return real_remove(path)

        with mock.patch.object(
            installer,
            "remove_regular_file_or_symlink",
            side_effect=fail_backup_cleanup,
        ):
            with self.assertRaisesRegex(OSError, "backup cleanup failed"):
                installer.replace_staged_files(
                    self.target,
                    staged_files,
                    staged_lock,
                    {relative},
                    True,
                )

        self.assertEqual(
            installer.source_path(relative).read_bytes(), destination.read_bytes()
        )
        self.assertEqual(lock, self.read_lock())
        self.assertTrue(
            destination.with_name(
                f".{destination.name}.ai-framework-backup"
            ).exists()
        )


if __name__ == "__main__":
    unittest.main()
