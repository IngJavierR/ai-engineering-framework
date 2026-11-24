#!/usr/bin/env python3
"""Fail-closed PREPARE and VERIFY workflow for M2 frontend contracts.

This tool deliberately does not run consumer commands or certify authorship.  A
receipt is mutable evidence; VERIFY therefore requires a separately supplied
external anchor that binds the prepared identity to a trusted custody channel.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent


def _load_module(name: str, filename: str) -> Any:
    specification = importlib.util.spec_from_file_location(name, ROOT / "tools" / filename)
    if specification is None or specification.loader is None:
        raise RuntimeError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


structural = _load_module("frontend_workflow_structural", "validate_frontend_contracts.py")
semantics = _load_module("frontend_workflow_semantics", "validate_frontend_semantics.py")
guard = _load_module("frontend_workflow_guard", "validate_frontend_git_scope.py")

RECEIPT_VERSION = "frontend-workflow-receipt/v1"
ANCHOR_VERSION = "frontend-workflow-anchor/v1"
EVALUATION_VERSION = "frontend-workflow-evaluation/v1"


@dataclass(frozen=True)
class Phase:
    name: str
    status: str
    code: str
    message: str


@dataclass(frozen=True)
class WorkflowResult:
    status: str
    code: str
    message: str
    phases: tuple[Phase, ...]
    workflow_status: str
    frontend_evidence: str = "NOT_RUN"

    def payload(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "code": self.code,
            "message": self.message,
            "workflowStatus": self.workflow_status,
            "frontendEvidence": self.frontend_evidence,
            "limitations": [
                "PASS certifies only observable Git scope conformity.",
                "It does not certify change authorship or intermediate changes that were reverted.",
                "It does not execute or validate frontend tests, builds, or type checks.",
                "An external anchor proves only value correspondence with the receipt; it does not authenticate its custodian or provenance.",
                "The invoker is responsible for supplying the external anchor through an independently trusted custody channel.",
            ],
            "phases": [asdict(phase) for phase in self.phases],
        }


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def digest(path: Path) -> str:
    return f"sha256:{sha256(path)}"


def atomic_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        try:
            path.chmod(0o600)
        except OSError:
            pass
    finally:
        if temporary.exists():
            temporary.unlink()


def external_to_consumer(path: Path, consumer: Path) -> bool:
    try:
        path.resolve().relative_to(consumer.resolve())
    except ValueError:
        return True
    return False


def blocked(code: str, message: str, phases: list[Phase]) -> WorkflowResult:
    return WorkflowResult("BLOCKED", code, message, tuple(phases), "BLOCKED")


def failed(code: str, message: str, phases: list[Phase]) -> WorkflowResult:
    return WorkflowResult("FAIL", code, message, tuple(phases), "BLOCKED")


def _manifest(path: Path) -> dict[str, Any] | None:
    document, errors = structural._load_yaml(path)
    return document if not errors and isinstance(document, dict) else None


def validate_input(manifest_path: Path, workspace_root: Path, phases: list[Phase]) -> dict[str, Any] | WorkflowResult:
    structural_errors = structural.validate_document(manifest_path, "frontend-ui-input/v1")
    if structural_errors:
        phases.append(Phase("structural", "BLOCKED", "WF-STRUCTURAL-001", structural_errors[0].format()))
        return blocked("WF-STRUCTURAL-001", "structural validation failed", phases)
    phases.append(Phase("structural", "PASS", "WF-STRUCTURAL-000", "input contract is structurally valid"))

    semantic_errors = semantics.validate_manifest(manifest_path, workspace_root)
    if semantic_errors:
        phases.append(Phase("semantic", "BLOCKED", "WF-SEMANTIC-001", semantic_errors[0].format()))
        return blocked("WF-SEMANTIC-001", "semantic validation failed", phases)
    document = _manifest(manifest_path)
    if document is None:
        phases.append(Phase("manifest", "BLOCKED", "WF-MANIFEST-001", "manifest cannot be read after validation"))
        return blocked("WF-MANIFEST-001", "manifest cannot be read", phases)
    if document["templateStatus"] != "ready-for-execution":
        phases.append(Phase("template", "BLOCKED", "WF-TEMPLATE-001", "illustrative manifest is not executable"))
        return blocked("WF-TEMPLATE-001", "manifest is not ready for execution", phases)
    phases.append(Phase("semantic", "PASS", "WF-SEMANTIC-000", "input facts and consumer metadata are valid"))
    return document


def receipt_paths(evidence: Path, execution_id: str) -> tuple[Path, Path]:
    return evidence / f"{execution_id}.snapshot.json", evidence / f"{execution_id}.receipt.json"


def consumer_identity(manifest: dict[str, Any], consumer: Path) -> dict[str, str]:
    consumer_data = manifest["consumer"]
    return {
        "id": consumer_data.get("id", consumer_data["repositoryRoot"]),
        "root": str(consumer.resolve()),
        "stack": consumer_data["stack"] if "stack" in consumer_data else manifest["stack"],
    }


def manifest_inputs(manifest: dict[str, Any]) -> dict[str, str]:
    if "files" in manifest:
        return {item["path"]: item["sha256"] for item in manifest["files"]}
    return {manifest["openapi"]["path"]: manifest["openapi"]["sha256"], manifest["testCases"]["path"]: manifest["testCases"]["sha256"]}


def matches_manifest_consumer(manifest_path: Path, manifest: dict[str, Any], consumer: Path) -> bool:
    try:
        declared = (manifest_path.parent / manifest["consumer"]["repositoryRoot"]).resolve(strict=True)
    except (OSError, KeyError, TypeError):
        return False
    return declared == consumer.resolve()


def prepare(manifest_path: Path, consumer: Path, workspace_root: Path, evidence: Path, validator=validate_input) -> tuple[WorkflowResult, Path | None]:
    phases: list[Phase] = []
    if not external_to_consumer(evidence, consumer):
        return blocked("WF-EVIDENCE-001", "evidence directory must be outside the consumer repository", phases), None
    document_or_result = validator(manifest_path, workspace_root, phases)
    if isinstance(document_or_result, WorkflowResult):
        return document_or_result, None
    document = document_or_result
    if not matches_manifest_consumer(manifest_path, document, consumer):
        phases.append(Phase("consumer", "BLOCKED", "WF-CONSUMER-002", "supplied consumer differs from manifest"))
        return blocked("WF-CONSUMER-002", "consumer identity differs from manifest", phases), None
    if not consumer.is_dir() or not guard.is_git_repo(consumer):
        phases.append(Phase("consumer", "BLOCKED", "WF-CONSUMER-001", "consumer is not a Git work tree"))
        return blocked("WF-CONSUMER-001", "consumer repository is unavailable", phases), None

    execution_id = str(uuid.uuid4())
    snapshot_path, receipt_path = receipt_paths(evidence, execution_id)
    ignored_work_paths = document["scope"].get("ignoredWorkPaths", [])
    snapshot_result = guard.write_snapshot(consumer, snapshot_path, ignored_work_paths)
    phases.append(Phase("snapshot", snapshot_result.status, snapshot_result.code, snapshot_result.message))
    if snapshot_result.status != "PASS":
        return blocked("WF-SNAPSHOT-001", "initial snapshot capture failed", phases), None
    try:
        snapshot_data = json.loads(snapshot_path.read_text(encoding="utf-8"))
        if snapshot_data["branch"] in {"main", "master", "develop"}:
            phases.append(Phase("branch", "WARN", "WF-PREPARE-WARN-001", f"PREPARE is running on shared branch {snapshot_data['branch']}; create a feature branch before implementation"))
        receipt = {
            "receiptVersion": RECEIPT_VERSION,
            "executionId": execution_id,
            "manifest": {"path": str(manifest_path.resolve()), "sha256": digest(manifest_path)},
            "inputs": manifest_inputs(document),
            "consumer": consumer_identity(document, consumer),
            "ignoredWorkPaths": ignored_work_paths,
            "baseCommit": snapshot_data["head"],
            "snapshot": {"path": str(snapshot_path.resolve()), "sha256": digest(snapshot_path)},
        }
        atomic_json(receipt_path, receipt)
    except (OSError, ValueError, KeyError, TypeError) as error:
        phases.append(Phase("receipt", "BLOCKED", "WF-RECEIPT-001", str(error)))
        return blocked("WF-RECEIPT-001", "preparation receipt could not be persisted", phases), None
    phases.append(Phase("receipt", "PASS", "WF-RECEIPT-000", "receipt written outside consumer; it is not a trust authority"))
    return WorkflowResult("PASS", "WF-PREPARE-000", "prepared; external custody anchor is required before VERIFY", tuple(phases), "BLOCKED"), receipt_path


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("sha256:") and len(value) == 71 and all(character in "0123456789abcdef" for character in value[7:])


def is_commit(value: Any) -> bool:
    return isinstance(value, str) and len(value) in {40, 64} and all(character in "0123456789abcdef" for character in value)


def is_execution_id(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value
    except ValueError:
        return False


def is_regular_path(value: Any) -> bool:
    return isinstance(value, str) and bool(value) and Path(value).is_absolute()


def valid_inputs(value: Any) -> bool:
    return isinstance(value, dict) and all(
        isinstance(path, str) and bool(path) and is_sha256(file_hash)
        for path, file_hash in value.items()
    )


def valid_consumer(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"id", "root", "stack"}
        and all(isinstance(value[key], str) and value[key] for key in ("id", "root", "stack"))
        and Path(value["root"]).is_absolute()
    )


def valid_file_reference(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == {"path", "sha256"}
        and is_regular_path(value.get("path"))
        and is_sha256(value.get("sha256"))
    )


def load_json(path: Path) -> tuple[dict[str, Any] | None, str | None]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return None, str(error)
    if not isinstance(value, dict):
        return None, "JSON root must be an object"
    return value, None


def validate_receipt(value: dict[str, Any]) -> str | None:
    required = {"receiptVersion", "executionId", "manifest", "inputs", "consumer", "baseCommit", "snapshot"}
    if set(value) not in (required, required | {"ignoredWorkPaths"}):
        return "receipt fields are missing or unexpected"
    if value.get("receiptVersion") != RECEIPT_VERSION:
        return "receiptVersion is invalid"
    if not is_execution_id(value.get("executionId")):
        return "executionId is invalid"
    if not valid_file_reference(value.get("manifest")):
        return "manifest reference is invalid"
    if not valid_inputs(value.get("inputs")):
        return "inputs are invalid"
    if not valid_consumer(value.get("consumer")):
        return "consumer is invalid"
    if "ignoredWorkPaths" in value and (not isinstance(value["ignoredWorkPaths"], list) or not all(isinstance(item, str) for item in value["ignoredWorkPaths"])):
        return "ignoredWorkPaths is invalid"
    if not is_commit(value.get("baseCommit")):
        return "baseCommit is invalid"
    if not valid_file_reference(value.get("snapshot")):
        return "snapshot reference is invalid"
    return None


def validate_anchor(value: dict[str, Any]) -> str | None:
    required = {"anchorVersion", "executionId", "receiptSha256", "manifestSha256", "inputs", "consumer", "baseCommit", "snapshotSha256"}
    if set(value) != required:
        return "anchor fields are missing or unexpected"
    if value.get("anchorVersion") != ANCHOR_VERSION:
        return "anchorVersion is invalid"
    if not is_execution_id(value.get("executionId")):
        return "executionId is invalid"
    if not all(is_sha256(value.get(key)) for key in ("receiptSha256", "manifestSha256", "snapshotSha256")):
        return "anchor SHA-256 value is invalid"
    if not valid_inputs(value.get("inputs")):
        return "anchor inputs are invalid"
    if not valid_consumer(value.get("consumer")):
        return "anchor consumer is invalid"
    if not is_commit(value.get("baseCommit")):
        return "anchor baseCommit is invalid"
    return None


def anchor_matches(anchor: dict[str, Any], receipt: dict[str, Any], receipt_path: Path) -> bool:
    return (
        anchor["executionId"] == receipt["executionId"]
        and anchor["receiptSha256"] == digest(receipt_path)
        and anchor["manifestSha256"] == receipt["manifest"]["sha256"]
        and anchor["inputs"] == receipt["inputs"]
        and anchor["consumer"] == receipt["consumer"]
        and anchor["baseCommit"] == receipt["baseCommit"]
        and anchor["snapshotSha256"] == receipt["snapshot"]["sha256"]
    )


def frontend_scope_guard(consumer: Path, manifest_path: Path, snapshot_path: Path, snapshot_sha256: str, _document: dict[str, Any]) -> Any:
    return guard.verify(consumer, manifest_path, snapshot_path, snapshot_sha256)


def verify(manifest_path: Path, consumer: Path, workspace_root: Path, receipt_path: Path, anchor_path: Path, evidence: Path, validator=validate_input, scope_guard=frontend_scope_guard) -> tuple[WorkflowResult, Path | None]:
    phases: list[Phase] = []
    if not external_to_consumer(receipt_path, consumer) or not external_to_consumer(evidence, consumer):
        return blocked("WF-EVIDENCE-001", "receipt and evidence must be outside the consumer repository", phases), None
    if anchor_path.resolve().parent == receipt_path.resolve().parent or not external_to_consumer(anchor_path, consumer):
        return blocked("WF-ANCHOR-001", "external anchor must be supplied from a custody location independent of the receipt", phases), None
    receipt, receipt_error = load_json(receipt_path)
    if receipt is None:
        return blocked("WF-RECEIPT-002", f"receipt is unreadable: {receipt_error}", phases), None
    receipt_error = validate_receipt(receipt)
    if receipt_error:
        return blocked("WF-RECEIPT-003", receipt_error, phases), None
    anchor, anchor_error = load_json(anchor_path)
    if anchor is None:
        return blocked("WF-ANCHOR-002", f"independent external anchor is unreadable: {anchor_error}", phases), None
    anchor_error = validate_anchor(anchor)
    if anchor_error:
        return blocked("WF-ANCHOR-004", anchor_error, phases), None
    if not anchor_matches(anchor, receipt, receipt_path):
        return blocked("WF-ANCHOR-003", "external anchor values do not correspond to this receipt", phases), None
    phases.append(Phase("custody", "PASS", "WF-ANCHOR-000", "external anchor values correspond to the receipt; custodian authority is not verified"))

    document_or_result = validator(manifest_path, workspace_root, phases)
    if isinstance(document_or_result, WorkflowResult):
        return document_or_result, None
    document = document_or_result
    if not matches_manifest_consumer(manifest_path, document, consumer):
        return blocked("WF-CONSUMER-002", "supplied consumer differs from manifest", phases), None
    if not consumer.is_dir() or not guard.is_git_repo(consumer):
        return blocked("WF-CONSUMER-001", "consumer repository is unavailable", phases), None
    receipt_manifest = receipt.get("manifest")
    if not isinstance(receipt_manifest, dict) or receipt_manifest.get("path") != str(manifest_path.resolve()) or receipt_manifest.get("sha256") != digest(manifest_path):
        return blocked("WF-IDENTITY-001", "manifest changed or differs from PREPARE", phases), None
    if receipt.get("inputs") != manifest_inputs(document):
        return blocked("WF-IDENTITY-002", "referenced inputs differ from PREPARE", phases), None
    if receipt.get("consumer") != consumer_identity(document, consumer):
        return blocked("WF-IDENTITY-003", "consumer identity or scope differs from PREPARE", phases), None
    snapshot = receipt["snapshot"]
    expected_snapshot_path, _ = receipt_paths(evidence.resolve(), receipt["executionId"])
    snapshot_path = Path(snapshot["path"])
    if snapshot_path != expected_snapshot_path or snapshot_path.resolve() != expected_snapshot_path.resolve():
        return blocked("WF-SNAPSHOT-003", "snapshot path does not match this execution evidence location", phases), None
    if snapshot_path.is_symlink() or not external_to_consumer(snapshot_path, consumer) or not snapshot_path.is_file():
        return blocked("WF-SNAPSHOT-002", "initial snapshot is unavailable or unsafe", phases), None
    if snapshot["sha256"] != digest(snapshot_path) or anchor["snapshotSha256"] != snapshot["sha256"]:
        return blocked("WF-SNAPSHOT-002", "initial snapshot digest does not match receipt and anchor", phases), None
    if receipt["baseCommit"] != anchor["baseCommit"]:
        return blocked("WF-IDENTITY-004", "base commit differs from anchored identity", phases), None
    guard_result = scope_guard(consumer, manifest_path, snapshot_path, snapshot["sha256"], document)
    phases.append(Phase("git-scope", guard_result.status, guard_result.code, guard_result.message))
    status = guard_result.status
    result = failed("WF-VERIFY-FAIL", "Git scope guard reported FAIL", phases) if status == "FAIL" else blocked("WF-VERIFY-BLOCKED", "Git scope guard reported BLOCKED", phases) if status != "PASS" else WorkflowResult("PASS", "WF-VERIFY-000", "observable scope conforms; no attribution or frontend execution is certified", tuple(phases), "BLOCKED")
    evaluation_path = evidence / f"{receipt['executionId']}.evaluation.json"
    try:
        evaluation = {"evaluationVersion": EVALUATION_VERSION, "executionId": receipt["executionId"], "receiptSha256": digest(receipt_path), **result.payload()}
        atomic_json(evaluation_path, evaluation)
    except OSError as error:
        return blocked("WF-EVALUATION-001", str(error), phases), None
    return result, evaluation_path


def parser() -> argparse.ArgumentParser:
    command = argparse.ArgumentParser(description="Fail-closed M2 PREPARE/VERIFY workflow invoker.")
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
    try:
        if arguments.operation == "prepare":
            result, artifact = prepare(arguments.manifest, arguments.consumer_repository, arguments.workspace_root, arguments.evidence_directory)
        else:
            result, artifact = verify(arguments.manifest, arguments.consumer_repository, arguments.workspace_root, arguments.receipt, arguments.external_anchor, arguments.evidence_directory)
    except (OSError, ValueError, KeyError, TypeError) as error:
        result, artifact = blocked("WF-UNEXPECTED-001", f"controlled workflow error: {error}", []), None
    payload = result.payload()
    if artifact is not None:
        payload["artifact"] = str(artifact)
    print(json.dumps(payload, sort_keys=True))
    return 0 if result.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
