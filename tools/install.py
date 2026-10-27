
#!/usr/bin/env python3
"""Minimal installer for AI Engineering Framework."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_NAME = ".ai-framework.lock.json"
FRAMEWORK_NAME = "ai-engineering-framework"
FRAMEWORK_SOURCE = (
    "https://github.com/IngJavierR/ai-engineering-framework"
)
LEGACY_VERSION = "0.2.0"

MANAGED_FILES = [
    ".github/instructions/java.instructions.md",
    ".github/instructions/openapi-ddd.instructions.md",
    ".github/instructions/liquibase.instructions.md",
    ".github/skills/openapi-to-ddd/SKILL.md",
    ".github/skills/openapi-to-ddd/references/ddd-structure.md",
    ".github/skills/openapi-to-ddd/references/"
    "contract-compatibility.md",
    ".github/skills/liquibase-versioning/SKILL.md",
    ".github/skills/liquibase-versioning/references/"
    "xml-conventions.md",
]
LEGACY_MANAGED_FILES = [
    ".github/instructions/java.instructions.md",
]


class RecoveryError(OSError):
    """Reports an operation failure whose rollback was incomplete."""


def git_at(directory, *args):
    return subprocess.check_output(
        ["git", "-C", str(directory), *args],
        text=True,
    ).strip()


def git(*args):
    return git_at(ROOT, *args)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_sha256(value):
    return isinstance(value, str) and re.fullmatch(
        r"[0-9a-f]{64}", value
    ) is not None


def version():
    config = (ROOT / "framework.yaml").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"^\s{2}version:\s*([^\s#]+)",
        config,
        re.MULTILINE,
    )
    if not match:
        raise ValueError("Missing framework version")
    return match.group(1).strip("\"'")


def absolute_path(path):
    return Path(os.path.abspath(path))


def path_lexists(path):
    return os.path.lexists(path)


def remove_regular_file_or_symlink(path):
    if not path_lexists(path):
        return
    if path.is_symlink() or path.is_file():
        path.unlink()
        return
    raise OSError(f"Expected a file or symlink: {path}")


def reject_symlink_ancestors(path):
    # The target path and every existing ancestor must be real
    # directories so managed paths cannot escape through a symlink.
    for component in (path, *path.parents):
        if component.is_symlink():
            raise ValueError(
                "Target directory path must not contain a symlink: "
                f"{component}"
            )


def validate_target(target):
    target = absolute_path(target)

    reject_symlink_ancestors(target)

    if not target.is_dir():
        raise ValueError("Target directory does not exist")

    if not (target / ".git").exists():
        raise ValueError("Target must be a Git repository")

    if target == ROOT:
        raise ValueError("Cannot install into framework source")

    try:
        if git_at(target, "rev-parse", "--is-inside-work-tree") != "true":
            raise ValueError("Target must be a Git work tree")
    except subprocess.CalledProcessError as exc:
        raise ValueError("Target must be a valid Git repository") from exc

    return target


def destination_path(target, relative):
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"Unsafe managed path: {relative}")

    current = target
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"Symlink is not allowed: {relative}")

    destination = target / relative_path
    if os.path.commonpath([str(target), str(destination)]) != str(target):
        raise ValueError(f"Managed path escapes target: {relative}")

    return destination


def source_path(relative):
    source = ROOT / relative
    if not source.is_file() or source.is_symlink():
        raise ValueError(f"Missing regular source file: {relative}")
    return source


def source_manifest():
    manifest = {}
    for relative in MANAGED_FILES:
        manifest[relative] = sha256(source_path(relative))
    return manifest


def build_lock(release, commit, files):
    return {
        "framework": FRAMEWORK_NAME,
        "version": release,
        "source": FRAMEWORK_SOURCE,
        "commit": commit,
        "files": files,
    }


def load_lock(lock_path):
    if lock_path.is_symlink():
        raise ValueError("Existing framework lock must not be a symlink")
    if not lock_path.is_file():
        raise ValueError("Existing framework lock must be a regular file")

    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("Existing framework lock is invalid") from exc

    if not isinstance(lock, dict):
        raise ValueError("Existing framework lock is invalid")

    return lock


def validate_lock(lock):
    expected_keys = {"framework", "version", "source", "commit", "files"}
    if set(lock) != expected_keys:
        raise ValueError("Existing framework lock has an unknown schema")

    if lock["framework"] != FRAMEWORK_NAME:
        raise ValueError("Existing framework lock has an unknown framework")

    if lock["source"] != FRAMEWORK_SOURCE:
        raise ValueError("Existing framework lock has an unknown source")

    if not isinstance(lock["version"], str):
        raise ValueError("Existing framework lock has an invalid version")

    if not isinstance(lock["commit"], str) or re.fullmatch(
        r"[0-9a-f]{40}", lock["commit"]
    ) is None:
        raise ValueError("Existing framework lock has an invalid commit")

    if not isinstance(lock["files"], dict):
        raise ValueError("Existing framework lock has an invalid manifest")

    for relative, digest in lock["files"].items():
        if not isinstance(relative, str) or not is_sha256(digest):
            raise ValueError("Existing framework lock has an invalid manifest")


def is_legacy_lock(lock):
    return (
        lock["version"] == LEGACY_VERSION
        and list(lock["files"]) == LEGACY_MANAGED_FILES
    )


def validate_local_manifest(target, files):
    for relative, expected_digest in files.items():
        destination = destination_path(target, relative)
        if not destination.exists() or not destination.is_file():
            raise ValueError(f"Managed file is missing: {relative}")
        if sha256(destination) != expected_digest:
            raise ValueError(
                f"Managed file was modified locally: {relative}"
            )


def validate_legacy_source(lock):
    for relative, expected_digest in lock["files"].items():
        try:
            content = subprocess.check_output(
                [
                    "git",
                    "-C",
                    str(ROOT),
                    "show",
                    f"{lock['commit']}:{relative}",
                ]
            )
        except subprocess.CalledProcessError as exc:
            raise ValueError(
                "Cannot verify legacy source revision; "
                "perform a manual upgrade"
            ) from exc

        if hashlib.sha256(content).hexdigest() != expected_digest:
            raise ValueError(
                "Legacy lock does not match its source revision; "
                "perform a manual upgrade"
            )


def validate_new_file_conflicts(target, existing_files):
    for relative in MANAGED_FILES:
        if relative in existing_files:
            continue
        destination = destination_path(target, relative)
        if path_lexists(destination):
            raise ValueError(
                f"Conflict: unmanaged destination exists: {relative}"
            )


def prepare_staged_files(staging, manifest, lock):
    staged_files = {}
    for relative in MANAGED_FILES:
        source = source_path(relative)
        staged = staging / relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, staged)
        if sha256(staged) != manifest[relative]:
            raise OSError(f"Staged file digest differs: {relative}")
        staged_files[relative] = staged

    staged_lock = staging / LOCK_NAME
    staged_lock.write_text(
        json.dumps(lock, indent=2) + "\n",
        encoding="utf-8",
    )
    return staged_files, staged_lock


def restore_files(created, backups, lock_path, lock_backup, lock_replaced):
    failures = []

    try:
        if lock_replaced:
            remove_regular_file_or_symlink(lock_path)
            if lock_backup is not None and path_lexists(lock_backup):
                os.replace(lock_backup, lock_path)
    except OSError as exc:
        failures.append(f"lock: {exc}")

    for destination in reversed(created):
        try:
            remove_regular_file_or_symlink(destination)
        except OSError as exc:
            failures.append(f"created file {destination}: {exc}")

    for destination, backup in reversed(list(backups.items())):
        try:
            remove_regular_file_or_symlink(destination)
            if path_lexists(backup):
                os.replace(backup, destination)
        except OSError as exc:
            failures.append(f"backup {backup}: {exc}")

    return failures


def cleanup_backups(backups, lock_backup):
    failures = []
    for backup in backups.values():
        try:
            remove_regular_file_or_symlink(backup)
        except OSError as exc:
            failures.append(str(exc))
    if lock_backup is not None:
        try:
            remove_regular_file_or_symlink(lock_backup)
        except OSError as exc:
            failures.append(str(exc))
    if failures:
        raise OSError(
            "Installation completed but backup cleanup failed: "
            + "; ".join(failures)
        )


def replace_staged_files(
    target, staged_files, staged_lock, replace_files, replace_lock
):
    backups = {}
    created = []
    lock_path = target / LOCK_NAME
    lock_backup = None
    lock_replaced = False

    try:
        for relative in MANAGED_FILES:
            destination = destination_path(target, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination = destination_path(target, relative)
            if path_lexists(destination):
                if destination.is_symlink():
                    raise OSError(f"Symlink is not allowed: {relative}")
                if not destination.is_file():
                    raise OSError(
                        "Managed destination must be a regular file: "
                        f"{relative}"
                    )
                if relative not in replace_files:
                    raise OSError(
                        "Unmanaged destination appeared during "
                        f"installation: {relative}"
                    )
                backup = destination.with_name(
                    f".{destination.name}.ai-framework-backup"
                )
                if path_lexists(backup):
                    raise OSError(f"Backup path exists: {relative}")
                os.replace(destination, backup)
                backups[destination] = backup
            else:
                created.append(destination)
            os.replace(staged_files[relative], destination)

        if path_lexists(lock_path):
            if lock_path.is_symlink():
                raise OSError("Framework lock must not be a symlink")
            if not lock_path.is_file():
                raise OSError("Framework lock must be a regular file")
            if not replace_lock:
                raise OSError(
                    "Unmanaged framework lock appeared during installation"
                )
            lock_backup = lock_path.with_name(
                f".{LOCK_NAME}.ai-framework-backup"
            )
            if path_lexists(lock_backup):
                raise OSError("Framework lock backup path exists")
            os.replace(lock_path, lock_backup)
            lock_replaced = True

        os.replace(staged_lock, lock_path)
    except OSError as exc:
        failures = restore_files(
            created, backups, lock_path, lock_backup, lock_replaced
        )
        if failures:
            raise RecoveryError(
                "Installation failed: "
                f"{exc}. Rollback was incomplete; recoverable backups "
                "were preserved. Recovery failures: "
                + "; ".join(failures)
            ) from exc
        raise
    else:
        cleanup_backups(backups, lock_backup)


def install(target, dry_run=False, upgrade=False):
    target = validate_target(target)

    if git("status", "--porcelain"):
        raise ValueError(
            "Framework source has uncommitted changes"
        )

    commit = git("rev-parse", "HEAD")
    release = version()
    files = source_manifest()
    lock = build_lock(release, commit, files)
    lock_path = target / LOCK_NAME
    replace_files = set()

    if path_lexists(lock_path):
        existing = load_lock(lock_path)
        validate_lock(existing)
        if existing != lock:
            if not upgrade:
                raise ValueError(
                    "Existing framework lock differs; "
                    "use --upgrade after reviewing the change"
                )
            if not is_legacy_lock(existing):
                raise ValueError(
                    "Existing framework lock is not a supported legacy "
                    "format; perform a manual upgrade"
                )
            validate_local_manifest(target, existing["files"])
            validate_legacy_source(existing)
            validate_new_file_conflicts(target, existing["files"])
            replace_files = set(existing["files"])
        else:
            validate_local_manifest(target, existing["files"])
    else:
        if upgrade:
            raise ValueError(
                "Cannot upgrade without an existing framework lock"
            )
        validate_new_file_conflicts(target, {})

    print(f"Framework version: {release}")
    print(f"Source commit: {commit}")
    print(f"Destination: {target}")

    if dry_run:
        if lock_path.exists() and not replace_files:
            print("Already installed: matching lock and files")
        elif replace_files:
            print("DRY RUN: legacy installation would be upgraded")
        else:
            print("DRY RUN: clean installation would be created")
        return

    if lock_path.exists() and not replace_files:
        print("Already installed: matching lock and files")
        return

    staging = Path(tempfile.mkdtemp(
        prefix=".ai-framework-stage-",
        dir=target,
    ))
    try:
        staged_files, staged_lock = prepare_staged_files(
            staging, files, lock
        )
        replace_staged_files(
            target,
            staged_files,
            staged_lock,
            replace_files,
            path_lexists(lock_path),
        )
    finally:
        shutil.rmtree(staging, ignore_errors=True)

    if replace_files:
        print("Upgrade completed")
    else:
        print("Installation completed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target", required=True, type=Path
    )
    parser.add_argument(
        "--dry-run", action="store_true"
    )
    parser.add_argument(
        "--upgrade", action="store_true",
        help="Upgrade a verified legacy v0.2.0 installation",
    )
    args = parser.parse_args()

    try:
        install(args.target, args.dry_run, args.upgrade)
    except (
        ValueError,
        OSError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
