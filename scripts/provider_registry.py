#!/usr/bin/env python3
"""Provider contracts and safe selection plan for a future PersonalNewsHost 2.0.

No network requests, payments or secret access occur in this module.
"""
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol

try:
    from .processing_location import validate_location
except ImportError:
    from processing_location import validate_location


class NewsProvider(Protocol):
    def prepare(self, articles: list[dict]) -> str: ...


class VoiceProvider(Protocol):
    def synthesize(self, script: str, output_path: str) -> None: ...


class AvatarProvider(Protocol):
    def render(self, audio_path: str, output_path: str) -> None: ...


class VideoProvider(Protocol):
    def assemble(self, assets: list[str], output_path: str) -> None: ...


@dataclass(frozen=True)
class ProviderSpec:
    stage: str
    key: str
    paid: bool
    implemented: bool


REGISTRY = {
    "news": {
        "disabled": ProviderSpec("news", "disabled", False, True),
        "openai": ProviderSpec("news", "openai", True, False),
        "other": ProviderSpec("news", "other", True, False),
    },
    "voice": {
        "local": ProviderSpec("voice", "local", False, True),
        "openai": ProviderSpec("voice", "openai", True, False),
        "other": ProviderSpec("voice", "other", True, False),
    },
    "avatar": {
        "static": ProviderSpec("avatar", "static", False, True),
        "paid": ProviderSpec("avatar", "paid", True, False),
    },
    "video": {
        "local": ProviderSpec("video", "local", False, True),
        "paid": ProviderSpec("video", "paid", True, False),
    },
}
DEFAULTS = {"news": "disabled", "voice": "local", "avatar": "static", "video": "local"}


def _budget(value, label):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"{label} must be a finite nonnegative euro amount") from None
    if not amount.is_finite() or amount < 0:
        raise ValueError(f"{label} must be a finite nonnegative euro amount")
    return amount


def plan(config: dict) -> dict:
    """Validate a proposed provider mix; return metadata only, never execute it."""
    advanced = config.get("advanced_services", {})
    if not isinstance(advanced, dict):
        raise ValueError("advanced_services must be an object")
    location = validate_location(advanced)
    chosen = {}
    for stage, default in DEFAULTS.items():
        key = advanced.get(stage + "_provider", default)
        if key not in REGISTRY[stage]:
            raise ValueError(f"Unknown {stage} provider: {key}")
        chosen[stage] = REGISTRY[stage][key]
    per_video = _budget(advanced.get("max_per_video_eur", 0), "max_per_video_eur")
    per_month = _budget(advanced.get("max_per_month_eur", 0), "max_per_month_eur")
    paid = any(spec.paid for spec in chosen.values())
    allowed = advanced.get("allow_paid", False) is True
    return {
        "providers": {stage: spec.key for stage, spec in chosen.items()},
        "processing_location": location,
        "paid_requested": paid,
        "consent": allowed,
        "per_video_eur": str(per_video),
        "per_month_eur": str(per_month),
        "ready": not paid and all(spec.implemented for spec in chosen.values()),
        "blockers": (
            (["Paid services are not authorized"] if paid and not allowed else [])
            + (["Positive per-video and monthly budgets required"] if paid and (per_video <= 0 or per_month <= 0) else [])
            + (["Processing location not verified for this provider"] if paid and location["strict"] else [])
            + (["Paid adapters and enforceable billing controls are not implemented"] if paid else [])
        ),
    }


def require_executable_version(config: dict) -> None:
    """Fail closed until the separate 2.0 runtime has been implemented and tested."""
    version = str(config.get("production_version", "1.0"))
    if version == "1.0":
        return
    if version == "2.0":
        plan(config)
        raise RuntimeError("Version 2.0 is a configuration preview only; no paid API calls are permitted")
    raise ValueError(f"Unknown production version: {version}")
