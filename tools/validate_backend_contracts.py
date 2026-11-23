#!/usr/bin/env python3
"""Validate contract-first backend feature inputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent.parent
SCHEMAS = {
    "backend-service-input/v1": ROOT / "docs/backend/schemas/backend-service-input.v1.schema.json",
    "backend-test-cases/v1": ROOT / "docs/backend/schemas/backend-test-cases.v1.schema.json",
}
HTTP_METHODS = {"get", "put", "post", "delete", "patch", "head", "options", "trace"}
VALID_PROFILES = {"smoke", "baseline", "stress"}


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_schema(document: Any, version: str) -> list[str]:
    schema = json.loads(SCHEMAS[version].read_text(encoding="utf-8"))
    return [f"BE-SCHEMA-001: {error.message}" for error in Draft202012Validator(schema).iter_errors(document)]


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def operations(openapi: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], list[str]]:
    found, errors = {}, []
    for path, item in openapi.get("paths", {}).items():
        if not isinstance(item, dict):
            continue
        for method, operation in item.items():
            if method.lower() not in HTTP_METHODS or not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                errors.append("BE-OAS-002: every operation requires an operationId")
            elif operation_id in found:
                errors.append(f"BE-OAS-002: duplicate operationId {operation_id}")
            else:
                found[operation_id] = {"path": path, "method": method.upper(), "operation": operation}
    return found, errors


def component_exists(openapi: dict[str, Any], reference: Any) -> bool:
    if not isinstance(reference, str) or not reference.startswith("#/components/schemas/"):
        return False
    return reference.rsplit("/", 1)[-1] in openapi.get("components", {}).get("schemas", {})


def manifest_resource(base: Path, consumer: Path, value: dict[str, Any]) -> Path:
    return (consumer if value.get("pathBase") == "consumer" else base) / value["path"]


def performance_sources(performance_root: Path) -> list[Path]:
    source_root = performance_root / "src"
    extensions = {".java", ".kt", ".scala", ".conf", ".properties", ".json", ".yaml", ".yml", ".csv"}
    files = [path for path in source_root.rglob("*") if path.is_file() and path.suffix in extensions] if source_root.exists() else []
    files.extend(path for path in performance_root.glob("*.properties") if path.is_file())
    return files


def fixed_hosts(path: Path) -> list[tuple[int, str]]:
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        for host in re.findall(r"https?://([^/\s:'\"]+)", line, re.I):
            if host.lower() not in {"localhost", "127.0.0.1", "[::1]"}:
                found.append((number, host))
    return found


def changelog_changesets(path: Path, errors: list[str], visited: set[Path] | None = None) -> list[ET.Element]:
    visited = visited or set()
    path = path.resolve()
    if path in visited:
        return []
    visited.add(path)
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        errors.append(f"BE-DB-004: cannot read included changelog {path}")
        return []
    if root.tag.rsplit("}", 1)[-1] != "databaseChangeLog":
        errors.append("BE-DB-001: changelog root must be databaseChangeLog")
        return []
    changesets = []
    for element in root:
        name = element.tag.rsplit("}", 1)[-1]
        if name == "changeSet":
            changesets.append(element)
        elif name == "include":
            include = element.get("file")
            include_root = path.parent if element.get("relativeToChangelogFile", "false").lower() == "true" else path.parent
            if not include or not (include_root / include).is_file():
                errors.append(f"BE-DB-004: included changelog does not exist: {include}")
            else:
                changesets.extend(changelog_changesets(include_root / include, errors, visited))
        elif name == "includeAll":
            directory = element.get("path")
            include_root = path.parent if element.get("relativeToChangelogFile", "false").lower() == "true" else path.parent
            target = include_root / (directory or "")
            if not directory or not target.is_dir():
                errors.append(f"BE-DB-004: included changelog directory does not exist: {directory}")
            else:
                for included in sorted(target.rglob("*.xml")):
                    changesets.extend(changelog_changesets(included, errors, visited))
    return changesets


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate backend contract-first manifests.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--workspace-root", type=Path)
    parser.add_argument("--phase", choices=("preflight", "verify"), default="verify")
    args = parser.parse_args(argv)
    manifest_path = args.input.resolve()
    errors, blocked = [], []
    try:
        manifest = load_yaml(manifest_path)
    except (OSError, yaml.YAMLError) as exc:
        print(f"BE-SCHEMA-001: cannot read manifest: {exc}", file=sys.stderr)
        return 1
    errors.extend(validate_schema(manifest, "backend-service-input/v1"))
    if errors:
        print(*errors, sep="\n", file=sys.stderr)
        return 1
    base = manifest_path.parent
    consumer_root = (base / manifest["consumer"]["repositoryRoot"]).resolve()
    workspace_root = args.workspace_root.resolve() if args.workspace_root else consumer_root
    contract_path = manifest_resource(base, consumer_root, manifest["openapi"])
    cases_path = manifest_resource(base, consumer_root, manifest["testCases"])
    for path, declared in ((contract_path, manifest["openapi"]["sha256"]), (cases_path, manifest["testCases"]["sha256"])):
        if not path.is_file() or digest(path) != declared:
            errors.append(f"BE-HASH-001: digest mismatch for {path}")
    try:
        openapi, cases = load_yaml(contract_path), load_yaml(cases_path)
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"BE-OAS-001: cannot parse input: {exc}")
        openapi, cases = {}, {}
    if not isinstance(openapi, dict) or not re.fullmatch(r"3\.(0|1)(?:\.\d+)?", str(openapi.get("openapi", ""))):
        errors.append("BE-OAS-001: OpenAPI 3.0 or 3.1 document is required")
    errors.extend(validate_schema(cases, "backend-test-cases/v1"))
    operation_map, operation_errors = operations(openapi if isinstance(openapi, dict) else {})
    errors.extend(operation_errors)
    cases_by_operation: dict[str, list[dict[str, Any]]] = {}
    for case in cases.get("cases", []) if isinstance(cases, dict) else []:
        if not isinstance(case, dict):
            continue
        operation = operation_map.get(case.get("operationId"))
        if not operation or case.get("request", {}).get("method") != operation.get("method") or case.get("request", {}).get("path") != operation.get("path"):
            errors.append(f"BE-TEST-003: case {case.get('id')} does not match an operation")
            continue
        responses = operation["operation"].get("responses", {})
        if str(case.get("expected", {}).get("status")) not in responses:
            errors.append(f"BE-TEST-004: case {case.get('id')} has undeclared response status")
        if not component_exists(openapi, case.get("expected", {}).get("responseSchema")):
            errors.append(f"BE-TEST-005: case {case.get('id')} has an unknown response schema")
        cases_by_operation.setdefault(case["operationId"], []).append(case)
        if "negative" in case.get("classification", []) and not 400 <= case.get("expected", {}).get("status", 0) < 500:
            errors.append(f"BE-TEST-006: negative case {case.get('id')} must expect a 4xx status")
    for operation_id, operation in operation_map.items():
        operation_cases = cases_by_operation.get(operation_id, [])
        if not any(200 <= case.get("expected", {}).get("status", 0) < 400 for case in operation_cases):
            errors.append(f"BE-TEST-001: {operation_id} has no successful case")
        required_parameters = any(parameter.get("required") for parameter in operation["operation"].get("parameters", []) if isinstance(parameter, dict))
        if operation["operation"].get("requestBody") or required_parameters:
            if not any("negative" in case.get("classification", []) for case in operation_cases):
                errors.append(f"BE-TEST-002: {operation_id} has no negative case")
    database = manifest["database"]
    if not database["required"] and not database.get("reason"):
        errors.append("BE-REQ-001: database.required false requires reason")
    if database.get("migrationTool") != "liquibase":
        blocked.append("BE-DB-003: migrationTool must be liquibase")
    if database["required"]:
        changelog = workspace_root / database.get("changelogRoot", "")
        if args.phase == "preflight" and not changelog.exists():
            changelog = None
        if changelog is None:
            pass
        else:
            if not changelog.is_file():
                errors.append("BE-DB-001: changelogRoot must exist and be valid XML")
                changesets = []
            else:
                changesets = changelog_changesets(changelog, errors)
            identities = set()
            for changeset in changesets:
                identity = (changeset.get("id"), changeset.get("author"))
                if not identity[0] or not identity[1] or identity in identities:
                    errors.append("BE-DB-002: changesets require unique id and author")
                identities.add(identity)
            if args.phase == "verify" and not changesets:
                errors.append("BE-DB-005: changelog must contain at least one reachable changeSet")
    performance = manifest["performance"]
    if not performance["required"] and not performance.get("reason"):
        errors.append("BE-REQ-001: performance.required false requires reason")
    if performance["required"]:
        profiles = set(performance.get("profiles", []))
        if not performance.get("baseUrlEnv") or not profiles <= VALID_PROFILES or any(case.get("operationId") not in operation_map or not set(case.get("profile", [])) <= profiles for case in performance.get("scenarios", [])):
            errors.append("BE-PERF-001: invalid performance scenario or profile")
        perf_dir = workspace_root / "performance/gatling"
        sources = performance_sources(perf_dir)
        for source in sources:
            for line, host in fixed_hosts(source):
                errors.append(f"BE-PERF-002: {source}:{line} fixed non-loopback host {host}")
        if args.phase == "verify":
            if not any(path.suffix in {".java", ".kt", ".scala"} for path in sources):
                errors.append("BE-PERF-003: performance/gatling/src must contain a simulation source")
            text = "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in sources)
            for scenario in performance.get("scenarios", []):
                if scenario.get("operationId") not in text:
                    errors.append(f"BE-PERF-004: operationId is not referenced by a simulation: {scenario.get('operationId')}")
    print(*(errors + blocked), sep="\n", file=sys.stderr)
    if errors:
        return 1
    if blocked:
        return 2
    print(f"VALID {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
