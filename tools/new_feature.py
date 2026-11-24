#!/usr/bin/env python3
"""Create non-executable M2 input templates without inventing approvals."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

from ignored_defaults import safe_patterns_for

ROOT = Path(__file__).resolve().parent.parent


def is_git_repository(path: Path) -> bool:
    return path.is_dir() and subprocess.run(["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True).returncode == 0


def replace_feature_ids(path: Path, feature_id: str) -> None:
    suffix = feature_id.removeprefix("FEAT-")
    content = path.read_text(encoding="utf-8").replace("FEAT-CUSTOMER-API-001", feature_id)
    content = content.replace("TC-CUSTOMER-API-001-", f"TC-{suffix}-")
    path.write_text(content, encoding="utf-8")


def ignored_yaml(consumer: Path, stacks: set[str]) -> tuple[str, list[str]]:
    patterns, skipped = safe_patterns_for(consumer, stacks)
    return ", ".join(f'"{value}"' for value in patterns), skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="Create M2 feature input templates.")
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--stack", choices=("angular", "react", "java-spring", "python-fastapi", "generic"), required=True)
    parser.add_argument("--consumer", required=True)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--contract-dir")
    parser.add_argument("--frontend-root", default=".")
    args = parser.parse_args()
    consumer = Path(args.consumer).resolve()
    output = args.out.resolve()
    if not is_git_repository(consumer):
        print(f"NF-CONSUMER-001: consumer is not a Git repository: {consumer}", file=sys.stderr)
        return 1
    if output.exists() and any(output.iterdir()):
        raise SystemExit("ERROR: output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    if args.stack in {"java-spring", "python-fastapi", "generic"}:
        template = ROOT / "docs" / "backend" / "examples" / "customer-api"
        for name in ("backend.input.yaml", "openapi.yaml", "test-cases.yaml"):
            shutil.copy2(template / name, output / name)
        for path in (output / "backend.input.yaml", output / "test-cases.yaml"):
            replace_feature_ids(path, args.feature_id)
        manifest_path = output / "backend.input.yaml"
        repository_root = os.path.relpath(consumer, output)
        manifest_path.write_text(
            manifest_path.read_text(encoding="utf-8").replace(
                "../../../../tests/fixtures/fastapi", repository_root
            ),
            encoding="utf-8",
        )
        ignored, skipped = ignored_yaml(consumer, {"python", "gatling"})
        manifest_path.write_text(manifest_path.read_text(encoding="utf-8").replace("scope:\n", f"scope:\n  ignoredWorkPaths: [{ignored}]\n"), encoding="utf-8")
        if args.contract_dir:
            contract_dir = Path(args.contract_dir)
            if contract_dir.is_absolute() or ".." in contract_dir.parts:
                print("NF-CONTRACT-001: contract-dir must be a relative path inside the consumer", file=sys.stderr)
                return 1
            destination = consumer / contract_dir
            destination.mkdir(parents=True, exist_ok=True)
            for name in ("openapi.yaml", "test-cases.yaml"):
                shutil.copy2(output / name, destination / name)
                (output / name).unlink()
            document = manifest_path.read_text(encoding="utf-8")
            document = document.replace("path: openapi.yaml", f"path: {contract_dir.as_posix()}/openapi.yaml\n  pathBase: consumer")
            document = document.replace("path: test-cases.yaml", f"path: {contract_dir.as_posix()}/test-cases.yaml\n  pathBase: consumer")
            document = document.replace("protectedPaths: [{path: frontend, kind: directory}", f"protectedPaths: [{{path: {contract_dir.as_posix()}, kind: directory}}, {{path: frontend, kind: directory}}")
            manifest_path.write_text(document, encoding="utf-8")
        print(f"Created illustrative backend templates in {output}")
        if skipped:
            print(f"NF-IGNORED-WARN-001: omitted defaults matching tracked files: {', '.join(skipped)}", file=sys.stderr)
        return 0
    template = ROOT / "docs" / "m2" / "examples" / "customer-profile"
    for name in ("specification.md", "mockup.html", "unit-tests.yaml", f"{args.stack}.input.yaml"):
        shutil.copy2(template / name, output / name)
    manifest = (output / f"{args.stack}.input.yaml").read_text(encoding="utf-8")
    manifest = manifest.replace("FEAT-CUSTOMER-PROFILE-001", args.feature_id)
    repository_root = os.path.relpath(consumer, output)
    manifest = manifest.replace("../../../../labs/angular-customer-profile-consumer", repository_root)
    ignored, skipped = ignored_yaml(consumer, {"node"})
    manifest = manifest.replace("scope:\n", f"scope:\n  ignoredWorkPaths: [{ignored}]\n", 1)
    frontend_root = Path(args.frontend_root)
    if frontend_root != Path("."):
        if frontend_root.is_absolute() or ".." in frontend_root.parts:
            print("NF-FRONTEND-001: frontend-root must be a relative path inside the consumer", file=sys.stderr)
            return 1
        prefix = frontend_root.as_posix()
        manifest = manifest.replace("manifestPath: package.json", f"manifestPath: {prefix}/package.json")
        manifest = manifest.replace("lockfilePath: package-lock.json", f"lockfilePath: {prefix}/package-lock.json")
        lines = []
        in_scope = False
        for line in manifest.splitlines():
            stripped = line.strip()
            if stripped == "scope:":
                in_scope = True
            elif in_scope and not line.startswith(" "):
                in_scope = False
            if in_scope and "path:" in line and not any(item in stripped for item in ("evidence/", ".github")):
                before, value = line.split("path:", 1)
                value = value.strip()
                if value and not value.startswith(prefix + "/"):
                    line = f"{before}path: {prefix}/{value}"
            lines.append(line)
        manifest = "\n".join(lines) + "\n"
        siblings = [item.name for item in consumer.iterdir() if item.is_dir() and item.name != frontend_root.parts[0] and item.name != ".git"]
        if siblings:
            marker = "protectedPaths:"
            manifest = manifest.replace(marker, marker + "\n" + "\n".join(f"    - {{path: {name}, kind: directory}}" for name in siblings), 1)
    (output / f"{args.stack}.input.yaml").write_text(manifest, encoding="utf-8")
    unit = (output / "unit-tests.yaml").read_text(encoding="utf-8").replace("FEAT-CUSTOMER-PROFILE-001", args.feature_id)
    (output / "unit-tests.yaml").write_text(unit, encoding="utf-8")
    print(f"Created illustrative M2 templates in {output}")
    if skipped:
        print(f"NF-IGNORED-WARN-001: omitted defaults matching tracked files: {', '.join(skipped)}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
