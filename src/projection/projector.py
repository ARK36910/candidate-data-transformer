"""
Projector.

Reads output_config.json and applies a projection to the canonical Candidate dict:
  - Select only the requested fields
  - Rename fields using an optional "rename" map
  - Include or strip confidence and provenance blocks
  - Represent missing values as null (JSON null) or omit them entirely

output_config.json schema:
{
  "fields": ["full_name", "emails", ...],   // fields to include; omit to include all
  "rename": {"full_name": "name"},           // optional rename map
  "include_confidence": true,
  "include_provenance": false,
  "missing_values": "null" | "omit"
}
"""

from __future__ import annotations
import json
from typing import Any


def load_config(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def project(canonical: dict[str, Any], config: dict) -> dict[str, Any]:
    """
    Apply the projection config to the canonical candidate dict.
    Returns a new dict representing the projected output.
    """
    fields: list[str] | None = config.get("fields")
    rename: dict[str, str] = config.get("rename", {})
    include_confidence: bool = config.get("include_confidence", True)
    include_provenance: bool = config.get("include_provenance", True)
    missing_strategy: str = config.get("missing_values", "null")  # "null" or "omit"

    # Determine which fields to project
    if fields:
        selected_keys = list(fields)
    else:
        selected_keys = [k for k in canonical.keys() if k not in ("overall_confidence", "provenance")]

    result: dict[str, Any] = {}

    for key in selected_keys:
        output_key = rename.get(key, key)
        value = canonical.get(key)

        # Decide what to do with missing / empty values
        is_missing = value is None or value == [] or value == {}
        if is_missing:
            if missing_strategy == "omit":
                continue
            else:  # "null"
                result[output_key] = None
        else:
            result[output_key] = value

    # Conditionally include confidence
    if include_confidence:
        conf_key = rename.get("overall_confidence", "overall_confidence")
        result[conf_key] = canonical.get("overall_confidence")

    # Conditionally include provenance
    if include_provenance:
        prov_key = rename.get("provenance", "provenance")
        result[prov_key] = canonical.get("provenance")

    return result
