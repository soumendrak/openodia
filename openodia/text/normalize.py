"""Unicode normalization and cleanup for Odia text.

The functions here are *deterministic* and have no external dependencies.
They are intended to be the first step of any text-processing pipeline.

Typical usage:

>>> from openodia import normalize, clean
>>> normalize("ଡ଼")          # decomposed ଡ଼
'ଡ଼'
>>> clean("ନମ‌ସ୍କାର 123")  # strips ZWNJ, optionally converts digits
'ନମସ୍କାର 123'
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal

UnicodeForm = Literal["NFC", "NFD", "NFKC", "NFKD"]

# Zero-width joiners frequently appear as IME / copy-paste noise in Odia text.
ZWJ: str = "‍"
ZWNJ: str = "‌"

# Digit blocks. Ordered ``0..9`` so ``str.translate`` tables map index-for-index.
ASCII_DIGITS: str = "0123456789"
ODIA_DIGITS: str = "୦୧୨୩୪୫୬୭୮୯"

_LATIN_TO_ODIA_DIGITS = str.maketrans(ASCII_DIGITS, ODIA_DIGITS)
_ODIA_TO_LATIN_DIGITS = str.maketrans(ODIA_DIGITS, ASCII_DIGITS)


def normalize(text: str, form: UnicodeForm = "NFC") -> str:
    """Return ``text`` in the requested Unicode normalization form.

    Args:
        text: Input string.
        form: One of ``"NFC"``, ``"NFD"``, ``"NFKC"``, ``"NFKD"``.
            Defaults to ``"NFC"`` (the right choice for Indic Unicode).

    Returns:
        The normalized string.

    Raises:
        ValueError: If ``form`` is not one of the four standard forms.
    """
    if form not in ("NFC", "NFD", "NFKC", "NFKD"):
        raise ValueError(f"form must be one of NFC, NFD, NFKC, NFKD; got {form!r}")
    return unicodedata.normalize(form, text)


@dataclass(frozen=True)
class CleanOptions:
    """Options for :func:`clean`.

    Attributes:
        form: Unicode normalization form applied first. Defaults to ``"NFC"``.
        strip_zwj: Drop zero-width joiner (U+200D).
        strip_zwnj: Drop zero-width non-joiner (U+200C).
        collapse_whitespace: Replace runs of whitespace with a single space
            and trim leading/trailing whitespace.
        latin_to_odia_digits: Convert ASCII digits ``0-9`` to Odia digits.
        odia_to_latin_digits: Convert Odia digits ``୦-୯`` to ASCII digits.
            Mutually exclusive with ``latin_to_odia_digits``.
    """

    form: UnicodeForm = "NFC"
    strip_zwj: bool = True
    strip_zwnj: bool = True
    collapse_whitespace: bool = True
    latin_to_odia_digits: bool = False
    odia_to_latin_digits: bool = False

    def __post_init__(self) -> None:
        if self.latin_to_odia_digits and self.odia_to_latin_digits:
            raise ValueError("latin_to_odia_digits and odia_to_latin_digits are mutually exclusive")


DEFAULT_CLEAN: CleanOptions = CleanOptions()


def clean(text: str, options: CleanOptions | None = None) -> str:
    """Return ``text`` with common Odia-specific anomalies removed.

    Always applied (unless disabled in ``options``):

    * Unicode normalization (NFC by default).
    * ZWJ / ZWNJ stripping.
    * Whitespace collapsing.

    Off by default:

    * Latin ↔ Odia digit conversion.

    Args:
        text: Input string.
        options: Cleanup configuration. ``None`` uses :data:`DEFAULT_CLEAN`.

    Returns:
        The cleaned string. ``clean(clean(x)) == clean(x)`` for any ``x``.
    """
    if options is None:
        options = DEFAULT_CLEAN

    out = normalize(text, options.form)

    if options.strip_zwj:
        out = out.replace(ZWJ, "")
    if options.strip_zwnj:
        out = out.replace(ZWNJ, "")
    if options.latin_to_odia_digits:
        out = out.translate(_LATIN_TO_ODIA_DIGITS)
    if options.odia_to_latin_digits:
        out = out.translate(_ODIA_TO_LATIN_DIGITS)
    if options.collapse_whitespace:
        out = " ".join(out.split())

    return out
