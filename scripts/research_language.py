"""Language-neutral groundwork for news research (DE/EN).

This module does not translate or alter production behavior until explicitly wired
into the research pipeline. It uses no external service or API key.
"""
from urllib.parse import urlparse

SUPPORTED_LANGUAGES = ("de", "en")
DEFAULT_LANGUAGE = "de"


def normalize_language(value, default=DEFAULT_LANGUAGE):
    """Return a supported ISO 639-1 language or a safe default."""
    if isinstance(value, str):
        code = value.strip().lower().replace("_", "-").split("-")[0]
        if code in SUPPORTED_LANGUAGES:
            return code
    return default


def research_terms(headline, language="de"):
    """Prepare language-tagged search terms without inventing translations."""
    return {"query": str(headline).strip(), "language": normalize_language(language)}


def source_metadata(url, language="de"):
    """Annotate a source with language and publisher host for later comparisons."""
    parsed = urlparse(url)
    return {"url": url, "publisher": parsed.hostname or "", "language": normalize_language(language)}
