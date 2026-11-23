#!/usr/bin/env python3
"""Create non-executable M2 input templates without inventing approvals."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser(description="Create M2 feature input templates.")
    parser.add_argument("--feature-id", required=True)
    parser.add_argument("--stack", choices=("angular", "react", "java-spring", "python-fastapi", "generic"), required=True)
    parser.add_argument("--consumer", required=True)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    output = args.out
    if output.exists() and any(output.iterdir()):
        raise SystemExit("ERROR: output directory must be absent or empty")
    output.mkdir(parents=True, exist_ok=True)
    if args.stack in {"java-spring", "python-fastapi", "generic"}:
        template = ROOT / "docs" / "backend" / "examples" / "customer-api"
        for name in ("backend.input.yaml", "openapi.yaml", "test-cases.yaml"):
            shutil.copy2(template / name, output / name)
        for path in (output / "backend.input.yaml", output / "test-cases.yaml"):
            path.write_text(path.read_text(encoding="utf-8").replace("FEAT-CUSTOMER-API-001", args.feature_id), encoding="utf-8")
        print(f"Created illustrative backend templates in {output}")
        return 0
    template = ROOT / "docs" / "m2" / "examples" / "customer-profile"
    for name in ("specification.md", "mockup.html", "unit-tests.yaml", f"{args.stack}.input.yaml"):
        shutil.copy2(template / name, output / name)
    manifest = (output / f"{args.stack}.input.yaml").read_text(encoding="utf-8")
    manifest = manifest.replace("FEAT-CUSTOMER-PROFILE-001", args.feature_id)
    manifest = manifest.replace("../../../../labs/angular-customer-profile-consumer", args.consumer)
    (output / f"{args.stack}.input.yaml").write_text(manifest, encoding="utf-8")
    unit = (output / "unit-tests.yaml").read_text(encoding="utf-8").replace("FEAT-CUSTOMER-PROFILE-001", args.feature_id)
    (output / "unit-tests.yaml").write_text(unit, encoding="utf-8")
    print(f"Created illustrative M2 templates in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
