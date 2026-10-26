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


# Conservative bilingual event candidates: no automatic translation or factual merging.
import re
import unicodedata

_SHARED_TERMS = {
    "usa": "unitedstates", "us": "unitedstates", "america": "unitedstates",
    "vereinigte": "unitedstates", "staaten": "unitedstates",
    "ukraine": "ukraine", "ukrainian": "ukraine",
    "eu": "europeanunion", "european": "europeanunion", "europäische": "europeanunion",
    "wahl": "election", "wahlen": "election", "election": "election", "elections": "election",
    "regierung": "government", "government": "government",
    "präsident": "president", "president": "president",
    "polizei": "police", "police": "police",
    "unfall": "accident", "accident": "accident",
    "klima": "climate", "climate": "climate",
    "gericht": "court", "court": "court",
    "krieg": "war", "war": "war",
}
_STOPWORDS = set("der die das dem den des ein eine einer eines und oder im in am an auf zu zum zur mit von für aus über nach ist sind wird bei the a an and or of to for from in on at with by as is are was were has have new latest says said".split())


def event_tokens(headline):
    """Normalized bilingual headline tokens; never translate full article text."""
    normalized = unicodedata.normalize("NFKC", str(headline)).casefold().replace("ß", "ss")
    words = re.findall(r"[^\W_]+", normalized, re.UNICODE)
    return {_SHARED_TERMS.get(word, word) for word in words if len(word) >= 3 and word not in _STOPWORDS}


def event_candidate(a, b):
    """Return review-only evidence; require two shared tokens and an entity-like anchor.

    This is a high-precision candidate heuristic, not proof that articles report
    the same event, are independent, or corroborate one another.
    """
    left, right = event_tokens(a), event_tokens(b)
    common = left & right
    if len(common) < 2:
        return {"candidate": False, "score": 0.0, "shared_terms": sorted(common), "review_required": True}
    score = len(common) / max(1, len(left | right))
    return {"candidate": score >= 0.3, "score": round(score, 3),
            "shared_terms": sorted(common), "review_required": True}
