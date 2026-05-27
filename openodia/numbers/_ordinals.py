"""Ordinal forms in Odia."""

from __future__ import annotations

from openodia.numbers._tables import ORDINAL_SUFFIX, ORDINALS_IRREGULAR
from openodia.numbers._words import to_words


def to_ordinal(n: int) -> str:
    """Return the ordinal Odia word for the positive integer ``n``.

    Ordinals 1..10 use their irregular forms (ପ୍ରଥମ, ଦ୍ୱିତୀୟ, ...).
    For n ≥ 11 the cardinal word is suffixed with ``ତମ``.

    Args:
        n: Positive integer.

    Raises:
        ValueError: If ``n`` is zero or negative.
    """
    if n < 1:
        raise ValueError(f"ordinals are defined for n >= 1, got {n}")
    if n in ORDINALS_IRREGULAR:
        return ORDINALS_IRREGULAR[n]
    return f"{to_words(n)}{ORDINAL_SUFFIX}"
