"""
Email normalizer.

Converts raw email strings to lowercase, stripped canonical form.

Examples:
  ABC @ Gmail.com   → abc@gmail.com
  " User+tag@WORK.org " → user+tag@work.org
"""

from __future__ import annotations
import re


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def normalise_email(raw: str) -> str:
    """
    Strip whitespace, remove spaces around @, lowercase.
    Returns the cleaned string; raises ValueError if invalid.
    """
    cleaned = re.sub(r"\s+", "", raw).lower()
    if not _EMAIL_RE.match(cleaned):
        raise ValueError(f"Invalid email address: {raw!r}")
    return cleaned


def normalise_emails(emails: list[str]) -> list[str]:
    """Normalise a list of email strings, silently dropping invalid ones and deduplicating."""
    seen: set[str] = set()
    result: list[str] = []
    for e in emails:
        try:
            normalised = normalise_email(e)
            if normalised not in seen:
                seen.add(normalised)
                result.append(normalised)
        except ValueError:
            pass
    return result
