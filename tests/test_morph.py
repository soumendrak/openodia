from __future__ import annotations

import json
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Literal

import pytest

from openodia.morph import (
    FiniteVerb,
    Lemma,
    NonfiniteVerb,
    NounFeatures,
    UnknownFeatures,
    lemma,
    stem,
    suffixes,
)
import openodia.morph as morph

_MATRA = frozenset("ାିୀୁୂୃୄେୈୋୌୖୗୢୣଅଆଇଈଉଊଋଌଏଐଓଔ")
_BARE = NounFeatures("singular", "nominative", False)

_NOUNS = (
    "ଘର",
    "ଫୁଲ",
    "ବହି",
    "ପୁରୀ",
    "ମନ୍ଦିର",
    "ସରକାର",
    "ବଜାର",
    "ଅଧିକାର",
    "ପରିବାର",
    "ଗଛ",
    "ନଦୀ",
    "ଦିନ",
    "ରାସ୍ତା",
    "କଥା",
    "ଜଳ",
    "ଫଳ",
    "ଓଡ଼ିଶା",
    "ପିଲା",
    "ଭାଇ",
    "ହାତ",
)
_HUMANS = ("ଲୋକ", "ବାଳକ", "ମଣିଷ", "ଛାତ୍ର")
_VERBS = {
    "ଆସ": "ଆସିବା",
    "କର": "କରିବା",
    "ବସ": "ବସିବା",
    "ଶୁଣ": "ଶୁଣିବା",
    "ଦେଖ": "ଦେଖିବା",
    "ରହ": "ରହିବା",
    "କହ": "କହିବା",
    "ଚାହ": "ଚାହିବା",
    "ପଢ଼": "ପଢ଼ିବା",
    "ଖା": "ଖାଇବା",
    "ପା": "ପାଇବା",
    "ଗା": "ଗାଇବା",
    "ଯା": "ଯିବା",
    "ଥା": "ଥିବା",
    "ଦେ": "ଦେବା",
    "ନେ": "ନେବା",
    "ହେ": "ହେବା",
}
_CONSONANT_ROOTS = ("ଆସ", "କର", "ବସ", "ଶୁଣ", "ଦେଖ", "ରହ", "କହ", "ଚାହ", "ପଢ଼")
_AA_ROOTS = ("ଖା", "ପା", "ଗା", "ଯା", "ଥା")
_E_ROOTS = ("ଦେ", "ନେ", "ହେ")

_CASES: tuple[tuple[str, str], ...] = (
    ("ର", "genitive"),
    ("କୁ", "dative"),
    ("ରେ", "locative"),
    ("ରୁ", "ablative"),
    ("ଠାରୁ", "ablative"),
    ("ଠାରେ", "locative"),
    ("ଠୁ", "ablative"),
    ("ଦ୍ୱାରା", "instrumental"),
    ("ଦେଇ", "instrumental"),
)
_DEFINITE = ("ଟି", "ଟା", "ଟେ", "ଟିଏ")
_INANIMATE_PLURAL = ("ଗୁଡ଼ିକ", "ଗୁଡ଼ା", "ଗୁଡ଼ାକ", "ଗୁଡ଼ିଏ", "ଙ୍କ")
_HUMAN_PLURAL = ("ମାନେ", "ମାନଙ୍କ")
_STACK_CASES = ("ର", "କୁ", "ରେ")

_CONSONANT_ENDINGS: tuple[tuple[str, FiniteVerb | NonfiniteVerb], ...] = (
    ("ୁଥିଲେ", FiniteVerb("past", "progressive", 3, "plural")),
    ("ୁଥିଲା", FiniteVerb("past", "progressive", 3, "singular")),
    ("ୁଥିଲି", FiniteVerb("past", "progressive", 1, "singular")),
    ("ୁଛି", FiniteVerb("present", "progressive", 3, "singular")),
    ("ୁଛୁ", FiniteVerb("present", "progressive", 1, "plural")),
    ("ୁଛନ୍ତି", FiniteVerb("present", "progressive", 3, "plural")),
    ("ିଲା", FiniteVerb("past", "simple", 3, "singular")),
    ("ିଲେ", FiniteVerb("past", "simple", 3, "plural")),
    ("ିଲି", FiniteVerb("past", "simple", 1, "singular")),
    ("ିବ", FiniteVerb("future", "simple", 3, "singular")),
    ("ିବି", FiniteVerb("future", "simple", 1, "singular")),
    ("ିବେ", FiniteVerb("future", "simple", 3, "plural")),
    ("ିବା", NonfiniteVerb("infinitive")),
    ("ିଛି", FiniteVerb("present", "perfect", 3, "singular")),
    ("ିଥିଲେ", FiniteVerb("past", "perfect", 3, "plural")),
    ("ିଥାଏ", FiniteVerb("present", "habitual", 3, "singular")),
    ("ଥାଏ", FiniteVerb("present", "habitual", 3, "singular")),
    ("ନ୍ତି", FiniteVerb("present", "simple", 3, "plural")),
    ("େ", FiniteVerb("present", "simple", 3, "singular")),
    ("ି", NonfiniteVerb("conjunctive")),
)
_AA_ENDINGS: tuple[tuple[str, FiniteVerb | NonfiniteVerb], ...] = (
    ("ଇବା", NonfiniteVerb("infinitive")),
    ("ଇଲା", FiniteVerb("past", "simple", 3, "singular")),
    ("ଇଲେ", FiniteVerb("past", "simple", 3, "plural")),
    ("ଇଲି", FiniteVerb("past", "simple", 1, "singular")),
    ("ଉଛି", FiniteVerb("present", "progressive", 3, "singular")),
    ("ଉଥିଲେ", FiniteVerb("past", "progressive", 3, "plural")),
    ("ଉଥିଲା", FiniteVerb("past", "progressive", 3, "singular")),
    ("ଇବ", FiniteVerb("future", "simple", 3, "singular")),
    ("ଇବେ", FiniteVerb("future", "simple", 3, "plural")),
    ("ଇଛି", FiniteVerb("present", "perfect", 3, "singular")),
    ("ଏ", FiniteVerb("present", "simple", 3, "singular")),
    ("ଇ", NonfiniteVerb("conjunctive")),
)
_E_ENDINGS: tuple[tuple[str, FiniteVerb | NonfiniteVerb], ...] = (
    ("ବା", NonfiniteVerb("infinitive")),
    ("ବ", FiniteVerb("future", "simple", 3, "singular")),
    ("ବି", FiniteVerb("future", "simple", 1, "singular")),
    ("ବେ", FiniteVerb("future", "simple", 3, "plural")),
    ("ଉଛି", FiniteVerb("present", "progressive", 3, "singular")),
    ("ଉଥିଲେ", FiniteVerb("past", "progressive", 3, "plural")),
    ("ଉଥିଲା", FiniteVerb("past", "progressive", 3, "singular")),
    ("ଇ", NonfiniteVerb("conjunctive")),
)

_IRREGULAR: tuple[tuple[str, str, FiniteVerb | NonfiniteVerb], ...] = (
    ("କଲି", "କର", FiniteVerb("past", "simple", 1, "singular")),
    ("କଲୁ", "କର", FiniteVerb("past", "simple", 1, "plural")),
    ("କଲା", "କର", FiniteVerb("past", "simple", 3, "singular")),
    ("କଲେ", "କର", FiniteVerb("past", "simple", 3, "plural")),
    ("ଗଲି", "ଯା", FiniteVerb("past", "simple", 1, "singular")),
    ("ଗଲୁ", "ଯା", FiniteVerb("past", "simple", 1, "plural")),
    ("ଗଲା", "ଯା", FiniteVerb("past", "simple", 3, "singular")),
    ("ଗଲେ", "ଯା", FiniteVerb("past", "simple", 3, "plural")),
    ("ଦେଲା", "ଦେ", FiniteVerb("past", "simple", 3, "singular")),
    ("ଦେଲେ", "ଦେ", FiniteVerb("past", "simple", 3, "plural")),
    ("ନେଲା", "ନେ", FiniteVerb("past", "simple", 3, "singular")),
    ("ନେଲେ", "ନେ", FiniteVerb("past", "simple", 3, "plural")),
    ("ହେଲା", "ହେ", FiniteVerb("past", "simple", 3, "singular")),
    ("ହେଲେ", "ହେ", FiniteVerb("past", "simple", 3, "plural")),
    ("ଯିବା", "ଯା", NonfiniteVerb("infinitive")),
    ("ଥିବା", "ଥା", NonfiniteVerb("infinitive")),
    ("ଥିଲା", "ଥା", FiniteVerb("past", "simple", 3, "singular")),
    ("ଥିଲେ", "ଥା", FiniteVerb("past", "simple", 3, "plural")),
    ("ଅଛି", "ଥା", FiniteVerb("present", "progressive", 3, "singular")),
)

_UNKNOWN = ("ପବନ", "ଆକାଶ", "ସୂର୍ଯ୍ୟ", "ତାରା", "ମେଘ", "ହସ", "ନୀଳ", "ଧବଳ", "hello", "୧୨୩")
_ISSUE_TAILS = (
    "ଗୁଡ଼ିକ",
    "ମାନେ",
    "ର",
    "କୁ",
    "ଠାରୁ",
    "ରେ",
    "ଠାରେ",
    "ଦ୍ୱାରା",
    "ଥିଲେ",
    "ଥିଲା",
    "ଥାଏ",
    "ଉଛି",
    "ଇବ",
    "ିଲା",
    "ୁଥିଲେ",
)
_CITATIONS = ("Neukom", "Patnaik", "Mohapatra", "Jena", "Rautaray", "Sethi", "Chaupattnaik")


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def _consonant_final(text: str) -> bool:
    return text[-1] not in _MATRA


def _noun(
    form: str,
    number: Literal["singular", "plural"] = "singular",
    case: Literal["nominative", "genitive", "dative", "locative", "ablative", "instrumental"] = "nominative",
    definite: bool = False,
) -> Lemma:
    return Lemma(_nfc(form), "NOUN", NounFeatures(number, case, definite))


def _verb(root: str, features: FiniteVerb | NonfiniteVerb) -> Lemma:
    return Lemma(_nfc(_VERBS[root]), "VERB", features)


def _add_nominal(rows: list[tuple[str, str, Lemma]], stem_form: str, ending: str, item: Lemma) -> None:
    rows.append((_nfc(stem_form + ending), _nfc(stem_form), item))


def _common_noun_rows() -> list[tuple[str, str, Lemma]]:
    rows: list[tuple[str, str, Lemma]] = []
    for noun in _NOUNS:
        rows.append((_nfc(noun), _nfc(noun), _noun(noun)))
        for ending, case in _CASES:
            _add_nominal(rows, noun, ending, _noun(noun, case=case))
        for ending in _DEFINITE:
            _add_nominal(rows, noun, ending, _noun(noun, definite=True))
        for definite in ("ଟି", "ଟା"):
            for case_ending, case in _CASES[:3]:
                _add_nominal(rows, noun, definite + case_ending, _noun(noun, case=case, definite=True))
        for plural in _INANIMATE_PLURAL:
            _add_nominal(rows, noun, plural, _noun(noun, number="plural"))
            for case_ending in _STACK_CASES:
                stacked = {"ର": "genitive", "କୁ": "dative", "ରେ": "locative"}[case_ending]
                _add_nominal(rows, noun, plural + case_ending, _noun(noun, "plural", stacked))
        if _consonant_final(noun):
            _add_nominal(rows, noun, "େ", _noun(noun, case="locative"))
    return rows


def _human_noun_rows() -> list[tuple[str, str, Lemma]]:
    rows: list[tuple[str, str, Lemma]] = []
    for human in _HUMANS:
        rows.append((_nfc(human), _nfc(human), _noun(human)))
        for ending, case in _CASES:
            _add_nominal(rows, human, ending, _noun(human, case=case))
        for plural in _HUMAN_PLURAL:
            _add_nominal(rows, human, plural, _noun(human, number="plural"))
        for case_ending, case in (("ର", "genitive"), ("କୁ", "dative"), ("ରେ", "locative")):
            _add_nominal(rows, human, "ମାନଙ୍କ" + case_ending, _noun(human, "plural", case))
        _add_nominal(rows, human, "େ", _noun(human, number="plural"))
    return rows


def _noun_rows() -> list[tuple[str, str, Lemma]]:
    return _common_noun_rows() + _human_noun_rows()


def _verb_rows() -> list[tuple[str, str, Lemma]]:
    rows: list[tuple[str, str, Lemma]] = []
    groups = (
        (_CONSONANT_ROOTS, _CONSONANT_ENDINGS),
        (_AA_ROOTS, _AA_ENDINGS),
        (_E_ROOTS, _E_ENDINGS),
    )
    for roots, endings in groups:
        for root in roots:
            rows.append((_nfc(root), _nfc(root), _verb(root, NonfiniteVerb("infinitive"))))
            for ending, features in endings:
                rows.append((_nfc(root + ending), _nfc(root), _verb(root, features)))
    for surface, root, features in _IRREGULAR:
        rows.append((_nfc(surface), _nfc(root), _verb(root, features)))
    return rows


def _unknown_rows() -> list[tuple[str, str, Lemma]]:
    rows: list[tuple[str, str, Lemma]] = []
    for word in _UNKNOWN:
        text = _nfc(word)
        rows.append((text, text, Lemma(text, "UNKNOWN", UnknownFeatures())))
    return rows


def _gold() -> list[tuple[str, str, Lemma]]:
    return _noun_rows() + _verb_rows() + _unknown_rows()


def test_issue_examples() -> None:
    assert stem("ଘରଗୁଡ଼ିକର") == "ଘର"
    assert stem("ଆସୁଥିଲେ") == "ଆସ"
    got = lemma("ଆସୁଥିଲେ")
    assert got == Lemma("ଆସିବା", "VERB", FiniteVerb("past", "progressive", 3, "plural"))
    assert got.form == "ଆସିବା"
    assert got.pos == "VERB"
    assert isinstance(got.features, FiniteVerb)
    assert got.features.tense == "past"
    assert got.features.person == 3
    assert got.features.number == "plural"
    assert lemma("ଘରଗୁଡ଼ିକର") == _noun("ଘର", "plural", "genitive")


def test_orthographic_traps() -> None:
    assert stem("ଘର") == "ଘର"
    assert stem("ଘରେ") == "ଘର"
    assert stem("ଘରରେ") == "ଘର"
    assert lemma("ଘରେ").features == NounFeatures("singular", "locative", False)
    assert stem("କରେ") == "କର"
    assert lemma("କରେ") == Lemma("କରିବା", "VERB", FiniteVerb("present", "simple", 3, "singular"))
    assert stem("ସରକାର") == "ସରକାର"
    assert stem("ସରକାରର") == "ସରକାର"
    assert stem("ସରକାରେ") == "ସରକାର"
    assert stem("ମନ୍ଦିରେ") == "ମନ୍ଦିର"
    assert stem("ଲୋକେ") == "ଲୋକ"
    assert lemma("ଲୋକେ").features == NounFeatures("plural", "nominative", False)
    assert stem("କଲା") == "କର"
    assert stem("ଗଲା") == "ଯା"
    assert lemma("ଗଲା").form == "ଯିବା"
    assert lemma("ଯିବା") == Lemma("ଯିବା", "VERB", NonfiniteVerb("infinitive"))
    assert stem("କରିବା") == "କର"
    assert lemma("କରିବା").form == "କରିବା"
    assert stem("ଖାଇବା") == "ଖା"
    assert stem("ଦେବା") == "ଦେ"
    assert lemma("ଦେଇ") == Lemma("ଦେବା", "VERB", NonfiniteVerb("conjunctive"))


def test_case_on_an_irregular_infinitive_stays_a_verb() -> None:
    assert stem("ଯିବାକୁ") == "ଯା"
    assert stem(stem("ଯିବାକୁ")) == stem("ଯିବାକୁ")
    assert lemma("ଯିବାକୁ") == Lemma("ଯିବା", "VERB", NonfiniteVerb("infinitive"))
    assert stem("ଥିବାକୁ") == "ଥା"
    assert stem(stem("ଥିବାକୁ")) == "ଥା"
    assert lemma("ଥିବାକୁ") == Lemma("ଥିବା", "VERB", NonfiniteVerb("infinitive"))
    assert lemma("ଦେବାକୁ") == Lemma("ଦେବା", "VERB", NonfiniteVerb("infinitive"))


def test_verbal_tail_does_not_eat_a_listed_noun() -> None:
    assert stem("ଘରୁଛି") == "ଘରୁଛି"
    assert lemma("ଘରୁଛି") == Lemma("ଘରୁଛି", "UNKNOWN", UnknownFeatures())


def test_empty_and_type() -> None:
    assert stem("") == ""
    assert lemma("") == Lemma("", "UNKNOWN", UnknownFeatures())
    bad: object = None
    with pytest.raises(TypeError):
        stem(bad)
    with pytest.raises(ValueError):
        Lemma("ଘର", "NOUN", UnknownFeatures())


def test_eval_accuracy_and_idempotence() -> None:
    rows = _gold()
    assert len(rows) >= 500
    stem_hits = 0
    lemma_hits = 0
    known = 0
    for surface, expected_stem, expected_lemma in rows:
        got_stem = stem(surface)
        got_lemma = lemma(surface)
        stem_hits += got_stem == expected_stem
        lemma_hits += got_lemma == expected_lemma
        known += expected_lemma.pos != "UNKNOWN"
        assert got_stem == expected_stem
        assert got_lemma == expected_lemma
        assert stem(got_stem) == got_stem
        assert stem(got_lemma.form) == got_stem
    total = len(rows)
    assert stem_hits / total >= 0.85
    assert lemma_hits / total >= 0.60
    assert known / total >= 0.60


def test_every_tail_occurs_in_the_eval() -> None:
    surfaces = [surface for surface, _, _ in _gold()]
    for item in suffixes():
        for tail in item.tails:
            assert any(surface.endswith(tail) and len(surface) > len(tail) for surface in surfaces)


def test_suffix_inventory_is_documented() -> None:
    inventory = suffixes()
    tails = {tail for item in inventory for tail in item.tails}
    assert sum(len(item.tails) for item in inventory) >= 50
    for required in _ISSUE_TAILS:
        assert _nfc(required) in tails
    documented = morph.__doc__ or ""
    for name in _CITATIONS:
        assert name in documented
    for item in inventory:
        assert f"{item.citation} ({item.kind})" in documented
        assert item.kind in {"nominal", "verbal"}


def test_root_exports_morph_beside_phonetic() -> None:
    script = (
        "import json, sys\n"
        "import openodia\n"
        "loaded = 'openodia.morph' in sys.modules\n"
        "from openodia import morph\n"
        "heavy = ('faker', 'deep_translator', 'requests', 'bs4')\n"
        "print(json.dumps({\n"
        "    'version': openodia.__version__,\n"
        "    'all': openodia.__all__,\n"
        "    'loaded': loaded,\n"
        "    'same': openodia.morph is morph,\n"
        "    'stem': morph.stem('ଘରଗୁଡ଼ିକର'),\n"
        "    'heavy': sorted(name for name in heavy if name in sys.modules),\n"
        "}))\n"
    )
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, check=True)
    payload = json.loads(result.stdout.splitlines()[-1])
    assert payload["version"] == "0.1.14"
    assert "phonetic" in payload["all"]
    assert "morph" in payload["all"]
    assert payload["loaded"] is True
    assert payload["same"] is True
    assert payload["stem"] == "ଘର"
    assert payload["heavy"] == []


def test_agent_docs_name_stem_and_lemma() -> None:
    root = Path(__file__).resolve().parent.parent
    for relative in ("AGENTS.md", "docs/llms.txt", "skills/openodia/SKILL.md"):
        text = (root / relative).read_text(encoding="utf-8")
        assert "morph" in text
        assert "stem" in text
        assert "lemma" in text
