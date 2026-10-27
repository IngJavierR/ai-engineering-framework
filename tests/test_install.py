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

    def install(self, dry_run=False, upgrade=False):
        with mock.patch.object(installer, "git", self.framework_git):
            installer.install(self.target, dry_run=dry_run, upgrade=upgrade)

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

    def test_t04_unmanaged_managed_file_conflict_is_rejected(self):
        relative = installer.MANAGED_FILES[1]
        destination = self.destination(relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text("consumer content", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "unmanaged destination"):
            self.install()

        self.assertEqual("consumer content", destination.read_text(encoding="utf-8"))
        self.assertFalse(os.path.lexists(self.lock_path()))

    def test_t05_invalid_unknown_corrupt_and_tampered_locks_are_rejected(self):
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

    def test_t06_locally_modified_managed_file_is_rejected(self):
        self.install()
        destination = self.destination(installer.MANAGED_FILES[0])
        original_lock = self.lock_path().read_bytes()
        destination.write_text("consumer modification", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "modified locally"):
            self.install()

        self.assertEqual("consumer modification", destination.read_text(encoding="utf-8"))
        self.assertEqual(original_lock, self.lock_path().read_bytes())

    def test_t07_verified_v020_upgrade_preserves_consumer_files(self):
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
    def test_t08_upgrade_rejects_unverifiable_historical_revision(self):
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

    def test_t09_managed_path_symlinks_and_broken_symlinks_are_rejected(self):
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

    def test_t10_target_with_symlink_ancestor_is_rejected(self):
        real_parent = self.temporary_root / "real-parent"
        real_parent.mkdir()
        linked_parent = self.temporary_root / "linked-parent"
        linked_parent.symlink_to(real_parent, target_is_directory=True)
        linked_target = linked_parent / "consumer"
        linked_target.mkdir()
        self.run_git("init", linked_target)

        with self.assertRaisesRegex(ValueError, "must not contain a symlink"):
            installer.validate_target(linked_target)

    def test_t11_file_replace_failure_rolls_back_created_files(self):
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

    def test_t12_lock_publication_failure_rolls_back_created_files(self):
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

    def test_t13_incomplete_rollback_preserves_backups_and_cause(self):
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

    def test_t14_cleanup_failure_reports_completed_install_and_keeps_backup(self):
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
