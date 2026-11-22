import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_FONTS = ("ORTTSarala",)

_FONTS_DIR = Path(__file__).resolve().parent / "fonts"
_CONSONANT_CODES = (*range(0x0B15, 0x0B29), *range(0x0B2A, 0x0B31), 0x0B32, 0x0B33, *range(0x0B35, 0x0B3A))
_CONSONANTS = frozenset(chr(code) for code in (*_CONSONANT_CODES, 0x0B5C, 0x0B5D, 0x0B5F, 0x0B71))
_VOWEL_SIGNS = frozenset("ାିୀୁୂୃେୈୋୌ")
_NASALS = frozenset("ଁଂଃ")
_JOINERS = frozenset("\u200c\u200d")
_HALANT = "\u0b4d"
_NUKTA = "\u0b3c"
_REPH = "ର୍"


@dataclass(frozen=True)
class _Font:
    pairs: tuple[tuple[str, str], ...]
    marker: str
    default: str
    halves: dict[str, str]
    reph: str
    post: tuple[tuple[re.Pattern[str], str], ...]


def _load(name: str) -> _Font:
    table = json.loads((_FONTS_DIR / f"{name}.json").read_text(encoding="utf-8"))
    matra = table["matra"]
    return _Font(
        pairs=tuple((source, target) for source, target in table["pairs"]),
        marker=matra["marker"],
        default=matra["default"],
        halves=dict(matra["forms"]),
        reph=table["reph"],
        post=tuple((re.compile(pattern), replacement) for pattern, replacement in table["post"]),
    )


_FONTS = {name: _load(name) for name in SUPPORTED_FONTS}


def _subjoined_end(text: str, halant: int) -> int:
    end = halant + 1
    while end < len(text) and text[end] in _JOINERS:
        end += 1
    if end < len(text) and text[end] in _CONSONANTS:
        end += 1
    return end


def _vowel(signs: list[str], font: _Font) -> str:
    half = next((index for index, sign in enumerate(signs) if sign in font.halves), None)
    if half is not None and font.marker in signs:
        signs[signs.index(font.marker)] = font.halves[signs[half]]
        del signs[half]
    return "".join(font.default if sign == font.marker else sign for sign in signs)


def _syllable(text: str, start: int, font: _Font) -> tuple[str, int]:
    signs = [font.marker] if text[start] == font.marker else []
    cursor = start + len(signs)
    base = text[cursor] if cursor < len(text) and text[cursor] in _CONSONANTS else ""
    cursor += len(base)
    pieces = [[base]]
    carrier = pieces[0]
    nasals: list[str] = []
    reph = ""
    while cursor < len(text):
        char = text[cursor]
        if char == _HALANT:
            end = _subjoined_end(text, cursor)
            pieces.append([text[cursor:end]])
            if text[end - 1] in _CONSONANTS:
                carrier = pieces[-1]
            cursor = end
            continue
        if char == font.marker and text[cursor + 1 : cursor + 2] not in _CONSONANTS:
            signs.append(char)
        elif char == font.reph and base:
            reph = _REPH
        elif char in _VOWEL_SIGNS or char in font.halves:
            signs.append(char)
        elif char in _NASALS:
            nasals.append(char)
        elif char == _NUKTA:
            carrier.append(char)
        else:
            break
        cursor += 1
    letters = "".join("".join(piece) for piece in pieces)
    return reph + letters + _vowel(signs, font) + "".join(nasals), cursor


def _syllables(text: str, font: _Font) -> str:
    out: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char in _CONSONANTS or char in _VOWEL_SIGNS or char in _NASALS or char == font.marker:
            piece, index = _syllable(text, index, font)
        else:
            piece, index = (_REPH if char == font.reph else char), index + 1
        out.append(piece)
    return "".join(out)


def _replace(text: str, font: _Font) -> str:
    for source, target in font.pairs:
        text = text.replace(source, target)
    return text


def _apply_post(text: str, font: _Font) -> str:
    for pattern, replacement in font.post:
        while (updated := pattern.sub(replacement, text)) != text:
            text = updated
    return text


def to_unicode(text: str, font: str) -> str:
    """Convert keystrokes typed in a legacy 8-bit Odia font to NFC Unicode Odia.

    ``text`` is the output of ``decode``. ``font`` is a name in
    ``SUPPORTED_FONTS``.

    Raises:
        ValueError: ``font`` is not in ``SUPPORTED_FONTS``.
    """
    found = _FONTS.get(font)
    if found is None:
        raise ValueError(f"unknown font {font!r}; choose from {', '.join(SUPPORTED_FONTS)}")
    converted = _apply_post(_syllables(_replace(text, found), found), found)
    return unicodedata.normalize("NFC", converted)
