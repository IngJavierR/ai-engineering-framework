
#!/usr/bin/env python3
"""Minimal installer for AI Engineering Framework."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCK_NAME = ".ai-framework.lock.json"

MANAGED_FILES = [
    ".github/instructions/java.instructions.md",
]


def git(*args):
    return subprocess.check_output(
        ["git", "-C", str(ROOT), *args],
        text=True,
    ).strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


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


def install(target, dry_run=False):
    target = target.resolve()

    if not target.is_dir():
        raise ValueError("Target directory does not exist")

    if not (target / ".git").exists():
        raise ValueError("Target must be a Git repository")

    if target == ROOT:
        raise ValueError("Cannot install into framework source")

    if git("status", "--porcelain"):
        raise ValueError(
            "Framework source has uncommitted changes"
        )

    commit = git("rev-parse", "HEAD")
    release = version()

    files = {}

    # Validate all files before writing anything.
    for relative in MANAGED_FILES:
        source = ROOT / relative
        destination = target / relative

        if not source.is_file():
            raise ValueError(f"Missing source: {relative}")

        digest = sha256(source)

        if destination.exists():
            if not destination.is_file():
                raise ValueError(
                    f"Destination is not a file: {relative}"
                )
            if sha256(destination) != digest:
                raise ValueError(
                    f"Conflict: {relative} already differs"
                )

        files[relative] = digest

    lock = {
        "framework": "ai-engineering-framework",
        "version": release,
        "source": "https://github.com/IngJavierR/"
                  "ai-engineering-framework",
        "commit": commit,
        "files": files,
    }

    lock_path = target / LOCK_NAME

    if lock_path.exists():
        try:
            existing = json.loads(
                lock_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise ValueError(
                "Existing framework lock is invalid"
            ) from exc

        if existing != lock:
            raise ValueError(
                "Existing framework lock differs; "
                "automatic upgrade is not supported"
            )

    print(f"Framework version: {release}")
    print(f"Source commit: {commit}")
    print(f"Destination: {target}")

    if dry_run:
        print("DRY RUN: no files modified")
        return

    for relative in MANAGED_FILES:
        source = ROOT / relative
        destination = target / relative

        destination.parent.mkdir(
            parents=True, exist_ok=True
        )

        if not destination.exists():
            shutil.copy2(source, destination)
            print(f"Installed: {relative}")
        else:
            print(f"Already installed: {relative}")

    if not lock_path.exists():
        lock_path.write_text(
            json.dumps(lock, indent=2) + "\n",
            encoding="utf-8",
        )

    print("Installation completed")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--target", required=True, type=Path
    )
    parser.add_argument(
        "--dry-run", action="store_true"
    )
    args = parser.parse_args()

    try:
        install(args.target, args.dry_run)
    except (
        ValueError,
        OSError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
