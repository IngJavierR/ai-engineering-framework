
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
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_NAME = ".ai-framework.lock.json"
FRAMEWORK_NAME = "ai-engineering-framework"
FRAMEWORK_SOURCE = (
    "https://github.com/IngJavierR/ai-engineering-framework"
)
LEGACY_VERSION = "0.2.0"
HISTORICAL_VERSION = "0.3.0"
LOCK_SCHEMA = "capability-lock/v1"

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
BASE_CAPABILITY = "java-base"
FRONTEND_CAPABILITIES = frozenset({
    "frontend-ui-design",
    "angular-ui-implementation",
    "react-ui-implementation",
})


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


def framework_config():
    return (ROOT / "framework.yaml").read_text(encoding="utf-8")


def version():
    match = re.search(
        r"^\s{2}version:\s*([^\s#]+)",
        framework_config(),
        re.MULTILINE,
    )
    if not match:
        raise ValueError("Missing framework version")
    return match.group(1).strip("\"'")


def capability_inventory():
    match = re.search(
        r"^    inventory: \|\n(?P<json>(?:^      .*\n?)*)",
        framework_config(),
        re.MULTILINE,
    )
    if not match:
        raise ValueError("Missing capability inventory")

    try:
        inventory = json.loads(textwrap.dedent(match.group("json")))
    except json.JSONDecodeError as exc:
        raise ValueError("Capability inventory is invalid") from exc

    if not isinstance(inventory, dict):
        raise ValueError("Capability inventory is invalid")
    validate_capability_inventory(inventory)
    return inventory


def validate_inventory_path(relative):
    if not isinstance(relative, str):
        raise ValueError("Capability artifact path is invalid")
    if not relative or "\\" in relative or relative.startswith("/"):
        raise ValueError(f"Unsafe capability artifact path: {relative}")

    segments = relative.split("/")
    if any(segment in {"", ".", ".."} for segment in segments):
        raise ValueError(f"Non-canonical capability artifact path: {relative}")

    relative_path = Path(relative)
    if (
        relative_path.is_absolute()
        or relative_path.as_posix() != relative
        or segments[0] != ".github"
    ):
        raise ValueError(f"Unsafe capability artifact path: {relative}")
    return relative


def validate_capability_artifacts(capability, artifacts):
    if not isinstance(artifacts, list) or not artifacts:
        raise ValueError(
            f"Capability has an invalid artifact list: {capability}"
        )
    for relative in artifacts:
        validate_inventory_path(relative)

    if capability in FRONTEND_CAPABILITIES:
        skill_root = f".github/skills/{capability}/"
        skill_file = f"{skill_root}SKILL.md"
        if skill_file not in artifacts:
            raise ValueError(
                f"Frontend capability lacks its canonical SKILL.md: "
                f"{capability}"
            )
        if any(not relative.startswith(skill_root) for relative in artifacts):
            raise ValueError(
                f"Frontend capability artifact escapes skill directory: "
                f"{capability}"
            )


def declared_local_references(skill_file):
    content = skill_file.read_text(encoding="utf-8")
    references = []
    for reference in re.findall(r"\[[^]]+\]\(([^)]+)\)", content):
        if reference.startswith(("./", "../")):
            references.append(reference)
    return tuple(references)


def validate_frontend_skill_references(capability, artifacts):
    skill_root = f".github/skills/{capability}/"
    skill_relative = f"{skill_root}SKILL.md"
    skill_file = source_path(skill_relative)
    inventory_artifacts = set(artifacts)

    for reference in declared_local_references(skill_file):
        if not reference.startswith("./"):
            raise ValueError(
                f"Skill reference escapes skill directory: {reference}"
            )
        relative = f"{skill_root}{reference[2:]}"
        validate_inventory_path(relative)
        if not relative.startswith(skill_root):
            raise ValueError(
                f"Skill reference escapes skill directory: {reference}"
            )
        if relative not in inventory_artifacts:
            raise ValueError(
                f"Skill reference is not inventoried: {reference}"
            )
        source_path(relative)


def resolve_capabilities(requested, inventory=None):
    if inventory is None:
        inventory = capability_inventory()
    if not isinstance(requested, (list, tuple)):
        raise ValueError("Requested capabilities must be a list")

    resolved = []
    artifacts = []
    seen_capabilities = set()
    visiting = set()
    seen_artifacts = set()

    def visit(capability):
        if capability in visiting:
            raise ValueError(f"Capability dependency cycle: {capability}")
        if capability in seen_capabilities:
            return
        definition = inventory.get(capability)
        if not isinstance(definition, dict):
            raise ValueError(f"Unknown capability: {capability}")
        dependencies = definition.get("dependencies")
        if not isinstance(dependencies, list):
            raise ValueError(
                f"Capability has invalid dependencies: {capability}"
            )
        visiting.add(capability)
        for dependency in dependencies:
            if not isinstance(dependency, str) or dependency not in inventory:
                raise ValueError(
                    f"Capability has unknown dependency: {capability}"
                )
            visit(dependency)
        visiting.remove(capability)

        capability_artifacts = definition.get("artifacts")
        validate_capability_artifacts(capability, capability_artifacts)
        for relative in capability_artifacts:
            if relative in seen_artifacts:
                raise ValueError(
                    f"Duplicate capability artifact path: {relative}"
                )
            seen_artifacts.add(relative)
            artifacts.append(relative)
        seen_capabilities.add(capability)
        resolved.append(capability)

    visit(BASE_CAPABILITY)
    requested_capabilities = set()
    for capability in requested:
        if not isinstance(capability, str):
            raise ValueError("Capability ID is invalid")
        if capability in requested_capabilities:
            raise ValueError(f"Duplicate requested capability: {capability}")
        requested_capabilities.add(capability)
        visit(capability)

    return tuple(resolved), tuple(artifacts)


def validate_capability_inventory(inventory=None):
    if inventory is None:
        inventory = capability_inventory()
    for capability, definition in inventory.items():
        artifacts = definition.get("artifacts") if isinstance(
            definition, dict
        ) else None
        validate_capability_artifacts(capability, artifacts)
        for relative in artifacts:
            source_path(relative)
        if capability in FRONTEND_CAPABILITIES:
            validate_frontend_skill_references(capability, artifacts)

    for capability in inventory:
        resolve_capabilities((capability,), inventory)


def frontend_capabilities(resolved):
    return tuple(
        capability for capability in resolved
        if capability in FRONTEND_CAPABILITIES
    )


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


def source_manifest(files=MANAGED_FILES):
    manifest = {}
    for relative in files:
        manifest[relative] = sha256(source_path(relative))
    return manifest


def build_lock(release, commit, files, capabilities=None):
    lock = {
        "framework": FRAMEWORK_NAME,
        "version": release,
        "source": FRAMEWORK_SOURCE,
        "commit": commit,
        "files": files,
    }
    if capabilities is not None:
        lock["schema"] = LOCK_SCHEMA
        lock["capabilities"] = list(capabilities)
    return lock


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
    legacy_keys = {"framework", "version", "source", "commit", "files"}
    current_keys = legacy_keys | {"schema", "capabilities"}
    if set(lock) != legacy_keys and set(lock) != current_keys:
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

    seen_files = set()
    for relative, digest in lock["files"].items():
        validate_inventory_path(relative)
        if relative in seen_files or not is_sha256(digest):
            raise ValueError("Existing framework lock has an invalid manifest")
        seen_files.add(relative)

    if set(lock) == current_keys:
        if lock["schema"] != LOCK_SCHEMA:
            raise ValueError("Existing framework lock has an unknown schema")
        capabilities = lock["capabilities"]
        if (
            not isinstance(capabilities, list)
            or not capabilities
            or any(
                not isinstance(capability, str) or not capability
                for capability in capabilities
            )
        ):
            raise ValueError("Existing framework lock has invalid capabilities")
        if len(capabilities) != len(set(capabilities)):
            raise ValueError("Existing framework lock has duplicate capabilities")
        try:
            resolved, files = resolve_capabilities(capabilities[1:])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Existing framework lock has invalid capabilities"
            ) from exc
        if tuple(capabilities) != resolved or list(lock["files"]) != list(files):
            raise ValueError("Existing framework lock is internally inconsistent")


def is_legacy_lock(lock):
    return (
        set(lock) == {"framework", "version", "source", "commit", "files"}
        and lock["version"] == LEGACY_VERSION
        and list(lock["files"]) == LEGACY_MANAGED_FILES
    )


def is_historical_lock(lock):
    return (
        set(lock) == {"framework", "version", "source", "commit", "files"}
        and lock["version"] == HISTORICAL_VERSION
        and list(lock["files"]) == MANAGED_FILES
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


def historical_file_content(commit, relative):
    try:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "show", f"{commit}:{relative}"]
        )
    except subprocess.CalledProcessError as exc:
        raise ValueError(
            "Cannot verify legacy source revision; perform a manual upgrade"
        ) from exc


def historical_inventory(config):
    match = re.search(
        r"^    inventory: \|\n(?P<json>(?:^      .*\n?)*)",
        config,
        re.MULTILINE,
    )
    if not match:
        raise ValueError("Historical capability inventory is unavailable")
    try:
        inventory = json.loads(textwrap.dedent(match.group("json")))
    except json.JSONDecodeError as exc:
        raise ValueError("Historical capability inventory is invalid") from exc
    if not isinstance(inventory, dict):
        raise ValueError("Historical capability inventory is invalid")
    return inventory


def validate_historical_source(lock):
    config = historical_file_content(lock["commit"], "framework.yaml").decode(
        "utf-8"
    )
    name_match = re.search(
        r"^  name:\s*([^\s#]+)", config, re.MULTILINE
    )
    version_match = re.search(
        r"^  version:\s*([^\s#]+)", config, re.MULTILINE
    )
    if (
        name_match is None
        or name_match.group(1).strip("\"'") != FRAMEWORK_NAME
        or version_match is None
        or version_match.group(1).strip("\"'") != lock["version"]
    ):
        raise ValueError(
            "Historical framework identity does not match the lock"
        )

    for relative, expected_digest in lock["files"].items():
        content = historical_file_content(lock["commit"], relative)
        if hashlib.sha256(content).hexdigest() != expected_digest:
            raise ValueError(
                "Historical lock does not match its source revision"
            )

    if lock.get("schema") == LOCK_SCHEMA:
        inventory = historical_inventory(config)
        try:
            resolved, files = resolve_capabilities(
                lock["capabilities"][1:], inventory
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "Historical lock capabilities are invalid"
            ) from exc
        if (
            tuple(lock["capabilities"]) != resolved
            or list(lock["files"]) != list(files)
        ):
            raise ValueError(
                "Historical lock does not match its capability inventory"
            )


def validate_new_file_conflicts(target, existing_files, files):
    for relative in files:
        if relative in existing_files:
            continue
        destination = destination_path(target, relative)
        if path_lexists(destination):
            raise ValueError(
                f"Conflict: unmanaged destination exists: {relative}"
            )


def prepare_staged_files(staging, manifest, lock):
    staged_files = {}
    for relative in manifest:
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
        for relative in staged_files:
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


def install(target, dry_run=False, upgrade=False, capabilities=()):
    resolved, resolved_files = resolve_capabilities(capabilities)
    target = validate_target(target)

    if git("status", "--porcelain"):
        raise ValueError("Framework source has uncommitted changes")

    commit = git("rev-parse", "HEAD")
    release = version()
    files = source_manifest(resolved_files)
    lock = build_lock(release, commit, files, resolved)
    lock_path = target / LOCK_NAME
    replace_files = set()
    scenario = "clean installation"

    if path_lexists(lock_path):
        existing = load_lock(lock_path)
        validate_lock(existing)
        if existing != lock:
            if not upgrade:
                raise ValueError(
                    "Existing framework lock differs; "
                    "use --upgrade after reviewing the change"
                )
            if not (is_legacy_lock(existing) or is_historical_lock(existing)):
                if existing.get("schema") != LOCK_SCHEMA:
                    raise ValueError(
                        "Existing framework lock is not a supported format; "
                        "perform a manual upgrade"
                    )
                existing_capabilities = tuple(existing["capabilities"])
                if not set(existing_capabilities).issubset(resolved):
                    raise ValueError(
                        "Capability removal is BLOCKED during upgrade"
                    )
            validate_historical_source(existing)
            validate_local_manifest(target, existing["files"])
            if not set(existing["files"]).issubset(files):
                raise ValueError(
                    "Artifact removal is BLOCKED during upgrade"
                )
            validate_new_file_conflicts(target, existing["files"], files)
            replace_files = set(existing["files"])
            scenario = "upgrade"
        else:
            validate_local_manifest(target, existing["files"])
            scenario = "matching installation"
    else:
        if upgrade:
            raise ValueError("Cannot upgrade without an existing framework lock")
        validate_new_file_conflicts(target, {}, files)

    print("Requested capabilities: " + ", ".join(capabilities or ("none",)))
    print("Resolved capabilities: " + ", ".join(resolved))
    print("Resolved files:")
    for relative in resolved_files:
        print(f"  {relative}")
    print(f"Framework version: {release}")
    print(f"Source commit: {commit}")
    print(f"Destination: {target}")

    if dry_run:
        print(f"DRY RUN: {scenario} would be performed")
        return

    if scenario == "matching installation":
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
        help="Upgrade a verified v0.2.0, v0.3.0, or capability-lock installation",
    )
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help=(
            "Resolve an opt-in capability. Frontend capability installation "
            "is blocked until B.4B.2."
        ),
    )
    args = parser.parse_args()

    try:
        install(
            args.target,
            args.dry_run,
            args.upgrade,
            args.capability,
        )
    except (
        ValueError,
        OSError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
