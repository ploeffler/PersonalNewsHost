"""Processing-location preference validation for future provider integrations.

This is not a verified provider residency directory.
"""
COUNTRIES = {
    "eu": ("AT", "DE", "FR", "IE", "NL", "SE"),
    "europe": ("AT", "DE", "FR", "IE", "NL", "SE", "CH", "GB"),
    "north_america": ("US", "CA"),
    "south_america": ("BR",),
    "asia": ("JP", "SG", "IN"),
    "oceania": ("AU",),
    "africa": ("ZA",),
    "any": (),
}


def validate_location(settings):
    region = settings.get("processing_region", "eu")
    country = settings.get("processing_country", "")
    strict = settings.get("require_verified_region", True)
    if region not in COUNTRIES:
        raise ValueError("Invalid processing region")
    if not isinstance(country, str):
        raise ValueError("Invalid processing country")
    if country and country not in {code for codes in COUNTRIES.values() for code in codes}:
        raise ValueError("Unknown processing country")
    if country and region != "any" and country not in COUNTRIES[region]:
        raise ValueError("Country and region mismatch")
    if not isinstance(strict, bool):
        raise ValueError("Strict processing location flag must be boolean")
    return {"region": region, "country": country, "strict": strict}
