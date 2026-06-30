"""
Country normalizer.

Converts country names and common aliases to ISO 3166-1 alpha-2 codes.

Examples:
  India          → IN
  United States  → US
  USA            → US
  Deutschland    → DE
"""

from __future__ import annotations

_COUNTRY_MAP: dict[str, str] = {
    # Common English names
    "afghanistan": "AF", "albania": "AL", "algeria": "DZ", "argentina": "AR",
    "australia": "AU", "austria": "AT", "bangladesh": "BD", "belgium": "BE",
    "brazil": "BR", "canada": "CA", "chile": "CL", "china": "CN",
    "colombia": "CO", "czech republic": "CZ", "czechia": "CZ",
    "denmark": "DK", "egypt": "EG", "finland": "FI", "france": "FR",
    "germany": "DE", "deutschland": "DE", "ghana": "GH", "greece": "GR",
    "hong kong": "HK", "hungary": "HU", "india": "IN", "indonesia": "ID",
    "iran": "IR", "iraq": "IQ", "ireland": "IE", "israel": "IL",
    "italy": "IT", "japan": "JP", "jordan": "JO", "kenya": "KE",
    "malaysia": "MY", "mexico": "MX", "morocco": "MA", "netherlands": "NL",
    "new zealand": "NZ", "nigeria": "NG", "norway": "NO", "pakistan": "PK",
    "peru": "PE", "philippines": "PH", "poland": "PL", "portugal": "PT",
    "romania": "RO", "russia": "RU", "russian federation": "RU",
    "saudi arabia": "SA", "singapore": "SG", "south africa": "ZA",
    "south korea": "KR", "korea": "KR", "spain": "ES", "sri lanka": "LK",
    "sweden": "SE", "switzerland": "CH", "taiwan": "TW", "thailand": "TH",
    "turkey": "TR", "türkiye": "TR", "ukraine": "UA",
    "united arab emirates": "AE", "uae": "AE",
    "united kingdom": "GB", "uk": "GB", "great britain": "GB",
    "united states": "US", "usa": "US", "us": "US", "america": "US",
    "vietnam": "VN", "viet nam": "VN",
}


def normalise_country(raw: str) -> str:
    """
    Convert a country name or alias to its ISO 3166-1 alpha-2 code.
    Returns the uppercased raw string when no match is found (could already be a code).
    """
    key = raw.strip().lower()

    # Direct lookup
    if key in _COUNTRY_MAP:
        return _COUNTRY_MAP[key]

    # Maybe it's already an alpha-2 code
    upper = raw.strip().upper()
    if len(upper) == 2 and upper.isalpha():
        return upper

    # Partial match: allow "United States of America" → "united states"
    for name, code in _COUNTRY_MAP.items():
        if name in key or key in name:
            return code

    return upper  # best effort
