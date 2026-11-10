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
_FLAP = frozenset("ଡଢ")
_MATRAS = frozenset(HUNTERIAN["matras"])
_FOLDS = (("chh", "ch"), ("aa", "a"), ("ii", "i"), ("uu", "u"))
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
    seen: set[str] = set()
    for spelling in _flap_spellings(word):
        key = _fold(to_roman(spelling, "Hunterian"))
        if key not in seen and _LATIN_KEY.fullmatch(key):
            seen.add(key)
            found.append(key)
    return tuple(found)


def _token_counts() -> Counter[str]:
    counts: Counter[str] = Counter()
    for value in get_dictionary().values():
        for token in _ODIA_RUN.findall(unicodedata.normalize("NFC", value)):
            if akshara_count(token) >= 1 and not _doubled_matra(token):
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
    key = _fold(token)
    bucket = _lexicon().get(key)
    if bucket:
        return bucket
    return ((from_roman(key, "Hunterian"), 0),)


def _best(text: str) -> str:
    if not text:
        return ""
    return "".join(_options(span)[0][0] if is_word else span for is_word, span in _pieces(text))


def _extend(
    beam: list[tuple[int, tuple[str, ...]]],
    options: Iterable[tuple[str, int]],
) -> list[tuple[int, tuple[str, ...]]]:
    scored = [(score + count, words + (word,)) for score, words in beam for word, count in options]
    scored.sort(key=lambda item: (-item[0], item[1]))
    kept: list[tuple[int, tuple[str, ...]]] = []
    seen: set[tuple[str, ...]] = set()
    for item in scored:
        if item[1] in seen:
            continue
        seen.add(item[1])
        kept.append(item)
        if len(kept) == _LIMIT:
            break
    return kept


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
    beam: list[tuple[int, tuple[str, ...]]] = [(0, ())]
    for opts in options:
        beam = _extend(beam, opts)
    rows: list[str] = []
    seen: set[str] = set()
    for _score, words in beam:
        row = _render(pieces, words)
        if row not in seen:
            seen.add(row)
            rows.append(row)
    return rows


@overload
def type_odia(text: str, *, candidates: Literal[False] = False) -> str: ...


@overload
def type_odia(text: str, *, candidates: Literal[True]) -> list[str]: ...


def type_odia(text: str, *, candidates: bool = False) -> str | list[str]:
    """Type Roman Odia into Odia script.

    Each run of ASCII letters becomes the bundled-dictionary word whose
    folded Hunterian spelling matches, most frequent gloss first. A run
    with no such word is read by Hunterian ``from_roman``. Every other
    character is copied, so whitespace and punctuation stay put.

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
