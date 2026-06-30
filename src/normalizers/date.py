"""
Date normalizer.

Converts human-readable date strings to YYYY-MM format.

Examples:
  January 2023  → 2023-01
  Jan 2023      → 2023-01
  2023-01-15    → 2023-01
  Present       → present
  03/2020       → 2020-03
"""

from __future__ import annotations
import re
from dateutil import parser as dateutil_parser


_PRESENT_RE = re.compile(r"^\s*(present|current|now|ongoing)\s*$", re.IGNORECASE)


def normalise_date(raw: str) -> str:
    """
    Parse a date string and return YYYY-MM.
    Returns 'present' for "Present / Current" strings.
    Returns the original stripped string if parsing fails.
    """
    raw = raw.strip()

    if _PRESENT_RE.match(raw):
        return "present"

    # Handle bare year: "2022"
    if re.match(r"^\d{4}$", raw):
        return raw  # keep as YYYY; no month available

    # Handle MM/YYYY or YYYY/MM
    m = re.match(r"^(\d{1,2})/(\d{4})$", raw)
    if m:
        return f"{m.group(2)}-{int(m.group(1)):02d}"

    try:
        dt = dateutil_parser.parse(raw, default=dateutil_parser.parse("1900-01-01"))
        return dt.strftime("%Y-%m")
    except (ValueError, OverflowError):
        return raw


def normalise_date_range(start: str | None, end: str | None) -> tuple[str | None, str | None]:
    """Normalise a start/end date pair, returning (YYYY-MM | None, YYYY-MM | 'present' | None)."""
    norm_start = normalise_date(start) if start else None
    norm_end = normalise_date(end) if end else None
    return norm_start, norm_end
