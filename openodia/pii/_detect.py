"""Rule-based detection of Indian PII in Odia and Latin text."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Callable, Iterable
from datetime import date
from typing import NamedTuple

from openodia.common.constants import FIRST_NAMES, LAST_NAMES, MIDDLE_NAMES, PREFIXES
from openodia.numbers import odia_to_ascii
from openodia.numbers._tables import GREGORIAN_MONTHS
from openodia.pii._entity import PII_TYPES, PIIEntity, PIIType
from openodia.pii._verhoeff import is_valid

_URL = re.compile(r"(?i:https?://|(?<![A-Za-z0-9@.-])www\.)(?:[^\s<>\"'।]|'(?=[^\s<>\"'।.,;:!?)\]]))*[^\s<>\"'।.,;:!?)\]]")
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
_CURRENCY_PREFIX = re.compile(r"(?:₹|(?<![A-Za-z])(?i:Rs\.?|INR)(?![A-Za-z]))")
_CURRENCY_SUFFIX = re.compile(r"(?:ଟଙ୍କା|ରୁପିଆ)(?![\u0B00-\u0B7F])")
_DIGITS = "0123456789"
_DATE_NUMERIC = re.compile(r"(?<![0-9])(0?[1-9]|[12][0-9]|3[01])[./-](0?[1-9]|1[0-2])[./-]((?:19|20)[0-9]{2})(?![0-9])")
_ADMIN = re.compile(r"(?<![\u0B00-\u0B7F])(?:ଗ୍ରାମ|ଜିଲ୍ଲା|ସହର|ବ୍ଲକ|ଥାନା|ପଞ୍ଚାୟତ)(?![\u0B00-\u0B7F])")
_BARE_PIN = re.compile(r"(?<![0-9])[1-9][0-9]{5}(?![0-9])")
_ODIA_WORD = re.compile(r"[\u0B00-\u0B7F]+")

_ENGLISH_MONTHS: dict[int, tuple[str, ...]] = {
    1: ("January", "Jan"),
    2: ("February", "Feb"),
    3: ("March", "Mar"),
    4: ("April", "Apr"),
    5: ("May",),
    6: ("June", "Jun"),
    7: ("July", "Jul"),
    8: ("August", "Aug"),
    9: ("September", "Sept", "Sep"),
    10: ("October", "Oct"),
    11: ("November", "Nov"),
    12: ("December", "Dec"),
}
_MONTH_NUMBER: dict[str, int] = {name.casefold(): number for number, name in enumerate(GREGORIAN_MONTHS, start=1)}
for _number, _names in _ENGLISH_MONTHS.items():
    for _name in _names:
        _MONTH_NUMBER[_name.casefold()] = _number
_MONTH_ALT = "|".join(re.escape(name) for name in sorted(_MONTH_NUMBER, key=len, reverse=True))
_MONTH = rf"(?<![A-Za-z\u0B00-\u0B7F])({_MONTH_ALT})(?![A-Za-z\u0B00-\u0B7F])"
_DAY = r"(0?[1-9]|[12][0-9]|3[01])(?:st|nd|rd|th)?"
_YEAR = r"((?:19|20)[0-9]{2})(?![0-9])"
_DATE_DMY_NAME = re.compile(rf"(?<![0-9]){_DAY}[ ]+{_MONTH}[ ]+{_YEAR}", re.IGNORECASE)
_DATE_MDY_NAME = re.compile(rf"{_MONTH}[ ]+{_DAY},?[ ]+{_YEAR}", re.IGNORECASE)

_GIVEN = frozenset(FIRST_NAMES) | frozenset(MIDDLE_NAMES)
_SURNAMES = frozenset(LAST_NAMES)
_NAME_WORDS = _GIVEN | _SURNAMES
_PREFIXES = frozenset(PREFIXES)
_ADDRESS_GAP = 40

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
_TIE_ORDER: tuple[PIIType, ...] = (
    "EMAIL",
    "URL",
    "AADHAAR",
    "PAN",
    "PHONE",
    "DATE",
    "MONEY",
    "NAME",
    "ADDRESS",
    "PINCODE",
)
_RANK = {kind: rank for rank, kind in enumerate(_TIE_ORDER)}


class _Candidate(NamedTuple):
    start: int
    end: int
    kind: PIIType
    confidence: float


def _collapse(group: list[_Candidate]) -> _Candidate:
    lead = min(group, key=lambda c: (c.start - c.end, _RANK[c.kind]))
    return _Candidate(group[0].start, max(c.end for c in group), lead.kind, lead.confidence)


def _merge(candidates: Iterable[_Candidate]) -> list[_Candidate]:
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


def _regex_candidates(text: str, wanted: frozenset[str], min_confidence: float) -> list[_Candidate]:
    found: list[_Candidate] = []
    for kind, pattern, group, confidence_of in _DETECTORS:
        if kind not in wanted:
            continue
        for match in pattern.finditer(text):
            start, end = match.span(group)
            confidence = confidence_of(text[start:end])
            if confidence >= min_confidence:
                found.append(_Candidate(start, end, kind, confidence))
    return found


def _real_date(day: int, month: int, year: int) -> bool:
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def _named_date(match: re.Match[str], day_group: int, month_group: int, year_group: int) -> _Candidate | None:
    month = _MONTH_NUMBER.get(match.group(month_group).casefold())
    if month is None or not _real_date(int(match.group(day_group)), month, int(match.group(year_group))):
        return None
    return _Candidate(match.start(), match.end(), "DATE", 0.85)


def _date_candidates(text: str, wanted: frozenset[str], min_confidence: float) -> list[_Candidate]:
    if "DATE" not in wanted or min_confidence > 0.85:
        return []
    found: list[_Candidate] = []
    for match in _DATE_DMY_NAME.finditer(text):
        candidate = _named_date(match, 1, 2, 3)
        if candidate is not None:
            found.append(candidate)
    for match in _DATE_MDY_NAME.finditer(text):
        candidate = _named_date(match, 2, 1, 3)
        if candidate is not None:
            found.append(candidate)
    if min_confidence > 0.7:
        return found
    for match in _DATE_NUMERIC.finditer(text):
        if _real_date(int(match.group(1)), int(match.group(2)), int(match.group(3))):
            found.append(_Candidate(match.start(), match.end(), "DATE", 0.7))
    return found


def _read_digits(text: str, index: int, limit: int) -> tuple[int, int, bool]:
    count = 0
    while index < len(text) and text[index] in _DIGITS and count < limit:
        count += 1
        index += 1
    return index, count, index < len(text) and text[index] in _DIGITS


def _read_groups(text: str, index: int) -> int | None:
    while index < len(text) and text[index] == ",":
        index, count, overflow = _read_digits(text, index + 1, 3)
        if count < 2 or overflow:
            return None
    return index


def _read_decimal(text: str, index: int) -> int | None:
    if index >= len(text) or text[index] != ".":
        return index
    index, count, overflow = _read_digits(text, index + 1, 2)
    if count == 0 or overflow:
        return None
    return index


def _parse_amount(text: str, start: int) -> int | None:
    if start >= len(text) or text[start] not in _DIGITS:
        return None
    index, first, overflow = _read_digits(text, start, 12)
    if overflow or first == 0:
        return None
    if index < len(text) and text[index] == ",":
        if first > 3:
            return None
        grouped = _read_groups(text, index)
        if grouped is None:
            return None
        index = grouped
    return _read_decimal(text, index)


def _amount_touching(text: str, end: int) -> int | None:
    start = end
    while start > 0 and text[start - 1] in "0123456789,.":
        start -= 1
    if _parse_amount(text, start) == end:
        return start
    return None


def _money_candidates(text: str, wanted: frozenset[str], min_confidence: float) -> list[_Candidate]:
    if "MONEY" not in wanted or min_confidence > 0.9:
        return []
    found: list[_Candidate] = []
    for match in _CURRENCY_PREFIX.finditer(text):
        start = match.end()
        while start < len(text) and text[start] in " \t":
            start += 1
        end = _parse_amount(text, start)
        if end is not None:
            found.append(_Candidate(match.start(), end, "MONEY", 0.9))
    for match in _CURRENCY_SUFFIX.finditer(text):
        end = match.start()
        while end > 0 and text[end - 1] in " \t":
            end -= 1
        amount_start = _amount_touching(text, end)
        if amount_start is not None:
            found.append(_Candidate(amount_start, match.end(), "MONEY", 0.9))
    return found


def _nfc_bounds(text: str) -> tuple[str, list[int] | None]:
    if unicodedata.is_normalized("NFC", text):
        return text, None
    nfc = unicodedata.normalize("NFC", text)
    bounds = [0]
    start = 0
    for char in nfc:
        end = start + 1
        while unicodedata.normalize("NFC", text[start:end]) != char:
            end += 1
        bounds.append(end)
        start = end
    return nfc, bounds


def _one_space(text: str, left: re.Match[str], right: re.Match[str]) -> bool:
    return right.start() == left.end() + 1 and text[left.end()] == " "


def _piece_end(text: str, words: list[re.Match[str]], index: int, room: int) -> int | None:
    if room >= 2 and index + 1 < len(words) and _one_space(text, words[index], words[index + 1]):
        if f"{words[index].group()} {words[index + 1].group()}" in _GIVEN:
            return index + 1
    if room >= 1 and words[index].group() in _NAME_WORDS:
        return index
    return None


def _honorific_end(text: str, words: list[re.Match[str]], index: int) -> int | None:
    if words[index].group() not in _PREFIXES:
        return None
    end = index
    nxt = index + 1
    used = 0
    while nxt < len(words) and used < 3 and _one_space(text, words[nxt - 1], words[nxt]):
        piece = _piece_end(text, words, nxt, 3 - used)
        if piece is None:
            break
        used += piece - nxt + 1
        end = piece
        nxt = piece + 1
    if end == index:
        return None
    if used == 3:
        end = _more_surnames(text, words, end)
    return end


def _more_surnames(text: str, words: list[re.Match[str]], end: int) -> int:
    nxt = end + 1
    while nxt < len(words) and _one_space(text, words[end], words[nxt]) and words[nxt].group() in _SURNAMES:
        end = nxt
        nxt += 1
    return end


def _given_end(text: str, words: list[re.Match[str]], index: int) -> int | None:
    given = _piece_end(text, words, index, 2)
    if given is None:
        return None
    if given > index or words[index].group() in _GIVEN:
        return given
    return None


def _surname_end(text: str, words: list[re.Match[str]], index: int) -> int | None:
    given = _given_end(text, words, index)
    if given is None:
        return None
    nxt = given + 1
    if nxt >= len(words) or not _one_space(text, words[given], words[nxt]):
        return None
    if words[nxt].group() in _SURNAMES:
        return _more_surnames(text, words, nxt)
    if (
        nxt + 1 < len(words)
        and _one_space(text, words[nxt], words[nxt + 1])
        and words[nxt].group() in _GIVEN
        and words[nxt + 1].group() in _SURNAMES
    ):
        return _more_surnames(text, words, nxt + 1)
    return None


def _name_candidates(text: str, wanted: frozenset[str], min_confidence: float) -> list[_Candidate]:
    if "NAME" not in wanted or min_confidence > 0.8:
        return []
    words = list(_ODIA_WORD.finditer(text))
    found: list[_Candidate] = []
    index = 0
    while index < len(words):
        honorific = _honorific_end(text, words, index)
        if honorific is not None and 0.8 >= min_confidence:
            found.append(_Candidate(words[index].start(), words[honorific].end(), "NAME", 0.8))
            index = honorific + 1
            continue
        surname = _surname_end(text, words, index)
        if surname is not None and 0.7 >= min_confidence:
            found.append(_Candidate(words[index].start(), words[surname].end(), "NAME", 0.7))
            index = surname + 1
            continue
        index += 1
    return found


def _address_candidates(text: str, wanted: frozenset[str], min_confidence: float) -> list[_Candidate]:
    if "ADDRESS" not in wanted or min_confidence > 0.45:
        return []
    admins = list(_ADMIN.finditer(text))
    pins = list(_BARE_PIN.finditer(text))
    if not admins or not pins:
        return []
    found: list[_Candidate] = []
    pin_index = 0
    for admin in admins:
        while pin_index < len(pins) and pins[pin_index].end() < admin.start() - _ADDRESS_GAP:
            pin_index += 1
        scan = pin_index
        while scan < len(pins) and pins[scan].start() <= admin.end() + _ADDRESS_GAP:
            pin = pins[scan]
            gap = admin.start() - pin.end() if admin.start() >= pin.end() else pin.start() - admin.end()
            if 0 <= gap <= _ADDRESS_GAP:
                found.append(_Candidate(min(admin.start(), pin.start()), max(admin.end(), pin.end()), "ADDRESS", 0.45))
            scan += 1
    return found


def detect(text: str, types: Iterable[str] | None = None, min_confidence: float = 0.0) -> list[PIIEntity]:
    """Find PII spans in ``text``, sorted by position and never overlapping.

    Odia and ASCII digits are both recognised. ``types`` limits the search to some of
    ``PII_TYPES``. ``min_confidence`` (0 to 1) drops weaker matches first. Matches that
    overlap are merged into one entity spanning all of them, so for every detected value no
    part of it is left visible; see the limits below. Its type and confidence come from the
    longest match.

    Limits: an email local part over 64 characters is not found, and one with punctuation keeps
    its earlier part visible; one that starts with non-ASCII letters keeps those letters visible.

    Raises:
        TypeError: ``text`` is not a ``str``, or ``types`` is a bare string.
        ValueError: ``types`` names an unknown type, or ``min_confidence`` is outside 0 to 1.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be str, got {type(text).__name__}")
    wanted = validated_types(types)
    _validate_min_confidence(min_confidence)
    nfc_text, bounds = _nfc_bounds(text)
    ascii_text = odia_to_ascii(nfc_text)
    candidates = _regex_candidates(ascii_text, wanted, min_confidence)
    candidates.extend(_money_candidates(ascii_text, wanted, min_confidence))
    candidates.extend(_date_candidates(ascii_text, wanted, min_confidence))
    candidates.extend(_name_candidates(ascii_text, wanted, min_confidence))
    candidates.extend(_address_candidates(ascii_text, wanted, min_confidence))
    entities = []
    for candidate in _merge(candidates):
        start, end = candidate.start, candidate.end
        if bounds is not None:
            start, end = bounds[start], bounds[end]
        entities.append(PIIEntity(candidate.kind, text[start:end], start, end, candidate.confidence))
    return entities
