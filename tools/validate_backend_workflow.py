#!/usr/bin/env python3
"""Fail-closed PREPARE and VERIFY workflow for backend contracts."""

from __future__ import annotations

import argparse
import contextlib
import io
import importlib.util
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def load_module(name: str, filename: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


workflow = load_module("backend_workflow_shared", "validate_frontend_workflow.py")
backend = load_module("backend_workflow_contracts", "validate_backend_contracts.py")
guard = load_module("backend_workflow_scope", "validate_frontend_git_scope.py")


def validate_input(manifest_path: Path, _workspace_root: Path, phases: list[Any], phase: str = "preflight") -> dict[str, Any] | Any:
    try:
        document = backend.load_yaml(manifest_path)
    except (OSError, backend.yaml.YAMLError) as error:
        phases.append(workflow.Phase("contract", "BLOCKED", "BE-WF-CONTRACT-001", str(error)))
        return workflow.blocked("BE-WF-CONTRACT-001", "backend manifest cannot be read", phases)
    errors = backend.validate_schema(document, "backend-service-input/v1")
    if errors:
        phases.append(workflow.Phase("structural", "BLOCKED", "BE-WF-STRUCTURAL-001", errors[0]))
        return workflow.blocked("BE-WF-STRUCTURAL-001", "structural validation failed", phases)
    with contextlib.redirect_stdout(io.StringIO()):
        result = backend.main(["--input", str(manifest_path), "--phase", phase])
    if result:
        phases.append(workflow.Phase(phase, "BLOCKED", "BE-WF-VALIDATION-001", f"backend {phase} validation failed"))
        return workflow.blocked("BE-WF-VALIDATION-001", f"backend {phase} validation failed", phases)
    phases.append(workflow.Phase(phase, "PASS", "BE-WF-VALIDATION-000", f"backend input is valid for {phase}"))
    return document


def scope_guard(consumer: Path, _manifest_path: Path, snapshot_path: Path, snapshot_sha256: str, document: dict[str, Any]) -> Any:
    return guard.verify_scope(consumer, document["scope"], snapshot_path, snapshot_sha256)


def verify_input(manifest_path: Path, workspace_root: Path, phases: list[Any]) -> dict[str, Any] | Any:
    return validate_input(manifest_path, workspace_root, phases, "verify")


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Fail-closed backend PREPARE/VERIFY workflow invoker.")
    subparsers = command.add_subparsers(dest="operation", required=True)
    for name in ("prepare", "verify"):
        item = subparsers.add_parser(name)
        item.add_argument("--manifest", required=True, type=Path)
        item.add_argument("--consumer-repository", required=True, type=Path)
        item.add_argument("--workspace-root", required=True, type=Path)
        item.add_argument("--evidence-directory", required=True, type=Path)
    verify_parser = subparsers.choices["verify"]
    verify_parser.add_argument("--receipt", required=True, type=Path)
    verify_parser.add_argument("--external-anchor", required=True, type=Path)
    return command


def main(argv: list[str] | None = None) -> int:
    arguments = parser().parse_args(argv)
    if arguments.operation == "prepare":
        result, artifact = workflow.prepare(arguments.manifest, arguments.consumer_repository, arguments.workspace_root, arguments.evidence_directory, validate_input)
    else:
        result, artifact = workflow.verify(arguments.manifest, arguments.consumer_repository, arguments.workspace_root, arguments.receipt, arguments.external_anchor, arguments.evidence_directory, verify_input, scope_guard)
    payload = result.payload()
    payload["backendEvidence"] = payload.pop("frontendEvidence")
    payload["limitations"] = [
        item.replace("frontend tests, builds, or type checks", "backend tests, builds, Liquibase, or Gatling")
        for item in payload["limitations"]
    ]
    if artifact is not None:
        payload["artifact"] = str(artifact)
    print(workflow.json.dumps(payload, sort_keys=True))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
