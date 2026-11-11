from __future__ import annotations

import json
import re
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

_DOUBLED_MATRA = re.compile("[ିୀୁୂେୈୋୌା]{2}")
_MORPH_NOTE = "`openodia.morph` needs a release newer than 0.1.14"
_ADVERTISED = (
    "README.md",
    "docs/index.md",
    "AGENTS.md",
    "docs/llms.txt",
    "skills/openodia/SKILL.md",
)
_PERF_S = FiniteVerb("past", "perfect", 3, "singular")
_PERF_P = FiniteVerb("past", "perfect", 3, "plural")
_PROG_S = FiniteVerb("past", "progressive", 3, "singular")
_PROG_P = FiniteVerb("past", "progressive", 3, "plural")
_PRES_PERF_P = FiniteVerb("present", "perfect", 3, "plural")
_PRES_PROG_S = FiniteVerb("present", "progressive", 3, "singular")
_PRES_PROG_P = FiniteVerb("present", "progressive", 3, "plural")
_SIMPLE_S = FiniteVerb("past", "simple", 3, "singular")
_SIMPLE_P = FiniteVerb("past", "simple", 3, "plural")
_FUT_S = FiniteVerb("future", "simple", 3, "singular")
_FUT_P = FiniteVerb("future", "simple", 3, "plural")
_PRES_S = FiniteVerb("present", "simple", 3, "singular")
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


def _noun(
    form: str,
    number: Literal["singular", "plural"] = "singular",
    case: Literal["nominative", "genitive", "dative", "locative", "ablative", "instrumental"] = "nominative",
    definite: bool = False,
) -> Lemma:
    return Lemma(_nfc(form), "NOUN", NounFeatures(number, case, definite))


def _verb(form: str, features: FiniteVerb | NonfiniteVerb) -> Lemma:
    return Lemma(_nfc(form), "VERB", features)


def _gold() -> list[tuple[str, str, Lemma]]:
    noun = _noun
    verb = _verb
    inf = NonfiniteVerb("infinitive")
    conj = NonfiniteVerb("conjunctive")
    rows: list[tuple[str, str, Lemma]] = [
        ("ଘର", "ଘର", noun("ଘର")),
        ("ଘରର", "ଘର", noun("ଘର", case="genitive")),
        ("ଘରକୁ", "ଘର", noun("ଘର", case="dative")),
        ("ଘରରେ", "ଘର", noun("ଘର", case="locative")),
        ("ଘରେ", "ଘର", noun("ଘର", case="locative")),
        ("ଘରଠାରୁ", "ଘର", noun("ଘର", case="ablative")),
        ("ଘରଠାରେ", "ଘର", noun("ଘର", case="locative")),
        ("ଘରରୁ", "ଘର", noun("ଘର", case="ablative")),
        ("ଘରଦ୍ୱାରା", "ଘର", noun("ଘର", case="instrumental")),
        ("ଘରଟି", "ଘର", noun("ଘର", definite=True)),
        ("ଘରଟା", "ଘର", noun("ଘର", definite=True)),
        ("ଘରଗୁଡ଼ିକ", "ଘର", noun("ଘର", number="plural")),
        ("ଘରଗୁଡ଼ିକର", "ଘର", noun("ଘର", number="plural", case="genitive")),
        ("ଘରଗୁଡ଼ିକୁ", "ଘର", noun("ଘର", number="plural", case="dative")),
        ("ଘରଗୁଡ଼ା", "ଘର", noun("ଘର", number="plural")),
        ("ସରକାର", "ସରକାର", noun("ସରକାର")),
        ("ସରକାରର", "ସରକାର", noun("ସରକାର", case="genitive")),
        ("ସରକାରେ", "ସରକାର", noun("ସରକାର", case="locative")),
        ("ମନ୍ଦିର", "ମନ୍ଦିର", noun("ମନ୍ଦିର")),
        ("ମନ୍ଦିରେ", "ମନ୍ଦିର", noun("ମନ୍ଦିର", case="locative")),
        ("ମନ୍ଦିରର", "ମନ୍ଦିର", noun("ମନ୍ଦିର", case="genitive")),
        ("ବହି", "ବହି", noun("ବହି")),
        ("ବହିଟି", "ବହି", noun("ବହି", definite=True)),
        ("ବହିରେ", "ବହି", noun("ବହି", case="locative")),
        ("ଫୁଲ", "ଫୁଲ", noun("ଫୁଲ")),
        ("ଫୁଲର", "ଫୁଲ", noun("ଫୁଲ", case="genitive")),
        ("ପୁରୀରେ", "ପୁରୀ", noun("ପୁରୀ", case="locative")),
        ("ଓଡ଼ିଶାର", "ଓଡ଼ିଶା", noun("ଓଡ଼ିଶା", case="genitive")),
        ("ଲୋକ", "ଲୋକ", noun("ଲୋକ")),
        ("ଲୋକର", "ଲୋକ", noun("ଲୋକ", case="genitive")),
        ("ଲୋକମାନେ", "ଲୋକ", noun("ଲୋକ", number="plural")),
        ("ଲୋକମାନଙ୍କ", "ଲୋକ", noun("ଲୋକ", number="plural")),
        ("ଲୋକମାନଙ୍କର", "ଲୋକ", noun("ଲୋକ", number="plural", case="genitive")),
        ("ଲୋକମାନଙ୍କୁ", "ଲୋକ", noun("ଲୋକ", number="plural", case="dative")),
        ("ଲୋକେ", "ଲୋକ", noun("ଲୋକ", number="plural")),
        ("ଲୋକଙ୍କୁ", "ଲୋକ", noun("ଲୋକ", number="plural", case="dative")),
        ("ପିଲା", "ପିଲା", noun("ପିଲା")),
        ("ପିଲାର", "ପିଲା", noun("ପିଲା", case="genitive")),
        ("ପିଲାମାନଙ୍କୁ", "ପିଲା", noun("ପିଲା", number="plural", case="dative")),
        ("ମୁଖ୍ୟମନ୍ତ୍ରୀଙ୍କୁ", "ମୁଖ୍ୟମନ୍ତ୍ରୀ", noun("ମୁଖ୍ୟମନ୍ତ୍ରୀ", number="plural", case="dative")),
        ("ଆସ", "ଆସ", verb("ଆସିବା", inf)),
        ("ଆସୁଥିଲେ", "ଆସ", verb("ଆସିବା", _PROG_P)),
        ("ଆସୁଥିଲା", "ଆସ", verb("ଆସିବା", _PROG_S)),
        ("ଆସୁଛି", "ଆସ", verb("ଆସିବା", _PRES_PROG_S)),
        ("ଆସିଲା", "ଆସ", verb("ଆସିବା", _SIMPLE_S)),
        ("ଆସିଲେ", "ଆସ", verb("ଆସିବା", _SIMPLE_P)),
        ("ଆସିବ", "ଆସ", verb("ଆସିବା", _FUT_S)),
        ("ଆସିବେ", "ଆସ", verb("ଆସିବା", _FUT_P)),
        ("ଆସିବା", "ଆସ", verb("ଆସିବା", inf)),
        ("ଆସେ", "ଆସ", verb("ଆସିବା", _PRES_S)),
        ("ଆସନ୍ତି", "ଆସ", verb("ଆସିବା", FiniteVerb("present", "simple", 3, "plural"))),
        ("ଆସି", "ଆସ", verb("ଆସିବା", conj)),
        ("କର", "କର", verb("କରିବା", inf)),
        ("କରେ", "କର", verb("କରିବା", _PRES_S)),
        ("କରିବା", "କର", verb("କରିବା", inf)),
        ("କରୁଛି", "କର", verb("କରିବା", _PRES_PROG_S)),
        ("କରିଥିଲା", "କର", verb("କରିବା", _PERF_S)),
        ("କରିଥିଲେ", "କର", verb("କରିବା", _PERF_P)),
        ("କରିଛନ୍ତି", "କର", verb("କରିବା", _PRES_PERF_P)),
        ("କଲା", "କର", verb("କରିବା", _SIMPLE_S)),
        ("କଲେ", "କର", verb("କରିବା", _SIMPLE_P)),
        ("ଦେ", "ଦେ", verb("ଦେବା", inf)),
        ("ଦେବା", "ଦେ", verb("ଦେବା", inf)),
        ("ଦେବ", "ଦେ", verb("ଦେବା", _FUT_S)),
        ("ଦେଉଛି", "ଦେ", verb("ଦେବା", _PRES_PROG_S)),
        ("ଦେଇଥିଲା", "ଦେ", verb("ଦେବା", _PERF_S)),
        ("ଦେଇଥିଲେ", "ଦେ", verb("ଦେବା", _PERF_P)),
        ("ଦେଇଛନ୍ତି", "ଦେ", verb("ଦେବା", _PRES_PERF_P)),
        ("ଦେଲା", "ଦେ", verb("ଦେବା", _SIMPLE_S)),
        ("ଦେଇ", "ଦେ", verb("ଦେବା", conj)),
        ("ନେବ", "ନେ", verb("ନେବା", _FUT_S)),
        ("ହେବେ", "ହେ", verb("ହେବା", _FUT_P)),
        ("ହେଲା", "ହେ", verb("ହେବା", _SIMPLE_S)),
        ("ଖାଇବା", "ଖା", verb("ଖାଇବା", inf)),
        ("ଖାଇଥିଲା", "ଖା", verb("ଖାଇବା", _PERF_S)),
        ("ଖାଇଥିଲେ", "ଖା", verb("ଖାଇବା", _PERF_P)),
        ("ଖାଇଛନ୍ତି", "ଖା", verb("ଖାଇବା", _PRES_PERF_P)),
        ("ଖାଉଛି", "ଖା", verb("ଖାଇବା", _PRES_PROG_S)),
        ("ଖାଏ", "ଖା", verb("ଖାଇବା", _PRES_S)),
        ("ଫେରୁଥିଲେ", "ଫେର", verb("ଫେରିବା", _PROG_P)),
        ("ଫେରୁଥିଲା", "ଫେର", verb("ଫେରିବା", _PROG_S)),
        ("ଫେରୁଛନ୍ତି", "ଫେର", verb("ଫେରିବା", _PRES_PROG_P)),
        ("ଫେରିବା", "ଫେର", verb("ଫେରିବା", inf)),
        ("ଯିବା", "ଯା", verb("ଯିବା", inf)),
        ("ଯିବାକୁ", "ଯା", verb("ଯିବା", inf)),
        ("ଗଲା", "ଯା", verb("ଯିବା", _SIMPLE_S)),
        ("ଥିବା", "ଥା", verb("ଥିବା", inf)),
        ("ଥିଲା", "ଥା", verb("ଥିବା", _SIMPLE_S)),
        ("ଅଛି", "ଥା", verb("ଥିବା", _PRES_PROG_S)),
        ("ଶୁଣିଲା", "ଶୁଣ", verb("ଶୁଣିବା", _SIMPLE_S)),
        ("ଦେଖୁଛି", "ଦେଖ", verb("ଦେଖିବା", _PRES_PROG_S)),
        ("ରହିବ", "ରହ", verb("ରହିବା", _FUT_S)),
        ("ପବନ", "ପବନ", Lemma("ପବନ", "UNKNOWN", UnknownFeatures())),
        ("ଆକାଶ", "ଆକାଶ", Lemma("ଆକାଶ", "UNKNOWN", UnknownFeatures())),
        ("hello", "hello", Lemma("hello", "UNKNOWN", UnknownFeatures())),
    ]
    return [(_nfc(surface), _nfc(expected), item) for surface, expected, item in rows]


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
    surfaces = [surface for surface, _, _ in rows]
    assert all("କକୁ" not in surface for surface in surfaces)
    assert any("ମାନଙ୍କୁ" in surface for surface in surfaces)
    assert any("ଗୁଡ଼ିକୁ" in surface for surface in surfaces)
    assert any(surface.endswith("ଙ୍କୁ") and "ମାନ" not in surface for surface in surfaces)
    stem_hits = 0
    lemma_hits = 0
    for surface, expected_stem, expected_lemma in rows:
        got_stem = stem(surface)
        got_lemma = lemma(surface)
        stem_hits += got_stem == expected_stem
        lemma_hits += got_lemma == expected_lemma
        assert got_stem == expected_stem
        assert got_lemma == expected_lemma
        assert stem(got_stem) == got_stem
        assert stem(got_lemma.form) == got_stem
        assert _DOUBLED_MATRA.search(got_lemma.form) is None
    total = len(rows)
    assert stem_hits / total >= 0.85
    assert lemma_hits / total >= 0.60


def test_perfect_verbs_stay_on_the_root() -> None:
    perfect = {
        "କରିଥିଲା": ("କର", "କରିବା", _PERF_S),
        "କରିଥିଲେ": ("କର", "କରିବା", _PERF_P),
        "କରିଛନ୍ତି": ("କର", "କରିବା", _PRES_PERF_P),
        "ଦେଇଥିଲା": ("ଦେ", "ଦେବା", _PERF_S),
        "ଦେଇଥିଲେ": ("ଦେ", "ଦେବା", _PERF_P),
        "ଦେଇଛନ୍ତି": ("ଦେ", "ଦେବା", _PRES_PERF_P),
        "ଖାଇଥିଲା": ("ଖା", "ଖାଇବା", _PERF_S),
        "ଖାଇଥିଲେ": ("ଖା", "ଖାଇବା", _PERF_P),
        "ଖାଇଛନ୍ତି": ("ଖା", "ଖାଇବା", _PRES_PERF_P),
    }
    progressive = {
        "ଫେରୁଥିଲା": ("ଫେର", "ଫେରିବା", _PROG_S),
        "ଫେରୁଥିଲେ": ("ଫେର", "ଫେରିବା", _PROG_P),
        "ଫେରୁଛନ୍ତି": ("ଫେର", "ଫେରିବା", _PRES_PROG_P),
    }
    for word, (root, form, features) in {**perfect, **progressive}.items():
        assert stem(word) == root
        assert stem(stem(word)) == root
        got = lemma(word)
        assert got.form == form
        assert got.features == features
        assert stem(got.form) == root
        assert _DOUBLED_MATRA.search(got.form) is None


def test_plural_dative_uses_the_real_endings() -> None:
    expected = {
        "ଲୋକମାନଙ୍କୁ": "ଲୋକ",
        "ପିଲାମାନଙ୍କୁ": "ପିଲା",
        "ଲୋକଙ୍କୁ": "ଲୋକ",
        "ମୁଖ୍ୟମନ୍ତ୍ରୀଙ୍କୁ": "ମୁଖ୍ୟମନ୍ତ୍ରୀ",
        "ଘରଗୁଡ଼ିକୁ": "ଘର",
    }
    for word, root in expected.items():
        got = lemma(word)
        assert stem(word) == root
        assert got.pos == "NOUN"
        assert got.features == NounFeatures("plural", "dative", False)


def test_precomposed_nukta_matches_the_plural_genitive() -> None:
    word = "ଘରଗୁ" + "\u0b5c" + "ିକର"
    assert "\u0b5c" in word
    assert stem(word) == "ଘର"


def test_virama_is_not_left_as_a_stem() -> None:
    blocked = "ଘର୍କୁ"
    assert "\u0b4d" in blocked
    assert "\u0bcd" not in blocked
    assert stem(blocked) == blocked
    assert stem("ଲୋକଙ୍କୁ") == "ଲୋକ"


def test_advertised_pages_name_the_morph_release() -> None:
    root = Path(__file__).resolve().parent.parent
    for relative in _ADVERTISED:
        text = (root / relative).read_text(encoding="utf-8")
        assert _MORPH_NOTE in text


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
