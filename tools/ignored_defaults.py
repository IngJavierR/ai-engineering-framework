"""Ignored working-artifact defaults and conservative stack detection."""

from __future__ import annotations

from pathlib import Path
from fnmatch import fnmatch

DEFAULTS = {
    "node": ("**/node_modules/**", "**/.angular/**", "**/dist/**", "**/coverage/**", "**/.nx/**"),
    "python": ("**/.venv/**", "**/__pycache__/**", "**/.pytest_cache/**", "**/.hypothesis/**", "**/.mypy_cache/**", "**/.ruff_cache/**", "**/.coverage", "**/htmlcov/**", "**/*.egg-info/**"),
    "gatling": ("performance/gatling/target/**",),
    "java": ("**/target/**", "**/.gradle/**", "**/build/**"),
}


def detect_stacks(consumer: Path, include_gatling: bool = False) -> set[str]:
    files = {path.name for path in consumer.rglob("*") if path.is_file() and ".git" not in path.parts}
    stacks: set[str] = set()
    if "package.json" in files:
        stacks.add("node")
    if any(name == "pyproject.toml" or name == "setup.py" or name.startswith("requirements") and name.endswith(".txt") for name in files):
        stacks.add("python")
    if "pom.xml" in files or any(name.startswith("build.gradle") for name in files):
        stacks.add("java")
    if include_gatling or (consumer / "performance/gatling").is_dir():
        stacks.add("gatling")
    return stacks


def patterns_for(consumer: Path, feature_stacks: set[str]) -> list[str]:
    stacks = detect_stacks(consumer) | feature_stacks
    return sorted({pattern for stack in stacks for pattern in DEFAULTS[stack]})


def safe_patterns_for(consumer: Path, feature_stacks: set[str]) -> tuple[list[str], list[str]]:
    tracked = {path.relative_to(consumer).as_posix() for path in consumer.rglob("*") if path.is_file() and ".git" not in path.parts}
    accepted, skipped = [], []
    for pattern in patterns_for(consumer, feature_stacks):
        if any(fnmatch(path, pattern) for path in tracked):
            skipped.append(pattern)
        else:
            accepted.append(pattern)
    return accepted, skipped
