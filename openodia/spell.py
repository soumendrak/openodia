"""Check Odia spelling against the offline dictionary.

A word is correct when its NFC form is a dictionary word or a bundled stopword.
Suggestions are other dictionary words within Damerau-Levenshtein distance 2
over aksharas (insertion, deletion, substitution, or transposition of two
adjacent aksharas, including a transposition combined with another edit),
closest distance first and, for a tie, the word that appears more often in the
dictionary. ``correct_text`` replaces
each unknown Odia word with its first suggestion and leaves whitespace, punctuation,
digits and non-Odia text as written. It does not join or split words. A word with
no candidate within distance 2 is left as written.

This module needs a release newer than 0.1.14: ``import openodia.spell`` fails on
0.1.14.

Examples:
    >>> from openodia import spell
    >>> spell.is_correct("ନମସ୍କାର")
    True
    >>> spell.is_correct("ନମସ୍କର")
    False
    >>> spell.suggest("ନମସ୍କର", top_k=1)
    ['ନମସ୍କାର']
    >>> spell.correct_text("ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତ")
    'ସେ ଆମ ଘରକୁ ଆସୁଛନ୍ତି'
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from openodia.common.constants import STOPWORDS
from openodia.corpus.dictionary import get_dictionary
from openodia.syllable import split

_MAX_DISTANCE = 2
_WORD = re.compile(r"[\u0b00-\u0b63\u0b71\u200c\u200d]+")
_Entry = tuple[str, tuple[int, ...], frozenset[int]]


def _has_base(token: str) -> bool:
    for char in token:
        code = ord(char)
        if 0x0B05 <= code <= 0x0B39 or 0x0B5C <= code <= 0x0B61 or code == 0x0B71:
            return True
    return False


def _pieces(word: str) -> tuple[str, ...]:
    return tuple(split(unicodedata.normalize("NFC", word)))


@lru_cache(maxsize=1)
def _frequencies() -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in get_dictionary().values():
        normalized = unicodedata.normalize("NFC", value)
        for word in _WORD.findall(normalized):
            if _has_base(word):
                counts[word] = counts.get(word, 0) + 1
    for word in STOPWORDS:
        token = unicodedata.normalize("NFC", word)
        if _has_base(token) and token not in counts:
            counts[token] = 1
    return counts


@lru_cache(maxsize=1)
def _catalog() -> tuple[dict[str, int], dict[int, tuple[_Entry, ...]]]:
    vocab: dict[str, int] = {}
    grouped: dict[int, list[_Entry]] = {}
    for word in _frequencies():
        units = tuple(vocab.setdefault(part, len(vocab)) for part in _pieces(word))
        grouped.setdefault(len(units), []).append((word, units, frozenset(units)))
    return vocab, {length: tuple(entries) for length, entries in grouped.items()}


def _encode(word: str, vocab: dict[str, int]) -> tuple[int, ...]:
    local: dict[str, int] = {}
    fresh = -1
    encoded: list[int] = []
    for part in _pieces(word):
        known = vocab.get(part)
        if known is None:
            known = local.get(part)
            if known is None:
                known = fresh
                local[part] = fresh
                fresh -= 1
        encoded.append(known)
    return tuple(encoded)


def _within(left: tuple[int, ...], right: tuple[int, ...], limit: int) -> int:
    last_seen: dict[int, int] = {}
    left_len = len(left)
    right_len = len(right)
    width = right_len + 2
    ceiling = left_len + right_len
    table = [ceiling] * ((left_len + 2) * width)
    for i in range(left_len + 1):
        table[(i + 1) * width] = ceiling
        table[(i + 1) * width + 1] = i
    for j in range(right_len + 1):
        table[j + 1] = ceiling
        table[width + j + 1] = j
    for i in range(1, left_len + 1):
        last_match = 0
        row = i * width
        next_row = row + width
        for j in range(1, right_len + 1):
            seen_row = last_seen.get(right[j - 1], 0)
            matched_col = last_match
            if left[i - 1] == right[j - 1]:
                cost = 0
                last_match = j
            else:
                cost = 1
            transposed = table[seen_row * width + matched_col] + (i - seen_row - 1) + 1 + (j - matched_col - 1)
            table[next_row + j + 1] = min(
                table[row + j] + cost,
                table[next_row + j] + 1,
                table[row + j + 1] + 1,
                transposed,
            )
        last_seen[left[i - 1]] = i
    distance = table[(left_len + 1) * width + right_len + 1]
    if distance > limit:
        return limit + 1
    return distance


def _too_far(chars: frozenset[int], present: frozenset[int]) -> bool:
    return len(chars - present) > _MAX_DISTANCE or len(present - chars) > _MAX_DISTANCE


def _matches(token: str) -> list[str]:
    vocab, buckets = _catalog()
    units = _encode(token, vocab)
    present = frozenset(code for code in units if code >= 0)
    frequencies = _frequencies()
    ranked: list[tuple[int, int, str]] = []
    for size in range(max(0, len(units) - _MAX_DISTANCE), len(units) + _MAX_DISTANCE + 1):
        for candidate, candidate_units, chars in buckets.get(size, ()):
            if _too_far(chars, present):
                continue
            distance = _within(units, candidate_units, _MAX_DISTANCE)
            if distance <= _MAX_DISTANCE:
                ranked.append((distance, -frequencies[candidate], candidate))
    ranked.sort()
    return [item[2] for item in ranked]


def is_correct(word: str) -> bool:
    """Return whether ``word`` is in the dictionary after NFC normalization."""
    return unicodedata.normalize("NFC", word) in _frequencies()


def suggest(word: str, top_k: int = 5) -> list[str]:
    """Return up to ``top_k`` dictionary corrections, best first.

    A dictionary word returns itself and nothing else. An empty word returns
    ``[]``. ``top_k`` must be an integer greater than or equal to 0.
    """
    if isinstance(top_k, bool) or not isinstance(top_k, int):
        raise TypeError("top_k must be an integer")
    if top_k < 0:
        raise ValueError("top_k must be >= 0")
    if top_k == 0:
        return []
    token = unicodedata.normalize("NFC", word)
    if not token:
        return []
    if token in _frequencies():
        return [token]
    return _matches(token)[:top_k]


def correct_text(text: str) -> str:
    """Replace each misspelled Odia word with its first suggestion.

    Whitespace, punctuation, digits and non-Odia text are copied through.
    A known word keeps the characters it was written with.
    """

    def replace(match: re.Match[str]) -> str:
        token = match.group()
        if not _has_base(token) or is_correct(token):
            return token
        choices = suggest(token, top_k=1)
        if not choices:
            return token
        return choices[0]

    return _WORD.sub(replace, text)


__all__ = ["correct_text", "is_correct", "suggest"]
