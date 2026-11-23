#!/usr/bin/env python3
"""Refresh hashes and verified consumer metadata in a frontend input manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def git_clean(path: Path) -> str:
    changes = subprocess.check_output(["git", "-C", str(path), "status", "--porcelain"], text=True)
    if changes:
        raise ValueError(f"RM-GIT-001: consumer working tree is not clean: {', '.join(line[3:] for line in changes.splitlines())}")
    return subprocess.check_output(["git", "-C", str(path), "rev-parse", "HEAD"], text=True).strip()


def main() -> int:
    parser = argparse.ArgumentParser(description="Refresh M2 manifest hashes and consumer versions.")
    parser.add_argument("--manifest", required=True, type=Path)
    args = parser.parse_args()
    manifest_path = args.manifest.resolve()
    try:
        document = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as error:
        print(f"RM-MANIFEST-001: cannot read manifest: {error}", file=sys.stderr)
        return 1
    if not isinstance(document, dict):
        raise SystemExit("ERROR: manifest root must be a mapping")
    if document.get("schemaVersion") == "backend-service-input/v1":
        consumer = (manifest_path.parent / document["consumer"]["repositoryRoot"]).resolve()
        for key in ("openapi", "testCases"):
            root = consumer if document[key].get("pathBase") == "consumer" else manifest_path.parent
            document[key]["sha256"] = digest(root / document[key]["path"])
        try:
            document["consumer"]["baseline"]["commit"] = git_clean(consumer)
        except (OSError, subprocess.CalledProcessError, ValueError) as error:
            print(str(error), file=sys.stderr)
            return 1
        manifest_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        return subprocess.run([sys.executable, str(ROOT / "tools" / "validate_backend_contracts.py"), "--input", str(manifest_path), "--phase", "preflight"], check=False).returncode
    consumer = (manifest_path.parent / document["consumer"]["repositoryRoot"]).resolve()
    try:
        package = json.loads((consumer / document["consumer"]["detection"]["manifestPath"]).read_text(encoding="utf-8"))
        lock = json.loads((consumer / document["consumer"]["detection"]["lockfilePath"]).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        print(f"RM-CONSUMER-001: consumer manifest or lockfile is unavailable; use --frontend-root when needed: {error}", file=sys.stderr)
        return 1
    dependency = "@angular/core" if document["consumer"]["stack"] == "angular" else "react"
    version_key = "angularCore" if document["consumer"]["stack"] == "angular" else "react"
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    resolved = lock.get("packages", {}).get(f"node_modules/{dependency}", {}).get("version")
    typescript_resolved = lock.get("packages", {}).get("node_modules/typescript", {}).get("version")
    if dependency not in dependencies or not resolved or "typescript" not in dependencies or not typescript_resolved:
        print("RM-CONSUMER-001: consumer dependency or lock version is unavailable", file=sys.stderr)
        return 1
    detection = document["consumer"]["detection"]
    detection["declaredVersions"] = {version_key: dependencies[dependency], "typescript": dependencies["typescript"]}
    detection["resolvedVersions"] = {version_key: resolved, "typescript": typescript_resolved}
    detection["detectionMethod"] = "package.json and package-lock.json refreshed by tools/refresh_manifest.py"
    detection["reason"] = "Consumer metadata and lockfile were read from the clean consumer repository."
    document["consumer"]["verificationStatus"] = "verified"
    try:
        document["baseline"]["commit"] = git_clean(consumer)
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(str(error), file=sys.stderr)
        return 1
    document["baseline"]["verificationStatus"] = "verified"
    document["baseline"]["reason"] = "Baseline commit was captured from the clean consumer repository."
    references = [document["functionalSpecification"], *document["mockups"], document["unitTests"]]
    for item in references:
        item["sha256"] = digest(manifest_path.parent / item["path"])
    hashes = {item["path"]: digest(manifest_path.parent / item["path"]) for item in document["files"]}
    for item in document["files"]:
        item["sha256"] = hashes[item["path"]]
    manifest_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
    structural = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_frontend_contracts.py"), "--input", str(manifest_path)], check=False)
    semantic = subprocess.run([sys.executable, str(ROOT / "tools" / "validate_frontend_semantics.py"), "--input", str(manifest_path), "--workspace-root", str(consumer.parent)], check=False)
    return 0 if structural.returncode == semantic.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
