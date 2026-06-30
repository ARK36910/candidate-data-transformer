"""
Phone normalizer.

Converts raw phone strings to E.164 format: +<country_code><number>
Falls back to the cleaned numeric string when parsing fails.

Examples:
  9876543210       → +919876543210   (assumes India default)
  +1 (555) 123-4567 → +15551234567
  020 7946 0958    → +442079460958
"""

from __future__ import annotations
import re
import phonenumbers


_DEFAULT_REGION = "IN"  # assumed region when no country code is present


def normalise_phone(raw: str, default_region: str = _DEFAULT_REGION) -> str:
    """
    Parse and format a phone number in E.164.
    Returns the cleaned original string if parsing fails.
    """
    raw = raw.strip()
    try:
        parsed = phonenumbers.parse(raw, default_region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.phonenumberutil.NumberParseException:
        pass

    # Strip everything except digits and leading +
    digits = re.sub(r"[^\d+]", "", raw)
    return digits if digits else raw


def normalise_phones(phones: list[str], default_region: str = _DEFAULT_REGION) -> list[str]:
    """Normalise a list of phone strings, deduplicating by E.164 result."""
    seen: set[str] = set()
    result: list[str] = []
    for p in phones:
        normalised = normalise_phone(p, default_region)
        if normalised not in seen:
            seen.add(normalised)
            result.append(normalised)
    return result
