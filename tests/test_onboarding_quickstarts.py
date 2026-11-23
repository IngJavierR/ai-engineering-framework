"""Offline onboarding regression using the documented backend command sequence."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class OnboardingQuickstartTest(unittest.TestCase):
    def command(self, *arguments: str, cwd: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *arguments], cwd=cwd, text=True, capture_output=True, check=False)

    def test_backend_quickstart_prepares_and_verifies_after_in_scope_commit(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory)
            consumer = workspace / "consumer"; consumer.mkdir()
            subprocess.run(["git", "-C", str(consumer), "init", "-q"], check=True)
            subprocess.run(["git", "-C", str(consumer), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(consumer), "config", "user.name", "Test"], check=True)
            (consumer / ".gitignore").write_text(".venv/\n__pycache__/\nperformance/gatling/target/\n")
            (consumer / "backend/app").mkdir(parents=True)
            (consumer / "backend/app/main.py").write_text("value = 1\n")
            subprocess.run(["git", "-C", str(consumer), "add", "."], check=True)
            subprocess.run(["git", "-C", str(consumer), "commit", "-qm", "initial"], check=True)
            feature = workspace / "features/orders-api"
            scaffold = self.command(str(ROOT / "tools/new_feature.py"), "--stack", "python-fastapi", "--feature-id", "FEAT-ORDERS-001", "--consumer", "consumer", "--out", "features/orders-api", cwd=workspace)
            self.assertEqual(0, scaffold.returncode, scaffold.stderr)
            refresh = self.command(str(ROOT / "tools/refresh_manifest.py"), "--manifest", str(feature / "backend.input.yaml"), cwd=workspace)
            self.assertEqual(0, refresh.returncode, refresh.stderr)
            prepared = self.command(str(ROOT / "tools/validate_backend_workflow.py"), "prepare", "--manifest", str(feature / "backend.input.yaml"), "--consumer-repository", "consumer", "--workspace-root", ".", "--evidence-directory", "evidence", cwd=workspace)
            self.assertEqual(0, prepared.returncode, prepared.stderr)
            receipt = Path(json.loads(prepared.stdout)["artifact"])
            anchor = workspace / "custody/anchor.json"
            anchored = self.command(str(ROOT / "tools/make_anchor.py"), "--receipt", str(receipt), "--output", str(anchor), cwd=workspace)
            self.assertEqual(0, anchored.returncode, anchored.stderr)
            changes = consumer / "backend/db/changelog/changes"; changes.mkdir(parents=True)
            (changes / "001.xml").write_text('<databaseChangeLog><changeSet id="1" author="test"/></databaseChangeLog>')
            (consumer / "backend/db/changelog/db.changelog-master.xml").write_text('<databaseChangeLog><include file="changes/001.xml" relativeToChangelogFile="true"/></databaseChangeLog>')
            simulation = consumer / "performance/gatling/src/Simulation.scala"; simulation.parent.mkdir(parents=True); simulation.write_text("// getCustomer\n")
            (consumer / "backend/app/__pycache__").mkdir(); (consumer / "backend/app/__pycache__/main.pyc").write_bytes(b"cache")
            subprocess.run(["git", "-C", str(consumer), "add", "backend", "performance"], check=True)
            subprocess.run(["git", "-C", str(consumer), "commit", "-qm", "implementation"], check=True)
            verified = self.command(str(ROOT / "tools/validate_backend_workflow.py"), "verify", "--manifest", str(feature / "backend.input.yaml"), "--consumer-repository", "consumer", "--workspace-root", ".", "--evidence-directory", "evidence", "--receipt", str(receipt), "--external-anchor", str(anchor), cwd=workspace)
            self.assertEqual(0, verified.returncode, verified.stderr)
            self.assertEqual("PASS", json.loads(verified.stdout)["status"])
