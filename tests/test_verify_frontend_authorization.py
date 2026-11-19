"""Tests for fail-closed local SSH authorization verification."""

import importlib.util
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
VERIFIER_PATH = REPOSITORY_ROOT / "tools" / "verify_frontend_authorization.py"
SPEC = importlib.util.spec_from_file_location("frontend_authorization", VERIFIER_PATH)
authorization = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = authorization
assert SPEC.loader is not None
SPEC.loader.exec_module(authorization)


class FrontendAuthorizationVerifierTestCase(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.consumer = self.root / "consumer"
        self.external = self.root / "external"
        self.external.mkdir()
        self.git("init", str(self.consumer), cwd=self.root)
        self.git("config", "user.name", "Fixture", cwd=self.consumer)
        self.git("config", "user.email", "fixture@example.invalid", cwd=self.consumer)
        self.key = self.create_key("authorized")
        self.other_key = self.create_key("other")
        self.commit_number = 0

    def tearDown(self):
        self.temporary_directory.cleanup()

    def git(self, *arguments, cwd):
        environment = {
            key: value for key, value in os.environ.items() if not key.startswith("GIT_")
        }
        return subprocess.run(
            ["git", *arguments], cwd=cwd, env=environment, check=True,
            capture_output=True, text=True,
        )

    def create_key(self, name):
        key = self.root / name
        subprocess.run(
            ["ssh-keygen", "-q", "-t", "ed25519", "-N", "", "-f", str(key)],
            check=True,
            capture_output=True,
            text=True,
        )
        return key

    def commit(self, key=None, message="authorization fixture"):
        self.commit_number += 1
        (self.consumer / "record.txt").write_text(
            f"{message}-{self.commit_number}", encoding="utf-8"
        )
        self.git("add", "record.txt", cwd=self.consumer)
        arguments = ["commit", "-m", message]
        if key:
            arguments = [
                "-c", "gpg.format=ssh",
                "-c", f"user.signingkey={key}",
                "-c", "commit.gpgsign=true",
                *arguments,
            ]
        self.git(*arguments, cwd=self.consumer)
        return self.git("rev-parse", "HEAD", cwd=self.consumer).stdout.strip()

    def policy(self, *, key=None, principal="owner@example.invalid", feature_ids=None,
               decision_ids=None, requirement_ids=None, repository_root=None,
               revoked=None, directory=None):
        key = key or self.key
        document = {
            "schemaVersion": "authorization-trust/v1",
            "repositoryRoot": repository_root or str(self.consumer.resolve()),
            "authorizedSigners": [{
                "principal": principal,
                "publicKey": key.with_suffix(".pub").read_text(encoding="utf-8").strip(),
                "featureIds": feature_ids or ["FEAT-CUSTOMER-PROFILE-001"],
                "decisionIds": decision_ids or ["DEC-CUSTOMER-PROFILE-001-01"],
                "requirementIds": requirement_ids or ["REQ-CUSTOMER-PROFILE-001-02"],
            }],
            "revokedKeyFingerprints": revoked or [],
        }
        target = (directory or self.external) / "policy.yaml"
        target.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        return target

    def verify(self, approval, baseline=None, policy="default", **overrides):
        if policy == "default":
            policy = self.policy()
        return authorization.verify_authorization(
            consumer_repository=overrides.get("consumer_repository", self.consumer),
            policy_path=policy,
            approval_commit=approval,
            baseline_commit=baseline or approval,
            principal=overrides.get("principal", "owner@example.invalid"),
            feature_id=overrides.get("feature_id", "FEAT-CUSTOMER-PROFILE-001"),
            decision_id=overrides.get("decision_id", "DEC-CUSTOMER-PROFILE-001-01"),
            requirement_ids=overrides.get("requirement_ids", ("REQ-CUSTOMER-PROFILE-001-02",)),
            manifest_directory=overrides.get("manifest_directory"),
        )

    def test_t01_accepts_trusted_signed_ancestor(self):
        approval = self.commit(self.key)
        self.consumer.joinpath("consumer-signers").write_text("invalid", encoding="utf-8")
        self.git("config", "gpg.ssh.allowedSignersFile", "consumer-signers", cwd=self.consumer)
        result = self.verify(approval)
        self.assertEqual(("PASS", "AUTH-000"), (result.status, result.code))

    def test_t02_blocks_missing_or_invalid_policy(self):
        approval = self.commit(self.key)
        self.assertEqual("AUTH-POLICY-000", self.verify(approval, policy=None).code)
        invalid = self.external / "invalid.yaml"
        invalid.write_text("schemaVersion: authorization-trust/v1\n", encoding="utf-8")
        self.assertEqual("AUTH-POLICY-001", self.verify(approval, policy=invalid).code)

    def test_t03_blocks_unsafe_or_mismatched_policy_location(self):
        approval = self.commit(self.key)
        inside = self.policy(directory=self.consumer)
        self.assertEqual("AUTH-POLICY-002", self.verify(approval, policy=inside).code)
        mismatch = self.policy(repository_root="/other/consumer")
        self.assertEqual("AUTH-POLICY-003", self.verify(approval, policy=mismatch).code)
        linked_directory = self.root / "linked-external"
        linked_directory.symlink_to(self.external, target_is_directory=True)
        linked_policy = linked_directory / "policy.yaml"
        self.assertEqual("AUTH-POLICY-002", self.verify(approval, policy=linked_policy).code)
        self.assertEqual(
            "AUTH-POLICY-002",
            self.verify(approval, manifest_directory=self.external).code,
        )

    def test_t04_blocks_missing_unsigned_and_invalid_signature_commits(self):
        signed = self.commit(self.key)
        self.assertEqual("AUTH-COMMIT-002", self.verify("a" * 40, policy=self.policy()).code)
        unsigned = self.commit()
        self.assertEqual("AUTH-SIGNATURE-001", self.verify(unsigned, policy=self.policy()).code)
        raw = self.git("cat-file", "commit", signed, cwd=self.consumer).stdout
        tampered = raw.replace("authorization fixture", "authorization fixturE", 1)
        result = subprocess.run(
            ["git", "hash-object", "-w", "-t", "commit", "--stdin"],
            cwd=self.consumer,
            input=tampered,
            capture_output=True,
            text=True,
            check=True,
        )
        invalid_sha = result.stdout.strip()
        self.assertEqual("AUTH-SIGNATURE-001", self.verify(invalid_sha, baseline=invalid_sha).code)

    def test_t05_blocks_untrusted_principal_and_scope(self):
        approval = self.commit(self.other_key)
        self.assertEqual("AUTH-SIGNATURE-001", self.verify(approval).code)
        trusted = self.commit(self.key)
        self.assertEqual("AUTH-SCOPE-001", self.verify(trusted, principal="other@example.invalid").code)
        self.assertEqual("AUTH-SCOPE-001", self.verify(trusted, feature_id="FEAT-OTHER-001").code)
        self.assertEqual("AUTH-SCOPE-001", self.verify(trusted, decision_id="DEC-OTHER-001-01").code)
        self.assertEqual("AUTH-SCOPE-001", self.verify(trusted, requirement_ids=("REQ-OTHER-001-01",)).code)

    def test_t06_blocks_non_ancestor_and_revoked_keys(self):
        approval = self.commit(self.key, "approved")
        self.git("checkout", "--orphan", "unrelated", cwd=self.consumer)
        self.git("rm", "-rf", ".", cwd=self.consumer)
        unrelated = self.commit(self.key, "unrelated")
        self.assertEqual("AUTH-COMMIT-003", self.verify(approval, baseline=unrelated).code)
        fingerprint = authorization._fingerprint(self.key.with_suffix(".pub").read_text().strip())
        self.assertEqual("AUTH-REVOKED-001", self.verify(approval, policy=self.policy(revoked=[fingerprint])).code)

    def test_t07_blocks_revoked_signer_when_another_candidate_is_available(self):
        approval = self.commit(self.key)
        other = self.commit(self.other_key)
        document = yaml.safe_load(self.policy().read_text(encoding="utf-8"))
        document["authorizedSigners"].append({
            **document["authorizedSigners"][0],
            "publicKey": self.other_key.with_suffix(".pub").read_text(encoding="utf-8").strip(),
        })
        fingerprint = authorization._fingerprint(
            self.key.with_suffix(".pub").read_text(encoding="utf-8").strip()
        )
        document["revokedKeyFingerprints"] = [fingerprint]
        policy = self.external / "mixed-policy.yaml"
        policy.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with mock.patch.object(authorization, "_read_policy", return_value=(document, None)):
            self.assertEqual("AUTH-SIGNATURE-001", self.verify(approval, policy=policy).code)
            self.assertEqual("PASS", self.verify(other, policy=policy).status)

    def test_t08_blocks_when_signature_environment_is_unavailable(self):
        approval = self.commit(self.key)
        with mock.patch.object(authorization.shutil, "which", return_value=None):
            self.assertEqual("AUTH-ENV-001", self.verify(approval).code)

    def test_t09_blocks_external_tool_failures_before_trust_evaluation(self):
        approval = self.commit(self.key)
        with mock.patch.object(
            authorization.subprocess,
            "run",
            side_effect=FileNotFoundError,
        ):
            self.assertEqual("AUTH-ENV-001", self.verify(approval).code)
        with mock.patch.object(
            authorization.subprocess,
            "run",
            side_effect=subprocess.TimeoutExpired("git", 15),
        ):
            self.assertEqual("AUTH-ENV-003", self.verify(approval).code)
        with mock.patch.object(
            authorization.subprocess,
            "run",
            side_effect=PermissionError,
        ):
            self.assertEqual("AUTH-ENV-002", self.verify(approval).code)

    def test_t10_rejects_non_individual_principals(self):
        approval = self.commit(self.key)
        for principal in (
            "owner@example.invalid,other@example.invalid",
            "owner@example.invalid other@example.invalid",
            "owner@example.invalid\tother@example.invalid",
            "owner-*",
            "!owner@example.invalid",
            "owner\\example.invalid",
        ):
            with self.subTest(principal=principal):
                self.assertEqual(
                    "AUTH-PRINCIPAL-001",
                    self.verify(approval, principal=principal).code,
                )
        document = yaml.safe_load(self.policy().read_text(encoding="utf-8"))
        document["authorizedSigners"][0]["principal"] = "owner@example.invalid,other@example.invalid"
        policy = self.external / "invalid-principal-policy.yaml"
        policy.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        with mock.patch.object(authorization, "_read_policy", return_value=(document, None)):
            self.assertEqual("AUTH-SCOPE-001", self.verify(approval, policy=policy).code)

    def test_t11_ignores_injected_git_configuration_and_repository_variables(self):
        approval = self.commit(self.key)
        other = self.root / "injected-repository"
        other.mkdir()
        self.git("init", cwd=other)
        self.git("config", "user.name", "Other", cwd=other)
        self.git("config", "user.email", "other@example.invalid", cwd=other)
        other_key = self.create_key("injected")
        (other / "record.txt").write_text("other", encoding="utf-8")
        self.git("add", "record.txt", cwd=other)
        self.git(
            "-c", "gpg.format=ssh", "-c", f"user.signingkey={other_key}",
            "-c", "commit.gpgsign=true", "commit", "-m", "other", cwd=other,
        )
        injected_signers = self.root / "injected-signers"
        injected_signers.write_text(
            f"owner@example.invalid {other_key.with_suffix('.pub').read_text().strip()}\n",
            encoding="utf-8",
        )
        injected_global = self.root / "global.gitconfig"
        injected_global.write_text(
            "[gpg \"ssh\"]\n\tallowedSignersFile = " + str(injected_signers) + "\n",
            encoding="utf-8",
        )
        injected = {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "gpg.ssh.allowedSignersFile",
            "GIT_CONFIG_VALUE_0": str(injected_signers),
            "GIT_CONFIG_GLOBAL": str(injected_global),
            "GIT_CONFIG_SYSTEM": str(injected_global),
            "GIT_DIR": str(other / ".git"),
            "GIT_WORK_TREE": str(other),
            "GIT_COMMON_DIR": str(other / ".git"),
            "GIT_OBJECT_DIRECTORY": str(other / ".git" / "objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(other / ".git" / "objects"),
        }
        with mock.patch.dict(os.environ, injected, clear=False):
            self.assertEqual("PASS", self.verify(approval).status)
            unsigned = self.commit()
            self.assertEqual("AUTH-SIGNATURE-001", self.verify(unsigned).code)

    def test_t12_rejects_consumer_subdirectory_and_linked_worktree(self):
        approval = self.commit(self.key)
        nested = self.consumer / "nested"
        nested.mkdir()
        self.assertEqual("AUTH-CONSUMER-002", self.verify(approval, consumer_repository=nested).code)
        linked = self.root / "linked-worktree"
        self.git("worktree", "add", "--detach", str(linked), approval, cwd=self.consumer)
        self.assertEqual("AUTH-CONSUMER-002", self.verify(approval, consumer_repository=linked).code)


if __name__ == "__main__":
    unittest.main()
