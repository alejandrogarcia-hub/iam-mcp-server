def get_country_code(country_name: str) -> str:
    """
    Convert full country name to ISO_3166-1_alpha-2 code in lowercase.

    Args:
        country_name: Full country name or existing ISO code

    Returns:
        ISO_3166-1_alpha-2 code in lowercase
    """
    # Common country name to ISO code mapping
    country_mapping = {
        # English names
        "united states": "us",
        "united kingdom": "gb",
        "canada": "ca",
        "australia": "au",
        "germany": "de",
        "france": "fr",
        "spain": "es",
        "italy": "it",
        "netherlands": "nl",
        "switzerland": "ch",
        "austria": "at",
        "belgium": "be",
        "sweden": "se",
        "norway": "no",
        "denmark": "dk",
        "finland": "fi",
        "poland": "pl",
        "czech republic": "cz",
        "hungary": "hu",
        "portugal": "pt",
        "ireland": "ie",
        "greece": "gr",
        "japan": "jp",
        "south korea": "kr",
        "china": "cn",
        "india": "in",
        "singapore": "sg",
        "hong kong": "hk",
        "israel": "il",
        "brazil": "br",
        "mexico": "mx",
        "argentina": "ar",
        "chile": "cl",
        "colombia": "co",
        "south africa": "za",
        "new zealand": "nz",
        "russia": "ru",
        "ukraine": "ua",
        "turkey": "tr",
        "saudi arabia": "sa",
        "united arab emirates": "ae",
        # Add more as needed
    }

    # Normalize input
    normalized = country_name.lower().strip()

    # If it's already a 2-letter code, return it lowercase
    if len(normalized) == 2 and normalized.isalpha():
        return normalized

    # Look up in mapping
    return country_mapping.get(normalized, None)
