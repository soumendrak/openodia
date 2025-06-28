"""Utility functions for text normalization and phonetic conversion."""

from __future__ import annotations

import string
import unicodedata

__all__ = ["normalize_text", "phonetic_odia"]


def normalize_text(text: str | None) -> str:
    """Normalize text by removing punctuation and collapsing whitespace."""
    if text is None:
        return ""

    normalized = unicodedata.normalize("NFC", str(text)).lower()
    punctuation_set = set(string.punctuation + "।")
    normalized = "".join(ch for ch in normalized if ch not in punctuation_set)
    normalized = " ".join(normalized.split())
    return normalized


_ODIA_PHONETIC_MAP = {
    "ଅ": "a",
    "ଆ": "aa",
    "ଇ": "i",
    "ଈ": "ii",
    "ଉ": "u",
    "ଊ": "uu",
    "ଋ": "r",
    "ଌ": "l",
    "ଏ": "e",
    "ଐ": "ai",
    "ଓ": "o",
    "ଔ": "au",
    "କ": "ka",
    "ଖ": "kha",
    "ଗ": "ga",
    "ଘ": "gha",
    "ଙ": "nga",
    "ଚ": "ca",
    "ଛ": "cha",
    "ଜ": "ja",
    "ଝ": "jha",
    "ଞ": "nya",
    "ଟ": "ta",
    "ଠ": "tha",
    "ଡ": "da",
    "ଢ": "dha",
    "ଣ": "na",
    "ତ": "ta",
    "ଥ": "tha",
    "ଦ": "da",
    "ଧ": "dha",
    "ନ": "na",
    "ପ": "pa",
    "ଫ": "pha",
    "ବ": "ba",
    "ଭ": "bha",
    "ମ": "ma",
    "ୟ": "ya",
    "ର": "ra",
    "ଲ": "la",
    "ଳ": "la",
    "ଵ": "va",
    "ଶ": "sha",
    "ଷ": "ssa",
    "ସ": "sa",
    "ହ": "ha",
    "୦": "0",
    "୧": "1",
    "୨": "2",
    "୩": "3",
    "୪": "4",
    "୫": "5",
    "୬": "6",
    "୭": "7",
    "୮": "8",
    "୯": "9",
}

_MATRA_MAP = {
    "ା": "aa",
    "ି": "i",
    "ୀ": "ii",
    "ୁ": "u",
    "ୂ": "uu",
    "ୃ": "ru",
    "ୄ": "ruu",
    "େ": "e",
    "ୈ": "ai",
    "ୋ": "o",
    "ୌ": "au",
}

_HALANT = "\u0b4d"


def phonetic_odia(text: str | None) -> str:
    """Return a very simple phonetic Latin representation of Odia text."""
    if text is None:
        return ""

    result: list[str] = []
    for char in text:
        if char == _HALANT:
            if result and result[-1].endswith("a"):
                result[-1] = result[-1][:-1]
            continue

        if char in _MATRA_MAP:
            if result:
                if result[-1].endswith("a"):
                    result[-1] = result[-1][:-1] + _MATRA_MAP[char]
                else:
                    result[-1] += _MATRA_MAP[char]
            else:
                result.append(_MATRA_MAP[char])
            continue

        result.append(_ODIA_PHONETIC_MAP.get(char, char))

    return "".join(result)

