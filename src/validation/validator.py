"""
Validator.

Validates the final output dict against schema.json using jsonschema.
Raises ValidationError with a clear message if the output does not conform.
"""

from __future__ import annotations
import json
import jsonschema
from jsonschema import validate, ValidationError


def load_schema(schema_path: str) -> dict:
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_output(output: dict, schema_path: str) -> None:
    """
    Validate the output dict against the JSON Schema at schema_path.
    Raises jsonschema.ValidationError on failure, returns None on success.
    """
    schema = load_schema(schema_path)
    try:
        validate(instance=output, schema=schema)
    except ValidationError as exc:
        raise ValidationError(
            f"Output validation failed: {exc.message}\n"
            f"  Field path: {' → '.join(str(p) for p in exc.absolute_path)}\n"
            f"  Failing value: {exc.instance!r}"
        ) from exc
