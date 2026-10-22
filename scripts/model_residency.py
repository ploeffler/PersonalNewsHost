"""Offline validation of model-level residency evidence; never calls provider APIs."""
from datetime import date
from urllib.parse import urlparse

REQUIRED = ("provider", "service", "model_id", "deployment_type", "source_region", "destination_regions", "processing_scope", "data_retention_policy", "evidence_url", "checked_on")


def validate_candidate(candidate, permitted_regions):
    """Fail closed: a complete record is necessary, not proof of provider behavior."""
    missing = [key for key in REQUIRED if not candidate.get(key)]
    if candidate.get("subprocessors_reviewed") is not True:
        missing.append("subprocessors_reviewed")
    destinations = candidate.get("destination_regions", [])
    if not isinstance(destinations, list) or not destinations:
        if "destination_regions" not in missing:
            missing.append("destination_regions")
    elif any(not isinstance(x, str) or x not in permitted_regions for x in destinations):
        missing.append("destination_regions_outside_policy")
    url = candidate.get("evidence_url", "")
    if not isinstance(url, str) or urlparse(url).scheme != "https" or not urlparse(url).netloc:
        missing.append("valid_https_evidence_url")
    try:
        checked = date.fromisoformat(candidate.get("checked_on") or "")
        if checked > date.today():
            missing.append("future_review_date")
    except (ValueError, TypeError):
        missing.append("valid_review_date")
    return {"documentation_complete": not missing, "missing": sorted(set(missing)), "approved": False}
