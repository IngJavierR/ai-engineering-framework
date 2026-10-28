#!/usr/bin/env python3
"""Validate M2 frontend YAML contracts structurally with Draft 2020-12."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Hashable, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
    from jsonschema import Draft202012Validator
    from jsonschema.exceptions import SchemaError
except ImportError as error:  # pragma: no cover - depends on runtime setup
    print(
        "ERROR DEPENDENCY: install dependencies from "
        "tools/requirements-frontend-contracts.txt",
        file=sys.stderr,
    )
    raise SystemExit(2) from error


ROOT = Path(__file__).resolve().parent.parent
SCHEMA_DIRECTORY = ROOT / "docs" / "m2" / "schemas"
SCHEMA_PATHS = {
    "frontend-ui-input/v1": SCHEMA_DIRECTORY / "frontend-ui-input.v1.schema.json",
    "frontend-unit-tests/v1": (
        SCHEMA_DIRECTORY / "frontend-unit-tests.v1.schema.json"
    ),
    "frontend-ui-output/v1": SCHEMA_DIRECTORY / "frontend-ui-output.v1.schema.json",
}
ARGUMENT_CONTRACTS = {
    "input": "frontend-ui-input/v1",
    "unit_tests": "frontend-unit-tests/v1",
    "output": "frontend-ui-output/v1",
}


class DuplicateKeyError(yaml.YAMLError):
    """Raised when a YAML mapping repeats a key."""


class InvalidMappingKeyError(yaml.YAMLError):
    """Raised when a YAML mapping key cannot be stored safely."""


def _construct_mapping(
    loader: yaml.SafeLoader,
    node: yaml.nodes.MappingNode,
    deep: bool = False,
) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        mark = key_node.start_mark
        if not isinstance(key, Hashable):
            raise InvalidMappingKeyError(
                f"mapping key must be hashable at line {mark.line + 1}, "
                f"column {mark.column + 1}"
            )
        try:
            duplicate = key in mapping
        except TypeError as error:
            raise InvalidMappingKeyError(
                f"invalid mapping key at line {mark.line + 1}, "
                f"column {mark.column + 1}: {error}"
            ) from error
        if duplicate:
            raise DuplicateKeyError(
                f"duplicate key {key!r} at line {mark.line + 1}, "
                f"column {mark.column + 1}"
            )
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


class UniqueKeySafeLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


UniqueKeySafeLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping,
)


@dataclass(frozen=True)
class ValidationError:
    """A human-readable error emitted by the validator."""

    code: str
    document: Path
    location: str
    message: str

    def format(self) -> str:
        return f"{self.code} {self.document} {self.location}: {self.message}"


def _location(path: Iterable[Any]) -> str:
    parts = [str(part) for part in path]
    return "$" if not parts else "$." + ".".join(parts)


def _load_yaml(path: Path) -> tuple[Any | None, list[ValidationError]]:
    try:
        contents = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, [
            ValidationError("READ-001", path, "$", "file does not exist")
        ]
    except OSError as error:
        return None, [ValidationError("READ-002", path, "$", str(error))]

    try:
        document = yaml.load(contents, Loader=UniqueKeySafeLoader)
    except DuplicateKeyError as error:
        return None, [ValidationError("YAML-002", path, "$", str(error))]
    except InvalidMappingKeyError as error:
        return None, [ValidationError("YAML-004", path, "$", str(error))]
    except yaml.YAMLError as error:
        return None, [ValidationError("YAML-001", path, "$", str(error))]

    if not isinstance(document, Mapping):
        return None, [
            ValidationError(
                "YAML-003", path, "$", "document root must be a mapping"
            )
        ]
    return document, []


def _load_schema(schema_version: str, document: Path) -> tuple[Any | None, list[ValidationError]]:
    schema_path = SCHEMA_PATHS[schema_version]
    try:
        return json.loads(schema_path.read_text(encoding="utf-8")), []
    except (OSError, json.JSONDecodeError) as error:
        return None, [
            ValidationError(
                "SCHEMA-001",
                document,
                "$",
                f"cannot load schema {schema_path}: {error}",
            )
        ]


def validate_document(path: Path, expected_schema_version: str | None = None) -> list[ValidationError]:
    """Validate one YAML contract without modifying the input document."""
    document, errors = _load_yaml(path)
    if errors:
        return errors

    schema_version = document.get("schemaVersion")
    if not isinstance(schema_version, str):
        return [
            ValidationError(
                "CONTRACT-001", path, "$.schemaVersion", "must be a string"
            )
        ]
    if schema_version not in SCHEMA_PATHS:
        return [
            ValidationError(
                "CONTRACT-002",
                path,
                "$.schemaVersion",
                f"unknown contract version {schema_version!r}",
            )
        ]
    if expected_schema_version and schema_version != expected_schema_version:
        return [
            ValidationError(
                "CONTRACT-003",
                path,
                "$.schemaVersion",
                f"expected {expected_schema_version!r}, got {schema_version!r}",
            )
        ]

    schema, errors = _load_schema(schema_version, path)
    if errors:
        return errors

    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as error:
        return [ValidationError("SCHEMA-002", path, "$", str(error))]

    validator = Draft202012Validator(schema)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda error: (
            tuple(str(part) for part in error.absolute_path),
            error.message,
        ),
    )

    return [
        ValidationError("SCHEMA-003", path, _location(error.absolute_path), error.message)
        for error in errors
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Validate M2 frontend YAML contracts structurally."
    )
    parser.add_argument(
        "--input",
        action="append",
        type=Path,
        default=[],
        metavar="PATH",
        help="Validate a frontend-ui-input/v1 document; repeatable.",
    )
    parser.add_argument(
        "--unit-tests",
        dest="unit_tests",
        action="append",
        type=Path,
        default=[],
        metavar="PATH",
        help="Validate a frontend-unit-tests/v1 document; repeatable.",
    )
    parser.add_argument(
        "--output",
        action="append",
        type=Path,
        default=[],
        metavar="PATH",
        help="Validate a frontend-ui-output/v1 document; repeatable.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = build_parser().parse_args(argv)
    requested = [
        (contract, path)
        for argument, contract in ARGUMENT_CONTRACTS.items()
        for path in getattr(arguments, argument)
    ]
    if not requested:
        print(
            "ERROR CLI-001: specify at least one of --input, --unit-tests, "
            "or --output",
            file=sys.stderr,
        )
        return 2

    failures: list[ValidationError] = []
    for expected_version, path in requested:
        errors = validate_document(path, expected_version)
        if errors:
            failures.extend(errors)
        else:
            print(f"VALID {path}")

    for error in failures:
        print(error.format(), file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
