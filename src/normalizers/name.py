"""
Name normalizer.

Converts raw name strings to title-cased, stripped canonical form.

Examples:
  " ANANYA  roy "  → Ananya Roy
  "ananya roy"     → Ananya Roy
  "JOHN DOE"       → John Doe
"""

from __future__ import annotations
import re


# Particles that should stay lowercase unless they start the name
_LOWERCASE_PARTICLES = {"van", "de", "der", "den", "von", "la", "le", "al", "bin", "binti"}


def normalise_name(raw: str) -> str:
    """
    Strip extra whitespace, title-case each word, preserve lowercase particles
    in the middle of the name.
    """
    # Collapse internal whitespace
    cleaned = re.sub(r"\s+", " ", raw).strip()

    words = cleaned.split()
    result: list[str] = []
    for i, word in enumerate(words):
        lower = word.lower()
        if i > 0 and lower in _LOWERCASE_PARTICLES:
            result.append(lower)
        else:
            # Handle hyphenated names: O'Brien, Anne-Marie
            result.append("-".join(part.capitalize() for part in word.split("-")))
    return " ".join(result)
