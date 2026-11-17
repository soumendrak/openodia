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
_MORPH_NOTE = "`openodia.morph` needs a release newer than 0.2.0: `from openodia import morph` fails on 0.2.0."
_ADVERTISED = (
    "README.md",
    "docs/index.md",
    "AGENTS.md",
    "docs/llms.txt",
    "skills/openodia/SKILL.md",
    "CHANGELOG.md",
)
_PERF_S = FiniteVerb("past", "perfect", 3, "singular")
_PERF_P = FiniteVerb("past", "perfect", 3, "plural")
_PROG_S = FiniteVerb("past", "progressive", 3, "singular")
_PROG_P = FiniteVerb("past", "progressive", 3, "plural")
_PRES_PERF_P = FiniteVerb("present", "perfect", 3, "plural")
_PRES_PROG_S = FiniteVerb("present", "progressive", 3, "singular")
_PRES_PROG_P = FiniteVerb("present", "progressive", 3, "plural")
_PRES_PROG_1P = FiniteVerb("present", "progressive", 1, "plural")
_PAST_PROG_1S = FiniteVerb("past", "progressive", 1, "singular")
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


def test_irregular_future_forms_of_ya_and_tha_resolve_to_the_listed_roots() -> None:
    cases = (
        ("ଯିବ", "ଯା", "ଯିବା", _FUT_S),
        ("ଯିବି", "ଯା", "ଯିବା", _FUT_1S),
        ("ଯିବେ", "ଯା", "ଯିବା", _FUT_P),
        ("ଥିବ", "ଥା", "ଥିବା", _FUT_S),
        ("ଥିବି", "ଥା", "ଥିବା", _FUT_1S),
        ("ଥିବେ", "ଥା", "ଥିବା", _FUT_P),
    )
    for word, root, form, features in cases:
        assert stem(word) == root, word
        assert lemma(word) == _verb(form, features), word
        assert stem(stem(word)) == root, word


def test_nasalized_present_progressive_endings_keep_the_listed_root() -> None:
    assert stem("ଚାହୁଁଛି") == "ଚାହ"
    assert lemma("ଚାହୁଁଛି") == _verb("ଚାହିଁବା", _PRES_PROG_S)
    assert stem("ଚାହୁଁଛନ୍ତି") == "ଚାହ"
    assert lemma("ଚାହୁଁଛନ୍ତି") == _verb("ଚାହିଁବା", _PRES_PROG_P)
    assert stem(stem("ଚାହୁଁଛି")) == "ଚାହ"
    assert stem(stem("ଚାହୁଁଛନ୍ତି")) == "ଚାହ"


def test_genitive_peels_after_a_definite_or_plural_aa_suffix() -> None:
    assert stem("ଘରଟାର") == "ଘର"
    assert lemma("ଘରଟାର") == _noun("ଘର", definite=True, case="genitive")
    assert stem("ଘରଗୁଡ଼ାର") == "ଘର"
    assert lemma("ଘରଗୁଡ଼ାର") == _noun("ଘର", number="plural", case="genitive")
    assert stem("ବିଚାର") == "ବିଚାର"
    assert stem(stem("ଘରଟାର")) == "ଘର"


def test_a_noun_listed_root_still_takes_verbal_endings() -> None:
    assert stem("ଜଳ") == "ଜଳ"
    assert lemma("ଜଳ") == _noun("ଜଳ")
    assert stem("ଜଳିବା") == "ଜଳ"
    assert lemma("ଜଳିବା") == _verb("ଜଳିବା", _INF)
    assert stem("ଜଳୁଛି") == "ଜଳ"
    assert lemma("ଜଳୁଛି") == _verb("ଜଳିବା", _PRES_PROG_S)
    assert stem("ଜଳିଲା") == "ଜଳ"
    assert lemma("ଜଳିଲା") == _verb("ଜଳିବା", _SIMPLE_S)
    assert stem(stem("ଜଳିବା")) == "ଜଳ"


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


def test_unlisted_verbal_roots_keep_a_final_ra() -> None:
    cases = {
        "ବିଚାରିବା": ("ବିଚାର", "ବିଚାରିବା"),
        "ସ୍ୱୀକାରିବା": ("ସ୍ୱୀକାର", "ସ୍ୱୀକାରିବା"),
    }
    for word, (root, form) in cases.items():
        assert stem(word) == root
        assert stem(root) == root
        assert stem(stem(word)) == root
        got = lemma(word)
        assert got == Lemma(form, "VERB", NonfiniteVerb("infinitive"))
        assert stem(got.form) == root


def test_vowel_final_roots_use_independent_progressive_endings() -> None:
    cases = {
        "ଖାଉଛନ୍ତି": ("ଖା", "ଖାଇବା", _PRES_PROG_P),
        "ଦେଉଛନ୍ତି": ("ଦେ", "ଦେବା", _PRES_PROG_P),
        "ଖାଉଥିଲି": ("ଖା", "ଖାଇବା", _PAST_PROG_1S),
        "ଖାଉଛୁ": ("ଖା", "ଖାଇବା", _PRES_PROG_1P),
        "ଦେଉଛୁ": ("ଦେ", "ଦେବା", _PRES_PROG_1P),
    }
    for word, (root, form, features) in cases.items():
        assert stem(word) == root
        assert stem(stem(word)) == root
        got = lemma(word)
        assert got == Lemma(form, "VERB", features)
        assert stem(got.form) == root


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
    assert payload["version"] == "0.2.0"
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


_FUT_1S = FiniteVerb("future", "simple", 1, "singular")
_INF = NonfiniteVerb("infinitive")
_PAST_1S = FiniteVerb("past", "simple", 1, "singular")
_PAST_1P = FiniteVerb("past", "simple", 1, "plural")
_HAB_S = FiniteVerb("present", "habitual", 3, "singular")
_PERF_1S = FiniteVerb("past", "perfect", 1, "singular")
_REJECT_REGRESSIONS: tuple[tuple[str, str, Lemma], ...] = (
    ("ଚାହିଁଥିଲା", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _PERF_S)),
    ("ଚାହିଁଥିଲେ", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _PERF_P)),
    ("ଚାହୁଁଥିଲା", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _PROG_S)),
    ("ଚାହୁଁଥିଲେ", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _PROG_P)),
    ("ଚାହିଁବା", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _INF)),
    ("ଗାଥିଲେ", "ଗା", Lemma("ଗାଇବା", "VERB", _PERF_P)),
    ("ପିଇବା", "ପି", Lemma("ପିଇବା", "VERB", _INF)),
    ("ପିଇଥିଲା", "ପି", Lemma("ପିଇବା", "VERB", _PERF_S)),
    ("ପିଉଥିଲା", "ପି", Lemma("ପିଇବା", "VERB", _PROG_S)),
    ("ଶୁଇବା", "ଶୁ", Lemma("ଶୁଇବା", "VERB", _INF)),
    ("ଶୋଇବା", "ଶୋ", Lemma("ଶୋଇବା", "VERB", _INF)),
    ("ଧୋଇବା", "ଧୋ", Lemma("ଧୋଇବା", "VERB", _INF)),
    ("ହୋଇଥିଲା", "ହେ", Lemma("ହେବା", "VERB", _PERF_S)),
    ("ହୋଇଥିଲେ", "ହେ", Lemma("ହେବା", "VERB", _PERF_P)),
    ("ହୋଇବା", "ହୋ", Lemma("ହୋଇବା", "VERB", _INF)),
    ("ଦେଇଥିଲା", "ଦେ", Lemma("ଦେବା", "VERB", _PERF_S)),
    ("ଦେବା", "ଦେ", Lemma("ଦେବା", "VERB", _INF)),
    ("ଖାଇବି", "ଖା", Lemma("ଖାଇବା", "VERB", _FUT_1S)),
    ("ପାଇବି", "ପା", Lemma("ପାଇବା", "VERB", _FUT_1S)),
    ("ଗାଇବି", "ଗା", Lemma("ଗାଇବା", "VERB", _FUT_1S)),
    ("ଆସିବି", "ଆସ", Lemma("ଆସିବା", "VERB", _FUT_1S)),
    ("ଗାଁର", "ଗାଁ", Lemma("ଗାଁ", "NOUN", NounFeatures("singular", "genitive", False))),
    ("ଗାଁକୁ", "ଗାଁ", Lemma("ଗାଁ", "NOUN", NounFeatures("singular", "dative", False))),
    ("ଫେର", "ଫେର", Lemma("ଫେର", "UNKNOWN", UnknownFeatures())),
    ("ବିଚାର", "ବିଚାର", Lemma("ବିଚାର", "UNKNOWN", UnknownFeatures())),
    ("କରିବାର", "କର", Lemma("କରିବା", "VERB", _INF)),
    ("ଖାଇବାର", "ଖା", Lemma("ଖାଇବା", "VERB", _INF)),
    ("ଯିବାର", "ଯା", Lemma("ଯିବା", "VERB", _INF)),
    ("ଦେବାର", "ଦେ", Lemma("ଦେବା", "VERB", _INF)),
    ("ଚାହିଁବାର", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _INF)),
    ("ଦେଲି", "ଦେ", Lemma("ଦେବା", "VERB", _PAST_1S)),
    ("ଦେଲୁ", "ଦେ", Lemma("ଦେବା", "VERB", _PAST_1P)),
    ("ନେଲି", "ନେ", Lemma("ନେବା", "VERB", _PAST_1S)),
    ("ନେଲୁ", "ନେ", Lemma("ନେବା", "VERB", _PAST_1P)),
    ("ହେଲି", "ହେ", Lemma("ହେବା", "VERB", _PAST_1S)),
    ("ହେଲୁ", "ହେ", Lemma("ହେବା", "VERB", _PAST_1P)),
    ("ଥିଲି", "ଥା", Lemma("ଥିବା", "VERB", _PAST_1S)),
    ("ଥିଲୁ", "ଥା", Lemma("ଥିବା", "VERB", _PAST_1P)),
    ("କଲାର", "କଲାର", Lemma("କଲାର", "UNKNOWN", UnknownFeatures())),
    ("ମହିଲାର", "ମହିଲାର", Lemma("ମହିଲାର", "UNKNOWN", UnknownFeatures())),
    ("ଦେଇଥାଏ", "ଦେ", Lemma("ଦେବା", "VERB", _HAB_S)),
    ("ଖାଇଥାଏ", "ଖା", Lemma("ଖାଇବା", "VERB", _HAB_S)),
    ("ପାଇଥାଏ", "ପା", Lemma("ପାଇବା", "VERB", _HAB_S)),
    ("କରିଥିଲି", "କର", Lemma("କରିବା", "VERB", _PERF_1S)),
    ("ଖାଇଥିଲି", "ଖା", Lemma("ଖାଇବା", "VERB", _PERF_1S)),
    ("ଚାହିଁଥିଲି", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _PERF_1S)),
    ("ଗାଥିଲି", "ଗା", Lemma("ଗାଇବା", "VERB", _PERF_1S)),
    ("ବାଡ଼େଇବା", "ବାଡ଼େ", Lemma("ବାଡ଼େଇବା", "VERB", _INF)),
    ("ଗାଧେଇବା", "ଗାଧେ", Lemma("ଗାଧେଇବା", "VERB", _INF)),
    ("ଚାହୁଁଥିଲି", "ଚାହ", Lemma("ଚାହିଁବା", "VERB", _PAST_PROG_1S)),
    ("କରିନଥିଲେ", "କର", Lemma("କରିବା", "VERB", _PERF_P)),
    ("ହୋଇନଥିଲା", "ହେ", Lemma("ହେବା", "VERB", _PERF_S)),
    ("ଖାଇନଥିଲା", "ଖା", Lemma("ଖାଇବା", "VERB", _PERF_S)),
    ("କରିନଥିଲି", "କର", Lemma("କରିବା", "VERB", _PERF_1S)),
    ("କରିନଥିଲା", "କର", Lemma("କରିବା", "VERB", _PERF_S)),
    ("ଖାଇନଥିଲେ", "ଖା", Lemma("ଖାଇବା", "VERB", _PERF_P)),
    ("ଖାଇନଥିଲି", "ଖା", Lemma("ଖାଇବା", "VERB", _PERF_1S)),
    ("ହୋଇ", "ହେ", Lemma("ହେବା", "VERB", NonfiniteVerb("conjunctive"))),
)


@pytest.mark.parametrize(("word", "root", "expected"), _REJECT_REGRESSIONS)
def test_reject_regression_table(word: str, root: str, expected: Lemma) -> None:
    got = lemma(word)
    assert (stem(word), got) == (_nfc(root), Lemma(_nfc(expected.form), expected.pos, expected.features))
    assert stem(stem(word)) == stem(word)
    assert stem(got.form) == stem(word)
    assert _DOUBLED_MATRA.search(got.form) is None
    if got.pos == "VERB" and got.features == _INF:
        assert _nfc(word) in (got.form, got.form + _nfc("ର"))
        assert lemma(got.form) == got


@pytest.mark.parametrize("word", ("ଚାହିଁଥିଲା", "ଚାହିଁଥିଲେ", "ଚାହୁଁଥିଲା", "କରିନଥିଲେ", "ଗାଥିଲେ", "ହୋଇନଥିଲା"))
def test_no_stem_is_cut_inside_thi(word: str) -> None:
    assert not stem(word).endswith("ଥ")


def test_reject_regression_table_is_pinned_and_documented() -> None:
    words = [word for word, _, _ in _REJECT_REGRESSIONS]
    assert len(words) == len(set(words)) == 58
    for required in ("ଚାହିଁଥିଲା", "ପିଇବା", "ଶୁଇବା", "ଧୋଇବା", "ହୋଇଥିଲା", "ଖାଇବି", "ପାଇବି", "ଗାଇବି", "ଗାଁର"):
        assert required in words
    tails = {tail for item in suffixes() for tail in item.tails}
    assert {_nfc("ଇବି"), _nfc("ିଁଥିଲା"), _nfc("ୁଁଥିଲା"), _nfc("ିଁଥିଲେ"), _nfc("ୁଁଥିଲେ")} <= tails
    documented = morph.__doc__ or ""
    assert "ଇବି (verbal): ିବି, ଇବି, ବି" in documented
    assert "ଗାଁର" in documented
