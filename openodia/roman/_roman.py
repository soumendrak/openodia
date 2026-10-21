"""Romanisation engine for Odia text."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Literal

from openodia.roman._tables import HUNTERIAN, ISO15919, ITRANS, SchemeTable

Scheme = Literal["ISO15919", "Hunterian", "ITRANS"]

SCHEMES: tuple[Scheme, ...] = ("ISO15919", "Hunterian", "ITRANS")

_HALANT = "୍"


def _table(scheme: Scheme) -> SchemeTable:
    if scheme == "ISO15919":
        return ISO15919
    if scheme == "Hunterian":
        return HUNTERIAN
    if scheme == "ITRANS":
        return ITRANS
    raise ValueError(f"unknown scheme {scheme!r}; supported: {SCHEMES}")


def to_roman(text: str, scheme: Scheme = "ISO15919", *, reversible: bool = False) -> str:  # noqa: C901
    """Transliterate Odia ``text`` to the Latin script.

    Args:
        text: Source Odia string.
        scheme: One of ``"ISO15919"``, ``"Hunterian"``, ``"ITRANS"``.
        reversible: For ``ISO15919`` and ``ITRANS`` only. When true, non-Odia
            text is escaped so :func:`from_roman` restores the input exactly:
            a literal separator (``:`` / ``_``) is doubled, and any non-Odia
            run that could be read as Roman letters, or that contains
            combining marks, is quoted (``କi`` gives ``ka:{i:}``). Ignored
            for ``Hunterian``.

    Returns:
        The transliterated string. Unless ``reversible`` is true, characters
        outside the Odia block come back exactly as given.

    Raises:
        ValueError: If ``scheme`` is not recognised.

    Examples:
        >>> to_roman("ଓଡ଼ିଆ", "ISO15919")
        'ōṛiā'
        >>> to_roman("ନମସ୍କାର", "Hunterian")
        'namaskara'
    """
    table = _table(scheme)
    vowels: dict[str, str] = table["vowels"]
    consonants: dict[str, str] = table["consonants"]
    matras: dict[str, str] = table["matras"]
    modifiers: dict[str, str] = table["modifiers"]
    schwa: str = table["schwa"]

    text = _ODIA_RUN.sub(lambda m: unicodedata.normalize("NFC", m.group()), text)
    text = text.replace("ଡ" + chr(0x0B3C), chr(0x0B5C))
    text = text.replace("ଢ" + chr(0x0B3C), chr(0x0B5D))

    out: list[str] = []
    literal: list[bool] = []
    pending_schwa = False
    after_halant = False
    sep = _SEPARATORS.get(scheme)
    escape = reversible and sep is not None

    def flush_schwa() -> None:
        nonlocal pending_schwa
        if pending_schwa:
            emit(schwa)
            pending_schwa = False

    def emit(token: str, is_literal: bool = False) -> None:
        out.append(token)
        literal.append(is_literal)

    for ch in text:
        halant_before = after_halant
        after_halant = False
        if ch in consonants:
            flush_schwa()
            emit(consonants[ch])
            pending_schwa = True
        elif ch in vowels:
            flush_schwa()
            if halant_before and sep is not None:
                emit(_HALANT_MARK)
            emit(vowels[ch])
        elif ch in matras:
            emit(matras[ch])
            pending_schwa = False
        elif ch == _HALANT:
            after_halant = pending_schwa
            pending_schwa = False
        elif ch in modifiers:
            flush_schwa()
            emit(modifiers[ch])
        else:
            flush_schwa()
            emit(ch * 2 if escape and ch == sep else ch, is_literal=True)

    flush_schwa()
    if escape:
        out, literal = _quote_literals(out, literal, scheme)
    return _join_tokens(out, scheme, literal)


def _quote_literals(tokens: list[str], literal: list[bool], scheme: Scheme) -> tuple[list[str], list[bool]]:
    """Quote pass-through runs that the decoder would read as Roman tokens.

    Only used with ``reversible=True``: ``କi`` would otherwise give ``kai``
    (``କୈ``), and ``hello`` would decode as Odia. Each maximal run of literal characters
    other than whitespace and escaped separators is written as
    ``<sep>{run<sep>}`` when it contains a character used in Roman tokens or
    a combining mark,
    e.g. ``ka:{i:}``.
    """
    sep = _SEPARATORS[scheme]
    roman_tokens, _ = _build_reverse_index(scheme)
    token_chars = set("".join(roman_tokens))
    new_tokens: list[str] = []
    new_literal: list[bool] = []
    run: list[str] = []

    def close_run() -> None:
        if run:
            text = "".join(run)
            needs_quote = token_chars.intersection(text) or any(unicodedata.combining(c) for c in text)
            new_tokens.append(sep + "{" + text + sep + "}" if needs_quote else text)
            new_literal.append(True)
            run.clear()

    for tok, is_lit in zip(tokens, literal):
        if is_lit and len(tok) == 1 and tok != sep and not tok.isspace():
            run.append(tok)
            continue
        close_run()
        new_tokens.append(tok)
        new_literal.append(is_lit)
    close_run()
    return new_tokens, new_literal


_ODIA_RUN = re.compile("[\u0b00-\u0b7f]+")

_SEPARATORS: dict[str, str] = {"ISO15919": ":", "ITRANS": "_"}


_HALANT_MARK = "\x00halant"


def _join_tokens(tokens: list[str], scheme: Scheme, literal: list[bool] | None = None) -> str:
    """Join emitted tokens, marking boundaries a decoder would otherwise merge.

    Example: ``କଇ`` emits ``k``, ``a``, ``i``. Plain joining gives ``kai``,
    which decodes as ``କୈ``, so ISO writes ``ka:i``. ``କ୍ହ`` likewise gives
    ``k:ha`` rather than ``kha`` (``ଖ``). Pass-through text (*literal*) is
    never separated, so non-Odia input comes back unchanged.
    """
    sep = _SEPARATORS.get(scheme)
    if sep is None:
        return "".join(t for t in tokens if t != _HALANT_MARK)
    literal = literal or [False] * len(tokens)
    roman_tokens, _ = _build_reverse_index(scheme)
    out: list[str] = []
    for i, tok in enumerate(tokens):
        if tok == _HALANT_MARK:
            out.append(sep)
            continue
        out.append(tok)
        if literal[i] or i + 1 >= len(tokens) or literal[i + 1] or tokens[i + 1] == _HALANT_MARK:
            continue
        following = []
        for j in range(i + 1, min(i + 3, len(tokens))):
            if literal[j] or tokens[j] == _HALANT_MARK:
                break
            following.append(tokens[j])
        joined = tok + "".join(following)
        if any(len(t) > len(tok) and t.startswith(tok) and joined.startswith(t) for t in roman_tokens):
            out.append(sep)
    return "".join(out)


_HUNTERIAN_PREFERRED: dict[str, str] = {
    "n": "ନ",
    "t": "ତ",
    "th": "ଥ",
    "d": "ଦ",
    "dh": "ଧ",
}


def _first_wins(items: Iterable[tuple[str, str]]) -> dict[str, str]:
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
    for roman, odia in _first_wins(table["modifiers"].items()).items():
        index[roman] = ("modifier", odia)
    for roman, odia in _first_wins(table["vowels"].items()).items():
        index[roman] = ("vowel", odia)
    consonants = _first_wins(table["consonants"].items())
    if scheme == "Hunterian":
        consonants.update(_HUNTERIAN_PREFERRED)
    for roman, odia in consonants.items():
        index[roman] = ("consonant", odia)
    tokens = sorted(index, key=len, reverse=True)
    return tokens, index


def _normalize_outside_quotes(text: str, sep: str) -> str:
    """NFC *text* except for ``<sep>{...<sep>}`` spans written by to_roman.

    Scans with the decoder's precedence: an escaped ``<sep><sep>`` is plain
    text, so it cannot open a quote.
    """
    parts: list[str] = []
    plain_start = i = 0
    while i < len(text):
        if text.startswith(sep * 2, i):
            i += 2 * len(sep)
            continue
        if text.startswith(sep + "{", i):
            end = text.find(sep + "}", i + len(sep) + 1)
            if end != -1:
                parts.append(unicodedata.normalize("NFC", text[plain_start:i]))
                plain_start = end + len(sep) + 1
                parts.append(text[i:plain_start])
                i = plain_start
                continue
        i += 1
    parts.append(unicodedata.normalize("NFC", text[plain_start:]))
    return "".join(parts)


def from_roman(text: str, scheme: Scheme = "ISO15919") -> str:  # noqa: C901
    """Reverse of :func:`to_roman`.

    Best-effort for ``Hunterian`` since that scheme is intentionally
    lossy (no diacritics). Its ``n`` and ``h`` always decode as the
    consonants ``ନ`` and ``ହ``, so ``ନ୍`` endings and clusters such as
    ``ନ୍ସ`` and ``ଙ୍କ`` come back intact; anusvara and visarga need the
    explicit marks of ``ISO15919`` (``ṁ``, ``ḥ``) or ``ITRANS`` (``M``, ``H``).
    ``ISO15919`` and ``ITRANS`` round-trip correctly for text produced by
    ``to_roman`` in the same scheme; for input that also contains non-Odia
    text, use ``to_roman(..., reversible=True)``.

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
        >>> from_roman("jesan", "Hunterian")
        'ଜେସନ୍'
    """
    tokens, index = _build_reverse_index(scheme)
    table = _table(scheme)
    schwa: str = table["schwa"]
    matras = _first_wins(table["matras"].items())
    if scheme == "ISO15919":
        text = _normalize_outside_quotes(text, _SEPARATORS[scheme])

    out: list[str] = []
    after_consonant = False

    sep = _SEPARATORS.get(scheme)
    prev_was_token = False
    i = 0
    while i < len(text):
        if sep is not None and text.startswith(sep * 2, i):
            if after_consonant:
                out.append(_HALANT)
                after_consonant = False
            out.append(sep)
            i += 2 * len(sep)
            prev_was_token = False
            continue
        if sep is not None and text.startswith(sep + "{", i):
            end = text.find(sep + "}", i + len(sep) + 1)
            if end != -1:
                if after_consonant:
                    out.append(_HALANT)
                    after_consonant = False
                out.append(text[i + len(sep) + 1 : end])
                i = end + len(sep) + 1
                prev_was_token = False
                continue
        match = next((t for t in tokens if text.startswith(t, i)), None)
        if (
            match is None
            and sep is not None
            and text.startswith(sep, i)
            and prev_was_token
            and any(text.startswith(t, i + len(sep)) for t in tokens)
        ):
            i += len(sep)
            nxt = next(t for t in tokens if text.startswith(t, i))
            if after_consonant and index[nxt][0] == "vowel":
                out.append(_HALANT)
                after_consonant = False
            continue
        prev_was_token = match is not None
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
