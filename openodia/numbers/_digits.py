"""Odia ↔ ASCII digit conversion."""

from __future__ import annotations

ASCII_DIGITS: str = "0123456789"
ODIA_DIGITS: str = "୦୧୨୩୪୫୬୭୮୯"

_ASCII_TO_ODIA = str.maketrans(ASCII_DIGITS, ODIA_DIGITS)
_ODIA_TO_ASCII = str.maketrans(ODIA_DIGITS, ASCII_DIGITS)


def ascii_to_odia(text: str) -> str:
    """Convert ASCII digits in ``text`` to Odia digits. Non-digits pass through."""
    return text.translate(_ASCII_TO_ODIA)


def odia_to_ascii(text: str) -> str:
    """Convert Odia digits in ``text`` to ASCII digits. Non-digits pass through."""
    return text.translate(_ODIA_TO_ASCII)
