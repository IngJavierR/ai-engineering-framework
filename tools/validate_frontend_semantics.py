#!/usr/bin/env python3
"""Validate semantic consistency of M2 frontend input contracts."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
STRUCTURAL_PATH = ROOT / "tools" / "validate_frontend_contracts.py"
SPEC = importlib.util.spec_from_file_location("frontend_structural_validator", STRUCTURAL_PATH)
structural = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = structural
assert SPEC.loader is not None
SPEC.loader.exec_module(structural)


@dataclass(frozen=True)
class SemanticError:
    code: str
    document: Path
    location: str
    message: str
    blocked: bool = True

    def format(self) -> str:
        status = "BLOCKED" if self.blocked else "ERROR"
        return f"{status} {self.code} {self.document} {self.location}: {self.message}"


def error(code: str, path: Path, location: str, message: str) -> SemanticError:
    return SemanticError(code, path, location, message)


def load_yaml(path: Path) -> tuple[dict[str, Any] | None, list[SemanticError]]:
    document, errors = structural._load_yaml(path)
    if errors:
        return None, [error("SEM-STRUCTURAL", path, item.location, item.message) for item in errors]
    if not isinstance(document, dict):
        return None, [error("SEM-STRUCTURAL", path, "$", "document root must be a mapping")]
    return document, []


def _has_symlink_ancestor(path: Path) -> bool:
    current = path.absolute()
    temp_root = Path(tempfile.gettempdir()).absolute()
    while True:
        if current.is_symlink():
            return True
        if current == temp_root or current == current.parent:
            return False
        current = current.parent


def _walk_relative(base: Path, relative: str) -> tuple[Path | None, str | None]:
    """Walk lexical path components and reject every traversed symlink."""
    current = base.absolute()
    for component in relative.split("/"):
        current = current.parent if component == ".." else current / component
        if current.is_symlink():
            return None, f"symlink is not allowed: {relative}"
    return current, None


def resolve_input_file(manifest: Path, relative: str, location: str) -> tuple[Path | None, list[SemanticError]]:
    if _has_symlink_ancestor(manifest.parent):
        return None, [error("SEM-PATH-002", manifest, location, "manifest path has a symlink ancestor")]
    base = manifest.parent.absolute()
    candidate, walk_error = _walk_relative(base, relative)
    if walk_error:
        return None, [error("SEM-PATH-002", manifest, location, walk_error)]
    assert candidate is not None
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError:
        return None, [error("SEM-FILE-001", manifest, location, f"file does not exist: {relative}")]
    except OSError as exc:
        return None, [error("SEM-FILE-002", manifest, location, str(exc))]
    try:
        resolved.relative_to(base.resolve())
    except ValueError:
        return None, [error("SEM-PATH-001", manifest, location, f"path escapes input package: {relative}")]
    if not resolved.is_file():
        return None, [error("SEM-FILE-003", manifest, location, f"expected a regular file: {relative}")]
    return resolved, []


def check_hash(manifest: Path, item: dict[str, Any], location: str) -> list[SemanticError]:
    path, errors = resolve_input_file(manifest, item["path"], f"{location}.path")
    if errors:
        return errors
    try:
        actual = f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
    except OSError as exc:
        return [error("SEM-FILE-004", manifest, f"{location}.path", str(exc))]
    if item["sha256"] != actual:
        return [error("SEM-HASH-001", manifest, f"{location}.sha256", "hash does not match file bytes")]
    return []


def duplicate_ids(manifest: Path, label: str, values: list[dict[str, Any]]) -> tuple[set[str], list[SemanticError]]:
    seen: set[str] = set()
    errors: list[SemanticError] = []
    for index, value in enumerate(values):
        identifier = value["id"]
        if identifier in seen:
            errors.append(error("SEM-ID-001", manifest, f"{label}[{index}].id", f"duplicate ID {identifier}"))
        seen.add(identifier)
    return seen, errors


def validate_manifest(path: Path, workspace_root: Path | None = None) -> list[SemanticError]:
    structural_errors = structural.validate_document(path, "frontend-ui-input/v1")
    if structural_errors:
        return [error("SEM-STRUCTURAL", path, item.location, item.message) for item in structural_errors]
    manifest, errors = load_yaml(path)
    if errors:
        return errors

    errors = []
    references = [manifest["functionalSpecification"], *manifest["mockups"], *manifest["assets"], manifest["unitTests"]]
    expected_inventory: dict[str, str] = {}
    for index, item in enumerate(references):
        previous = expected_inventory.get(item["path"])
        if previous is not None and previous != item["sha256"]:
            errors.append(error("SEM-INVENTORY-001", path, f"$.references[{index}]", "same referenced path has conflicting hashes"))
        expected_inventory[item["path"]] = item["sha256"]
    actual_inventory: dict[str, str] = {}
    for index, item in enumerate(manifest["files"]):
        if item["path"] in actual_inventory:
            errors.append(error("SEM-INVENTORY-002", path, f"$.files[{index}]", "duplicate inventory file"))
        actual_inventory[item["path"]] = item["sha256"]
    for item_path, digest in expected_inventory.items():
        if item_path not in actual_inventory:
            errors.append(error("SEM-INVENTORY-003", path, "$.files", f"referenced file is absent from inventory: {item_path}"))
        elif actual_inventory[item_path] != digest:
            errors.append(error("SEM-INVENTORY-001", path, "$.files", f"inventory hash differs for {item_path}"))
    for item_path in actual_inventory:
        if item_path not in expected_inventory:
            errors.append(error("SEM-INVENTORY-004", path, "$.files", f"unreferenced inventory file: {item_path}"))
    files = [*references, *manifest["files"]]
    for index, item in enumerate(files):
        errors.extend(check_hash(path, item, f"$.filesOrReferences[{index}]"))

    requirement_ids, duplicate_errors = duplicate_ids(path, "$.requirements.confirmed", manifest["requirements"]["confirmed"])
    errors.extend(duplicate_errors)
    component_ids, duplicate_errors = duplicate_ids(path, "$.conceptualComponents", manifest["conceptualComponents"])
    errors.extend(duplicate_errors)
    for group in ("ambiguities", "inferences", "authorizedDecisions"):
        _, duplicate_errors = duplicate_ids(path, f"$.requirements.{group}", manifest["requirements"][group])
        errors.extend(duplicate_errors)

    known_sources = {manifest["functionalSpecification"]["id"], *(item["id"] for item in manifest["mockups"])}
    for group in ("confirmed", "ambiguities", "inferences"):
        for index, item in enumerate(manifest["requirements"][group]):
            if item["sourceId"] not in known_sources:
                errors.append(error("SEM-REF-004", path, f"$.requirements.{group}[{index}].sourceId", "unknown source"))
    for index, mockup in enumerate(manifest["mockups"]):
        for component_id in mockup["conceptualComponentIds"]:
            if component_id not in component_ids:
                errors.append(error("SEM-REF-003", path, f"$.mockups[{index}].conceptualComponentIds", "unknown conceptual component"))

    ambiguity_ids = {item["id"] for item in manifest["requirements"]["ambiguities"]}
    decision_by_ambiguity = {item["resolvesAmbiguityId"]: item for item in manifest["requirements"]["authorizedDecisions"]}
    for index, ambiguity in enumerate(manifest["requirements"]["ambiguities"]):
        for requirement_id in ambiguity["blocksRequirementIds"]:
            if requirement_id not in requirement_ids:
                errors.append(error("SEM-REF-001", path, f"$.requirements.ambiguities[{index}].blocksRequirementIds", f"unknown requirement {requirement_id}"))
        decision = decision_by_ambiguity.get(ambiguity["id"])
        if decision is None:
            errors.append(error("SEM-AMB-001", path, f"$.requirements.ambiguities[{index}]", "blocking ambiguity has no decision"))
        else:
            evidence = decision["authorizationEvidence"]
            errors.append(error("SEM-AUTH-001", path, "$.requirements.authorizedDecisions", f"authorization for {decision['id']} is not externally verifiable"))

    for index, decision in enumerate(manifest["requirements"]["authorizedDecisions"]):
        if decision["resolvesAmbiguityId"] not in ambiguity_ids:
            errors.append(error("SEM-REF-002", path, f"$.requirements.authorizedDecisions[{index}].resolvesAmbiguityId", "unknown ambiguity"))
        for requirement_id in decision["appliesToRequirementIds"]:
            if requirement_id not in requirement_ids:
                errors.append(error("SEM-REF-001", path, f"$.requirements.authorizedDecisions[{index}].appliesToRequirementIds", f"unknown requirement {requirement_id}"))

    for index, component in enumerate(manifest["conceptualComponents"]):
        for requirement_id in component["requirementIds"]:
            if requirement_id not in requirement_ids:
                errors.append(error("SEM-REF-001", path, f"$.conceptualComponents[{index}].requirementIds", f"unknown requirement {requirement_id}"))

    unit_path, unit_errors = resolve_input_file(path, manifest["unitTests"]["path"], "$.unitTests.path")
    errors.extend(unit_errors)
    unit_document: dict[str, Any] | None = None
    if unit_path:
        unit_structural = structural.validate_document(unit_path, "frontend-unit-tests/v1")
        if unit_structural:
            errors.extend(error("SEM-STRUCTURAL", unit_path, item.location, item.message) for item in unit_structural)
        else:
            unit_document, unit_errors = load_yaml(unit_path)
            errors.extend(unit_errors)
    if unit_document:
        if unit_document["featureId"] != manifest["featureId"]:
            errors.append(error("SEM-FEATURE-001", path, "$.unitTests", "featureId differs from unit test document"))
        declared_cases = manifest["unitTests"]["caseIds"]
        actual_cases, case_duplicates = duplicate_ids(unit_path, "$.cases", unit_document["cases"])
        errors.extend(case_duplicates)
        if set(declared_cases) != actual_cases or len(declared_cases) != len(actual_cases):
            errors.append(error("SEM-CASE-001", path, "$.unitTests.caseIds", "declared cases must exactly match the unit test document"))
        covered: set[str] = set()
        decision_ids = {item["id"] for item in manifest["requirements"]["authorizedDecisions"]}
        component_requirements = {item["id"]: set(item["requirementIds"]) for item in manifest["conceptualComponents"]}
        for index, case in enumerate(unit_document["cases"]):
            target_id = case["target"]["conceptualUnitId"]
            if target_id not in component_ids:
                errors.append(error("SEM-REF-003", unit_path, f"$.cases[{index}].target.conceptualUnitId", "unknown conceptual component"))
            elif target_id not in case["componentIds"]:
                errors.append(error("SEM-TRACE-002", unit_path, f"$.cases[{index}].target.conceptualUnitId", "target component is not listed in componentIds"))
            for requirement_id in case["requirementIds"]:
                if requirement_id not in requirement_ids:
                    errors.append(error("SEM-REF-001", unit_path, f"$.cases[{index}].requirementIds", f"unknown requirement {requirement_id}"))
                else:
                    covered.add(requirement_id)
                    if target_id in component_requirements and requirement_id not in component_requirements[target_id]:
                        errors.append(error("SEM-TRACE-001", unit_path, f"$.cases[{index}]", "case requirement is not linked to target component"))
            for component_id in case["componentIds"]:
                if component_id not in component_ids:
                    errors.append(error("SEM-REF-003", unit_path, f"$.cases[{index}].componentIds", f"unknown conceptual component {component_id}"))
            for precondition in case["preconditions"]:
                decision_id = precondition.get("decisionId")
                if decision_id and decision_id not in decision_ids:
                    errors.append(error("SEM-REF-005", unit_path, f"$.cases[{index}].preconditions", "unknown decision"))
                elif decision_id:
                    decision = next(item for item in manifest["requirements"]["authorizedDecisions"] if item["id"] == decision_id)
                    if not set(case["requirementIds"]).intersection(decision["appliesToRequirementIds"]):
                        errors.append(error("SEM-TRACE-003", unit_path, f"$.cases[{index}].preconditions", "decision does not apply to any case requirement"))
        for requirement_id in requirement_ids - covered:
            errors.append(error("SEM-TEST-001", path, "$.requirements.confirmed", f"unit-testable requirement has no unit test case: {requirement_id}"))

    consumer = manifest["consumer"]
    if workspace_root is None:
        errors.append(error("SEM-WORKSPACE-001", path, "$.consumer.repositoryRoot", "a trusted --workspace-root is required"))
    else:
        workspace = workspace_root.absolute()
        if _has_symlink_ancestor(workspace) or not workspace.is_dir():
            errors.append(error("SEM-WORKSPACE-002", path, "$.consumer.repositoryRoot", "workspace root is unavailable or uses a symlink"))
        else:
            candidate, walk_error = _walk_relative(path.parent.absolute(), consumer["repositoryRoot"])
            if walk_error:
                errors.append(error("SEM-CONSUMER-001", path, "$.consumer.repositoryRoot", walk_error))
                candidate = None
            if candidate is not None:
                try:
                    root = candidate.resolve(strict=True)
                    root.relative_to(workspace.resolve())
                except FileNotFoundError:
                    errors.append(error("SEM-CONSUMER-002", path, "$.consumer.repositoryRoot", "consumer repository is not available for verification"))
                    root = None
                except (OSError, ValueError) as exc:
                    errors.append(error("SEM-CONSUMER-003", path, "$.consumer.repositoryRoot", f"consumer repository is not trusted: {exc}"))
                    root = None
                if root is not None:
                    manifest_file, manifest_error = _walk_relative(root, consumer["detection"]["manifestPath"])
                    lockfile, lock_error = _walk_relative(root, consumer["detection"]["lockfilePath"])
                    if manifest_error or lock_error or not manifest_file or not lockfile or not manifest_file.is_file() or not lockfile.is_file():
                        errors.append(error("SEM-VERSION-001", path, "$.consumer.detection", "package manifest or lockfile is unavailable"))
                    else:
                        try:
                            package = json.loads(manifest_file.read_text(encoding="utf-8"))
                            lock = json.loads(lockfile.read_text(encoding="utf-8"))
                        except (OSError, json.JSONDecodeError) as exc:
                            errors.append(error("SEM-VERSION-002", path, "$.consumer.detection", f"invalid package metadata: {exc}"))
                        else:
                            dependency = "@angular/core" if consumer["stack"] == "angular" else "react"
                            version_key = "angularCore" if consumer["stack"] == "angular" else "react"
                            dependencies: dict[str, Any] = {}
                            lock_version: str | None = None
                            package_valid = isinstance(package, dict)
                            lock_valid = isinstance(lock, dict)
                            if not package_valid:
                                errors.append(error("SEM-VERSION-002", path, "$.consumer.detection.manifestPath", "package.json root must be an object"))
                            else:
                                dependencies_value = package.get("dependencies", {})
                                dev_dependencies_value = package.get("devDependencies", {})
                                if not isinstance(dependencies_value, dict) or not isinstance(dev_dependencies_value, dict):
                                    errors.append(error("SEM-VERSION-002", path, "$.consumer.detection", "package.json dependency sections must be objects"))
                                else:
                                    dependencies = {**dependencies_value, **dev_dependencies_value}
                            if not lock_valid:
                                errors.append(error("SEM-VERSION-005", path, "$.consumer.detection.lockfilePath", "package-lock.json root must be an object"))
                            elif lock.get("lockfileVersion") in (2, 3):
                                packages_value = lock.get("packages")
                                if not isinstance(packages_value, dict):
                                    errors.append(error("SEM-VERSION-005", path, "$.consumer.detection.lockfilePath", "npm lockfile packages must be an object"))
                                else:
                                    package_entry = packages_value.get(f"node_modules/{dependency}")
                                    if package_entry is not None and not isinstance(package_entry, dict):
                                        errors.append(error("SEM-VERSION-005", path, "$.consumer.detection.lockfilePath", "npm stack package entry must be an object"))
                                    elif isinstance(package_entry, dict):
                                        lock_version = package_entry.get("version")
                            if package_valid and dependency not in dependencies:
                                errors.append(error("SEM-VERSION-003", path, "$.consumer.stack", f"missing {dependency} dependency"))
                            elif dependencies and consumer["detection"]["declaredVersions"].get(version_key) != dependencies[dependency]:
                                errors.append(error("SEM-VERSION-004", path, "$.consumer.detection.declaredVersions", "declared version differs from package.json"))
                            if not isinstance(lock_version, str):
                                errors.append(error("SEM-VERSION-005", path, "$.consumer.detection.lockfilePath", "npm lockfile v2/v3 lacks exact stack version"))
                            elif consumer["detection"]["resolvedVersions"].get(version_key) != lock_version:
                                errors.append(error("SEM-VERSION-006", path, "$.consumer.detection.resolvedVersions", "resolved version differs from package-lock.json"))
                    if consumer["verificationStatus"] != "verified":
                        errors.append(error("SEM-CONSUMER-004", path, "$.consumer.verificationStatus", "consumer is declared not verified"))
    if manifest["templateStatus"] == "illustrative-not-ready-for-execution":
        errors.append(error("SEM-TEMPLATE-001", path, "$.templateStatus", "illustrative template is not ready for execution"))
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate frontend input contract semantics.")
    parser.add_argument("--input", action="append", type=Path, default=[], metavar="PATH")
    parser.add_argument("--workspace-root", type=Path, metavar="PATH")
    arguments = parser.parse_args(argv)
    if not arguments.input:
        print("ERROR CLI-001: specify at least one --input PATH", file=sys.stderr)
        return 2
    failures: list[SemanticError] = []
    for path in arguments.input:
        failures.extend(validate_manifest(path, arguments.workspace_root))
    for item in failures:
        print(item.format(), file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
