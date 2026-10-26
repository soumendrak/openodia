"""Rule-based detection of Indian PII in Odia and Latin text."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable
from typing import NamedTuple

from openodia.numbers import odia_to_ascii
from openodia.pii._entity import PII_TYPES, PIIEntity, PIIType
from openodia.pii._verhoeff import is_valid

_URL = re.compile(r"(?i:https?://|(?<![A-Za-z0-9@.-])www\.)[^\s<>\"'।]*[^\s<>\"'।.,;:!?)\]]")
_EMAIL = re.compile(
    r"(?<![A-Za-z0-9])[A-Za-z0-9._%+\-!#$&'*/=?^`{|}~]{1,64}@[A-Za-z0-9-]{1,63}(?:\.[A-Za-z0-9-]{1,63})*\.[A-Za-z]{2,63}"
)
_PHONE = re.compile(r"(?<![0-9])(?:\(?(?:\+|00)91\)?[ -]?|91[ -]|0)?[6-9][0-9]{4}[ -]?[0-9]{5}(?![0-9])")
_AADHAAR = re.compile(r"(?<![0-9])[2-9][0-9]{3}([ -]?)[0-9]{4}\1[0-9]{4}(?![0-9])")
_PAN = re.compile(r"(?<![A-Za-z])[A-Z]{3}[PCHFATBLJG][A-Z][0-9]{4}[A-Z](?![A-Za-z])")
_PINCODE = re.compile(
    r"(?:(?<![A-Za-z])pin(?:[\s-]?code)?|ପିନ[\u0B00-\u0B7F\u200c\u200d]{0,10})[\s:.-]{0,3}(?<![0-9])([1-9][0-9]{5})(?![0-9])",
    re.IGNORECASE,
)

_CHECKSUM_PASSED = 0.95
_SHAPE_ONLY = 0.5


def _fixed(confidence: float) -> Callable[[str], float]:
    return lambda _: confidence


def _aadhaar_confidence(number: str) -> float:
    return _CHECKSUM_PASSED if is_valid(re.sub(r"\D", "", number)) else _SHAPE_ONLY


_DETECTORS: tuple[tuple[PIIType, re.Pattern[str], int, Callable[[str], float]], ...] = (
    ("EMAIL", _EMAIL, 0, _fixed(0.95)),
    ("URL", _URL, 0, _fixed(0.9)),
    ("AADHAAR", _AADHAAR, 0, _aadhaar_confidence),
    ("PAN", _PAN, 0, _fixed(0.95)),
    ("PHONE", _PHONE, 0, _fixed(0.9)),
    ("PINCODE", _PINCODE, 1, _fixed(0.8)),
)
_RANK = {kind: rank for rank, (kind, *_) in enumerate(_DETECTORS)}


class _Candidate(NamedTuple):
    start: int
    end: int
    kind: PIIType
    confidence: float


def _collapse(group: list[_Candidate]) -> _Candidate:
    lead = min(group, key=lambda c: (c.start - c.end, _RANK[c.kind]))
    return _Candidate(group[0].start, max(c.end for c in group), lead.kind, lead.confidence)


def _merge(candidates: Iterable[_Candidate]) -> list[_Candidate]:
    """Join overlapping candidates into one span each, typed by the longest member.

    Equal lengths go to the earlier type in :data:`_DETECTORS`. One sorted pass, so linear in the
    number of candidates.
    """
    merged: list[_Candidate] = []
    group: list[_Candidate] = []
    group_end = 0
    for candidate in sorted(candidates, key=lambda c: (c.start, -c.end)):
        if group and candidate.start >= group_end:
            merged.append(_collapse(group))
            group = []
        group.append(candidate)
        group_end = max(group_end, candidate.end) if len(group) > 1 else candidate.end
    if group:
        merged.append(_collapse(group))
    return merged


def validated_types(types: Iterable[str] | None) -> frozenset[str]:
    if isinstance(types, (str, bytes)):
        raise TypeError("types must be a list of PII type names, not a single string; wrap it in a list")
    wanted = frozenset(PII_TYPES if types is None else types)
    unknown = wanted - set(PII_TYPES)
    if unknown:
        raise ValueError(f"unknown PII type {sorted(unknown)[0]!r}; choose from {', '.join(PII_TYPES)}")
    return wanted


def _validate_min_confidence(value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 1:
        raise ValueError(f"min_confidence must be a number between 0 and 1, got {value!r}")


def detect(text: str, types: Iterable[str] | None = None, min_confidence: float = 0.0) -> list[PIIEntity]:
    """Find PII spans in ``text``, sorted by position and never overlapping.

    Odia and ASCII digits are both recognised. ``types`` limits the search to some of
    :data:`PII_TYPES`; ``min_confidence`` (0 to 1) drops weaker matches first. Matches that
    overlap are merged into one entity spanning all of them, so no part of a value is left
    visible. Its type and confidence come from the longest match; on a tie the earlier of EMAIL,
    URL, AADHAAR, PAN, PHONE, PINCODE wins.

    Raises:
        TypeError: ``text`` is not a ``str``, or ``types`` is a bare string.
        ValueError: ``types`` names an unknown type, or ``min_confidence`` is outside 0 to 1.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    wanted = validated_types(types)
    _validate_min_confidence(min_confidence)
    ascii_text = odia_to_ascii(text)
    candidates = []
    for kind, pattern, group, confidence_of in _DETECTORS:
        if kind not in wanted:
            continue
        for match in pattern.finditer(ascii_text):
            start, end = match.span(group)
            confidence = confidence_of(ascii_text[start:end])
            if confidence >= min_confidence:
                candidates.append(_Candidate(start, end, kind, confidence))
    return [PIIEntity(c.kind, text[c.start : c.end], c.start, c.end, c.confidence) for c in _merge(candidates)]
