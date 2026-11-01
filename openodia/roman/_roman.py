"""Romanisation engine for Odia text."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

from openodia.roman._tables import HUNTERIAN, ISO15919, ITRANS, SchemeTable

Scheme = Literal["ISO15919", "Hunterian", "ITRANS"]

SCHEMES: tuple[Scheme, ...] = ("ISO15919", "Hunterian", "ITRANS")

_HALANT = "୍"
_NUKTA = "\u0b3c"
_NUKTA_MARKS: dict[str, str] = {"ISO15919": "\u00b7", "Hunterian": "", "ITRANS": "`"}

_ODIA_TO_ASCII_DIGITS = str.maketrans("୦୧୨୩୪୫୬୭୮୯", "0123456789")


def _table(scheme: Scheme) -> SchemeTable:
    if scheme == "ISO15919":
        return ISO15919
    if scheme == "Hunterian":
        return HUNTERIAN
    if scheme == "ITRANS":
        return ITRANS
    raise ValueError(f"unknown scheme {scheme!r}; supported: {SCHEMES}")


def _writes_ascii_digits(scheme: Scheme, reversible: bool) -> bool:
    return scheme == "Hunterian" or (scheme == "ITRANS" and not reversible)


def to_roman(text: str, scheme: Scheme = "ISO15919", *, reversible: bool = False) -> str:
    """Transliterate Odia ``text`` to the Latin script.

    Args:
        text: Source Odia string.
        scheme: One of ``"ISO15919"``, ``"Hunterian"``, ``"ITRANS"``.
        reversible: For ``ISO15919`` and ``ITRANS`` only. When true, non-Odia
            text is escaped so ``from_roman`` gives back the input:
            a literal separator (``:`` / ``_``) is doubled, and any non-Odia
            run that could be read as Roman letters, or that contains
            combining marks, is quoted (``କi`` gives ``ka:{i:}``). Ignored
            for ``Hunterian``. Odia digits ``୦``-``୯`` become ASCII ``0``-``9``
            in ``Hunterian`` and in ``ITRANS`` unless ``reversible`` is true
            (an ASCII digit could not be told from a literal one); ``ISO15919``
            keeps them. With ``reversible=True``, Odia text in NFC comes back
            from ``from_roman`` with the same code points, and Odia text
            in any other normal form comes back in NFC (U+0B5C gives
            U+0B21 U+0B3C); non-Odia text comes back exactly as given.

    A nukta after any consonant except ଡ and ଢ is written as ``·`` (ISO 15919)
    or a backtick (ITRANS) right after the consonant; ``Hunterian`` drops it.
    ଡ଼ and ଢ଼ keep their own letters: ``ṛ``/``ṛh`` (ISO 15919), ``.D``/``.Dh``
    (ITRANS) and ``r``/``rh`` (Hunterian, where plain ଡ and ଢ give ``d``/``dh``).

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
    sep = _SEPARATORS.get(scheme)
    escape = reversible and sep is not None
    encoder = _Encoder(table, scheme, sep, escape)
    for ch in _prepare_for_encoding(text, scheme, reversible):
        encoder.feed(ch)
    encoder.flush_schwa()
    out, literal = encoder.out, encoder.literal
    if escape:
        out, literal = _quote_literals(out, literal, scheme)
    return _join_tokens(out, scheme, literal)


def _prepare_for_encoding(text: str, scheme: Scheme, reversible: bool) -> str:
    if _writes_ascii_digits(scheme, reversible):
        text = text.translate(_ODIA_TO_ASCII_DIGITS)
    text = _ODIA_RUN.sub(lambda m: unicodedata.normalize("NFC", m.group()), text)
    text = text.replace("ଡ" + _NUKTA, chr(0x0B5C))
    return text.replace("ଢ" + _NUKTA, chr(0x0B5D))


@dataclass
class _Encoder:
    """Turns Odia characters into Roman tokens, one character at a time."""

    table: SchemeTable
    scheme: Scheme
    sep: str | None
    escape: bool
    out: list[str] = field(default_factory=list)
    literal: list[bool] = field(default_factory=list)
    pending_schwa: bool = False
    after_halant: bool = False

    def emit(self, token: str, is_literal: bool = False) -> None:
        self.out.append(token)
        self.literal.append(is_literal)

    def flush_schwa(self) -> None:
        if self.pending_schwa:
            self.emit(self.table["schwa"])
            self.pending_schwa = False

    def feed(self, ch: str) -> None:
        halant_before = self.after_halant
        self.after_halant = False
        if ch in self.table["consonants"]:
            self.flush_schwa()
            self.emit(self.table["consonants"][ch])
            self.pending_schwa = True
        elif ch in self.table["vowels"]:
            self.feed_vowel(ch, halant_before)
        elif ch in self.table["matras"]:
            self.emit(self.table["matras"][ch])
            self.pending_schwa = False
        elif ch == _HALANT:
            self.after_halant = self.pending_schwa
            self.pending_schwa = False
        elif ch == _NUKTA:
            self.emit(_NUKTA_MARKS[self.scheme])
        else:
            self.feed_other(ch)

    def feed_vowel(self, ch: str, halant_before: bool) -> None:
        self.flush_schwa()
        if halant_before:
            self.emit(_HALANT_MARK)
        self.emit(self.table["vowels"][ch])

    def feed_other(self, ch: str) -> None:
        self.flush_schwa()
        if ch in self.table["modifiers"]:
            self.emit(self.table["modifiers"][ch])
        else:
            self.emit(ch * 2 if self.escape and ch == self.sep else ch, is_literal=True)


def _quote_literals(tokens: list[str], literal: list[bool], scheme: Scheme) -> tuple[list[str], list[bool]]:
    """Quote pass-through runs that the decoder would read as Roman tokens.

    Only used with ``reversible=True``: ``କi`` would otherwise give ``kai``
    (``କୈ``), and ``hello`` would decode as Odia. Each maximal run of literal characters
    other than whitespace and escaped separators is written as
    ``<sep>{run<sep>}`` when it contains a character used in Roman tokens, a
    combining mark, or text that NFC changes (the ANGSTROM SIGN ``Å``),
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
            needs_quote = (
                token_chars.intersection(text)
                or any(unicodedata.combining(c) for c in text)
                or unicodedata.normalize("NFC", text) != text
            )
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


_ITRANS_ALIASES: dict[str, str] = {
    "aa": "A",
    "ii": "I",
    "uu": "U",
    "R^i": "RRi",
    "R^I": "RRI",
    "L^i": "LLi",
    "L^I": "LLI",
}


def _aliases(scheme: Scheme) -> dict[str, str]:
    return _ITRANS_ALIASES if scheme == "ITRANS" else {}


def _first_wins(items: Iterable[tuple[str, str]]) -> dict[str, str]:
    """``roman -> odia``, keeping the first letter listed for each spelling.

    Each ``odia`` value is NFC, so the decoder writes ଡ଼ and ଢ଼ as ``ଡ`` or
    ``ଢ`` plus the nukta: U+0B5C and U+0B5D are composition exclusions.
    """
    out: dict[str, str] = {}
    for odia, roman in items:
        out.setdefault(roman, unicodedata.normalize("NFC", odia))
    return out


def _is_consonant_then_vowel(spelling: str, consonants: dict[str, str], index: dict[str, tuple[str, str]]) -> bool:
    return index[spelling][0] == "vowel" and any(
        spelling[:cut] in consonants and index.get(spelling[cut:], ("",))[0] == "vowel" for cut in range(1, len(spelling))
    )


def _build_reverse_index(scheme: Scheme) -> tuple[list[str], dict[str, tuple[str, str]]]:
    """Return ``(tokens longest-first, roman -> (kind, odia))``.

    ``kind`` is ``"consonant"``, ``"vowel"``, ``"modifier"`` or ``"nukta"``. For vowels
    ``odia`` is the independent letter; the matching vowel sign is looked
    up separately so the decoder can choose by context.
    """
    table = _table(scheme)
    index: dict[str, tuple[str, str]] = {}
    for roman, odia in _first_wins(table["modifiers"].items()).items():
        index[roman] = ("modifier", odia)
    for roman, odia in _first_wins(table["vowels"].items()).items():
        index[roman] = ("vowel", odia)
    if _NUKTA_MARKS[scheme]:
        index[_NUKTA_MARKS[scheme]] = ("nukta", _NUKTA)
    consonants = _first_wins(table["consonants"].items())
    if scheme == "Hunterian":
        consonants.update(_HUNTERIAN_PREFERRED)
        for roman in [r for r in index if _is_consonant_then_vowel(r, consonants, index)]:
            del index[roman]
    for roman, odia in consonants.items():
        index[roman] = ("consonant", odia)
    for alias, canonical in _aliases(scheme).items():
        index[alias] = index[canonical]
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


def from_roman(text: str, scheme: Scheme = "ISO15919") -> str:
    """Reverse of ``to_roman``.

    Best-effort for ``Hunterian`` since that scheme is intentionally
    lossy (no diacritics). Its ``n`` and ``h`` always decode as the
    consonants ``ନ`` and ``ହ``, so ``ନ୍`` endings and clusters such as
    ``ନ୍ସ`` and ``ଙ୍କ`` come back intact; anusvara and visarga need the
    explicit marks of ``ISO15919`` (``ṁ``, ``ḥ``) or ``ITRANS`` (``M``, ``H``).
    For ``ISO15919`` and ``ITRANS``, ``from_roman(to_roman(text, scheme,
    reversible=True), scheme)`` equals ``unicodedata.normalize("NFC", text)``
    for Odia text and keeps non-Odia text exactly as given. The output is
    always NFC Odia, so ``ṛ`` decodes to ``ଡ଼`` as U+0B21 U+0B3C, never as
    the precomposed U+0B5C.

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
    matras = _first_wins(table["matras"].items())
    for alias, canonical in _aliases(scheme).items():
        matras[alias] = matras[canonical]
    sep = _SEPARATORS.get(scheme)
    if sep is not None and scheme == "ISO15919":
        text = _normalize_outside_quotes(text, sep)
    decoder = _Decoder(text, tokens, index, matras, table["schwa"], sep)
    while decoder.i < len(text):
        decoder.step()
    decoder.close_consonant()
    return "".join(decoder.out)


@dataclass
class _Decoder:
    """Reads Roman tokens left to right and writes the Odia text."""

    text: str
    tokens: list[str]
    index: dict[str, tuple[str, str]]
    matras: dict[str, str]
    schwa: str
    sep: str | None
    out: list[str] = field(default_factory=list)
    i: int = 0
    after_consonant: bool = False
    prev_was_token: bool = False

    def close_consonant(self) -> None:
        if self.after_consonant:
            self.out.append(_HALANT)
            self.after_consonant = False

    def step(self) -> None:
        if self.sep is not None and (self.read_escaped_separator(self.sep) or self.read_quoted(self.sep)):
            return
        match = next((t for t in self.tokens if self.text.startswith(t, self.i)), None)
        if match is not None:
            self.prev_was_token = True
            self.read_token(match)
        elif self.sep is None or not self.read_boundary(self.sep):
            self.prev_was_token = False
            self.read_literal()

    def read_escaped_separator(self, sep: str) -> bool:
        if not self.text.startswith(sep * 2, self.i):
            return False
        self.close_consonant()
        self.out.append(sep)
        self.i += 2 * len(sep)
        self.prev_was_token = False
        return True

    def read_quoted(self, sep: str) -> bool:
        if not self.text.startswith(sep + "{", self.i):
            return False
        end = self.text.find(sep + "}", self.i + len(sep) + 1)
        if end == -1:
            return False
        self.close_consonant()
        self.out.append(self.text[self.i + len(sep) + 1 : end])
        self.i = end + len(sep) + 1
        self.prev_was_token = False
        return True

    def read_boundary(self, sep: str) -> bool:
        start = self.i + len(sep)
        if not (self.prev_was_token and self.text.startswith(sep, self.i)):
            return False
        nxt = next((t for t in self.tokens if self.text.startswith(t, start)), None)
        if nxt is None:
            return False
        self.i = start
        if self.index[nxt][0] == "vowel":
            self.close_consonant()
        return True

    def read_literal(self) -> None:
        self.close_consonant()
        self.out.append(self.text[self.i])
        self.i += 1

    def read_token(self, match: str) -> None:
        kind, odia = self.index[match]
        self.i += len(match)
        if kind == "nukta":
            self.out.append(odia)
        elif kind == "vowel" and self.after_consonant:
            if match != self.schwa:
                self.out.append(self.matras.get(match, odia))
            self.after_consonant = False
        else:
            self.close_consonant()
            self.out.append(odia)
            self.after_consonant = kind == "consonant"
