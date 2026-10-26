"""Rule-based detection of Indian PII in Odia and Latin text."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable

from openodia.numbers import odia_to_ascii
from openodia.pii._entity import PII_TYPES, PIIEntity
from openodia.pii._verhoeff import is_valid

_URL = re.compile(r"(?:https?://|www\.)[^\s<>\"'।]*[^\s<>\"'।.,;:!?)\]]")
_EMAIL = re.compile(r"(?<![\w.%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?<![0-9])(?:(?:\+91|0091)[ -]?|0)?[6-9][0-9]{4}[ -]?[0-9]{5}(?![0-9])")
_AADHAAR = re.compile(r"(?<![0-9])[2-9][0-9]{3}([ -]?)[0-9]{4}\1[0-9]{4}(?![0-9])")
_PAN = re.compile(r"(?<![A-Za-z0-9])[A-Z]{3}[PCHFATBLJG][A-Z][0-9]{4}[A-Z](?![A-Za-z0-9])")
_PINCODE = re.compile(
    r"(?:\bpin(?:[\s-]?code)?|ପିନ[\u0B00-\u0B7F\u200c\u200d]{0,10})[\s:.-]{0,3}(?<![0-9])([1-9][0-9]{5})(?![0-9])",
    re.IGNORECASE,
)

_CHECKSUM_PASSED = 0.95
_SHAPE_ONLY = 0.5


def _fixed(confidence: float) -> Callable[[str], float]:
    return lambda _: confidence


def _aadhaar_confidence(number: str) -> float:
    return _CHECKSUM_PASSED if is_valid(re.sub(r"\D", "", number)) else _SHAPE_ONLY


_DETECTORS: tuple[tuple[str, re.Pattern[str], int, Callable[[str], float]], ...] = (
    ("URL", _URL, 0, _fixed(0.9)),
    ("EMAIL", _EMAIL, 0, _fixed(0.95)),
    ("AADHAAR", _AADHAAR, 0, _aadhaar_confidence),
    ("PAN", _PAN, 0, _fixed(0.95)),
    ("PHONE", _PHONE, 0, _fixed(0.9)),
    ("PINCODE", _PINCODE, 1, _fixed(0.8)),
)


def _validate_types(types: Iterable[str] | None) -> frozenset[str]:
    wanted = frozenset(PII_TYPES if types is None else types)
    unknown = wanted - set(PII_TYPES)
    if unknown:
        raise ValueError(f"unknown PII type {sorted(unknown)[0]!r}; choose from {', '.join(PII_TYPES)}")
    return wanted


def detect(text: str, types: Iterable[str] | None = None, min_confidence: float = 0.0) -> list[PIIEntity]:
    """Find PII spans in ``text``, sorted by position.

    Odia and ASCII digits are both recognised. ``types`` limits the search to some of
    :data:`PII_TYPES`; ``min_confidence`` drops weaker matches. Where two matches overlap, the
    earlier entry in the order URL, EMAIL, AADHAAR, PAN, PHONE, PINCODE wins.
    """
    wanted = _validate_types(types)
    ascii_text = odia_to_ascii(text)
    taken: list[PIIEntity] = []
    for kind, pattern, group, confidence_of in _DETECTORS:
        if kind not in wanted:
            continue
        for match in pattern.finditer(ascii_text):
            start, end = match.span(group)
            confidence = confidence_of(ascii_text[start:end])
            overlaps = any(start < other.end and other.start < end for other in taken)
            if confidence >= min_confidence and not overlaps:
                taken.append(PIIEntity(kind, text[start:end], start, end, confidence))
    return sorted(taken, key=lambda entity: entity.start)
