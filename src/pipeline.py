"""
Pipeline orchestrator.

Keeps main.py clean by exposing a single run_pipeline() function that
executes every stage in order:

  Parse → Normalize → Merge → Confidence → Provenance → Projection → Validation

The PDF input is optional. If pdf_path is None or the file does not exist,
the pipeline runs with only the CSV source.
"""

from __future__ import annotations
import json
import os

from src.parsers.csv_parser import parse_csv
from src.parsers.pdf_parser import parse_pdf
from src.models import Candidate

from src.normalizers.phone import normalise_phones
from src.normalizers.email import normalise_emails
from src.normalizers.date import normalise_date_range
from src.normalizers.country import normalise_country
from src.normalizers.skill import normalise_skills
from src.normalizers.name import normalise_name

from src.merge.merger import merge
from src.confidence.confidence import assign_confidence
from src.provenance.provenance import build_provenance
from src.projection.projector import load_config, project
from src.validation.validator import validate_output


def _normalise_candidate(candidate: Candidate) -> Candidate:
    """Apply all field-level normalizers to a parsed Candidate in-place."""
    if candidate.full_name:
        candidate.full_name = normalise_name(candidate.full_name)

    candidate.emails = normalise_emails(candidate.emails)
    candidate.phones = normalise_phones(candidate.phones)
    candidate.skills = normalise_skills(candidate.skills)

    if candidate.location and candidate.location.country:
        candidate.location.country = normalise_country(candidate.location.country)

    for exp in candidate.experience:
        exp.start, exp.end = normalise_date_range(exp.start, exp.end)

    for edu in candidate.education:
        edu.start, edu.end = normalise_date_range(edu.start, edu.end)

    return candidate


def run_pipeline(
    csv_path: str,
    output_canonical: str,
    output_projected: str,
    output_config_path: str,
    schema_path: str,
    pdf_path: str | None = None,
) -> dict:
    """
    Full pipeline.

    pdf_path is optional. When omitted (or the file does not exist), the
    pipeline produces output from the CSV source alone.

    Returns a dict with keys 'canonical' and 'projected' containing the
    final output dicts (also written to disk).
    """
    print("[1/7] Parsing inputs...")
    csv_candidate = parse_csv(csv_path)

    pdf_available = pdf_path is not None and os.path.isfile(pdf_path)
    if pdf_available:
        pdf_candidate = parse_pdf(pdf_path)  # type: ignore[arg-type]
        print(f"       PDF source: {pdf_path}")
    else:
        pdf_candidate = Candidate()
        if pdf_path:
            print(f"       Warning: PDF not found at '{pdf_path}' — running with CSV source only.")
        else:
            print("       No PDF provided — running with CSV source only.")

    print("[2/7] Normalizing fields...")
    csv_candidate = _normalise_candidate(csv_candidate)
    if pdf_available:
        pdf_candidate = _normalise_candidate(pdf_candidate)

    print("[3/7] Merging sources...")
    merged = merge(csv_candidate, pdf_candidate)

    print("[4/7] Assigning confidence scores...")
    merged = assign_confidence(merged, csv_candidate, pdf_candidate)

    print("[5/7] Building provenance...")
    merged = build_provenance(merged)

    print("[6/7] Projecting output...")
    canonical_dict = merged.to_dict()
    config = load_config(output_config_path)
    projected_dict = project(canonical_dict, config)

    print("[7/7] Validating output...")
    validate_output(canonical_dict, schema_path)

    # Write outputs
    os.makedirs(os.path.dirname(output_canonical) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_projected) or ".", exist_ok=True)

    with open(output_canonical, "w", encoding="utf-8") as f:
        json.dump(canonical_dict, f, indent=2, default=str)

    with open(output_projected, "w", encoding="utf-8") as f:
        json.dump(projected_dict, f, indent=2, default=str)

    print(f"\nDone.")
    print(f"  Canonical  → {output_canonical}")
    print(f"  Projected  → {output_projected}")

    return {"canonical": canonical_dict, "projected": projected_dict}
