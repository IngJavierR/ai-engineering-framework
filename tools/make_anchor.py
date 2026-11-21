#!/usr/bin/env python3
"""Create a value-correspondence anchor from a valid M2 PREPARE receipt."""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("frontend_workflow", ROOT / "tools" / "validate_frontend_workflow.py")
workflow = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = workflow
SPEC.loader.exec_module(workflow)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create an external M2 workflow anchor from a PREPARE receipt.")
    parser.add_argument("--receipt", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    receipt_path = arguments.receipt.resolve()
    output = arguments.output.absolute()
    receipt, receipt_error = workflow.load_json(receipt_path)
    if receipt is None or workflow.validate_receipt(receipt):
        print(f"ERROR: invalid receipt: {receipt_error or workflow.validate_receipt(receipt)}", file=sys.stderr)
        return 1
    consumer = Path(receipt["consumer"]["root"])
    if output.parent.resolve() == receipt_path.parent.resolve() or not workflow.external_to_consumer(output, consumer):
        print("ERROR: anchor output must be outside both receipt custody and consumer repository", file=sys.stderr)
        return 1
    anchor = {
        "anchorVersion": workflow.ANCHOR_VERSION,
        "executionId": receipt["executionId"],
        "receiptSha256": workflow.digest(receipt_path),
        "manifestSha256": receipt["manifest"]["sha256"],
        "inputs": receipt["inputs"],
        "consumer": receipt["consumer"],
        "baseCommit": receipt["baseCommit"],
        "snapshotSha256": receipt["snapshot"]["sha256"],
    }
    workflow.atomic_json(output, anchor)
    print(json.dumps({"anchor": str(output), "warning": "The anchor proves only value correspondence; custody and authority remain the invoker's responsibility."}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
