#!/usr/bin/env python3
"""Create non-executable M2 input templates without inventing approvals."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create M2 feature input templates.")
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--stack", choices=("angular", "react"), required=True)
    parser.add_argument("--consumer", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    output = args.out
    if output.exists() and any(output.iterdir()):
        raise SystemExit("ERROR: output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    prefix = args.feature_id.replace("FEAT-", "").replace("-", "_").upper()
    (output / "specification.md").write_text(f"# {args.feature_id}\n\nDescribe confirmed requirements here.\n", encoding="utf-8")
    (output / "mockup.html").write_text("<!doctype html><html><body><main></main></body></html>\n", encoding="utf-8")
    (output / "unit-tests.yaml").write_text(f"schemaVersion: frontend-unit-tests/v1\nfeatureId: {args.feature_id}\ncases: []\n", encoding="utf-8")
    manifest = f'''schemaVersion: frontend-ui-input/v1
featureId: {args.feature_id}
templateStatus: illustrative-not-ready-for-execution
title: {args.feature_id} template
consumer:
  id: replace-consumer-id
  stack: {args.stack}
  repositoryRoot: {args.consumer}
  verificationStatus: not-verified
  detection:
    manifestPath: package.json
    lockfilePath: package-lock.json
    declaredVersions: {{"{args.stack if args.stack == "react" else "angularCore"}": not-verified, typescript: not-verified}}
    resolvedVersions: {{"{args.stack if args.stack == "react" else "angularCore"}": not-verified, typescript: not-verified}}
    detectionMethod: not-executed
    reason: Complete after reviewing consumer metadata.
baseline:
  commit: not-verified
  requiredInitialWorkingTreeState: clean
  snapshotPath: evidence/scope/initial-git-snapshot.json
  verificationStatus: not-verified
  reason: Complete after checking the consumer repository.
scope:
  allowedPaths: []
  protectedPaths: []
  deletionPolicy: {{allowed: false}}
functionalSpecification: {{id: SPEC-{prefix}-01, path: specification.md, sha256: sha256:{"0" * 64}}}
mockups: [{{id: SCR-{prefix}-01-01, title: Replace title, path: mockup.html, sha256: sha256:{"0" * 64}, conceptualComponentIds: []}}]
assets: []
apiContract: {{status: not-applicable, reason: Define if an API contract applies.}}
requirements: {{confirmed: [], ambiguities: [], inferences: [], authorizedDecisions: []}}
conceptualComponents: []
unitTests: {{path: unit-tests.yaml, sha256: sha256:{"0" * 64}, caseIds: []}}
files:
  - {{path: specification.md, sha256: sha256:{"0" * 64}}}
  - {{path: mockup.html, sha256: sha256:{"0" * 64}}}
  - {{path: unit-tests.yaml, sha256: sha256:{"0" * 64}}}
'''
    (output / f"{args.stack}.input.yaml").write_text(manifest, encoding="utf-8")
    print(f"Created illustrative M2 templates in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
