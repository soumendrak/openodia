"""Romanisation engine for Odia text."""

from __future__ import annotations

import unicodedata
from typing import Literal

from openodia.roman._tables import HUNTERIAN, ISO15919, ITRANS

Scheme = Literal["ISO15919", "Hunterian", "ITRANS"]

#: Available romanisation schemes.
SCHEMES: tuple[Scheme, ...] = ("ISO15919", "Hunterian", "ITRANS")

_HALANT = "୍"  # U+0B4D


def _table(scheme: Scheme) -> dict[str, object]:
    if scheme == "ISO15919":
        return ISO15919  # type: ignore[return-value]
    if scheme == "Hunterian":
        return HUNTERIAN  # type: ignore[return-value]
    if scheme == "ITRANS":
        return ITRANS  # type: ignore[return-value]
    raise ValueError(f"unknown scheme {scheme!r}; supported: {SCHEMES}")


def to_roman(text: str, scheme: Scheme = "ISO15919") -> str:
    """Transliterate Odia ``text`` to the Latin script.

    Args:
        text: Source Odia string.
        scheme: One of ``"ISO15919"``, ``"Hunterian"``, ``"ITRANS"``.

    Returns:
        The transliterated string. Characters outside the Odia block pass
        through unchanged.

    Raises:
        ValueError: If ``scheme`` is not recognised.

    Examples:
        >>> to_roman("ଓଡ଼ିଆ", "ISO15919")
        'ōṛiā'
        >>> to_roman("ନମସ୍କାର", "Hunterian")
        'namaskara'
    """
    table = _table(scheme)
    vowels: dict[str, str] = table["vowels"]  # type: ignore[assignment]
    consonants: dict[str, str] = table["consonants"]  # type: ignore[assignment]
    matras: dict[str, str] = table["matras"]  # type: ignore[assignment]
    modifiers: dict[str, str] = table["modifiers"]  # type: ignore[assignment]
    schwa: str = table["schwa"]  # type: ignore[assignment]

    # NFC first (handles common Indic composition cases). Then do the
    # two Odia-specific nukta compositions manually: U+0B5C and U+0B5D
    # are on Unicode's composition-exclusion list so NFC won't compose
    # them, but our tables key on the precomposed forms.
    text = unicodedata.normalize("NFC", text)
    text = text.replace("ଡ" + chr(0x0B3C), chr(0x0B5C))
    text = text.replace("ଢ" + chr(0x0B3C), chr(0x0B5D))

    out: list[str] = []
    pending_schwa = False  # last emitted token was a consonant + inherent schwa

    def flush_schwa() -> None:
        nonlocal pending_schwa
        if pending_schwa:
            out.append(schwa)
            pending_schwa = False

    for ch in text:
        if ch in consonants:
            flush_schwa()
            out.append(consonants[ch])
            pending_schwa = True
        elif ch in vowels:
            flush_schwa()
            out.append(vowels[ch])
        elif ch in matras:
            # Replace the pending schwa with this matra.
            out.append(matras[ch])
            pending_schwa = False
        elif ch == _HALANT:
            # Suppress the pending schwa entirely.
            pending_schwa = False
        elif ch in modifiers:
            flush_schwa()
            out.append(modifiers[ch])
        else:
            flush_schwa()
            out.append(ch)

    flush_schwa()
    return "".join(out)


# ---------------------------------------------------------------------------
# Reverse: roman → Odia
# ---------------------------------------------------------------------------


#: Canonical decodings for Hunterian spellings shared by several letters
#: (the scheme drops the dental/retroflex/nasal distinctions).
_HUNTERIAN_PREFERRED: dict[str, str] = {
    "n": "ନ",
    "t": "ତ",
    "th": "ଥ",
    "d": "ଦ",
    "dh": "ଧ",
}


def _first_wins(items) -> dict[str, str]:
    """``roman -> odia``, keeping the first letter listed for each spelling."""
    out: dict[str, str] = {}
    for odia, roman in items:
        out.setdefault(roman, odia)
    return out


def _build_reverse_index(scheme: Scheme) -> tuple[list[str], dict[str, tuple[str, str]]]:
    """Return ``(tokens longest-first, roman -> (kind, odia))``.

    ``kind`` is ``"consonant"``, ``"vowel"`` or ``"modifier"``. For vowels
    ``odia`` is the independent letter; the matching vowel sign is looked
    up separately so the decoder can choose by context.
    """
    table = _table(scheme)
    index: dict[str, tuple[str, str]] = {}
    for roman, odia in _first_wins(table["modifiers"].items()).items():  # type: ignore[union-attr]
        index[roman] = ("modifier", odia)
    for roman, odia in _first_wins(table["vowels"].items()).items():  # type: ignore[union-attr]
        index[roman] = ("vowel", odia)
    consonants = _first_wins(table["consonants"].items())  # type: ignore[union-attr]
    if scheme == "Hunterian":
        consonants.update(_HUNTERIAN_PREFERRED)
    for roman, odia in consonants.items():
        index[roman] = ("consonant", odia)
    tokens = sorted(index, key=len, reverse=True)
    return tokens, index


def from_roman(text: str, scheme: Scheme = "ISO15919") -> str:
    """Reverse of :func:`to_roman`.

    Best-effort for ``Hunterian`` since that scheme is intentionally
    lossy (no diacritics). ``ISO15919`` and ``ITRANS`` round-trip
    correctly for text produced by ``to_roman`` in the same scheme.

    The decoder tracks context: a vowel straight after a consonant becomes
    a vowel sign (``ā`` after ``n`` gives ``ନା``), the inherent ``a`` adds
    nothing, and a consonant with no vowel after it gets a halant.
    Elsewhere a vowel is written as the independent letter (``ଆ``).

    Args:
        text: Roman-script input.
        scheme: Scheme to decode against.

    Returns:
        Best-effort Odia output. Unknown characters pass through unchanged.

    Raises:
        ValueError: If ``scheme`` is not recognised.

    Examples:
        >>> from_roman("namaskāra")
        'ନମସ୍କାର'
        >>> from_roman("ā")
        'ଆ'
    """
    tokens, index = _build_reverse_index(scheme)
    table = _table(scheme)
    schwa: str = table["schwa"]  # type: ignore[assignment]
    matras = _first_wins(table["matras"].items())  # type: ignore[union-attr]
    if scheme == "ISO15919":
        # The tables use precomposed letters (ṭ, ā, …); accept decomposed
        # input such as "t\u0323" too. Combining marks that have no
        # precomposed form (r̥, m̐) stay as they are and still match.
        text = unicodedata.normalize("NFC", text)

    out: list[str] = []
    after_consonant = False  # last token was a consonant with no vowel yet

    i = 0
    while i < len(text):
        match = next((t for t in tokens if text.startswith(t, i)), None)
        if match is None:
            if after_consonant:
                out.append(_HALANT)
                after_consonant = False
            out.append(text[i])
            i += 1
            continue
        kind, odia = index[match]
        i += len(match)
        if kind == "vowel" and after_consonant:
            if match != schwa:
                out.append(matras.get(match, odia))
            after_consonant = False
            continue
        if after_consonant:
            out.append(_HALANT)
        out.append(odia)
        after_consonant = kind == "consonant"
    if after_consonant:
        out.append(_HALANT)
    return "".join(out)
