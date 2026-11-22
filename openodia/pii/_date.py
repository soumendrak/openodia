"""Find calendar dates written with digits or with an Odia or English month name."""

from __future__ import annotations

import re
from datetime import date

from openodia.numbers._tables import GREGORIAN_MONTHS

NAMED_CONFIDENCE = 0.85
NUMERIC_CONFIDENCE = 0.7

_ENGLISH_MONTHS = (
    ("January", "Jan"),
    ("February", "Feb"),
    ("March", "Mar"),
    ("April", "Apr"),
    ("May",),
    ("June", "Jun"),
    ("July", "Jul"),
    ("August", "Aug"),
    ("September", "Sept", "Sep"),
    ("October", "Oct"),
    ("November", "Nov"),
    ("December", "Dec"),
)
_MONTH_NUMBER = {name.casefold(): number for number, name in enumerate(GREGORIAN_MONTHS, start=1)} | {
    name.casefold(): number for number, names in enumerate(_ENGLISH_MONTHS, start=1) for name in names
}
_MONTH_NAMES = "|".join(re.escape(name) for name in sorted(_MONTH_NUMBER, key=len, reverse=True))
_GAP = "[ \t\u00a0]+"
_MONTH = rf"(?<![A-Za-z\u0B00-\u0B7F])({_MONTH_NAMES})(?![A-Za-z\u0B00-\u0B7F])\.?"
_DAY = r"(0?[1-9]|[12][0-9]|3[01])(?:st|nd|rd|th)?"
_YEAR = r"((?:19|20)[0-9]{2})(?![0-9])"
_DAY_MONTH_YEAR = re.compile(rf"(?<![0-9]){_DAY}{_GAP}{_MONTH},?{_GAP}{_YEAR}", re.IGNORECASE | re.ASCII)
_MONTH_DAY_YEAR = re.compile(rf"{_MONTH}{_GAP}{_DAY},?{_GAP}{_YEAR}", re.IGNORECASE | re.ASCII)
_NUMERIC = re.compile(r"(?<![0-9])(0?[1-9]|[12][0-9]|3[01])[./-](0?[1-9]|1[0-2])[./-]((?:19|20)[0-9]{2})(?![0-9])")


def _is_calendar_day(day: str, month: int, year: str) -> bool:
    try:
        date(int(year), month, int(day))
    except ValueError:
        return False
    return True


def find_dates(text: str) -> list[tuple[int, int, float]]:
    """Return ``(start, end, confidence)`` for each real calendar date in ASCII-digit ``text``."""
    found: list[tuple[int, int, float]] = []
    for pattern, day, month in ((_DAY_MONTH_YEAR, 1, 2), (_MONTH_DAY_YEAR, 2, 1)):
        for match in pattern.finditer(text):
            if _is_calendar_day(match[day], _MONTH_NUMBER[match[month].casefold()], match[3]):
                found.append((match.start(), match.end(), NAMED_CONFIDENCE))
    for match in _NUMERIC.finditer(text):
        if _is_calendar_day(match[1], int(match[2]), match[3]):
            found.append((match.start(), match.end(), NUMERIC_CONFIDENCE))
    return found
