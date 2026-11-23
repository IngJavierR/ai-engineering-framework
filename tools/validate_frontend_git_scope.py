#!/usr/bin/env python3
"""Read-only Git scope guard for M2 frontend consumer repositories."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from fnmatch import fnmatch
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
STRUCTURAL_PATH = ROOT / "tools" / "validate_frontend_contracts.py"
SPEC = importlib.util.spec_from_file_location("frontend_structural_validator", STRUCTURAL_PATH)
structural = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = structural
assert SPEC.loader is not None
SPEC.loader.exec_module(structural)

SNAPSHOT_VERSION = "frontend-git-scope-snapshot/v1"


@dataclass(frozen=True)
class GuardResult:
    status: str
    code: str
    message: str

    def format(self) -> str:
        return f"{self.status} {self.code}: {self.message}"


def run_git(repo: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), *args], text=True, stderr=subprocess.STDOUT
    )


def git_error(error: subprocess.CalledProcessError) -> str:
    command = " ".join(str(item) for item in error.cmd)
    return f"{command}: {(error.output or '').strip() or 'command failed'}"


def is_git_repo(repo: Path) -> bool:
    try:
        return run_git(repo, "rev-parse", "--is-inside-work-tree").strip() == "true"
    except (OSError, subprocess.CalledProcessError):
        return False


def sha256(path: Path) -> str | None:
    if not path.is_file() or path.is_symlink():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def file_type(path: Path) -> str:
    if path.is_symlink():
        return "symlink"
    if path.is_dir():
        return "directory"
    if path.is_file():
        return "regular-file"
    return "other"


def tracked_files(repo: Path) -> dict[str, dict[str, str | None]]:
    files: dict[str, dict[str, str | None]] = {}
    for relative in run_git(repo, "ls-files", "-z").split("\0"):
        if not relative:
            continue
        path = repo / relative
        files[relative] = {"type": file_type(path), "sha256": sha256(path)}
    return files


def porcelain(repo: Path) -> list[dict[str, str]]:
    records = run_git(repo, "status", "--porcelain=v1", "-z", "--untracked-files=all").split("\0")
    changes: list[dict[str, str]] = []
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        status, path = record[:2], record[3:]
        entry = {"status": status, "path": path}
        if status[0] in "RC" and index < len(records):
            entry["from"] = records[index]
            index += 1
        changes.append(entry)
    return changes


def matches_ignored_path(path: str, patterns: list[str]) -> bool:
    normalized = path.rstrip("/")
    for pattern in patterns:
        stripped = pattern.strip("/")
        if stripped.startswith("**/") and stripped.endswith("/**"):
            directory = stripped[3:-3]
            if normalized == directory or normalized.endswith(f"/{directory}") or f"/{directory}/" in f"/{normalized}/":
                return True
        if fnmatch(normalized, stripped) or fnmatch(f"{normalized}/", pattern):
            return True
    return False


def validate_ignored_work_paths(repo: Path, patterns: Any) -> GuardResult | None:
    if patterns is None:
        return None
    if not isinstance(patterns, list):
        return GuardResult("BLOCKED", "SCOPE-IGN-001", "ignoredWorkPaths must be a list")
    tracked = set(filter(None, run_git(repo, "ls-files", "-z").split("\0")))
    for pattern in patterns:
        if not isinstance(pattern, str) or not pattern or pattern in {"**", "*", "/"} or pattern.startswith("/") or ".." in pattern.split("/") or "\\" in pattern:
            return GuardResult("BLOCKED", "SCOPE-IGN-001", f"invalid ignoredWorkPaths pattern: {pattern!r}")
        if any(fnmatch(path, pattern) for path in tracked):
            return GuardResult("BLOCKED", "SCOPE-IGN-001", f"ignoredWorkPaths matches tracked file: {pattern}")
    return None


def filtered_ignored(repo: Path, patterns: list[str]) -> tuple[list[str], GuardResult | None]:
    ignored = sorted(item for item in run_git(repo, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").split("\0") if item)
    for path in ignored:
        if matches_ignored_path(path, patterns):
            try:
                subprocess.check_output(["git", "-C", str(repo), "check-ignore", "-q", "--", path], stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError:
                return [], GuardResult("BLOCKED", "SCOPE-IGN-001", f"ignoredWorkPaths match is not Git-ignored: {path}")
    return [path for path in ignored if not matches_ignored_path(path, patterns)], None


def snapshot(repo: Path, ignored_work_paths: list[str] | None = None) -> tuple[dict[str, Any] | None, GuardResult | None]:
    if not repo.is_dir() or not is_git_repo(repo):
        return None, GuardResult("BLOCKED", "GIT-001", "repository is missing or is not a Git work tree")
    try:
        head = run_git(repo, "rev-parse", "HEAD").strip()
        branch = run_git(repo, "symbolic-ref", "--quiet", "--short", "HEAD").strip()
        index_tree = hashlib.sha256(
            run_git(repo, "ls-files", "--stage", "-z").encode("utf-8")
        ).hexdigest()
        changes = porcelain(repo)
    except subprocess.CalledProcessError as exc:
        message = "detached HEAD; checkout a branch before PREPARE" if "symbolic-ref" in " ".join(exc.cmd) else git_error(exc)
        return None, GuardResult("BLOCKED", "GIT-002", message)
    patterns = ignored_work_paths or []
    problem = validate_ignored_work_paths(repo, patterns)
    if problem:
        return None, problem
    ignored, problem = filtered_ignored(repo, patterns)
    if problem:
        return None, problem
    return {
        "snapshotVersion": SNAPSHOT_VERSION,
        "head": head,
        "branch": branch,
        "indexTree": index_tree,
        "tracked": tracked_files(repo),
        "porcelain": changes,
        "ignored": ignored,
        "ignoredWorkPaths": patterns,
    }, None


def load_manifest(path: Path) -> tuple[dict[str, Any] | None, GuardResult | None]:
    errors = structural.validate_document(path, "frontend-ui-input/v1")
    if errors:
        return None, GuardResult("BLOCKED", "SCOPE-001", errors[0].message)
    document, errors = structural._load_yaml(path)
    if errors or not isinstance(document, dict):
        return None, GuardResult("BLOCKED", "SCOPE-002", "manifest cannot be read")
    return document, None


def scope_match(path: str, rule: dict[str, str]) -> bool:
    target = rule["path"]
    if rule["kind"] == "file":
        return path == target
    return path == target or path.startswith(target + "/")


def allowed(path: str, scope: dict[str, Any]) -> bool:
    if any(scope_match(path, rule) for rule in scope["protectedPaths"]):
        return False
    return any(scope_match(path, rule) for rule in scope["allowedPaths"])


def canonical_path(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and not value.startswith("/") and "\\" not in value and "//" not in value and all(part not in {"", ".", ".."} for part in value.split("/"))


def validate_snapshot(snapshot_data: Any) -> GuardResult | None:
    if not isinstance(snapshot_data, dict) or snapshot_data.get("snapshotVersion") != SNAPSHOT_VERSION:
        return GuardResult("BLOCKED", "SNAPSHOT-001", "snapshot is missing or has an unknown format")
    required = {"head", "branch", "indexTree", "tracked", "porcelain", "ignored"}
    valid_fields = (required | {"snapshotVersion"}, required | {"snapshotVersion", "ignoredWorkPaths"})
    if set(snapshot_data) not in valid_fields:
        return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot has unexpected or missing fields")
    if not all(isinstance(snapshot_data[key], str) for key in ("head", "branch", "indexTree")):
        return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot Git fields must be strings")
    if not isinstance(snapshot_data["tracked"], dict) or not isinstance(snapshot_data["porcelain"], list) or not isinstance(snapshot_data["ignored"], list):
        return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot tracked, porcelain, and ignored fields have invalid types")
    for path, entry in snapshot_data["tracked"].items():
        if not canonical_path(path) or not isinstance(entry, dict) or set(entry) != {"type", "sha256"}:
            return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot tracked entry is invalid")
        entry_type = entry["type"]
        entry_hash = entry["sha256"]
        if not isinstance(entry_type, str) or entry_type not in {"regular-file", "directory", "symlink", "submodule", "other"}:
            return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot tracked entry has an invalid type")
        if entry_type == "regular-file":
            if not isinstance(entry_hash, str) or len(entry_hash) != 64 or any(character not in "0123456789abcdef" for character in entry_hash):
                return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot regular file hash is invalid")
        elif entry_hash is not None:
            return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot non-regular file hash must be null")
    for entry in snapshot_data["porcelain"]:
        if not isinstance(entry, dict) or not isinstance(entry.get("status"), str) or not canonical_path(entry.get("path")):
            return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot porcelain entry is invalid")
    if not all(canonical_path(item) for item in snapshot_data["ignored"]):
        return GuardResult("BLOCKED", "SNAPSHOT-002", "snapshot ignored entry is invalid")
    if snapshot_data["porcelain"] or snapshot_data["ignored"]:
        return GuardResult("BLOCKED", "SNAPSHOT-003", "initial repository contains pre-existing changes or ignored files")
    return None


def snapshot_digest(snapshot_path: Path) -> str:
    return hashlib.sha256(snapshot_path.read_bytes()).hexdigest()


def write_snapshot(repo: Path, destination: Path, ignored_work_paths: list[str] | None = None) -> GuardResult:
    state, problem = snapshot(repo, ignored_work_paths)
    if problem:
        return problem
    if state["porcelain"] or state["ignored"]:
        return GuardResult("BLOCKED", "SNAPSHOT-003", "repository is not clean at capture")
    if destination.resolve().is_relative_to(repo.resolve()):
        return GuardResult("BLOCKED", "SNAPSHOT-004", "snapshot must be outside the consumer repository")
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except OSError as exc:
        return GuardResult("BLOCKED", "SNAPSHOT-005", str(exc))
    return GuardResult("PASS", "SNAPSHOT-000", f"snapshot captured; external digest sha256:{snapshot_digest(destination)}")


def verify(repo: Path, manifest_path: Path, snapshot_path: Path, expected_snapshot_sha256: str | None = None) -> GuardResult:
    manifest, problem = load_manifest(manifest_path)
    if problem:
        return problem
    return verify_scope(repo, manifest["scope"], snapshot_path, expected_snapshot_sha256)


def verify_scope(repo: Path, scope: dict[str, Any], snapshot_path: Path, expected_snapshot_sha256: str | None = None) -> GuardResult:
    if expected_snapshot_sha256 is None:
        return GuardResult("BLOCKED", "SNAPSHOT-006", "an external expected snapshot SHA-256 is required")
    if not expected_snapshot_sha256.startswith("sha256:") or len(expected_snapshot_sha256) != 71:
        return GuardResult("BLOCKED", "SNAPSHOT-006", "expected snapshot SHA-256 has invalid format")
    try:
        actual_digest = f"sha256:{snapshot_digest(snapshot_path)}"
        snapshot_data = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return GuardResult("BLOCKED", "SNAPSHOT-001", f"cannot read snapshot: {exc}")
    if actual_digest != expected_snapshot_sha256:
        return GuardResult("BLOCKED", "SNAPSHOT-007", "snapshot digest differs from the external expected digest")
    problem = validate_snapshot(snapshot_data)
    if problem:
        return problem
    patterns = snapshot_data.get("ignoredWorkPaths", scope.get("ignoredWorkPaths", []))
    problem = validate_ignored_work_paths(repo, patterns)
    if problem:
        return problem
    current, problem = snapshot(repo, patterns)
    if problem:
        return problem
    if current["branch"] != snapshot_data["branch"]:
        return GuardResult("BLOCKED", "GIT-003", "branch changed since snapshot")
    if subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor", snapshot_data["head"], current["head"]], capture_output=True).returncode:
        return GuardResult("BLOCKED", "GIT-003", "snapshot base is no longer an ancestor of HEAD")
    if current["ignored"] != snapshot_data["ignored"]:
        return GuardResult("BLOCKED", "GIT-005", "ignored path inventory changed since snapshot; ignored content is not monitored")
    before = snapshot_data["tracked"]
    after = current["tracked"]
    changes: list[tuple[str, str]] = []
    for path in sorted(set(before) | set(after)):
        if path not in before:
            changes.append(("created", path))
        elif path not in after:
            changes.append(("deleted", path))
        elif after[path]["type"] == "other":
            changes.append(("deleted", path))
        elif before[path] != after[path]:
            changes.append(("modified", path))
    for entry in current["porcelain"]:
        if entry["status"] == "??":
            changes.append(("created", entry["path"]))
        if "from" in entry:
            changes.append(("renamed-from", entry["from"]))
            changes.append(("renamed-to", entry["path"]))
    try:
        records = run_git(repo, "diff", "--name-status", "-z", f"{snapshot_data['head']}..{current['head']}").split("\0")
    except subprocess.CalledProcessError as error:
        return GuardResult("BLOCKED", "GIT-002", git_error(error))
    index = 0
    while index < len(records):
        status = records[index]
        index += 1
        if not status:
            continue
        if index >= len(records):
            return GuardResult("BLOCKED", "GIT-002", "invalid Git diff record")
        path = records[index]
        index += 1
        if status.startswith(("R", "C")):
            if index >= len(records):
                return GuardResult("BLOCKED", "GIT-002", "invalid Git rename record")
            changes.extend([("renamed-from", path), ("renamed-to", records[index])])
            index += 1
        else:
            changes.append(({"A": "created", "D": "deleted"}.get(status[0], "modified"), path))
    if not changes:
        return GuardResult("PASS", "SCOPE-000", "no changes detected")
    renamed_sources = {path for kind, path in changes if kind == "renamed-from"}
    for kind, path in changes:
        if kind == "deleted" and path not in renamed_sources and not scope.get("deletionPolicy", {}).get("allowed", False):
            return GuardResult("FAIL", "SCOPE-012", f"deletion is not allowed: {path}")
        if not allowed(path, scope):
            protected = any(scope_match(path, rule) for rule in scope["protectedPaths"])
            return GuardResult("FAIL", "SCOPE-009" if protected else "SCOPE-008", f"change outside authorized scope: {path}")
        current_path = repo / path
        if kind != "deleted" and file_type(current_path) in {"symlink", "submodule"}:
            return GuardResult("FAIL", "SCOPE-011", f"forbidden type change: {path}")
        if kind != "deleted":
            current_component = current_path
            while current_component != repo.parent:
                if current_component.is_symlink():
                    return GuardResult("FAIL", "SCOPE-011", f"symlink in changed path: {path}")
                current_component = current_component.parent
    return GuardResult("PASS", "SCOPE-000", "observable changes comply with scope policy; authorship and intermediate concurrent changes are not certified")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Capture or verify observable Git scope changes; it does not certify authorship or uninterrupted execution.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--capture", action="store_true")
    group.add_argument("--verify", action="store_true")
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--snapshot", required=True, type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--expected-snapshot-sha256")
    args = parser.parse_args(argv)
    if args.verify and (args.manifest is None or args.expected_snapshot_sha256 is None):
        parser.error("--manifest and --expected-snapshot-sha256 are required with --verify")
    result = write_snapshot(args.repository, args.snapshot) if args.capture else verify(args.repository, args.manifest, args.snapshot, args.expected_snapshot_sha256)
    print(result.format())
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
