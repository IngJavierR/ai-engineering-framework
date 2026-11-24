"""Ignored working-artifact defaults and conservative stack detection."""

from __future__ import annotations

import subprocess
from fnmatch import fnmatch
from pathlib import Path

DEFAULTS = {
    "node": ("**/node_modules/**", "**/.angular/**", "**/dist/**", "**/coverage/**", "**/.nx/**"),
    "python": ("**/.venv/**", "**/__pycache__/**", "**/.pytest_cache/**", "**/.hypothesis/**", "**/.mypy_cache/**", "**/.ruff_cache/**", "**/.coverage", "**/htmlcov/**", "**/*.egg-info/**"),
    "gatling": ("performance/gatling/target/**",),
    "java": ("**/target/**", "**/.gradle/**", "**/build/**"),
    "universal": ("**/.env", "**/.env.local"),
}


def _git_tracked(consumer: Path) -> set[str]:
    """C1: Use git ls-files instead of disk traversal for tracked-file detection."""
    out = subprocess.check_output(["git", "-C", str(consumer), "ls-files", "-z"], text=True)
    return set(filter(None, out.split("\0")))


def _pattern_matches(path: str, pattern: str) -> bool:
    """Match a relative file path against a glob pattern that may use **."""
    normalized = path.rstrip("/")
    stripped = pattern.strip("/")
    if stripped.startswith("**/") and stripped.endswith("/**"):
        directory = stripped[3:-3]
        if f"/{directory}/" in f"/{normalized}/":
            return True
    if stripped.startswith("**/") and not stripped.endswith("/**"):
        # e.g. **/.env → match any .env at any depth
        suffix = stripped[3:]
        if normalized == suffix or normalized.endswith(f"/{suffix}"):
            return True
    return fnmatch(normalized, stripped) or fnmatch(f"{normalized}/", pattern)


def detect_stacks(consumer: Path, include_gatling: bool = False) -> set[str]:
    stacks: set[str] = {"universal"}
    files_flat = {path.name for path in consumer.rglob("*") if path.is_file() and ".git" not in path.parts}
    if "package.json" in files_flat:
        stacks.add("node")
    if any(name == "pyproject.toml" or name == "setup.py" or (name.startswith("requirements") and name.endswith(".txt")) for name in files_flat):
        stacks.add("python")
    # C3: java only when pom.xml/build.gradle is OUTSIDE performance/gatling/
    for path in consumer.rglob("*"):
        if path.is_file() and ".git" not in path.parts:
            rel = path.relative_to(consumer).as_posix()
            if "performance/gatling" not in rel and (path.name == "pom.xml" or path.name.startswith("build.gradle")):
                stacks.add("java")
                break
    if include_gatling or (consumer / "performance/gatling").is_dir():
        stacks.add("gatling")
    return stacks


def patterns_for(consumer: Path, feature_stacks: set[str]) -> list[str]:
    stacks = detect_stacks(consumer) | feature_stacks
    return sorted({pattern for stack in stacks for pattern in DEFAULTS[stack]})


def safe_patterns_for(consumer: Path, feature_stacks: set[str]) -> tuple[list[str], list[str]]:
    """C1: Use git ls-files so disk-only files (caches, .venv) never discard defaults."""
    tracked = _git_tracked(consumer)
    accepted, skipped = [], []
    for pattern in patterns_for(consumer, feature_stacks):
        matches = [path for path in tracked if _pattern_matches(path, pattern)]
        if matches:
            skipped.append(f"{pattern} (tracked: {matches[0]})")
        else:
            accepted.append(pattern)
    return accepted, skipped
