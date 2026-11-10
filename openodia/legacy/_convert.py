import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_FONTS = ("AkrutiOriSarala", "ORTTSarala")

_CONSONANTS = frozenset("କଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲଳଵଶଷସହୟୱଡ଼ଢ଼")
_VOWEL_SIGNS = frozenset("ାିୀୁୂୃେୈୋୌ")
_ANUSVARA = frozenset("ଂଁ")
_REPH_SIGNS = _VOWEL_SIGNS | _ANUSVARA
_HALANT = "୍"
_NUKTA = "଼"
_FONTS_DIR = Path(__file__).resolve().parent / "fonts"


@dataclass(frozen=True)
class _Matra:
    marker: str
    default: str
    forms: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class _Rule:
    pattern: re.Pattern[str]
    repl: str
    repeat: bool


@dataclass(frozen=True)
class _Font:
    name: str
    pairs: tuple[tuple[str, str], ...]
    signatures: tuple[str, ...]
    matra: _Matra | None
    reph: str | None
    post: tuple[_Rule, ...]
    alphabet: frozenset[str]
    unique: frozenset[str]


def _pairs(value: object) -> tuple[tuple[str, str], ...]:
    if not isinstance(value, list):
        raise TypeError("font pairs must be a list")
    pairs: list[tuple[str, str]] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 2:
            raise TypeError("font pair must be two strings")
        src, dst = item
        if not isinstance(src, str) or not isinstance(dst, str) or src == "":
            raise TypeError("font pair must be two strings")
        pairs.append((src, dst))
    return tuple(pairs)


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise TypeError("font signatures must be a list")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or item == "":
            raise TypeError("font signatures must be non-empty strings")
        items.append(item)
    return tuple(items)


def _matra(value: object) -> _Matra | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError("font matra must be an object")
    marker = value.get("marker")
    default = value.get("default")
    forms = value.get("forms")
    if not isinstance(marker, str) or not isinstance(default, str) or not isinstance(forms, list):
        raise TypeError("font matra must name a marker, a default and forms")
    parsed: list[tuple[str, str]] = []
    for form in forms:
        if not isinstance(form, list) or len(form) != 2:
            raise TypeError("matra form must be a suffix and a vowel sign")
        suffix, sign = form
        if not isinstance(suffix, str) or not isinstance(sign, str) or suffix == "":
            raise TypeError("matra form must be a suffix and a vowel sign")
        parsed.append((suffix, sign))
    parsed.sort(key=lambda item: len(item[0]), reverse=True)
    return _Matra(marker, default, tuple(parsed))


def _rules(value: object) -> tuple[_Rule, ...]:
    if not isinstance(value, list):
        raise TypeError("font post rules must be a list")
    rules: list[_Rule] = []
    for item in value:
        if not isinstance(item, list) or len(item) != 3:
            raise TypeError("font post rule must be pattern, replacement, repeat")
        pattern, repl, repeat = item
        if not isinstance(pattern, str) or not isinstance(repl, str) or not isinstance(repeat, bool):
            raise TypeError("font post rule must be pattern, replacement, repeat")
        rules.append(_Rule(re.compile(pattern), repl, repeat))
    return tuple(rules)


def _reph(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value == "":
        raise TypeError("font reph must be a marker")
    return value


def _alphabet(pairs: tuple[tuple[str, str], ...], matra: _Matra | None, reph: str | None) -> frozenset[str]:
    chars: set[str] = set()
    for src, _dst in pairs:
        chars.update(src)
    if matra is not None:
        chars.add(matra.marker)
        for suffix, _sign in matra.forms:
            chars.update(suffix)
    if reph is not None:
        chars.add(reph)
    return frozenset(chars)


def _read_font(name: str) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...], _Matra | None, str | None, tuple[_Rule, ...]]:
    data = json.loads((_FONTS_DIR / f"{name}.json").read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise TypeError(f"{name} font must be an object")
    return (
        _pairs(data.get("pairs")),
        _strings(data.get("signatures")),
        _matra(data.get("matra")),
        _reph(data.get("reph")),
        _rules(data.get("post")),
    )


def _load() -> tuple[_Font, ...]:
    loaded = [_read_font(name) for name in SUPPORTED_FONTS]
    alphabets = [_alphabet(pairs, matra, reph) for pairs, _sigs, matra, reph, _post in loaded]
    fonts: list[_Font] = []
    for index, name in enumerate(SUPPORTED_FONTS):
        pairs, signatures, matra, reph, post = loaded[index]
        others: set[str] = set()
        for other, alphabet in enumerate(alphabets):
            if other != index:
                others.update(alphabet)
        fonts.append(
            _Font(
                name=name,
                pairs=pairs,
                signatures=signatures,
                matra=matra,
                reph=reph,
                post=post,
                alphabet=alphabets[index],
                unique=alphabets[index] - others,
            )
        )
    return tuple(fonts)


_FONTS = _load()
_BY_NAME = {font.name: font for font in _FONTS}


def _replace(text: str, pairs: tuple[tuple[str, str], ...]) -> str:
    for src, dst in pairs:
        text = text.replace(src, dst)
    return text


def _with_nukta(text: str, index: int) -> int:
    end = index + 1
    if end < len(text) and text[end] == _NUKTA:
        return end + 1
    return end


def _shift_consonant(text: str, marker: str) -> str:
    out: list[str] = []
    index = 0
    limit = len(text)
    while index < limit:
        if text[index] == marker and index + 1 < limit and text[index + 1] in _CONSONANTS:
            end = _with_nukta(text, index + 1)
            out.append(text[index + 1 : end])
            out.append(marker)
            index = end
            continue
        out.append(text[index])
        index += 1
    return "".join(out)


def _shift_halant(text: str, marker: str) -> str:
    out: list[str] = []
    index = 0
    limit = len(text)
    while index < limit:
        follows = index + 2 < limit and text[index + 1] == _HALANT and text[index + 2] in _CONSONANTS
        if text[index] == marker and follows:
            end = _with_nukta(text, index + 2)
            out.append(_HALANT)
            out.append(text[index + 2 : end])
            out.append(marker)
            index = end
            continue
        out.append(text[index])
        index += 1
    return "".join(out)


def _apply_matra(text: str, matra: _Matra) -> str:
    text = _shift_consonant(text, matra.marker)
    while True:
        shifted = _shift_halant(text, matra.marker)
        if shifted == text:
            break
        text = shifted
    for suffix, sign in matra.forms:
        text = text.replace(matra.marker + suffix, sign)
    return text.replace(matra.marker, matra.default)


def _shift_reph_signs(text: str, marker: str) -> str:
    out: list[str] = []
    index = 0
    limit = len(text)
    while index < limit:
        if text[index] in _CONSONANTS:
            end = _with_nukta(text, index)
            while end < limit and text[end] in _REPH_SIGNS:
                end += 1
            if end < limit and text[end] == marker:
                out.append(marker)
                out.append(text[index:end])
                index = end + 1
                continue
        out.append(text[index])
        index += 1
    return "".join(out)


def _shift_reph_halant(text: str, marker: str) -> str:
    out: list[str] = []
    index = 0
    limit = len(text)
    while index < limit:
        if text[index] in _CONSONANTS:
            base = _with_nukta(text, index)
            follows = base + 1 < limit and text[base] == _HALANT and text[base + 1] == marker
            if follows:
                out.append(marker)
                out.append(text[index:base])
                out.append(_HALANT)
                index = base + 2
                continue
        out.append(text[index])
        index += 1
    return "".join(out)


def _apply_reph(text: str, marker: str) -> str:
    text = _shift_reph_signs(text, marker)
    while True:
        shifted = _shift_reph_halant(text, marker)
        if shifted == text:
            break
        text = shifted
    return text.replace(marker, "ର୍")


def _shift_anusvara(text: str) -> str:
    out: list[str] = []
    index = 0
    limit = len(text)
    while index < limit:
        if text[index] in _ANUSVARA and index + 1 < limit and text[index + 1] in _VOWEL_SIGNS:
            out.append(text[index + 1])
            out.append(text[index])
            index += 2
            continue
        out.append(text[index])
        index += 1
    return "".join(out)


def _apply_anusvara(text: str) -> str:
    while True:
        shifted = _shift_anusvara(text)
        if shifted == text:
            return text
        text = shifted


def _apply_post(text: str, rules: tuple[_Rule, ...]) -> str:
    for rule in rules:
        if not rule.repeat:
            text = rule.pattern.sub(rule.repl, text)
            continue
        while True:
            updated = rule.pattern.sub(rule.repl, text)
            if updated == text:
                break
            text = updated
    return text


def _convert(text: str, font: _Font) -> str:
    if text == "":
        return ""
    text = _replace(text, font.pairs)
    if font.matra is not None:
        text = _apply_matra(text, font.matra)
    if font.reph is not None:
        text = _apply_reph(text, font.reph)
    text = _apply_anusvara(text)
    text = _apply_post(text, font.post)
    return unicodedata.normalize("NFC", text)


def to_unicode(text: str, font: str) -> str:
    found = _BY_NAME.get(font)
    if found is None:
        choices = ", ".join(SUPPORTED_FONTS)
        raise ValueError(f"unknown font {font!r}; choose from {choices}")
    return _convert(text, found)


def _score(text: str, font: _Font) -> int:
    score = 0
    for signature in font.signatures:
        score += 5 * text.count(signature)
    for char in text:
        if char in font.unique:
            score += 2
        elif char in font.alphabet:
            score += 1
    return score


def detect_font(text: str) -> dict[str, str | float | None]:
    if text == "":
        return {"font": None, "confidence": 0.0}
    scores = [_score(text, font) for font in _FONTS]
    best = max(scores)
    if best == 0:
        return {"font": None, "confidence": 0.0}
    chosen = scores.index(best)
    return {"font": _FONTS[chosen].name, "confidence": best / sum(scores)}


def to_unicode_auto(text: str) -> str:
    font = detect_font(text)["font"]
    if not isinstance(font, str):
        return text
    return to_unicode(text, font)
