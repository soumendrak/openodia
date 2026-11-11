from __future__ import annotations

import re
import unicodedata
from collections import Counter
from collections.abc import Iterable
from functools import lru_cache
from typing import Literal, overload

from openodia.corpus.dictionary import get_dictionary
from openodia.roman._roman import from_roman, to_roman
from openodia.roman._tables import HUNTERIAN
from openodia.syllable import count as akshara_count

_LIMIT = 8
_NUKTA = "\u0b3c"
_VIRAMA = "୍"
_FLAP = frozenset("ଡଢ")
_MATRAS = frozenset(HUNTERIAN["matras"])
_VOWELS = frozenset(HUNTERIAN["vowels"])
_CONS = frozenset(HUNTERIAN["consonants"])
_MODS = frozenset("ଁଂଃ")
_FOLDS = (("chh", "ch"), ("aa", "a"), ("ii", "i"), ("uu", "u"))
_LOAN = {"c": "k", "f": "ph", "q": "k", "x": "ks", "z": "j"}
_WORD = re.compile(r"[A-Za-z]+")
_ODIA_RUN = re.compile(r"[\u0b00-\u0b7f]+")
_LATIN_KEY = re.compile(r"[a-z]+")


def _fold(text: str) -> str:
    folded = text.lower()
    while True:
        stepped = folded
        for source, target in _FOLDS:
            stepped = stepped.replace(source, target)
        if stepped == folded:
            return folded
        folded = stepped


def _doubled_matra(word: str) -> bool:
    previous = ""
    for ch in word:
        if ch == previous and ch in _MATRAS:
            return True
        previous = ch
    return False


def _read_vowel(word: str, index: int) -> int:
    index += 1
    if index < len(word) and word[index] in _MODS:
        return index + 1
    return index


def _read_consonant(word: str, index: int) -> int:
    index += 1
    size = len(word)
    if index < size and word[index] == _NUKTA:
        index += 1
    if index < size and word[index] == _VIRAMA:
        return index + 1
    if index < size and word[index] in _MATRAS:
        sign = word[index]
        index += 1
        while index < size and word[index] == sign:
            index += 1
    if index < size and word[index] in _MODS:
        index += 1
    return index


def _signs_in_order(word: str) -> bool:
    index = 0
    while index < len(word):
        ch = word[index]
        if ch in _VOWELS:
            index = _read_vowel(word, index)
            continue
        if ch in _CONS:
            index = _read_consonant(word, index)
            continue
        return False
    return True


def _well_formed(word: str) -> bool:
    return _signs_in_order(word) and not _doubled_matra(word)


def _fallback_spelling(token: str) -> str:
    lowered = token.lower()
    parts: list[str] = []
    index = 0
    while index < len(lowered):
        if lowered.startswith("chh", index):
            parts.append("chh")
            index += 3
            continue
        if lowered.startswith("ch", index):
            parts.append("ch")
            index += 2
            continue
        parts.append(_LOAN.get(lowered[index], lowered[index]))
        index += 1
    return "".join(parts)


def _flap_indexes(chars: list[str]) -> list[int]:
    indexes = [i for i in range(1, len(chars)) if chars[i] == _NUKTA and chars[i - 1] in _FLAP]
    return indexes[:3]


def _flap_spellings(word: str) -> tuple[str, ...]:
    chars = list(unicodedata.normalize("NFC", word))
    indexes = _flap_indexes(chars)
    spellings: list[str] = []
    width = len(indexes)
    for mask in range(1 << width):
        drop = {indexes[bit] for bit in range(width) if mask & (1 << bit)}
        spellings.append("".join(ch for i, ch in enumerate(chars) if i not in drop))
    return tuple(spellings)


def _keys(word: str) -> tuple[str, ...]:
    found: list[str] = []
    for spelling in _flap_spellings(word):
        key = _fold(to_roman(spelling, "Hunterian"))
        if _LATIN_KEY.fullmatch(key):
            found.append(key)
    return tuple(found)


def _token_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for value in get_dictionary().values():
        for token in _ODIA_RUN.findall(unicodedata.normalize("NFC", value)):
            if akshara_count(token) >= 1 and _well_formed(token):
                counts[token] += 1
    return counts


def _bucket(rows: list[tuple[int, str]]) -> tuple[tuple[str, int], ...]:
    rows.sort(key=lambda item: (-item[0], item[1]))
    return tuple((word, count) for count, word in rows[:_LIMIT])


@lru_cache(maxsize=1)
def _lexicon() -> dict[str, tuple[tuple[str, int], ...]]:
    buckets: dict[str, list[tuple[int, str]]] = {}
    for word, count in _token_counts().items():
        for key in _keys(word):
            buckets.setdefault(key, []).append((count, word))
    return {key: _bucket(rows) for key, rows in buckets.items()}


def _pieces(text: str) -> tuple[tuple[bool, str], ...]:
    pieces: list[tuple[bool, str]] = []
    position = 0
    for match in _WORD.finditer(text):
        if match.start() > position:
            pieces.append((False, text[position : match.start()]))
        pieces.append((True, match.group()))
        position = match.end()
    if position < len(text):
        pieces.append((False, text[position:]))
    return tuple(pieces)


def _options(token: str) -> tuple[tuple[str, int], ...]:
    bucket = _lexicon().get(_fold(token))
    if bucket:
        return bucket
    return ((from_roman(_fallback_spelling(token), "Hunterian"), 0),)


def _best(text: str) -> str:
    if not text:
        return ""
    return "".join(_options(span)[0][0] if is_word else span for is_word, span in _pieces(text))


class _Beam:
    __slots__ = ("score", "word", "parent", "lex")

    def __init__(self, score: int, word: str, parent: _Beam | None, lex: int) -> None:
        self.score = score
        self.word = word
        self.parent = parent
        self.lex = lex


def _chain(node: _Beam) -> tuple[str, ...]:
    words: list[str] = []
    while node.parent is not None:
        words.append(node.word)
        node = node.parent
    words.reverse()
    return tuple(words)


def _parent_lex(item: _Beam) -> int:
    parent = item.parent
    if parent is None:
        return 0
    return parent.lex


def _extend(beam: list[_Beam], options: Iterable[tuple[str, int]]) -> list[_Beam]:
    grown = [_Beam(node.score + count, word, node, 0) for node in beam for word, count in options]
    order = sorted(range(len(grown)), key=lambda i: (_parent_lex(grown[i]), grown[i].word))
    for lex, index in enumerate(order):
        grown[index].lex = lex
    grown.sort(key=lambda item: (-item.score, item.lex))
    return grown[:_LIMIT]


def _render(pieces: tuple[tuple[bool, str], ...], words: tuple[str, ...]) -> str:
    chosen = iter(words)
    return "".join(next(chosen) if is_word else span for is_word, span in pieces)


def _ranked(text: str) -> list[str]:
    if not text:
        return []
    pieces = _pieces(text)
    options = [_options(span) for is_word, span in pieces if is_word]
    if not options:
        return [text]
    beam: list[_Beam] = [_Beam(0, "", None, 0)]
    for opts in options:
        beam = _extend(beam, opts)
    return [_render(pieces, _chain(node)) for node in beam]


@overload
def type_odia(text: str, *, candidates: Literal[False] = False) -> str: ...


@overload
def type_odia(text: str, *, candidates: Literal[True]) -> list[str]: ...


def type_odia(text: str, *, candidates: bool = False) -> str | list[str]:
    """Type Roman Odia into Odia script.

    Each run of ASCII letters becomes the bundled-dictionary word whose
    folded Hunterian spelling matches, most frequent gloss first. A run
    with no such word is lowercased, ``ch`` and ``chh`` are kept, and
    ``c``, ``f``, ``q``, ``x`` and ``z`` are read as ``k``, ``ph``, ``k``,
    ``ks`` and ``j``. That spelling is passed to Hunterian ``from_roman``.
    Every other character is copied, so whitespace and punctuation stay put.

    Args:
        text: Roman typing, or text that mixes it with Odia and punctuation.
        candidates: When true, return at most eight full strings, best
            first. The first of those equals ``type_odia(text)`` whenever
            ``text`` is not empty. ``type_odia("")`` is ``""`` and
            ``type_odia("", candidates=True)`` is ``[]``.

    Returns:
        The typed string, or the ranked strings when ``candidates`` is true.

    Raises:
        TypeError: If ``text`` is not a ``str`` or ``candidates`` is not a ``bool``.

    Examples:
        >>> type_odia("namaskara")
        'ନମସ୍କାର'
        >>> type_odia("odisha bhasha")
        'ଓଡ଼ିଶା ଭାଷା'
        >>> type_odia("ki bhabare achanti")
        'କି ଭାବରେ ଅଛନ୍ତି'
        >>> type_odia("ki", candidates=True)
        ['କି', 'କୀ']
    """
    if not isinstance(text, str) or not isinstance(candidates, bool):
        raise TypeError("text must be a str and candidates must be a bool")
    if candidates:
        return _ranked(text)
    return _best(text)
