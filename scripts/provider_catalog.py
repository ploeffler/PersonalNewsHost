"""Evidence-first processing location catalog for future paid providers.

Unknown is not evidence of residency. No external provider is approved.
"""
CATALOG = {
    ("news", "openai"): {"provider": "OpenAI", "status": "unverified", "regions": (), "countries": (), "evidence_url": None, "checked_on": None},
    ("news", "other"): {"provider": "Other (not specified)", "status": "unverified", "regions": (), "countries": (), "evidence_url": None, "checked_on": None},
    ("voice", "openai"): {"provider": "OpenAI", "status": "unverified", "regions": (), "countries": (), "evidence_url": None, "checked_on": None},
    ("voice", "other"): {"provider": "Other (not specified)", "status": "unverified", "regions": (), "countries": (), "evidence_url": None, "checked_on": None},
    ("avatar", "paid"): {"provider": "External avatar provider (not specified)", "status": "unverified", "regions": (), "countries": (), "evidence_url": None, "checked_on": None},
    ("video", "paid"): {"provider": "External video provider (not specified)", "status": "unverified", "regions": (), "countries": (), "evidence_url": None, "checked_on": None},
}


def evaluate(stage, provider, region, country, strict=True):
    """Return verification result, never infer region from company headquarters."""
    record = CATALOG.get((stage, provider))
    if record is None:
        return {"status": "local_or_disabled", "allowed": True, "reason": "No external provider selected"}
    evidence_ok = (
        record["status"] == "verified"
        and bool(record["evidence_url"])
        and bool(record["checked_on"])
        and (region == "any" or region in record["regions"])
        and (not country or country in record["countries"])
    )
    return {
        "status": record["status"],
        "allowed": evidence_ok if strict else True,
        "reason": "Processing location verified" if evidence_ok else "No verified location evidence for the requested region",
        "evidence_url": record["evidence_url"],
        "checked_on": record["checked_on"],
    }
