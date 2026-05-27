"""Currency-amount verbalization."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal

from openodia.numbers._tables import CURRENCY_PAISA, CURRENCY_RUPEE
from openodia.numbers._words import NumberingScale, to_words


def to_words_currency(
    amount: float | Decimal | int,
    currency: str = "INR",
    scale: NumberingScale = "indian",
) -> str:
    """Verbalize a monetary amount in Odia.

    Args:
        amount: Numeric value. Fractional part is rounded to two decimal
            places (paisa) using banker-friendly half-up rounding.
        currency: Currently only ``"INR"`` is supported. Defined as a
            parameter so additional currencies can be added without a
            breaking change.
        scale: Numbering scale to use for both rupee and paisa parts.

    Returns:
        For non-zero rupees and non-zero paisa::

            "<rupee_words> ଟଙ୍କା <paisa_words> ପଇସା"

        For zero paisa, the paisa half is omitted. For zero rupees and
        non-zero paisa, the rupee half is omitted.

    Raises:
        ValueError: If ``amount`` is negative or ``currency`` is not
            supported.

    Examples:
        >>> to_words_currency(1500.50)
        'ଏକ ହଜାର ପାଞ୍ଚ ଶହ ଟଙ୍କା ପଚାଶ ପଇସା'
        >>> to_words_currency(1)
        'ଏକ ଟଙ୍କା'
        >>> to_words_currency(0.05)
        'ପାଞ୍ଚ ପଇସା'
    """
    if currency != "INR":
        raise ValueError(f"unsupported currency {currency!r}; supported: 'INR'")

    decimal = Decimal(str(amount))
    if decimal < 0:
        raise ValueError(f"amount must be >= 0, got {amount}")

    rupees_dec, paisa_dec = divmod(
        (decimal * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP),
        100,
    )
    rupees = int(rupees_dec)
    paisa = int(paisa_dec)

    parts: list[str] = []
    if rupees > 0:
        parts.append(f"{to_words(rupees, scale=scale)} {CURRENCY_RUPEE}")
    if paisa > 0:
        parts.append(f"{to_words(paisa, scale=scale)} {CURRENCY_PAISA}")
    if not parts:
        # Zero rupees and zero paisa.
        return f"{to_words(0, scale=scale)} {CURRENCY_RUPEE}"
    return " ".join(parts)
