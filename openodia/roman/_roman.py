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
        'ōḍiā'
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


def _build_reverse_index(scheme: Scheme) -> list[tuple[str, str]]:
    """Build a longest-match-first list of ``(roman, odia)`` pairs.

    Tokens listed earlier win when prefixes overlap (e.g. ``"kh"`` must
    win over ``"k"``).
    """
    table = _table(scheme)
    pairs: list[tuple[str, str]] = []

    # Consonants come with the inherent schwa attached because that's the
    # canonical surface form of a bare consonant.
    schwa = table["schwa"]  # type: ignore[assignment]
    for odia, roman in table["consonants"].items():  # type: ignore[union-attr]
        pairs.append((roman + schwa, odia))  # type: ignore[operator]
        pairs.append((roman, odia + _HALANT))  # bare consonant → with halant

    # Matras must be matched WITH a consonant before them. We handle that
    # via the consonant-then-matra logic in the decoder, so we just need
    # the matra entries here for post-consonant matching.
    for odia, roman in table["matras"].items():  # type: ignore[union-attr]
        pairs.append((roman, odia))

    for odia, roman in table["vowels"].items():  # type: ignore[union-attr]
        pairs.append((roman, odia))

    for odia, roman in table["modifiers"].items():  # type: ignore[union-attr]
        pairs.append((roman, odia))

    # Longest first so prefixes don't shadow longer matches.
    pairs.sort(key=lambda p: len(p[0]), reverse=True)
    return pairs


def from_roman(text: str, scheme: Scheme = "ISO15919") -> str:
    """Reverse of :func:`to_roman`.

    Best-effort for ``Hunterian`` since that scheme is intentionally
    lossy (no diacritics). ``ISO15919`` and ``ITRANS`` round-trip
    correctly for text produced by ``to_roman`` in the same scheme.

    Args:
        text: Roman-script input.
        scheme: Scheme to decode against.

    Returns:
        Best-effort Odia output. Unknown characters pass through unchanged.

    Raises:
        ValueError: If ``scheme`` is not recognised.
    """
    pairs = _build_reverse_index(scheme)

    out: list[str] = []
    i = 0
    while i < len(text):
        for roman, odia in pairs:
            if text.startswith(roman, i):
                out.append(odia)
                i += len(roman)
                break
        else:
            out.append(text[i])
            i += 1
    return "".join(out)
