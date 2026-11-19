"""Integration tests for the M4 bootstrap facade in isolated Git consumers."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT
BOOTSTRAP = ROOT / "tools" / "bootstrap.py"


class BootstrapIntegrationTest(unittest.TestCase):
    def setUp(self):
        fixture_root = REPOSITORY_ROOT / ".bootstrap-test-tmp"
        fixture_root.mkdir(exist_ok=True)
        self.temporary_directory = tempfile.TemporaryDirectory(dir=fixture_root)
        self.root = Path(self.temporary_directory.name)
        self.target = self.root / "consumer"
        self.target.mkdir()
        subprocess.run(["git", "init", "-q", str(self.target)], check=True)
        self.policy = self.root / "policy.json"
        self.policy.write_text(json.dumps({
            "schemaVersion": "client-policy/v1",
            "clientId": "test-client",
            "enabledCapabilities": ["security-validation"],
            "additionalRules": [{"id": "TEST-001", "statement": "Keep local rules isolated."}],
            "exceptions": [],
        }), encoding="utf-8")

    def tearDown(self):
        self.temporary_directory.cleanup()

    def run_bootstrap(self, *extra):
        return subprocess.run([
            sys.executable, str(BOOTSTRAP), "--target", str(self.target),
            "--version", "0.4.0", "--client-policy", str(self.policy), *extra,
        ], cwd=ROOT, capture_output=True, text=True)

    def test_bootstrap_is_idempotent_and_preserves_isolated_policy(self):
        first = self.run_bootstrap()
        self.assertEqual(first.returncode, 0, first.stderr)
        state = json.loads((self.target / ".ai-framework/bootstrap.json").read_text())
        self.assertEqual(state["clientPolicy"], ".ai-framework/policies/test-client.json")
        second = self.run_bootstrap()
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("Already installed: matching lock and files", second.stdout)

    def test_unmanaged_artifacts_require_explicit_replacement(self):
        artifact = self.target / ".github/instructions/java.instructions.md"
        artifact.parent.mkdir(parents=True)
        artifact.write_text("consumer-owned", encoding="utf-8")
        blocked = self.run_bootstrap()
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("--replace-framework-artifacts", blocked.stderr)
        accepted = self.run_bootstrap("--replace-framework-artifacts")
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_dry_run_and_local_pr_proposal_do_not_require_remote_access(self):
        proposal = self.root / "proposal"
        dry_run = self.run_bootstrap("--dry-run", "--proposal-dir", str(proposal))
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        self.assertFalse((self.target / ".ai-framework.lock.json").exists())
        applied = self.run_bootstrap("--proposal-dir", str(proposal))
        self.assertEqual(applied.returncode, 0, applied.stderr)
        proposal_json = json.loads((proposal / "proposal.json").read_text())
        self.assertTrue(proposal_json["requiresHumanReview"])
        self.assertFalse(proposal_json["remotePullRequestCreated"])

    def test_different_existing_policy_requires_explicit_replacement(self):
        self.assertEqual(self.run_bootstrap().returncode, 0)
        replacement = json.loads(self.policy.read_text())
        replacement["additionalRules"] = [{"id": "TEST-002", "statement": "Different policy."}]
        self.policy.write_text(json.dumps(replacement), encoding="utf-8")
        blocked = self.run_bootstrap()
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn("--replace-client-policy", blocked.stderr)
        self.assertEqual(self.run_bootstrap("--replace-client-policy").returncode, 0)
