"""
Provenance builder.

Creates structured provenance entries for each field in the merged Candidate.
Called after merge; augments/replaces the raw per-parser provenance with
a clean, deduplicated record that lists every source that contributed data.
"""

from __future__ import annotations
from src.models import Candidate, ProvenanceEntry


def build_provenance(merged: Candidate) -> Candidate:
    """
    Deduplicate and finalize provenance entries.

    Keeps one entry per (field, source) pair — the first method encountered
    wins. If a field has data but no provenance entry (e.g. added programmatically),
    an 'inferred' entry is added.

    Returns the updated Candidate.
    """
    # Dedup: keep first occurrence per (field, source)
    seen: set[tuple[str, str]] = set()
    clean: list[ProvenanceEntry] = []

    for entry in merged.provenance:
        key = (entry.field, entry.source)
        if key not in seen:
            seen.add(key)
            clean.append(entry)

    # Ensure every populated field has at least one provenance entry
    field_sources = {e.field for e in clean}

    def _has_value(field: str) -> bool:
        val = getattr(merged, field, None)
        if isinstance(val, list):
            return len(val) > 0
        return val is not None

    fields_to_check = [
        "full_name", "emails", "phones", "headline",
        "skills", "location", "experience", "education", "links",
    ]

    for field in fields_to_check:
        if _has_value(field) and field not in field_sources:
            clean.append(ProvenanceEntry(
                field=field,
                source="pipeline",
                method="inferred",
            ))

    merged.provenance = clean
    return merged
