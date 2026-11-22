import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_FONTS = ("AkrutiOriSarala", "ORTTSarala")

_CONSONANTS = frozenset("କଖଗଘଙଚଛଜଝଞଟଠଡଢଣତଥଦଧନପଫବଭମଯରଲଳଵଶଷସହୟୱଡ଼ଢ଼")
_VOWEL_SIGNS = frozenset("ାିୀୁୂୃେୈୋୌ")
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


@dataclass(frozen=True)
class _Font:
    name: str
    pairs: tuple[tuple[str, str], ...]
    signatures: tuple[str, ...]
    matra: _Matra
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


def _matra(value: object) -> _Matra:
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
        if not isinstance(item, list) or len(item) != 2:
            raise TypeError("font post rule must be pattern and replacement")
        pattern, repl = item
        if not isinstance(pattern, str) or not isinstance(repl, str):
            raise TypeError("font post rule must be pattern and replacement")
        rules.append(_Rule(re.compile(pattern), repl))
    return tuple(rules)


def _reph(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or value == "":
        raise TypeError("font reph must be a marker")
    return value


_NOT_LEGACY_EVIDENCE = frozenset(chr(code) for code in range(0x0B00, 0x0B80)) | frozenset("।॥")


def _legacy_evidence(text: str) -> bool:
    return all(character not in _NOT_LEGACY_EVIDENCE for character in text)


def _alphabet(pairs: tuple[tuple[str, str], ...], matra: _Matra, reph: str | None) -> frozenset[str]:
    chars: set[str] = set()
    for src, _dst in pairs:
        chars.update(character for character in src if character not in _NOT_LEGACY_EVIDENCE)
    if _legacy_evidence(matra.marker):
        chars.add(matra.marker)
        for suffix, _sign in matra.forms:
            chars.update(character for character in suffix if character not in _NOT_LEGACY_EVIDENCE)
    if reph is not None and reph not in _NOT_LEGACY_EVIDENCE:
        chars.add(reph)
    return frozenset(chars)


def _read_font(
    name: str,
) -> tuple[tuple[tuple[str, str], ...], tuple[str, ...], _Matra, str | None, tuple[_Rule, ...]]:
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
                signatures=tuple(item for item in signatures if _legacy_evidence(item)),
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


_JOINERS = frozenset("\u200c\u200d")
_NASALS = frozenset("ଁଂଃ")
_REPH = "ର୍"


def _subjoined_end(text: str, index: int) -> int:
    cursor = index + 1
    while cursor < len(text) and text[cursor] in _JOINERS:
        cursor += 1
    if cursor < len(text) and text[cursor] in _CONSONANTS:
        return _with_nukta(text, cursor)
    return cursor


def _vowel(signs: list[str], matra: _Matra) -> str:
    forms = dict(matra.forms)
    found = next((index for index, sign in enumerate(signs) if sign in forms), None)
    if matra.marker in signs and found is not None:
        signs[signs.index(matra.marker)] = forms[signs[found]]
        del signs[found]
    return "".join(matra.default if sign == matra.marker else sign for sign in signs)


def _syllable(text: str, index: int, font: _Font) -> tuple[str, int]:
    matra = font.matra
    marker = matra.marker
    signs = [text[index]] if text[index] == marker else []
    cursor = index + len(signs)
    limit = len(text)
    base_end = _with_nukta(text, cursor) if cursor < limit and text[cursor] in _CONSONANTS else cursor
    base = text[cursor:base_end]
    chain: list[str] = []
    nasals: list[str] = []
    reph = False
    cursor = base_end
    while cursor < limit:
        char = text[cursor]
        if char == _HALANT:
            end = _subjoined_end(text, cursor)
            chain.append(text[cursor:end])
            cursor = end
            continue
        if char == marker and text[cursor + 1 : cursor + 2] not in _CONSONANTS:
            signs.append(char)
        elif char == font.reph and base:
            reph = True
        elif char in _VOWEL_SIGNS or char in dict(matra.forms):
            signs.append(char)
        elif char in _NASALS:
            nasals.append(char)
        else:
            break
        cursor += 1
    head = _REPH if reph else ""
    return head + base + "".join(chain) + _vowel(signs, matra) + "".join(nasals), cursor


def _canonical(text: str, font: _Font) -> str:
    marker = font.matra.marker
    out: list[str] = []
    index = 0
    limit = len(text)
    while index < limit:
        char = text[index]
        if char in _CONSONANTS or char in _VOWEL_SIGNS or char in _NASALS or char == marker:
            piece, index = _syllable(text, index, font)
            out.append(piece)
            continue
        out.append(_REPH if char == font.reph else char)
        index += 1
    return "".join(out)


def _apply_post(text: str, rules: tuple[_Rule, ...]) -> str:
    for rule in rules:
        while True:
            updated = rule.pattern.sub(rule.repl, text)
            if updated == text:
                break
            text = updated
    return text


def _convert(text: str, font: _Font) -> str:
    if text == "":
        return ""
    text = _canonical(_replace(text, font.pairs), font)
    text = _apply_post(text, font.post)
    return unicodedata.normalize("NFC", text)


def decode(data: bytes) -> str:
    """Decode legacy font bytes for ``to_unicode``.

    Defined bytes use cp1252. The five bytes that codec leaves undefined,
    0x81, 0x8D, 0x8F, 0x90 and 0x9D, stay as those code points.
    """
    if not isinstance(data, bytes | bytearray):
        raise TypeError("legacy font bytes are required")
    chars: list[str] = []
    for byte in data:
        try:
            chars.append(bytes((byte,)).decode("cp1252"))
        except UnicodeDecodeError:
            chars.append(chr(byte))
    return "".join(chars)


def to_unicode(text: str, font: str) -> str:
    """Convert legacy font keystrokes to NFC Unicode Odia.

    ``text`` comes from ``decode``. ``font`` is a name in ``SUPPORTED_FONTS``.
    """
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
    """Guess which legacy font produced ``text``.

    Returns ``font`` and ``confidence``. ``font`` is None on a tie, where
    ``confidence`` is 0.5, and when the text has no legacy-font evidence,
    where ``confidence`` is 0.0. Text that contains an Odia code point or a
    danda is already Unicode, so it has no legacy-font evidence.
    """
    if not _legacy_evidence(text):
        return {"font": None, "confidence": 0.0}
    scores = [_score(text, font) for font in _FONTS]
    best = max(scores)
    if best == 0:
        return {"font": None, "confidence": 0.0}
    winners = [font for font, score in zip(_FONTS, scores, strict=True) if score == best]
    if len(winners) != 1:
        return {"font": None, "confidence": best / sum(scores)}
    return {"font": winners[0].name, "confidence": best / sum(scores)}


def to_unicode_auto(text: str) -> str:
    """Detect the legacy font and convert it.

    Returns ``text`` unchanged when ``detect_font`` has no font: a tie
    (``confidence`` 0.5) or no legacy-font evidence (``confidence`` 0.0).
    Call ``detect_font`` to tell those apart.
    """
    font = detect_font(text)["font"]
    if not isinstance(font, str):
        return text
    return to_unicode(text, font)
