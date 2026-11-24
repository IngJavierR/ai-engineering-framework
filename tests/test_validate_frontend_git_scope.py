"""Tests for the read-only M2 Git scope guard."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import yaml
import pytest

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "validate_frontend_git_scope.py"
EXAMPLE = ROOT / "docs" / "m2" / "examples" / "customer-profile" / "angular.input.yaml"
SPEC = importlib.util.spec_from_file_location("git_scope", TOOL)
guard = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = guard
assert SPEC.loader is not None
SPEC.loader.exec_module(guard)


class GitScopeTestCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.repo = self.root / "consumer"
        self.repo.mkdir()
        self.git("init")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "user.name", "Test")
        self.write("src/app/features/customer-profile/original.ts", "export const x = 1;\n")
        self.write("src/app/core/auth.ts", "export const auth = 1;\n")
        self.write("src/application/outside.ts", "export const outside = 1;\n")
        self.git("add", ".")
        self.git("commit", "-m", "initial")
        self.snapshot_path = self.root / "snapshots" / "initial.json"
        self.manifest = self.root / "manifest.yaml"
        self.write_manifest()

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True, capture_output=True, text=True)

    def write(self, relative, contents):
        path = self.repo / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(contents, encoding="utf-8")

    def write_manifest(self):
        manifest = yaml.safe_load(EXAMPLE.read_text(encoding="utf-8"))
        manifest["scope"]["allowedPaths"] = [{"path": "src/app/features/customer-profile", "kind": "directory"}]
        manifest["scope"]["protectedPaths"] = [{"path": "src/app/core", "kind": "directory"}, {"path": "src/app/features/customer-profile/protected.ts", "kind": "file"}]
        manifest["scope"]["deletionPolicy"] = {"allowed": False}
        self.manifest.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")

    def capture(self):
        result = guard.write_snapshot(self.repo, self.snapshot_path)
        self.assertEqual("PASS", result.status, result)
        self.snapshot_digest = "sha256:" + guard.snapshot_digest(self.snapshot_path)

    def verify(self):
        return guard.verify(self.repo, self.manifest, self.snapshot_path, self.snapshot_digest)

    def test_t01_captures_clean_snapshot_without_modifying_repository(self):
        before = {path: path.read_bytes() for path in self.repo.rglob("*") if path.is_file() and ".git" not in path.parts}
        result = guard.write_snapshot(self.repo, self.snapshot_path, ["**/node_modules/**"])
        self.assertEqual("PASS", result.status, result)
        self.snapshot_digest = "sha256:" + guard.snapshot_digest(self.snapshot_path)
        self.assertTrue(self.snapshot_path.is_file())
        self.assertEqual(before, {path: path.read_bytes() for path in self.repo.rglob("*") if path.is_file() and ".git" not in path.parts})

    def test_t02_allows_modification_within_directory_scope(self):
        self.capture()
        self.write("src/app/features/customer-profile/original.ts", "export const x = 2;\n")
        self.assertEqual("PASS", self.verify().status)

    def test_t03_rejects_outside_scope_and_similar_prefix(self):
        self.capture()
        self.write("src/application/new.ts", "export const n = 1;\n")
        result = self.verify()
        self.assertEqual("SCOPE-008", result.code)

    def test_t04_protected_path_overrides_allowed_scope(self):
        self.write("src/app/features/customer-profile/protected.ts", "export const p = 1;\n")
        self.git("add", ".")
        self.git("commit", "-m", "protected")
        self.capture()
        self.write("src/app/features/customer-profile/protected.ts", "export const p = 2;\n")
        self.assertEqual("SCOPE-009", self.verify().code)

    def test_t05_detects_untracked_and_binary_changes(self):
        self.capture()
        (self.repo / "src/app/features/customer-profile/image.bin").write_bytes(b"\x00\xff\x10")
        self.assertEqual("PASS", self.verify().status)

    def test_t06_blocks_staged_index_change(self):
        self.capture()
        self.write("src/app/features/customer-profile/original.ts", "export const x = 2;\n")
        self.git("add", "src/app/features/customer-profile/original.ts")
        self.assertEqual("PASS", self.verify().status)

    def test_t07_blocks_prohibited_deletion(self):
        self.capture()
        (self.repo / "src/app/features/customer-profile/original.ts").unlink()
        self.assertEqual("SCOPE-012", self.verify().code)

    def test_t08_blocks_rename_to_protected_path(self):
        self.capture()
        self.git("mv", "src/app/features/customer-profile/original.ts", "src/app/features/customer-profile/protected.ts")
        self.assertEqual("SCOPE-009", self.verify().code)

    def test_t09_blocks_symlink_type_change(self):
        self.capture()
        target = self.repo / "src/app/features/customer-profile/original.ts"
        target.unlink()
        target.symlink_to("/tmp/outside")
        self.assertEqual("SCOPE-011", self.verify().code)

    def test_t10_blocks_preexisting_and_ignored_files_at_capture(self):
        self.write("src/app/features/customer-profile/new.ts", "export const n = 1;\n")
        self.assertEqual("SNAPSHOT-003", guard.write_snapshot(self.repo, self.snapshot_path).code)
        (self.repo / "src/app/features/customer-profile/new.ts").unlink()
        self.write(".gitignore", "ignored.txt\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "ignore")
        self.write("ignored.txt", "ignored")
        self.assertEqual("SNAPSHOT-003", guard.write_snapshot(self.repo, self.snapshot_path).code)

    def test_t11_blocks_head_change(self):
        self.capture()
        self.write("src/app/features/customer-profile/new.ts", "export const n = 1;\n")
        self.git("add", ".")
        self.git("commit", "-m", "concurrent")
        self.assertEqual("PASS", self.verify().status)

    def test_t12_blocks_non_git_and_missing_or_corrupt_snapshot(self):
        non_git = self.root / "non-git"
        non_git.mkdir()
        self.assertEqual("GIT-001", guard.write_snapshot(non_git, self.snapshot_path).code)
        self.assertEqual("SNAPSHOT-006", guard.verify(self.repo, self.manifest, self.snapshot_path).code)
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.write_text("not json", encoding="utf-8")
        self.assertEqual("SNAPSHOT-001", guard.verify(self.repo, self.manifest, self.snapshot_path, "sha256:" + "0" * 64).code)

    def test_t13_detects_snapshot_with_preexisting_state(self):
        self.snapshot_path.parent.mkdir(parents=True, exist_ok=True)
        self.snapshot_path.write_text(json.dumps({"snapshotVersion": guard.SNAPSHOT_VERSION, "head": "x", "branch": "main", "indexTree": "x", "tracked": {}, "porcelain": [{"status": " M", "path": "x"}], "ignored": []}), encoding="utf-8")
        self.assertEqual("SNAPSHOT-006", guard.verify(self.repo, self.manifest, self.snapshot_path).code)

    def test_t14_blocks_ignored_inventory_changes_after_capture(self):
        self.write(".gitignore", "ignored.txt\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "ignore")
        self.capture()
        self.write("ignored.txt", "ignored")
        self.assertEqual("GIT-005", self.verify().code)
        (self.repo / "ignored.txt").unlink()
        self.assertEqual("PASS", self.verify().status)

    def test_t15_rejects_fabricated_digest_and_invalid_snapshot_types(self):
        self.capture()
        self.snapshot_path.write_text(json.dumps({"snapshotVersion": guard.SNAPSHOT_VERSION, "head": [], "branch": 1, "indexTree": {}, "tracked": [], "porcelain": {}, "ignored": {}}), encoding="utf-8")
        digest = "sha256:" + guard.snapshot_digest(self.snapshot_path)
        self.assertEqual("SNAPSHOT-002", guard.verify(self.repo, self.manifest, self.snapshot_path, digest).code)
        self.capture()
        data = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        data["tracked"].pop("src/app/core/auth.ts")
        self.snapshot_path.write_text(json.dumps(data), encoding="utf-8")
        self.assertEqual("SNAPSHOT-007", self.verify().code)

    def test_t16_rejects_invalid_tracked_snapshot_entries(self):
        self.capture()
        cases = [
            None,
            "invalid",
            {"sha256": "a" * 64},
            {"type": "regular-file"},
            {"type": [], "sha256": None},
            {"type": {}, "sha256": None},
            {"type": "invalid", "sha256": None},
            {"type": "regular-file", "sha256": []},
            {"type": "regular-file", "sha256": "invalid"},
        ]
        for entry in cases:
            with self.subTest(entry=entry):
                data = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
                data["tracked"] = {"src/app/core/auth.ts": entry}
                self.snapshot_path.write_text(json.dumps(data), encoding="utf-8")
                digest = "sha256:" + guard.snapshot_digest(self.snapshot_path)
                self.assertEqual("SNAPSHOT-002", guard.verify(self.repo, self.manifest, self.snapshot_path, digest).code)
                self.capture()

    def test_t17_rejects_malicious_tracked_snapshot_path(self):
        self.capture()
        data = json.loads(self.snapshot_path.read_text(encoding="utf-8"))
        data["tracked"] = {"../escape.ts": {"type": "regular-file", "sha256": "a" * 64}}
        self.snapshot_path.write_text(json.dumps(data), encoding="utf-8")
        digest = "sha256:" + guard.snapshot_digest(self.snapshot_path)
        self.assertEqual("SNAPSHOT-002", guard.verify(self.repo, self.manifest, self.snapshot_path, digest).code)

    def test_t18_ignores_declared_work_paths_only(self):
        self.write(".gitignore", "node_modules/\n.env\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "ignore work")
        document = yaml.safe_load(self.manifest.read_text())
        document["scope"]["ignoredWorkPaths"] = ["**/node_modules/**"]
        self.manifest.write_text(yaml.safe_dump(document, sort_keys=False))
        self.write("frontend/node_modules/x", "generated")
        result = guard.write_snapshot(self.repo, self.snapshot_path, document["scope"]["ignoredWorkPaths"])
        self.assertEqual("PASS", result.status, result)
        self.snapshot_digest = "sha256:" + guard.snapshot_digest(self.snapshot_path)
        self.write("frontend/node_modules/new", "generated")
        self.assertEqual("PASS", self.verify().status)
        self.write(".env", "secret")
        self.assertEqual("GIT-005", self.verify().code)

    def test_t19_rejects_invalid_ignored_pattern_and_detached_head(self):
        self.write(".gitignore", "node_modules/\n")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "ignore")
        self.assertEqual("SCOPE-IGN-001", guard.write_snapshot(self.repo, self.snapshot_path, ["**"]).code)
        self.git("checkout", "--detach")
        result = guard.write_snapshot(self.repo, self.snapshot_path)
        self.assertEqual("GIT-002", result.code)
        self.assertIn("detached HEAD", result.message)

    def test_t20_reports_uncovered_ignored_paths_and_branch_names(self):
        self.write(".gitignore", ".env\n")
        self.git("add", ".gitignore"); self.git("commit", "-m", "ignore env")
        self.write(".env", "secret")
        result = guard.write_snapshot(self.repo, self.snapshot_path)
        self.assertEqual("SNAPSHOT-003", result.code)
        self.assertIn(".env", result.message)
        (self.repo / ".env").unlink(); self.capture()
        self.git("switch", "-c", "other")
        result = self.verify()
        self.assertEqual("GIT-003", result.code)
        self.assertIn("expected", result.message)
        self.assertIn("other", result.message)

    @pytest.mark.slow
    def test_t21_many_ignored_files_are_bounded(self):
        self.write(".gitignore", "frontend/node_modules/\n")
        self.git("add", ".gitignore"); self.git("commit", "-m", "ignore cache")
        cache = self.repo / "frontend/node_modules"; cache.mkdir(parents=True)
        for index in range(50_000):
            (cache / f"{index}.js").write_text("x")
        started = time.monotonic()
        result = guard.write_snapshot(self.repo, self.snapshot_path, ["**/node_modules/**"])
        self.assertEqual("PASS", result.status, result)
        digest = "sha256:" + guard.snapshot_digest(self.snapshot_path)
        self.assertEqual("PASS", guard.verify_scope(self.repo, self.document_scope(), self.snapshot_path, digest).status)
        self.assertLess(time.monotonic() - started, 10)

    def document_scope(self):
        return yaml.safe_load(self.manifest.read_text())["scope"]


if __name__ == "__main__":
    unittest.main()
