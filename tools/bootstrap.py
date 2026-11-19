#!/usr/bin/env python3
"""Controlled consumer bootstrap built on the framework installer."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
POLICY_SCHEMA = "client-policy/v1"
STATE_SCHEMA = "framework-bootstrap/v1"
POLICY_ROOT = ".ai-framework/policies"
STATE_PATH = ".ai-framework/bootstrap.json"


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot read JSON: {path}") from exc
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value


def validate_policy(policy: dict[str, Any]) -> None:
    required = {"schemaVersion", "clientId", "enabledCapabilities", "additionalRules", "exceptions"}
    if set(policy) != required or policy["schemaVersion"] != POLICY_SCHEMA:
        raise ValueError("Client policy has an unknown schema")
    if not isinstance(policy["clientId"], str) or not policy["clientId"]:
        raise ValueError("Client policy requires a clientId")
    if not isinstance(policy["enabledCapabilities"], list) or any(
        not isinstance(item, str) or not item for item in policy["enabledCapabilities"]
    ):
        raise ValueError("Client policy has invalid enabledCapabilities")
    if not isinstance(policy["additionalRules"], list) or not isinstance(policy["exceptions"], list):
        raise ValueError("Client policy has invalid rules")
    prohibited = {"disableMandatoryControls", "overrideFrameworkControls"}
    if any(isinstance(rule, dict) and prohibited.intersection(rule) for rule in policy["additionalRules"]):
        raise ValueError("Client policy cannot disable mandatory framework controls")


def framework_version() -> str:
    for line in (ROOT / "framework.yaml").read_text(encoding="utf-8").splitlines():
        if line.startswith("  version:"):
            return line.split(":", 1)[1].strip()
    raise ValueError("Framework version is unavailable")


def installer_command(target: Path, capabilities: list[str], upgrade: bool, dry_run: bool) -> list[str]:
    command = [sys.executable, str(ROOT / "tools" / "install.py"), "--target", str(target)]
    if upgrade:
        command.append("--upgrade")
    if dry_run:
        command.append("--dry-run")
    for capability in capabilities:
        command.extend(("--capability", capability))
    return command


def managed_conflicts(target: Path, capabilities: list[str]) -> list[Path]:
    import importlib.util

    spec = importlib.util.spec_from_file_location("framework_installer", ROOT / "tools" / "install.py")
    assert spec and spec.loader
    installer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(installer)
    _, files = installer.resolve_capabilities(capabilities)
    return [target / relative for relative in files if (target / relative).exists()]


def write_policy_and_state(target: Path, policy: dict[str, Any], version: str, capabilities: list[str], dry_run: bool, replace_policy: bool) -> None:
    policy_path = target / POLICY_ROOT / f"{policy['clientId']}.json"
    state_path = target / STATE_PATH
    state = {
        "schemaVersion": STATE_SCHEMA,
        "frameworkVersion": version,
        "clientPolicy": str(policy_path.relative_to(target)),
        "capabilities": capabilities,
    }
    if policy_path.exists() and load_json(policy_path) != policy and not replace_policy:
        raise ValueError("Existing client policy differs; use --replace-client-policy after review")
    if dry_run:
        print(f"DRY RUN: would write {policy_path.relative_to(target)} and {state_path.relative_to(target)}")
        return
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(json.dumps(policy, indent=2) + "\n", encoding="utf-8")
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")


def write_proposal(directory: Path, target: Path, version: str, capabilities: list[str], policy: dict[str, Any], dry_run: bool) -> None:
    proposal = directory / "proposal.json"
    markdown = directory / "PR_UPDATE.md"
    payload = {
        "schemaVersion": "framework-update-proposal/v1",
        "branch": f"ai-framework/update-{version}",
        "target": str(target),
        "frameworkVersion": version,
        "capabilities": capabilities,
        "clientId": policy["clientId"],
        "requiresHumanReview": True,
        "remotePullRequestCreated": False,
    }
    if dry_run:
        print(f"DRY RUN: would write update proposal to {directory}")
        return
    directory.mkdir(parents=True, exist_ok=True)
    proposal.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    markdown.write_text(
        "# Framework update proposal\n\n"
        f"- Branch: `{payload['branch']}`\n"
        f"- Framework version: `{version}`\n"
        f"- Client policy: `{policy['clientId']}`\n"
        "- Remote PR: not created; human review is required before merge.\n",
        encoding="utf-8",
    )


def bootstrap(args: argparse.Namespace) -> None:
    target = args.target.resolve()
    policy = load_json(args.client_policy)
    validate_policy(policy)
    version = framework_version()
    if args.version != version:
        raise ValueError(f"Requested version {args.version} is unavailable from this source; available: {version}")
    capabilities = args.capability or policy["enabledCapabilities"]
    if capabilities != policy["enabledCapabilities"]:
        raise ValueError("Selected capabilities must match the authorized client policy")

    lock = target / ".ai-framework.lock.json"
    upgrade = lock.exists()
    conflicts = [] if upgrade else managed_conflicts(target, capabilities)
    if conflicts and not args.replace_framework_artifacts:
        relative = ", ".join(str(path.relative_to(target)) for path in conflicts)
        raise ValueError(f"Existing unmanaged framework artifacts require --replace-framework-artifacts: {relative}")
    print(f"Framework version: {version}")
    print(f"Client policy: {policy['clientId']}")
    print("Capabilities: " + ", ".join(capabilities))
    if conflicts:
        print("Explicitly replacing unmanaged artifacts: " + ", ".join(str(path.relative_to(target)) for path in conflicts))
    if args.dry_run:
        subprocess.run(installer_command(target, capabilities, upgrade, True), check=True)
        write_policy_and_state(target, policy, version, capabilities, True, args.replace_client_policy)
        if args.proposal_dir:
            write_proposal(args.proposal_dir, target, version, capabilities, policy, True)
        return

    backup_root = None
    try:
        if conflicts:
            backup_root = Path(tempfile.mkdtemp(prefix=".ai-framework-adopt-", dir=target))
            for path in conflicts:
                backup = backup_root / path.relative_to(target)
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(path, backup)
        subprocess.run(installer_command(target, capabilities, upgrade, False), check=True)
        write_policy_and_state(target, policy, version, capabilities, False, args.replace_client_policy)
        if args.proposal_dir:
            write_proposal(args.proposal_dir, target, version, capabilities, policy, False)
    except Exception:
        if backup_root is not None:
            for backup in backup_root.rglob("*"):
                if backup.is_file():
                    destination = target / backup.relative_to(backup_root)
                    if not destination.exists():
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(backup, destination)
        raise
    finally:
        if backup_root is not None:
            shutil.rmtree(backup_root, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap a consumer with the versioned framework and an isolated client policy.")
    parser.add_argument("--target", required=True, type=Path)
    parser.add_argument("--version", required=True)
    parser.add_argument("--client-policy", required=True, type=Path)
    parser.add_argument("--capability", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--replace-framework-artifacts", action="store_true")
    parser.add_argument("--replace-client-policy", action="store_true")
    parser.add_argument("--proposal-dir", type=Path)
    args = parser.parse_args()
    try:
        bootstrap(args)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
