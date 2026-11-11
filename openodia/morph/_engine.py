"""Nominal plural and case peel from the right. A verb takes one fusional tail."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal, TypeVar

Pos = Literal["NOUN", "VERB", "UNKNOWN"]
Case = Literal["nominative", "genitive", "dative", "locative", "ablative", "instrumental"]
Number = Literal["singular", "plural"]
Tense = Literal["past", "present", "future"]
Aspect = Literal["simple", "progressive", "perfect", "habitual"]
Person = Literal[1, 2, 3]
Kind = Literal["nominal", "verbal"]
Guard = Literal["any", "noun_c", "human", "verb"]
NonfiniteForm = Literal["infinitive", "conjunctive"]

_MATRA = frozenset("ାିୀୁୂୃୄେୈୋୌୖୗୢୣ")
_INDEPENDENT = frozenset("ଅଆଇଈଉଊଋଌଏଐଓଔ")


@dataclass(frozen=True, slots=True)
class NounFeatures:
    """A bare noun is singular nominative."""

    number: Number
    case: Case
    definite: bool


@dataclass(frozen=True, slots=True)
class FiniteVerb:
    """One reading of a fusional finite ending.

    ଲେ and ଥିଲେ are third person plural, which is also the polite form.
    """

    tense: Tense
    aspect: Aspect
    person: Person
    number: Number


@dataclass(frozen=True, slots=True)
class NonfiniteVerb:
    """Infinitive (କରିବା) or conjunctive participle (କରି)."""

    form: NonfiniteForm


@dataclass(frozen=True, slots=True)
class UnknownFeatures:
    """No ending matched and the word is not in the lexicon."""


Features = NounFeatures | FiniteVerb | NonfiniteVerb | UnknownFeatures


@dataclass(frozen=True, slots=True)
class Lemma:
    """Verb ``form`` is the infinitive. Noun ``form`` is the stem."""

    form: str
    pos: Pos
    features: Features

    def __post_init__(self) -> None:
        matched = (
            (self.pos == "NOUN" and isinstance(self.features, NounFeatures))
            or (self.pos == "VERB" and isinstance(self.features, (FiniteVerb, NonfiniteVerb)))
            or (self.pos == "UNKNOWN" and isinstance(self.features, UnknownFeatures))
        )
        if not matched:
            raise ValueError("pos does not match features")


@dataclass(frozen=True, slots=True)
class Suffix:
    """One grammatical ending and the orthographic tails that realize it."""

    citation: str
    kind: Kind
    tails: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _Nominal:
    citation: str
    text: str
    guard: Guard
    number: Number | None = None
    case: Case | None = None
    definite: bool = False
    min_aksharas: int = 1


@dataclass(frozen=True, slots=True)
class _Verbal:
    citation: str
    text: str
    guard: Guard
    reading: FiniteVerb | NonfiniteVerb


_Row = _Nominal | _Verbal
_RowT = TypeVar("_RowT", _Nominal, _Verbal)


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _case(citation: str, text: str, case: Case, guard: Guard = "any", min_aksharas: int = 1) -> _Nominal:
    return _Nominal(_nfc(citation), _nfc(text), guard, case=case, min_aksharas=min_aksharas)


def _definite(text: str) -> _Nominal:
    normalized = _nfc(text)
    return _Nominal(normalized, normalized, "any", definite=True)


def _plural(citation: str, text: str, guard: Guard = "any") -> _Nominal:
    return _Nominal(_nfc(citation), _nfc(text), guard, number="plural")


def _plural_dative(text: str) -> _Nominal:
    normalized = _nfc(text)
    return _Nominal(normalized, normalized, "any", number="plural", case="dative")


def _finite(
    citation: str,
    text: str,
    tense: Tense,
    aspect: Aspect,
    person: Person,
    number: Number,
    guard: Guard = "any",
) -> _Verbal:
    reading = FiniteVerb(tense, aspect, person, number)
    return _Verbal(_nfc(citation), _nfc(text), guard, reading)


def _nonfinite(citation: str, text: str, form: NonfiniteForm, guard: Guard = "any") -> _Verbal:
    return _Verbal(_nfc(citation), _nfc(text), guard, NonfiniteVerb(form))


def _same(
    citation: str,
    texts: tuple[str, ...],
    tense: Tense,
    aspect: Aspect,
    person: Person,
    number: Number,
) -> tuple[_Verbal, ...]:
    return tuple(_finite(citation, text, tense, aspect, person, number) for text in texts)


_TAILS: tuple[_Row, ...] = (
    _case("ର", "ର", "genitive", min_aksharas=2),
    _case("କୁ", "କୁ", "dative"),
    _case("ରେ", "ରେ", "locative"),
    _case("ରେ", "େ", "locative", "noun_c"),
    _case("ରୁ", "ରୁ", "ablative"),
    _case("ଠାରୁ", "ଠାରୁ", "ablative"),
    _case("ଠୁ", "ଠୁ", "ablative"),
    _case("ଠାରେ", "ଠାରେ", "locative"),
    _case("ଦ୍ୱାରା", "ଦ୍ୱାରା", "instrumental"),
    _case("ଦେଇ", "ଦେଇ", "instrumental"),
    _definite("ଟି"),
    _definite("ଟା"),
    _definite("ଟେ"),
    _definite("ଟିଏ"),
    _plural("ମାନେ", "ମାନେ"),
    _plural("ମାନଙ୍କ", "ମାନଙ୍କ"),
    _plural("ଗୁଡ଼ିକ", "ଗୁଡ଼ିକ"),
    _plural("ଗୁଡ଼ା", "ଗୁଡ଼ା"),
    _plural("ଗୁଡ଼ାକ", "ଗୁଡ଼ାକ"),
    _plural("ଗୁଡ଼ିଏ", "ଗୁଡ଼ିଏ"),
    _plural("ଙ୍କ", "ଙ୍କ"),
    _plural("େ", "େ", "human"),
    _plural_dative("ମାନଙ୍କୁ"),
    _plural_dative("ଙ୍କୁ"),
    _plural_dative("ଗୁଡ଼ିକୁ"),
    *_same("ଉଥିଲେ", ("ୁଥିଲେ", "ଉଥିଲେ"), "past", "progressive", 3, "plural"),
    _finite("ଉଥିଲେ", "ଥିଲେ", "past", "progressive", 3, "plural", "verb"),
    *_same("ଉଥିଲା", ("ୁଥିଲା", "ଉଥିଲା"), "past", "progressive", 3, "singular"),
    _finite("ଉଥିଲା", "ଥିଲା", "past", "progressive", 3, "singular", "verb"),
    _finite("ଉଥିଲି", "ୁଥିଲି", "past", "progressive", 1, "singular"),
    *_same("ଉଛି", ("ୁଛି", "ଉଛି"), "present", "progressive", 3, "singular"),
    _finite("ଉଛୁ", "ୁଛୁ", "present", "progressive", 1, "plural"),
    _finite("ଉଛନ୍ତି", "ୁଛନ୍ତି", "present", "progressive", 3, "plural"),
    *_same("ଇଛି", ("ିଛି", "ଇଛି"), "present", "perfect", 3, "singular"),
    *_same("ଇଲା", ("ିଲା", "ଇଲା"), "past", "simple", 3, "singular"),
    *_same("ଇଲେ", ("ିଲେ", "ଇଲେ"), "past", "simple", 3, "plural"),
    *_same("ଇଲି", ("ିଲି", "ଇଲି"), "past", "simple", 1, "singular"),
    *_same("ଇବ", ("ିବ", "ଇବ"), "future", "simple", 3, "singular"),
    _finite("ଇବି", "ିବି", "future", "simple", 1, "singular"),
    *_same("ଇବେ", ("ିବେ", "ଇବେ"), "future", "simple", 3, "plural"),
    *_same("ଥାଏ", ("ଥାଏ", "ିଥାଏ"), "present", "habitual", 3, "singular"),
    _finite("ଇଥିଲେ", "ିଥିଲେ", "past", "perfect", 3, "plural"),
    _finite("ଇଥିଲେ", "ଇଥିଲେ", "past", "perfect", 3, "plural"),
    _finite("ଇଥିଲା", "ିଥିଲା", "past", "perfect", 3, "singular"),
    _finite("ଇଥିଲା", "ଇଥିଲା", "past", "perfect", 3, "singular"),
    _finite("ଇଛନ୍ତି", "ିଛନ୍ତି", "present", "perfect", 3, "plural"),
    _finite("ଇଛନ୍ତି", "ଇଛନ୍ତି", "present", "perfect", 3, "plural"),
    _finite("ନ୍ତି", "ନ୍ତି", "present", "simple", 3, "plural"),
    _finite("ଏ", "େ", "present", "simple", 3, "singular", "verb"),
    _finite("ଏ", "ଏ", "present", "simple", 3, "singular", "verb"),
    _nonfinite("ଇବା", "ିବା", "infinitive"),
    _nonfinite("ଇବା", "ଇବା", "infinitive"),
    _nonfinite("ଇବା", "ବା", "infinitive", "verb"),
    _finite("ଇବ", "ବ", "future", "simple", 3, "singular", "verb"),
    _finite("ଇବି", "ବି", "future", "simple", 1, "singular", "verb"),
    _finite("ଇବେ", "ବେ", "future", "simple", 3, "plural", "verb"),
    _nonfinite("ଇ", "ି", "conjunctive", "verb"),
    _nonfinite("ଇ", "ଇ", "conjunctive", "verb"),
)

_VERBS = frozenset(_nfc(word) for word in "ଆସ କର ବସ ଶୁଣ ଦେଖ ରହ କହ ଚାହ ପଢ଼ ଖା ପା ଗା ଯା ଥା ଦେ ନେ ହେ".split())
_NOUNS = frozenset(_nfc(word) for word in "ଘର ଫୁଲ ବହି ପୁରୀ ମନ୍ଦିର ସରକାର ବଜାର ଅଧିକାର ପରିବାର ଗଛ ନଦୀ ଦିନ ରାସ୍ତା କଥା ଜଳ ଫଳ ଓଡ଼ିଶା ପିଲା ଭାଇ ହାତ".split())
_HUMANS = frozenset(_nfc(word) for word in ("ଲୋକ", "ବାଳକ", "ମଣିଷ", "ଛାତ୍ର"))
_INFINITIVE_OVERRIDE = {_nfc("ଯା"): "ଯିବା", _nfc("ଥା"): "ଥିବା"}


def _past(root: str, person: Person, number: Number) -> tuple[str, FiniteVerb]:
    return _nfc(root), FiniteVerb("past", "simple", person, number)


_IRREGULAR: dict[str, tuple[str, FiniteVerb | NonfiniteVerb]] = {
    _nfc("କଲି"): _past("କର", 1, "singular"),
    _nfc("କଲୁ"): _past("କର", 1, "plural"),
    _nfc("କଲା"): _past("କର", 3, "singular"),
    _nfc("କଲେ"): _past("କର", 3, "plural"),
    _nfc("ଗଲି"): _past("ଯା", 1, "singular"),
    _nfc("ଗଲୁ"): _past("ଯା", 1, "plural"),
    _nfc("ଗଲା"): _past("ଯା", 3, "singular"),
    _nfc("ଗଲେ"): _past("ଯା", 3, "plural"),
    _nfc("ଦେଲା"): _past("ଦେ", 3, "singular"),
    _nfc("ଦେଲେ"): _past("ଦେ", 3, "plural"),
    _nfc("ନେଲା"): _past("ନେ", 3, "singular"),
    _nfc("ନେଲେ"): _past("ନେ", 3, "plural"),
    _nfc("ହେଲା"): _past("ହେ", 3, "singular"),
    _nfc("ହେଲେ"): _past("ହେ", 3, "plural"),
    _nfc("ଯିବା"): (_nfc("ଯା"), NonfiniteVerb("infinitive")),
    _nfc("ଥିବା"): (_nfc("ଥା"), NonfiniteVerb("infinitive")),
    _nfc("ଥିଲା"): _past("ଥା", 3, "singular"),
    _nfc("ଥିଲେ"): _past("ଥା", 3, "plural"),
    _nfc("ଅଛି"): (_nfc("ଥା"), FiniteVerb("present", "progressive", 3, "singular")),
}


def suffixes() -> tuple[Suffix, ...]:
    """Grammatical endings, longest tail first inside each citation.

    Returns:
        One entry per citation. Stacks such as ଗୁଡ଼ିକର are peels of these
        rows, not extra rows. The total number of tails is at least 50.
    """
    order: list[str] = []
    grouped: dict[str, list[str]] = {}
    kinds: dict[str, Kind] = {}
    for tail in _TAILS:
        bucket = grouped.get(tail.citation)
        if bucket is None:
            order.append(tail.citation)
            bucket = []
            grouped[tail.citation] = bucket
            kinds[tail.citation] = "verbal" if isinstance(tail, _Verbal) else "nominal"
        if tail.text not in bucket:
            bucket.append(tail.text)
    return tuple(
        Suffix(citation, kinds[citation], tuple(sorted(grouped[citation], key=len, reverse=True))) for citation in order
    )


def _aksharas(text: str) -> int:
    skipped = _MATRA | set("଼୍ଁଂଃ")
    return sum(1 for char in text if char not in skipped)


def _consonant_final(text: str) -> bool:
    last = text[-1]
    return last not in _MATRA and last not in _INDEPENDENT


def _shape(text: str) -> bool:
    first = text[0]
    return first not in _MATRA and first not in "଼୍" and not text.endswith("୍")


def _allows(guard: Guard, remainder: str) -> bool:
    if guard == "any":
        return True
    if guard == "verb":
        return remainder in _VERBS
    consonant = _consonant_final(remainder)
    if guard == "noun_c":
        return consonant and remainder in _NOUNS
    return consonant and remainder in _HUMANS


def _known_nominal(remainder: str) -> bool:
    return remainder in _NOUNS or remainder in _HUMANS


def _candidate(word: str, tail: _Row) -> str | None:
    if len(tail.text) >= len(word) or not word.endswith(tail.text):
        return None
    remainder = word[: -len(tail.text)]
    if len(remainder) < 2 or not _shape(remainder) or not _allows(tail.guard, remainder):
        return None
    if isinstance(tail, _Nominal) and _aksharas(remainder) < tail.min_aksharas:
        return None
    if isinstance(tail, _Verbal) and _known_nominal(remainder) and remainder not in _VERBS:
        return None
    return remainder


def _best(word: str, tails: tuple[_RowT, ...]) -> tuple[str, _RowT] | None:
    found: tuple[tuple[bool, int], str, _RowT] | None = None
    for tail in tails:
        remainder = _candidate(word, tail)
        if remainder is None:
            continue
        known = remainder in _VERBS if isinstance(tail, _Verbal) else _known_nominal(remainder)
        rank = (known, len(tail.text))
        if found is None or rank > found[0]:
            found = (rank, remainder, tail)
    if found is None:
        return None
    return found[1], found[2]


def _infinitive(root: str) -> str:
    override = _INFINITIVE_OVERRIDE.get(root)
    if override is not None:
        return override
    if root.endswith("ା"):
        return root + "ଇବା"
    if root.endswith(("େ", "ୋ", "ି", "ୀ", "ୁ", "ୂ", "ୈ", "ୌ")):
        return root + "ବା"
    return root + "ିବା"


def _verb_from(root: str, tail: _Verbal) -> Lemma:
    return Lemma(_infinitive(root), "VERB", tail.reading)


def _peel_nominal(word: str) -> tuple[str, NounFeatures] | None:
    current = word
    number: Number | None = None
    case: Case | None = None
    definite = False
    peeled = False
    nominal_tails = tuple(tail for tail in _TAILS if isinstance(tail, _Nominal))
    while True:
        if _known_nominal(current) or current in _VERBS:
            break
        hit = _best(current, nominal_tails)
        if hit is None:
            break
        current, tail = hit
        peeled = True
        if number is None and tail.number is not None:
            number = tail.number
        if case is None and tail.case is not None:
            case = tail.case
        if tail.definite:
            definite = True
    if not peeled:
        return None
    return current, NounFeatures(number or "singular", case or "nominative", definite)


def _prepare(word: str) -> str:
    if not isinstance(word, str):
        raise TypeError("word must be str")
    return _nfc(word)


def _irregular(surface: str) -> tuple[str, Lemma] | None:
    found = _IRREGULAR.get(surface)
    if found is None:
        return None
    root, features = found
    return root, Lemma(_infinitive(root), "VERB", features)


def _analyze(word: str) -> tuple[str, Lemma]:
    text = _prepare(word)
    if text == "":
        return "", Lemma("", "UNKNOWN", UnknownFeatures())
    irregular = _irregular(text)
    if irregular is not None:
        return irregular
    if text in _VERBS:
        return text, Lemma(_infinitive(text), "VERB", NonfiniteVerb("infinitive"))
    if _known_nominal(text):
        return text, Lemma(text, "NOUN", NounFeatures("singular", "nominative", False))
    nominal = _peel_nominal(text)
    current = text if nominal is None else nominal[0]
    peeled = _irregular(current)
    if peeled is not None:
        return peeled
    verbal_tails = tuple(tail for tail in _TAILS if isinstance(tail, _Verbal))
    verbal = _best(current, verbal_tails)
    if verbal is not None:
        return verbal[0], _verb_from(verbal[0], verbal[1])
    if nominal is not None:
        return nominal[0], Lemma(nominal[0], "NOUN", nominal[1])
    return text, Lemma(text, "UNKNOWN", UnknownFeatures())


def stem(word: str) -> str:
    """Return the noun stem or verb root of one word.

    Args:
        word: One token. A sentence is not split.

    Returns:
        The stem. ``stem(stem(word))`` is ``stem(word)``. ``""`` stays ``""``.
        A non-str raises ``TypeError``.
    """
    return _analyze(word)[0]


def lemma(word: str) -> Lemma:
    """Return the citation form, part of speech, and features of one word.

    Args:
        word: One token, the same string ``stem`` accepts.

    Returns:
        A ``Lemma``. Verb ``form`` is the infinitive. Noun ``form`` is the
        stem. Unknown words come back as ``pos="UNKNOWN"``.
    """
    return _analyze(word)[1]
