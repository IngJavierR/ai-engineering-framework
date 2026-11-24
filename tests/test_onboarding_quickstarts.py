"""C7: Full monorepo onboarding test following both quickstarts literally."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/onboarding"
EXAMPLES = ROOT / "docs/m2/examples/customer-profile"


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True, text=True)


def _cmd(cwd: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=cwd, capture_output=True, text=True, check=False)


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


class OnboardingMonorepoTest(unittest.TestCase):
    """C7.1–C7.6: Full monorepo quickstart execution."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp.name)
        self._start = time.monotonic()
        self._create_fixture()

    def tearDown(self):
        self.temp.cleanup()

    # ------------------------------------------------------------------ fixture

    def _create_fixture(self):
        """C7.1: Create the full monorepo before any command."""
        app = self.workspace / "app"
        app.mkdir()
        _git(app, "init", "-b", "main")
        _git(app, "config", "user.email", "test@example.invalid")
        _git(app, "config", "user.name", "Test")

        # Frontend (C7.1)
        (app / "frontend/src/app/features/customer-profile").mkdir(parents=True)
        (app / "frontend/src/app/features/customer-profile/original.ts").write_text("export const x = 1;\n")
        (app / "frontend/src/app").mkdir(exist_ok=True)
        (app / "frontend/src/app/app.routes.ts").write_text("export const routes = [];\n")
        pkg = {"dependencies": {"@angular/core": "^22.0.0"}, "devDependencies": {"typescript": "^5.6.0"}}
        lock = {"lockfileVersion": 3, "packages": {
            "node_modules/@angular/core": {"version": "22.0.1"},
            "node_modules/typescript": {"version": "5.6.0"},
        }}
        (app / "frontend/package.json").write_text(json.dumps(pkg))
        (app / "frontend/package-lock.json").write_text(json.dumps(lock))
        # 5000 node_modules files (C7.1)
        nm = app / "frontend/node_modules"
        nm.mkdir(parents=True)
        for i in range(5000):
            d = nm / f"pkg-{i}"; d.mkdir()
            (d / "index.js").write_text(f"module.exports={i}")
        # .angular cache
        (app / "frontend/.angular/cache").mkdir(parents=True)
        (app / "frontend/.angular/cache/x").write_text("cache")

        # Backend (C7.1)
        (app / "backend/app").mkdir(parents=True)
        (app / "backend/app/__init__.py").write_text("")
        (app / "backend/app/main.py").write_text("app = 1\n")
        (app / "backend/pyproject.toml").write_text("[project]\nname = 'app'\n")
        (app / "backend/.venv/bin").mkdir(parents=True)
        (app / "backend/.venv/bin/python").write_text("#!/bin/sh\npython3 $@")
        (app / "backend/backend.egg-info").mkdir()
        (app / "backend/backend.egg-info/PKG-INFO").write_text("Metadata-Version: 2.1\n")

        # Configuration (C7.1)
        (app / ".env").write_text("DB_PASSWORD=secret\n")
        (app / ".env.example").write_text("DB_PASSWORD=changeme\n")
        (app / "docker-compose.yml").write_text("version: '3'\nservices: {}\n")
        (app / "db").mkdir()
        (app / "db/Dockerfile").write_text("FROM liquibase/liquibase:5.0\n")

        # Gatling pom.xml with Maven namespaces (C7.1, should not trigger java stack C3)
        (app / "performance/gatling").mkdir(parents=True)
        (app / "performance/gatling/pom.xml").write_text(
            '<?xml version="1.0"?><project xmlns="http://maven.apache.org/POM/4.0.0" '
            'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
            'xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 '
            'http://maven.apache.org/xsd/maven-4.0.0.xsd">'
            "<modelVersion>4.0.0</modelVersion>"
            "<groupId>test</groupId><artifactId>test</artifactId><version>1.0</version></project>"
        )

        # .gitignore (C7.1)
        (app / ".gitignore").write_text(
            ".env\n.venv/\n__pycache__/\n.pytest_cache/\n.hypothesis/\n"
            "*.egg-info/\nnode_modules/\ndist/\n.angular/\ncoverage/\n"
            "performance/gatling/target/\n"
        )

        # Commit tracked files (not ignored ones)
        tracked = [
            ".env.example", ".gitignore", "frontend/package.json", "frontend/package-lock.json",
            "frontend/src", "backend/app", "backend/pyproject.toml",
            "docker-compose.yml", "db", "performance/gatling/pom.xml",
        ]
        subprocess.run(["git", "-C", str(app), "add", *tracked], check=True, capture_output=True)
        _git(app, "commit", "-qm", "initial commit")

    def _fw(self, *args: str, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
        return _cmd(cwd or self.workspace, str(ROOT / "tools" / args[0]), *args[1:])

    def _make_anchor(self, receipt: Path) -> Path:
        anchor = self.workspace / "custody" / "anchor.json"
        anchor.parent.mkdir(exist_ok=True)
        result = self._fw("make_anchor.py", "--receipt", str(receipt), "--output", str(anchor))
        self.assertEqual(0, result.returncode, f"make_anchor: {result.stderr}")
        return anchor

    def _load_receipt(self) -> Path:
        receipts = sorted((self.workspace / "evidence").glob("*.receipt.json"), key=lambda p: p.stat().st_mtime, reverse=True)
        self.assertTrue(receipts, "No receipt found in evidence/")
        return receipts[0]

    # ------------------------------------------------------------------ C7.3 backend

    def test_backend_quickstart_pass(self):
        """C7.3: Full backend quickstart → PREPARE PASS + VERIFY PASS."""
        ws = self.workspace
        app = ws / "app"
        fw = str(ROOT / "tools")

        # scaffold (C7.3 step 1)
        scaffold = self._fw("new_feature.py", "--stack", "python-fastapi",
                             "--feature-id", "FEAT-ORDERS-001",
                             "--consumer", "app", "--contract-dir", "backend/contract",
                             "--out", "features/orders-api")
        self.assertEqual(0, scaffold.returncode, f"scaffold: {scaffold.stderr}")

        # commit contract, refresh, preflight
        _git(app, "add", "backend/contract")
        _git(app, "commit", "-qm", "docs: add approved orders API contract")
        refresh = self._fw("refresh_manifest.py", "--manifest",
                           str(ws / "features/orders-api/backend.input.yaml"))
        self.assertEqual(0, refresh.returncode, f"refresh: {refresh.stderr}")

        preflight = self._fw("validate_backend_contracts.py",
                             "--input", str(ws / "features/orders-api/backend.input.yaml"),
                             "--phase", "preflight")
        self.assertEqual(0, preflight.returncode, f"preflight: {preflight.stderr}")

        # feature branch + PREPARE
        _git(app, "switch", "-c", "feat/orders-001")
        prepare = self._fw("validate_backend_workflow.py", "prepare",
                           "--manifest", str(ws / "features/orders-api/backend.input.yaml"),
                           "--consumer-repository", "app",
                           "--workspace-root", ".", "--evidence-directory", "evidence")
        self.assertEqual(0, prepare.returncode, f"PREPARE: {prepare.stderr}")
        receipt = Path(json.loads(prepare.stdout)["artifact"])
        # Verify no frontend vocabulary (C5)
        payload = json.loads(prepare.stdout)
        self.assertNotIn("frontend", json.dumps(payload).lower(),
                         f"Frontend vocabulary in PREPARE output: {prepare.stdout}")
        anchor = self._make_anchor(receipt)

        # implementation (C7.3 step 2–3)
        (app / "backend/db/changelog/changes").mkdir(parents=True)
        (app / "backend/db/changelog/changes/001.xml").write_text(
            '<databaseChangeLog><changeSet id="1" author="eng"/></databaseChangeLog>'
        )
        (app / "backend/db/changelog/db.changelog-master.xml").write_text(
            '<databaseChangeLog>'
            '<include file="changes/001.xml" relativeToChangelogFile="true"/>'
            '</databaseChangeLog>'
        )
        sim = app / "performance/gatling/src/test/java/Sim.java"
        sim.parent.mkdir(parents=True)
        sim.write_text('String base = System.getenv("TARGET_BASE_URL"); // getCustomer\n')
        subprocess.run(["git", "-C", str(app), "add",
                        "backend/db/changelog", "performance/gatling/src"], check=True, capture_output=True)
        _git(app, "commit", "-qm", "feat: implement backend")

        # caches that appear at runtime (C7.3 step 3 – before VERIFY)
        (app / "backend/app/__pycache__").mkdir(exist_ok=True)
        (app / "backend/app/__pycache__/m.pyc").write_bytes(b"cached")
        (app / "backend/.pytest_cache").mkdir(exist_ok=True)
        (app / "backend/.pytest_cache/x").write_text("x")
        (app / "backend/.hypothesis").mkdir(exist_ok=True)
        (app / "backend/.hypothesis/x").write_text("x")
        (app / "performance/gatling/target").mkdir(exist_ok=True)
        (app / "performance/gatling/target/x").write_text("x")

        # verify (C7.3 step 4)
        phase_verify = self._fw("validate_backend_contracts.py",
                                "--input", str(ws / "features/orders-api/backend.input.yaml"),
                                "--phase", "verify")
        self.assertEqual(0, phase_verify.returncode, f"--phase verify: {phase_verify.stderr}")
        verify = self._fw("validate_backend_workflow.py", "verify",
                          "--manifest", str(ws / "features/orders-api/backend.input.yaml"),
                          "--consumer-repository", "app",
                          "--workspace-root", ".", "--evidence-directory", "evidence",
                          "--receipt", str(receipt), "--external-anchor", str(anchor))
        self.assertEqual(0, verify.returncode, f"VERIFY: {verify.stderr}\nstdout={verify.stdout}")
        payload = json.loads(verify.stdout)
        self.assertEqual("PASS", payload["status"])
        self.assertNotIn("frontend", json.dumps(payload).lower(),
                         f"Frontend vocabulary in VERIFY output: {verify.stdout}")
        self.assertIn("backendEvidence", payload)
        # check time
        self.assertLess(time.monotonic() - self._start, 60, "Backend flow exceeded 60s")

    # ------------------------------------------------------------------ C7.5 negatives (backend)

    def _backend_prepare(self):
        """Set up a clean PREPARE state with minimal implementation for negative tests."""
        ws = self.workspace
        app = ws / "app"
        scaffold = self._fw("new_feature.py", "--stack", "python-fastapi",
                             "--feature-id", "FEAT-NEG-001",
                             "--consumer", "app", "--contract-dir", "backend/contract",
                             "--out", "features/neg-api")
        self.assertEqual(0, scaffold.returncode, scaffold.stderr)
        _git(app, "add", "backend/contract")
        _git(app, "commit", "-qm", "neg: contract")
        refresh = self._fw("refresh_manifest.py", "--manifest",
                           str(ws / "features/neg-api/backend.input.yaml"))
        self.assertEqual(0, refresh.returncode, refresh.stderr)
        _git(app, "switch", "-c", "feat/neg-001")
        # Add minimal implementation so --phase verify content checks pass
        (app / "backend/db/changelog/changes").mkdir(parents=True)
        (app / "backend/db/changelog/changes/001.xml").write_text(
            '<databaseChangeLog><changeSet id="1" author="eng"/></databaseChangeLog>')
        (app / "backend/db/changelog/db.changelog-master.xml").write_text(
            '<databaseChangeLog>'
            '<include file="changes/001.xml" relativeToChangelogFile="true"/>'
            '</databaseChangeLog>')
        sim = app / "performance/gatling/src/test/java/Sim.java"
        sim.parent.mkdir(parents=True)
        sim.write_text('String base = System.getenv("TARGET_BASE_URL"); // getCustomer\n')
        _git(app, "add", "backend/db/changelog", "performance/gatling/src")
        _git(app, "commit", "-qm", "neg: implementation")
        prepare = self._fw("validate_backend_workflow.py", "prepare",
                           "--manifest", str(ws / "features/neg-api/backend.input.yaml"),
                           "--consumer-repository", "app",
                           "--workspace-root", ".", "--evidence-directory", "evidence")
        self.assertEqual(0, prepare.returncode, prepare.stderr)
        receipt = Path(json.loads(prepare.stdout)["artifact"])
        anchor = self._make_anchor(receipt)
        return receipt, anchor

    def test_negative_backend_commit_in_frontend(self):
        """C7.5: commit in frontend/ from backend feature → FAIL SCOPE-009."""
        receipt, anchor = self._backend_prepare()
        (self.workspace / "app/frontend/src/app/app.ts").write_text("x=2")
        subprocess.run(["git", "-C", str(self.workspace / "app"), "add",
                        "frontend/src/app/app.ts"], check=True, capture_output=True)
        _git(self.workspace / "app", "commit", "-qm", "oops")
        result = self._fw("validate_backend_workflow.py", "verify",
                          "--manifest", str(self.workspace / "features/neg-api/backend.input.yaml"),
                          "--consumer-repository", "app", "--workspace-root", ".",
                          "--evidence-directory", "evidence",
                          "--receipt", str(receipt), "--external-anchor", str(anchor))
        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn("SCOPE-009", json.dumps(payload), f"Expected SCOPE-009: {payload}")

    def test_negative_backend_contract_modified(self):
        """C7.5: approved contract modified → BE-HASH-001."""
        receipt, anchor = self._backend_prepare()
        (self.workspace / "app/backend/contract/openapi.yaml").write_text("modified: true")
        result = self._fw("validate_backend_workflow.py", "verify",
                          "--manifest", str(self.workspace / "features/neg-api/backend.input.yaml"),
                          "--consumer-repository", "app", "--workspace-root", ".",
                          "--evidence-directory", "evidence",
                          "--receipt", str(receipt), "--external-anchor", str(anchor))
        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        self.assertIn("BE-HASH-001", json.dumps(payload), f"Expected BE-HASH-001: {payload}")

    def test_negative_branch_switch_reports_git003(self):
        """C7.5: switch to main after PREPARE → GIT-003 with both branches in message."""
        receipt, anchor = self._backend_prepare()
        _git(self.workspace / "app", "switch", "main")
        result = self._fw("validate_backend_workflow.py", "verify",
                          "--manifest", str(self.workspace / "features/neg-api/backend.input.yaml"),
                          "--consumer-repository", "app", "--workspace-root", ".",
                          "--evidence-directory", "evidence",
                          "--receipt", str(receipt), "--external-anchor", str(anchor))
        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        dump = json.dumps(payload)
        self.assertIn("GIT-003", dump, f"Expected GIT-003: {payload}")
        self.assertIn("feat/neg-001", dump)
        self.assertIn("main", dump)

    def test_negative_new_undeclared_ignored_path_blocks(self):
        """C7.5: new ignored path after PREPARE → GIT-005 with path in message."""
        receipt, anchor = self._backend_prepare()
        # Add a new exclude that wasn't there at PREPARE
        (self.workspace / "app/.git/info").mkdir(exist_ok=True)
        exclude = (self.workspace / "app/.git/info/exclude")
        exclude.write_text("backend/secrets.local\n")
        (self.workspace / "app/backend/secrets.local").write_text("token=x")
        result = self._fw("validate_backend_workflow.py", "verify",
                          "--manifest", str(self.workspace / "features/neg-api/backend.input.yaml"),
                          "--consumer-repository", "app", "--workspace-root", ".",
                          "--evidence-directory", "evidence",
                          "--receipt", str(receipt), "--external-anchor", str(anchor))
        self.assertNotEqual(0, result.returncode)
        payload = json.loads(result.stdout)
        dump = json.dumps(payload)
        self.assertIn("GIT-005", dump, f"Expected GIT-005: {payload}")
        self.assertIn("secrets.local", dump)


if __name__ == "__main__":
    unittest.main()
