"""
Parses a recruiter-supplied CSV file into a Candidate model.

Expected CSV columns (case-insensitive, flexible naming):
  name / full_name
  email / emails
  phone / phones
  location / city / country
  headline / title / role
  skills
  linkedin / github / links / portfolio / website
"""

from __future__ import annotations
import pandas as pd
from typing import Optional
from src.models import Candidate, Location, ProvenanceEntry


# Maps of normalised column name → canonical field
_COL_MAP: dict[str, str] = {
    "name": "full_name",
    "full_name": "full_name",
    "email": "emails",
    "emails": "emails",
    "e-mail": "emails",
    "phone": "phones",
    "phones": "phones",
    "mobile": "phones",
    "location": "location_raw",
    "city": "location_raw",
    "country": "country",
    "headline": "headline",
    "title": "headline",
    "role": "headline",
    "skills": "skills",
    # All link-type columns share the "links" canonical key
    "linkedin": "links",
    "github": "links",
    "links": "links",
    "portfolio": "links",
    "website": "links",
}


def _normalise_columns(df: pd.DataFrame) -> dict[str, list[str]]:
    """Return a mapping of canonical_field → [list of raw column names] for all present columns."""
    mapping: dict[str, list[str]] = {}
    for col in df.columns:
        key = col.strip().lower().replace(" ", "_")
        if key in _COL_MAP:
            canonical = _COL_MAP[key]
            mapping.setdefault(canonical, []).append(col)
    return mapping


def _split(value: str, sep: str = ",") -> list[str]:
    if not value or pd.isna(value):
        return []
    return [v.strip() for v in str(value).split(sep) if v.strip()]


def parse_csv(path: str) -> Candidate:
    """Read the recruiter CSV and return a partially-filled Candidate."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)

    if df.empty:
        raise ValueError(f"CSV file '{path}' is empty.")

    # Use the first data row
    row = df.iloc[0]
    col_map = _normalise_columns(df)

    def get_first(canonical: str) -> Optional[str]:
        """Return the row value for the first raw column mapped to this canonical field."""
        cols = col_map.get(canonical, [])
        for col in cols:
            val = row.get(col, "")
            if val and not pd.isna(val):
                return str(val).strip()
        return None

    def get_all(canonical: str) -> list[str]:
        """Collect and split values from ALL raw columns mapped to this canonical field."""
        results: list[str] = []
        for col in col_map.get(canonical, []):
            val = row.get(col, "")
            if val and not pd.isna(val):
                results.extend(_split(str(val)))
        return results

    candidate = Candidate()
    provenance: list[ProvenanceEntry] = []

    # --- full_name ---
    if name := get_first("full_name"):
        candidate.full_name = name
        provenance.append(ProvenanceEntry(field="full_name", source="recruiter.csv", method="csv_column"))

    # --- emails ---
    emails = get_all("emails")
    if emails:
        candidate.emails = emails
        provenance.append(ProvenanceEntry(field="emails", source="recruiter.csv", method="csv_column"))

    # --- phones ---
    phones = get_all("phones")
    if phones:
        candidate.phones = phones
        provenance.append(ProvenanceEntry(field="phones", source="recruiter.csv", method="csv_column"))

    # --- headline ---
    if headline := get_first("headline"):
        candidate.headline = headline
        provenance.append(ProvenanceEntry(field="headline", source="recruiter.csv", method="csv_column"))

    # --- skills ---
    skills = get_all("skills")
    if skills:
        candidate.skills = skills
        provenance.append(ProvenanceEntry(field="skills", source="recruiter.csv", method="csv_column"))

    # --- location ---
    loc_raw = get_first("location_raw")
    country_raw = get_first("country")
    if loc_raw or country_raw:
        candidate.location = Location(city=loc_raw, country=country_raw)
        provenance.append(ProvenanceEntry(field="location", source="recruiter.csv", method="csv_column"))

    # --- links: union ALL link-type columns ---
    links = get_all("links")
    if links:
        candidate.links = links
        provenance.append(ProvenanceEntry(field="links", source="recruiter.csv", method="csv_column"))

    candidate.provenance = provenance
    return candidate
