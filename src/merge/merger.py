"""
Merger.

Merges two Candidate objects (one from CSV, one from PDF) into a single
canonical Candidate, applying the following policy:

  emails    → union (deduped)
  phones    → union (deduped)
  skills    → union (deduped)
  links     → union (deduped)
  experience → combined, duplicates removed (by title+company key)
  education  → combined, duplicates removed (by degree+institution key)
  provenance → combined from both sources
  scalar fields (full_name, headline, location):
      1. Prefer the CSV value if present ("structured source")
      2. Fall back to the PDF value
      3. If both are present, use whichever is more complete (longer string)
"""

from __future__ import annotations
from src.models import Candidate, Experience, Education


def _dedup_experience(entries: list[Experience]) -> list[Experience]:
    seen: set[str] = set()
    result: list[Experience] = []
    for exp in entries:
        key = f"{(exp.title or '').lower().strip()}|{(exp.company or '').lower().strip()}"
        if key not in seen:
            seen.add(key)
            result.append(exp)
    return result


def _dedup_education(entries: list[Education]) -> list[Education]:
    seen: set[str] = set()
    result: list[Education] = []
    for edu in entries:
        key = f"{(edu.degree or '').lower().strip()}|{(edu.institution or '').lower().strip()}"
        if key not in seen:
            seen.add(key)
            result.append(edu)
    return result


def _pick_scalar(csv_val, pdf_val):
    """
    Choose a scalar field value.
    Preference order:
      1. CSV (structured source) — preferred when present
      2. PDF — fallback when CSV is missing
      3. Both present: whichever is more complete (longer string representation)
    """
    if csv_val and pdf_val:
        # Both sources provided a value — pick the more complete one
        csv_str = str(csv_val).strip()
        pdf_str = str(pdf_val).strip()
        return csv_val if len(csv_str) >= len(pdf_str) else pdf_val
    if csv_val:
        return csv_val
    if pdf_val:
        return pdf_val
    return None


def _union(a: list[str], b: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in a + b:
        lower = item.lower()
        if lower not in seen:
            seen.add(lower)
            result.append(item)
    return result


def merge(csv_candidate: Candidate, pdf_candidate: Candidate) -> Candidate:
    """
    Merge csv_candidate and pdf_candidate into one Candidate.
    The csv_candidate's candidate_id is kept as the authoritative ID.
    """
    merged = Candidate(candidate_id=csv_candidate.candidate_id)

    # --- Scalar fields ---
    merged.full_name = _pick_scalar(csv_candidate.full_name, pdf_candidate.full_name)
    merged.headline = _pick_scalar(csv_candidate.headline, pdf_candidate.headline)
    merged.location = _pick_scalar(csv_candidate.location, pdf_candidate.location)

    # --- List / union fields ---
    merged.emails = _union(csv_candidate.emails, pdf_candidate.emails)
    merged.phones = _union(csv_candidate.phones, pdf_candidate.phones)
    merged.skills = _union(csv_candidate.skills, pdf_candidate.skills)
    merged.links = _union(csv_candidate.links, pdf_candidate.links)

    # --- Structured lists with dedup ---
    merged.experience = _dedup_experience(csv_candidate.experience + pdf_candidate.experience)
    merged.education = _dedup_education(csv_candidate.education + pdf_candidate.education)

    # --- Provenance: combine both ---
    merged.provenance = csv_candidate.provenance + pdf_candidate.provenance

    return merged
