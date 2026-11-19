#!/usr/bin/env python3
"""Fail-closed local verification for SSH-signed frontend authorization commits."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_PATH = ROOT / "tools" / "validate_frontend_contracts.py"
SPEC = importlib.util.spec_from_file_location(
    "frontend_authorization_contracts", CONTRACTS_PATH
)
contracts = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = contracts
assert SPEC.loader is not None
SPEC.loader.exec_module(contracts)

SHA = re.compile(r"^[0-9a-f]{40}$")
PRINCIPAL = re.compile(r"^[^\s,!*?\[\]{}\\]+$")
TRAILER = re.compile(r"^(M2-[A-Za-z0-9-]+): (.+)$")
TRAILER_NAMES = frozenset({
    "M2-Authorization-Version", "M2-Feature", "M2-Decision",
    "M2-Requirements", "M2-Statement-SHA256", "M2-Consumer-Root-SHA256",
})
TIMEOUT_SECONDS = 15


@dataclass(frozen=True)
class AuthorizationResult:
    status: str
    code: str
    reason: str


class ExternalToolError(Exception):
    """Represents a controlled failure while invoking a required tool."""

    def __init__(self, code: str, reason: str) -> None:
        super().__init__(reason)
        self.code = code
        self.reason = reason


def blocked(code: str, reason: str) -> AuthorizationResult:
    return AuthorizationResult("BLOCKED", code, reason)


def passed() -> AuthorizationResult:
    return AuthorizationResult(
        "PASS",
        "AUTH-000",
        "SSH signature, policy scope, and signed authorization payload are valid.",
    )


def _has_symlink_ancestor(path: Path) -> bool:
    current = path.absolute()
    while current != current.parent:
        if current.is_symlink():
            if current == Path("/var") and current.resolve() == Path("/private/var"):
                current = current.parent
                continue
            return True
        current = current.parent
    return current.is_symlink()


def _is_outside(path: Path, container: Path) -> bool:
    try:
        path.relative_to(container)
    except ValueError:
        return True
    return False


def _git_environment() -> dict[str, str]:
    """Return a minimal environment that excludes consumer-controlled Git state."""
    return {
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_PAGER": "cat",
        "GIT_TERMINAL_PROMPT": "0",
        "HOME": tempfile.gettempdir(),
        "LC_ALL": "C",
        "PATH": os.defpath,
    }


def _tool(name: str) -> str:
    executable = shutil.which(name, path=os.defpath)
    if executable is None:
        raise ExternalToolError("AUTH-ENV-001", f"required tool is unavailable: {name}")
    return executable


def _run(arguments: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            arguments,
            cwd=cwd,
            env=_git_environment(),
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
    except FileNotFoundError:
        raise ExternalToolError("AUTH-ENV-001", "required tool is unavailable") from None
    except PermissionError:
        raise ExternalToolError("AUTH-ENV-002", "required tool cannot be executed") from None
    except subprocess.TimeoutExpired:
        raise ExternalToolError("AUTH-ENV-003", "required tool timed out") from None
    except OSError:
        raise ExternalToolError("AUTH-ENV-004", "required tool could not be invoked") from None
    except UnicodeDecodeError:
        raise ExternalToolError("AUTH-PAYLOAD-001", "commit message cannot be decoded") from None


def _git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    return _run([_tool("git"), "-C", str(repository), *arguments], cwd=repository)


def _read_policy(policy_path: Path) -> tuple[dict[str, Any] | None, AuthorizationResult | None]:
    errors = contracts.validate_document(policy_path, "authorization-trust/v1")
    if errors:
        return None, blocked("AUTH-POLICY-001", errors[0].format())
    document, errors = contracts._load_yaml(policy_path)
    if errors or not isinstance(document, dict):
        return None, blocked("AUTH-POLICY-001", "authorization trust policy cannot be read")
    return document, None


def _fingerprint(public_key: str, ssh_keygen: str | None = None) -> str | None:
    if ssh_keygen is None:
        ssh_keygen = _tool("ssh-keygen")
    with tempfile.TemporaryDirectory(prefix="frontend-auth-key-") as directory:
        key_path = Path(directory) / "key.pub"
        key_path.write_text(public_key + "\n", encoding="utf-8")
        result = _run(
            [ssh_keygen, "-lf", str(key_path), "-E", "sha256"],
            cwd=Path(directory),
        )
    if result.returncode != 0:
        return None
    fields = result.stdout.split()
    return fields[1] if len(fields) >= 2 else None


def _is_single_principal(value: str) -> bool:
    return bool(PRINCIPAL.fullmatch(value))


def _sha256(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _payload(message: str) -> tuple[dict[str, str] | None, AuthorizationResult | None]:
    lines = message.rstrip("\n").split("\n")
    start = len(lines)
    while start and TRAILER.fullmatch(lines[start - 1]):
        start -= 1
    if start < 2 or lines[start - 1] != "" or not any(line.strip() for line in lines[:start - 1]):
        return None, blocked("AUTH-PAYLOAD-001", "M2 trailers must be the final trailer block")
    body = lines[:start - 1]
    if any(line.lstrip().startswith("M2-") for line in body):
        return None, blocked("AUTH-PAYLOAD-001", "M2 trailers outside the final block are not allowed")
    values: dict[str, str] = {}
    for line in lines[start:]:
        match = TRAILER.fullmatch(line)
        assert match is not None
        name, value = match.groups()
        if name not in TRAILER_NAMES or name in values:
            return None, blocked("AUTH-PAYLOAD-001", "M2 trailers are unknown or ambiguous")
        values[name] = value
    if set(values) != TRAILER_NAMES:
        return None, blocked("AUTH-PAYLOAD-001", "M2 trailer block is incomplete")
    return values, None


def _consumer_root(consumer_repository: Path) -> tuple[Path | None, AuthorizationResult | None]:
    if not consumer_repository.is_dir() or _has_symlink_ancestor(consumer_repository):
        return None, blocked("AUTH-CONSUMER-001", "consumer repository is unavailable or unsafe")
    try:
        consumer = consumer_repository.resolve(strict=True)
    except OSError:
        return None, blocked("AUTH-CONSUMER-001", "consumer repository is unavailable or unsafe")
    if not (consumer / ".git").is_dir() or (consumer / ".git").is_symlink():
        return None, blocked("AUTH-CONSUMER-002", "consumer must be a non-worktree repository root")
    inside = _git(consumer, "rev-parse", "--is-inside-work-tree")
    bare = _git(consumer, "rev-parse", "--is-bare-repository")
    top_level = _git(consumer, "rev-parse", "--show-toplevel")
    if (
        inside.returncode != 0
        or inside.stdout.strip() != "true"
        or bare.returncode != 0
        or bare.stdout.strip() != "false"
        or top_level.returncode != 0
        or top_level.stdout.strip() != str(consumer)
    ):
        return None, blocked("AUTH-CONSUMER-002", "consumer must be its exact non-bare Git root")
    return consumer, None


def verify_authorization(
    *,
    consumer_repository: Path,
    policy_path: Path | None,
    approval_commit: str,
    baseline_commit: str,
    principal: str,
    feature_id: str,
    decision_id: str,
    requirement_ids: tuple[str, ...],
    decision_statement: str,
    manifest_directory: Path | None = None,
) -> AuthorizationResult:
    """Verify only the local signed-commit evidence and declared trust scope."""
    try:
        return _verify_authorization(
            consumer_repository=consumer_repository,
            policy_path=policy_path,
            approval_commit=approval_commit,
            baseline_commit=baseline_commit,
            principal=principal,
            feature_id=feature_id,
            decision_id=decision_id,
            requirement_ids=requirement_ids,
            decision_statement=decision_statement,
            manifest_directory=manifest_directory,
        )
    except ExternalToolError as error:
        return blocked(error.code, error.reason)


def _verify_authorization(
    *,
    consumer_repository: Path,
    policy_path: Path | None,
    approval_commit: str,
    baseline_commit: str,
    principal: str,
    feature_id: str,
    decision_id: str,
    requirement_ids: tuple[str, ...],
    decision_statement: str,
    manifest_directory: Path | None,
) -> AuthorizationResult:
    if policy_path is None:
        return blocked("AUTH-POLICY-000", "authorization trust policy is required")
    if not SHA.fullmatch(approval_commit) or not SHA.fullmatch(baseline_commit):
        return blocked("AUTH-COMMIT-001", "approval and baseline commits must be full 40-hex SHAs")
    if not _is_single_principal(principal):
        return blocked("AUTH-PRINCIPAL-001", "principal must be one literal identity")
    if not feature_id or not decision_id or not requirement_ids:
        return blocked("AUTH-REQUEST-001", "principal, scope IDs, and requirements are required")
    if len(requirement_ids) != len(set(requirement_ids)):
        return blocked("AUTH-REQUEST-001", "expected requirement IDs must be unique")
    if not decision_statement:
        return blocked("AUTH-REQUEST-001", "decision statement is required")
    try:
        statement_hash = _sha256(decision_statement)
    except UnicodeEncodeError:
        return blocked("AUTH-REQUEST-002", "decision statement cannot be encoded as UTF-8")
    consumer, failure = _consumer_root(consumer_repository)
    if failure:
        return failure
    assert consumer is not None
    if policy_path.is_symlink() or _has_symlink_ancestor(policy_path.parent):
        return blocked("AUTH-POLICY-002", "authorization trust policy path uses a symlink")
    try:
        policy = policy_path.resolve(strict=True)
    except OSError:
        return blocked("AUTH-POLICY-002", "authorization trust policy is unavailable")
    if not policy.is_file() or not _is_outside(policy, consumer):
        return blocked("AUTH-POLICY-002", "authorization trust policy must be outside the consumer")
    if manifest_directory is not None:
        if _has_symlink_ancestor(manifest_directory):
            return blocked("AUTH-POLICY-002", "manifest directory uses a symlink")
        try:
            manifest = manifest_directory.resolve(strict=True)
        except OSError:
            return blocked("AUTH-POLICY-002", "manifest directory is unavailable")
        if not _is_outside(policy, manifest):
            return blocked("AUTH-POLICY-002", "authorization trust policy must be outside the manifest package")

    document, failure = _read_policy(policy)
    if failure:
        return failure
    assert document is not None
    if document["repositoryRoot"] != str(consumer):
        return blocked("AUTH-POLICY-003", "policy repositoryRoot differs from the consumer path")

    for commit in (approval_commit, baseline_commit):
        if _git(consumer, "cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
            return blocked("AUTH-COMMIT-002", f"commit is unavailable: {commit}")
    if _git(consumer, "merge-base", "--is-ancestor", approval_commit, baseline_commit).returncode != 0:
        return blocked("AUTH-COMMIT-003", "approval commit is not an ancestor of the baseline")

    requirements = set(requirement_ids)
    ssh_keygen = _tool("ssh-keygen")
    candidates = [
        signer
        for signer in document["authorizedSigners"]
        if _is_single_principal(signer["principal"])
        and signer["principal"] == principal
        and feature_id in signer["featureIds"]
        and decision_id in signer["decisionIds"]
        and requirements.issubset(signer["requirementIds"])
    ]
    if not candidates:
        return blocked("AUTH-SCOPE-001", "no single trusted signer covers the requested scope")

    revoked = set(document["revokedKeyFingerprints"])
    allowed: list[dict[str, Any]] = []
    revoked_candidates = 0
    for signer in candidates:
        fingerprint = _fingerprint(signer["publicKey"], ssh_keygen)
        if fingerprint is None:
            return blocked("AUTH-KEY-001", "trusted public key fingerprint cannot be evaluated")
        if fingerprint in revoked:
            revoked_candidates += 1
            continue
        allowed.append(signer)
    if not allowed:
        return blocked("AUTH-REVOKED-001", "all trusted keys for the requested scope are revoked")

    with tempfile.TemporaryDirectory(prefix="frontend-auth-signers-") as directory:
        signers_path = Path(directory) / "allowed_signers"
        signers_path.write_text(
            "".join(f"{item['principal']} {item['publicKey']}\n" for item in allowed),
            encoding="utf-8",
        )
        result = _git(
            consumer,
            "-c", "gpg.format=ssh",
            "-c", f"gpg.ssh.program={ssh_keygen}",
            "-c", f"gpg.ssh.allowedSignersFile={signers_path}",
            "-c", "gpg.ssh.revocationFile=",
            "verify-commit",
            approval_commit,
        )
    if result.returncode != 0:
        reason = result.stderr.strip() or result.stdout.strip() or "SSH signature verification failed"
        return blocked("AUTH-SIGNATURE-001", reason)
    message_result = _git(consumer, "log", "-1", "--format=%B", approval_commit)
    if message_result.returncode != 0:
        return blocked("AUTH-PAYLOAD-001", "commit message cannot be extracted")
    payload, failure = _payload(message_result.stdout)
    if failure:
        return failure
    assert payload is not None
    canonical_requirements = ",".join(sorted(requirement_ids))
    expected = {
        "M2-Authorization-Version": "1",
        "M2-Feature": feature_id,
        "M2-Decision": decision_id,
        "M2-Requirements": canonical_requirements,
        "M2-Statement-SHA256": statement_hash,
        "M2-Consumer-Root-SHA256": _sha256(str(consumer)),
    }
    if payload != expected:
        return blocked("AUTH-PAYLOAD-002", "M2 trailer values do not match the authorization request")
    return passed()
