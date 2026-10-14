"""Date verbalization."""

from __future__ import annotations

from datetime import date

from openodia.numbers._ordinals import to_ordinal
from openodia.numbers._tables import GREGORIAN_MONTHS
from openodia.numbers._words import NumberingScale, to_words


def to_words_date(value: date, scale: NumberingScale = "indian") -> str:
    """Verbalize a Gregorian date in Odia.

    Output format: ``"<day_ordinal> <month_name>, <year_words>"``.

    Args:
        value: A :class:`datetime.date` (or :class:`datetime.datetime`).
        scale: Numbering scale for the year portion.

    Returns:
        Space-separated Odia string.

    Raises:
        ValueError: If ``value.year`` is non-positive.

    Examples:
        >>> from datetime import date
        >>> to_words_date(date(2026, 5, 27))
        'ସତାଇଶତମ ମଇ, ଦୁଇ ହଜାର ଛବିଶ'
    """
    if value.year < 1:
        raise ValueError(f"year must be >= 1, got {value.year}")
    day_word = to_ordinal(value.day)
    month_word = GREGORIAN_MONTHS[value.month - 1]
    year_word = to_words(value.year, scale=scale)
    return f"{day_word} {month_word}, {year_word}"
