"""
Confidence scorer.

Assigns a per-field and overall confidence score to a merged Candidate.

Base weights by source:
  CSV   → 0.95  (structured, recruiter-supplied)
  PDF   → 0.80  (unstructured, heuristic-parsed)

Adjustments:
  Both sources agree on a field → +0.05
  Sources conflict on a field   → -0.10
  Field is missing entirely     → -0.05 (from the overall average)

overall_confidence is the mean of all per-field scores, clamped to [0, 1].
"""

from __future__ import annotations
from src.models import Candidate, ProvenanceEntry


_BASE_SCORE = {"recruiter.csv": 0.95, "resume.pdf": 0.80}
_DEFAULT_BASE = 0.75
_AGREEMENT_BONUS = 0.05
_CONFLICT_PENALTY = 0.10
_MISSING_PENALTY = 0.05


def _sources_for_field(provenance: list[ProvenanceEntry], field: str) -> list[str]:
    return [p.source for p in provenance if p.field == field]


def _field_score(sources: list[str], csv_val, pdf_val) -> float:
    """Compute the confidence score for a single field."""
    if not sources:
        # Field present but no provenance entry — shouldn't normally happen
        return _DEFAULT_BASE

    base = max(_BASE_SCORE.get(s, _DEFAULT_BASE) for s in sources)

    has_csv = "recruiter.csv" in sources
    has_pdf = "resume.pdf" in sources

    if has_csv and has_pdf:
        # Check agreement: both produced a value; compare them
        if csv_val and pdf_val and str(csv_val).lower().strip() == str(pdf_val).lower().strip():
            base = min(1.0, base + _AGREEMENT_BONUS)
        elif csv_val and pdf_val:
            base = max(0.0, base - _CONFLICT_PENALTY)
        # If one is missing, no bonus or penalty (union still wins)

    return round(base, 4)


def assign_confidence(merged: Candidate, csv_candidate: Candidate, pdf_candidate: Candidate) -> Candidate:
    """
    Compute per-field scores and set merged.overall_confidence.
    Returns the updated merged Candidate.
    """
    provenance = merged.provenance

    # Fields to score
    fields_to_check = {
        "full_name":  (merged.full_name,   csv_candidate.full_name,   pdf_candidate.full_name),
        "emails":     (merged.emails,      csv_candidate.emails,      pdf_candidate.emails),
        "phones":     (merged.phones,      csv_candidate.phones,      pdf_candidate.phones),
        "headline":   (merged.headline,    csv_candidate.headline,    pdf_candidate.headline),
        "skills":     (merged.skills,      csv_candidate.skills,      pdf_candidate.skills),
        "location":   (merged.location,    csv_candidate.location,    pdf_candidate.location),
        "experience": (merged.experience,  csv_candidate.experience,  pdf_candidate.experience),
        "education":  (merged.education,   csv_candidate.education,   pdf_candidate.education),
        "links":      (merged.links,       csv_candidate.links,       pdf_candidate.links),
    }

    scores: list[float] = []

    for field, (merged_val, csv_val, pdf_val) in fields_to_check.items():
        sources = _sources_for_field(provenance, field)
        has_value = bool(merged_val) if not isinstance(merged_val, list) else len(merged_val) > 0

        if not has_value:
            # Field is missing — apply penalty to the running mean
            scores.append(max(0.0, _DEFAULT_BASE - _MISSING_PENALTY))
        else:
            scores.append(_field_score(sources, csv_val, pdf_val))

    overall = round(sum(scores) / len(scores), 4) if scores else 0.0
    merged.overall_confidence = max(0.0, min(1.0, overall))
    return merged
