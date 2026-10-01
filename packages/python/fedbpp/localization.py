"""Locale normalization and deterministic localized-name fallback helpers."""
from __future__ import annotations

import re
import unicodedata


def locale_candidates(locale: str | None) -> list[str]:
    """Return requested locale, base language, then English without duplicates."""
    requested = (locale or "en").replace("_", "-")
    parts = requested.split("-")
    base = parts[0]
    candidates = [requested]
    if base == "zh":
        script = next((part for part in parts[1:] if len(part) == 4), None)
        region = next((part for part in parts[1:] if len(part) == 2), None)
        if script in {"Hans", "Hant"} and script not in candidates:
            candidates.append(f"zh-{script}")
        elif region in {"CN", "SG", "MY"}:
            candidates.append("zh-Hans")
        elif region in {"TW", "HK", "MO"}:
            candidates.append("zh-Hant")
    if base not in candidates:
        candidates.append(base)
    if "en" not in candidates:
        candidates.append("en")
    return candidates


def searchable(value: str) -> str:
    """Normalize text for locale-independent exercise lookup."""
    folded = unicodedata.normalize("NFKD", value).casefold()
    folded = "".join(char for char in folded if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", folded).strip()
