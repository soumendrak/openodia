"""A split is kept only when both parts are lemmas and joining them rebuilds the word."""

from __future__ import annotations

import unicodedata
from collections.abc import Sequence
from typing import Literal, overload

from openodia.syllable import split as _aksharas

_VOWELS = ("ଅ", "ଆ", "ଇ", "ଈ", "ଉ", "ଊ", "ଋ", "ଏ", "ଐ", "ଓ", "ଔ")
_VOWEL_SET = frozenset(_VOWELS)
_MATRA = {
    "ଅ": "",
    "ଆ": "ା",
    "ଇ": "ି",
    "ଈ": "ୀ",
    "ଉ": "ୁ",
    "ଊ": "ୂ",
    "ଋ": "ୃ",
    "ୠ": "ୄ",
    "ଏ": "େ",
    "ଐ": "ୈ",
    "ଓ": "ୋ",
    "ଔ": "ୌ",
}
_FROM_MATRA = {mark: vowel for vowel, mark in _MATRA.items() if mark}
_CONSONANTS = frozenset("କଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲଳଵଶଷସହୱ") | frozenset(chr(code) for code in (0x0B5C, 0x0B5D, 0x0B5F))
_NUKTA = "଼"
_HALANT = "୍"
_A = ("ଅ", "ଆ")
_I = ("ଇ", "ଈ")
_U = ("ଉ", "ଊ")
_YAN = {"ଇ": "୍ୟ", "ଈ": "୍ୟ", "ଉ": "୍ୱ", "ଊ": "୍ୱ", "ଋ": "୍ର"}
_PALATAL = {"ଚ": "ଚ୍ଚ", "ଛ": "ଚ୍ଛ", "ଜ": "ଜ୍ଜ", "ଝ": "ଜ୍ଝ", "ଶ": "ଚ୍ଛ"}
_VARGAS = (
    ("କଖଗଘଙ", "ଙ"),
    ("ଚଛଜଝଞ", "ଞ"),
    ("ଟଠଡଢଣ", "ଣ"),
    ("ତଥଦଧନ", "ନ"),
    ("ପଫବଭମ", "ମ"),
)
_VISARGA_SIBILANTS = (("ଚଛ", "ଶ"), ("ଟଠ", "ଷ"), ("ତଥ", "ସ"))

_LEMMA_TEXT = """
ବିଦ୍ୟା ଆଳୟ ମହା ଆତ୍ମା ପୁସ୍ତକ ହିମ ଦେବ ଅର୍ଥୀ ଶିକ୍ଷା ଅନୁଷ୍ଠାନ
ଗଙ୍ଗା ଆରତି ଗିରି ଇନ୍ଦ୍ର କବି ନଦୀ ଈଶ ଭାନୁ ଉଦୟ ସିନ୍ଧୁ ଊର୍ମି
ରମା ରାଜା ପରମ ସୂର୍ଯ୍ୟ ଚନ୍ଦ୍ର ଉତ୍ସବ ଜଳ ସଦା ଏବ ଐଶ୍ୱର୍ଯ୍ୟ ଔଷଧ
ଇତି ଆଦି ସୁ ଆଗତ ଅତି ଅନ୍ତ ପ୍ରତି ଏକ ଅଧି ଅକ୍ଷ ନମଃ ତେ ନିଃ ଚଳ
ତାର ଉତ୍ ଚାରଣ ସମ୍ ତୋଷ କଳ୍ପ ଚୟ ଜ୍ୱଳ ରାଜ୍ୟ ପାଳ ଗୃହ କାର୍ଯ୍ୟ
ଜନ ସେବା ଲୋକ ସଭା ଗ୍ରାମ ପଞ୍ଚାୟତ ପଥ ରାଜ ଧାନୀ ଦେଶ ଧର୍ମ ଶାଳା
କିରଣ ରାମ ସୀତା ଘର
"""
_LEMMAS = frozenset(unicodedata.normalize("NFC", word) for word in _LEMMA_TEXT.split())


def _fill_savarna(table: dict[tuple[str, str], str]) -> None:
    groups = ((_A, "ଆ"), (_I, "ଈ"), (_U, "ଊ"), (("ଋ",), "ୠ"))
    for group, product in groups:
        mark = _MATRA[product]
        for left in group:
            for right in group:
                table[(left, right)] = mark


def _fill_a_sandhi(table: dict[tuple[str, str], str]) -> None:
    products = (
        (_I, _MATRA["ଏ"]),
        (_U, _MATRA["ଓ"]),
        (("ଋ",), "ର୍"),
        (("ଏ", "ଐ"), _MATRA["ଐ"]),
        (("ଓ", "ଔ"), _MATRA["ଔ"]),
    )
    for left in _A:
        for group, surface in products:
            for right in group:
                table[(left, right)] = surface


def _fill_yan(table: dict[tuple[str, str], str]) -> None:
    for left, glide in _YAN.items():
        for right in _VOWELS:
            table.setdefault((left, right), glide + _MATRA[right])


def _vowel_sandhi() -> dict[tuple[str, str], str]:
    table: dict[tuple[str, str], str] = {}
    _fill_savarna(table)
    _fill_a_sandhi(table)
    _fill_yan(table)
    return table


def _boundary_rules() -> tuple[tuple[str, str, str], ...]:
    rules: list[tuple[str, str, str]] = []
    for ending in ("ତ୍", "ଦ୍"):
        for consonant, surface in _PALATAL.items():
            rules.append((ending, consonant, surface))
    for consonants, nasal in _VARGAS:
        for consonant in consonants:
            rules.append(("ମ୍", consonant, nasal + _HALANT + consonant))
    for consonants, sibilant in _VISARGA_SIBILANTS:
        for consonant in consonants:
            rules.append(("ଃ", consonant, sibilant + _HALANT + consonant))
    for sibilant in "ଶଷସ":
        rules.append(("ଃ", sibilant, sibilant + _HALANT + sibilant))
    ranked = sorted(rules, key=lambda rule: (len(rule[0]), len(rule[1])), reverse=True)
    return tuple(ranked)


def _vowel_inverse(table: dict[tuple[str, str], str]) -> dict[str, tuple[tuple[str, str], ...]]:
    grouped: dict[str, list[tuple[str, str]]] = {}
    for pair, surface in table.items():
        grouped.setdefault(surface, []).append(pair)
    return {surface: tuple(pairs) for surface, pairs in grouped.items()}


_VOWEL_SANDHI = _vowel_sandhi()
_BOUNDARY = _boundary_rules()
_VOWEL_INVERSE = _vowel_inverse(_VOWEL_SANDHI)


def _ending_vowel(word: str) -> tuple[str, str] | None:
    last = word[-1]
    if last in _FROM_MATRA:
        return word[:-1], _FROM_MATRA[last]
    if last in _VOWEL_SET:
        return word[:-1], last
    if last in _CONSONANTS or last == _NUKTA:
        return word, "ଅ"
    return None


def _with_vowel(stem: str, vowel: str) -> str:
    if not stem:
        return vowel
    mark = _MATRA[vowel]
    if mark:
        return stem + mark
    return stem


def _join_pair(left: str, right: str) -> str:
    if not left or not right:
        return left + right
    for ending, start, surface in _BOUNDARY:
        if left.endswith(ending) and right.startswith(start):
            return left[: -len(ending)] + surface + right[len(start) :]
    ending_vowel = _ending_vowel(left)
    if ending_vowel is not None and right[0] in _VOWEL_SET:
        stem, vowel = ending_vowel
        fused = _VOWEL_SANDHI.get((vowel, right[0]))
        if fused is not None:
            written = stem + fused if stem else _FROM_MATRA.get(fused, fused)
            return written + right[1:]
    return left + right


def join(parts: Sequence[str]) -> str:
    """Join words, applying sandhi at each boundary.

    Examples:
        >>> join(["ବିଦ୍ୟା", "ଆଳୟ"])
        'ବିଦ୍ୟାଳୟ'
        >>> join(["ରାଜ୍ୟ", "ପାଳ"])
        'ରାଜ୍ୟପାଳ'
    """
    if not parts:
        return ""
    fused = unicodedata.normalize("NFC", parts[0])
    for part in parts[1:]:
        fused = _join_pair(fused, unicodedata.normalize("NFC", part))
    return fused


def _find(word: str, surface: str) -> list[int]:
    found: list[int] = []
    start = 0
    while True:
        at = word.find(surface, start)
        if at < 0:
            return found
        found.append(at)
        start = at + 1


def _boundary_proposals(word: str) -> list[tuple[str, str]]:
    proposals: list[tuple[str, str]] = []
    for ending, start, surface in _BOUNDARY:
        for at in _find(word, surface):
            left = word[:at] + ending
            right = start + word[at + len(surface) :]
            proposals.append((left, right))
    return proposals


def _vowel_proposals(word: str) -> list[tuple[str, str]]:
    proposals: list[tuple[str, str]] = []
    for surface, pairs in _VOWEL_INVERSE.items():
        for at in _find(word, surface):
            stem = word[:at]
            rest = word[at + len(surface) :]
            for left_vowel, right_vowel in pairs:
                left = _with_vowel(stem, left_vowel)
                right = right_vowel + rest
                proposals.append((left, right))
    return proposals


def _concat_proposals(word: str) -> list[tuple[str, str]]:
    offset = 0
    ends: list[int] = []
    for piece in _aksharas(word):
        offset += len(piece)
        ends.append(offset)
    return [(word[:end], word[end:]) for end in ends[:-1]]


def _proposals(word: str) -> list[tuple[str, str]]:
    return _boundary_proposals(word) + _vowel_proposals(word) + _concat_proposals(word)


def _ranked(text: str) -> list[list[str]]:
    if not text or text in _LEMMAS:
        return []
    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[str, str]] = []
    for left, right in _proposals(text):
        if left not in _LEMMAS or right not in _LEMMAS or (left, right) in seen:
            continue
        if _join_pair(left, right) != text:
            continue
        seen.add((left, right))
        pairs.append((left, right))
    pairs.sort(key=lambda item: (-len(item[0]), item[0], item[1]))
    return [[left, right] for left, right in pairs]


@overload
def split(word: str, *, candidates: Literal[False] = False) -> list[str]: ...


@overload
def split(word: str, *, candidates: Literal[True]) -> list[list[str]]: ...


def split(word: str, *, candidates: bool = False) -> list[str] | list[list[str]]:
    """Split a compound into the words sandhi joined.

    A lemma, and any word that does not split into two lemmas, comes back
    as ``[word]``. ``candidates=True`` returns every accepted split, longest
    left part first, or ``[]`` when nothing splits.

    Examples:
        >>> split("ବିଦ୍ୟାଳୟ")
        ['ବିଦ୍ୟା', 'ଆଳୟ']
        >>> split("ରାମ")
        ['ରାମ']
    """
    text = unicodedata.normalize("NFC", word)
    ranked = _ranked(text)
    if candidates:
        return ranked
    if not ranked:
        return [word]
    return ranked[0]
