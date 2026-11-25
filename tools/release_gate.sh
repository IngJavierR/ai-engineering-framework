#!/usr/bin/env bash
# Release gate for ai-engineering-framework. Exits 0 only on RELEASE_GATE_PASS.
set -euo pipefail

PYTHON="${PYTHON:-python3}"

echo "=== Installing dependencies ==="
"$PYTHON" -m pip install -q -r tools/requirements-frontend-contracts.txt pytest

echo "=== Running full test suite ==="
"$PYTHON" -m pytest -q tests

echo "=== Running slow tests ==="
"$PYTHON" -m pytest -q tests -m slow

echo "=== Running onboarding quickstart tests ==="
"$PYTHON" -m pytest -q tests/test_onboarding_quickstarts.py -vv

echo "=== Verifying java-spring profile dry-run ==="
_GATE_TMP=$(mktemp -d)
git init -q "$_GATE_TMP"
"$PYTHON" tools/install.py --target "$_GATE_TMP" --profile java-spring --dry-run >/dev/null
unset _GATE_TMP

echo "=== Verifying CHANGELOG entry matches framework version ==="
FW_VERSION=$("$PYTHON" -c 'import yaml; print(yaml.safe_load(open("framework.yaml"))["framework"]["version"])')
grep -q "^## \[${FW_VERSION}\]" CHANGELOG.md || { echo "ERROR: CHANGELOG missing section [${FW_VERSION}]"; exit 1; }

echo "RELEASE_GATE_PASS"
