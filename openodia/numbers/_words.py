"""Integer ↔ words conversion."""

from __future__ import annotations

from typing import Literal

from openodia.numbers._tables import (
    INDIAN_MULTIPLIERS,
    NEGATIVE_WORD,
    SHORT_MULTIPLIERS,
    UNDER_HUNDRED,
)

NumberingScale = Literal["indian", "short"]


def to_words(n: int, scale: NumberingScale = "indian") -> str:
    """Convert an integer to its Odia word form.

    Args:
        n: Any integer (positive, zero, or negative).
        scale: ``"indian"`` (default) uses lakh / crore. ``"short"`` uses
            million / billion / trillion.

    Returns:
        Space-separated Odia words.

    Raises:
        ValueError: If ``scale`` is not one of the two supported values.

    Examples:
        >>> to_words(0)
        'ଶୂନ୍ୟ'
        >>> to_words(1234)
        'ଏକ ହଜାର ଦୁଇ ଶହ ଚଉତିରିଶ'
        >>> to_words(1_000_000, scale="short")
        'ଏକ ମିଲିୟନ'
    """
    if scale == "indian":
        multipliers = INDIAN_MULTIPLIERS
    elif scale == "short":
        multipliers = SHORT_MULTIPLIERS
    else:
        raise ValueError(f"unknown scale {scale!r}; supported: 'indian', 'short'")

    if n < 0:
        return f"{NEGATIVE_WORD} {_compose(-n, multipliers)}"
    return _compose(n, multipliers)


def _compose(n: int, multipliers: tuple[tuple[int, str], ...]) -> str:
    """Build the word for a non-negative integer using the given multipliers."""
    if n < 100:
        return UNDER_HUNDRED[n]

    parts: list[str] = []
    remainder = n
    for value, word in multipliers:
        if remainder >= value:
            quotient, remainder = divmod(remainder, value)
            parts.append(f"{_compose(quotient, multipliers)} {word}")

    if remainder > 0:
        parts.append(UNDER_HUNDRED[remainder])

    return " ".join(parts)


def from_words(words: str, scale: NumberingScale = "indian") -> int:
    """Parse an Odia number-words string back to an integer.

    The inverse of :func:`to_words`. Accepts the output produced by this
    package; tolerates extra whitespace.

    Args:
        words: Odia number-words string.
        scale: Must match the scale used to produce ``words``.

    Returns:
        The integer value.

    Raises:
        ValueError: If a token is not recognised, if ``scale`` is invalid,
            or if ``words`` is empty after stripping.

    Examples:
        >>> from_words("ଏକ ହଜାର ଦୁଇ ଶହ ଚଉତିରିଶ")
        1234
    """
    if scale == "indian":
        multipliers = INDIAN_MULTIPLIERS
    elif scale == "short":
        multipliers = SHORT_MULTIPLIERS
    else:
        raise ValueError(f"unknown scale {scale!r}; supported: 'indian', 'short'")

    tokens = words.split()
    if not tokens:
        raise ValueError("empty input")

    sign = 1
    if tokens[0] == NEGATIVE_WORD:
        sign = -1
        tokens = tokens[1:]
        if not tokens:
            raise ValueError("missing magnitude after negative marker")

    # "ଶହ" (hundred) is intra-group — it combines with the running unit
    # accumulator without closing the group. Larger multipliers (ହଜାର,
    # ଲକ୍ଷ, କୋଟି, ମିଲିୟନ, ...) close the group and add to the total.
    group_terminators = {word: value for value, word in multipliers if value >= 1000}
    hundred_word = next((word for value, word in multipliers if value == 100), None)
    word_to_int = {word: i for i, word in enumerate(UNDER_HUNDRED)}

    total = 0
    group = 0
    current = 0
    for token in tokens:
        if token == hundred_word:
            coefficient = current if current else 1
            group += coefficient * 100
            current = 0
        elif token in group_terminators:
            # Close the current group: (group + current) is the coefficient
            # for this multiplier, e.g. "two hundred thirty-four thousand".
            coefficient = (group + current) if (group + current) else 1
            total += coefficient * group_terminators[token]
            group = 0
            current = 0
        elif token in word_to_int:
            current += word_to_int[token]
        else:
            raise ValueError(f"unrecognised token: {token!r}")

    return sign * (total + group + current)
