from __future__ import annotations

import unicodedata

import pytest

from openodia.morph import FiniteVerb, Lemma, NonfiniteVerb, NounFeatures, lemma, stem, suffixes

_CITATIONS = (
    "ଉଥିଲେ",
    "ଉଥିଲା",
    "ଉଥିଲି",
    "ଉଛି",
    "ଉଛୁ",
    "ଉଛନ୍ତି",
    "ଇଛି",
    "ଇଲା",
    "ଇଲେ",
    "ଇଲି",
    "ଇବ",
    "ଇବି",
    "ଇବେ",
    "ଥାଏ",
    "ଇଥିଲେ",
    "ଇଥିଲା",
    "ଇଥିଲି",
    "ଇଛନ୍ତି",
    "ନ୍ତି",
    "ଏ",
    "ଇବା",
    "ଇ",
)
_FEATURES = (
    FiniteVerb("past", "progressive", 3, "plural"),
    FiniteVerb("past", "progressive", 3, "singular"),
    FiniteVerb("past", "progressive", 1, "singular"),
    FiniteVerb("present", "progressive", 3, "singular"),
    FiniteVerb("present", "progressive", 1, "plural"),
    FiniteVerb("present", "progressive", 3, "plural"),
    FiniteVerb("present", "perfect", 3, "singular"),
    FiniteVerb("past", "simple", 3, "singular"),
    FiniteVerb("past", "simple", 3, "plural"),
    FiniteVerb("past", "simple", 1, "singular"),
    FiniteVerb("future", "simple", 3, "singular"),
    FiniteVerb("future", "simple", 1, "singular"),
    FiniteVerb("future", "simple", 3, "plural"),
    FiniteVerb("present", "habitual", 3, "singular"),
    FiniteVerb("past", "perfect", 3, "plural"),
    FiniteVerb("past", "perfect", 3, "singular"),
    FiniteVerb("past", "perfect", 1, "singular"),
    FiniteVerb("present", "perfect", 3, "plural"),
    FiniteVerb("present", "simple", 3, "plural"),
    FiniteVerb("present", "simple", 3, "singular"),
    NonfiniteVerb("infinitive"),
    NonfiniteVerb("conjunctive"),
)
_PARADIGMS = (
    ("ଆସ", "ଆସିବା", "ଆସୁଥିଲେ ଆସୁଥିଲା ଆସୁଥିଲି ଆସୁଛି ଆସୁଛୁ ଆସୁଛନ୍ତି ଆସିଛି ଆସିଲା ଆସିଲେ ଆସିଲି ଆସିବ ଆସିବି ଆସିବେ ଆସିଥାଏ ଆସିଥିଲେ ଆସିଥିଲା ଆସିଥିଲି ଆସିଛନ୍ତି ଆସନ୍ତି ଆସେ ଆସିବା ଆସି"),
    ("କର", "କରିବା", "କରୁଥିଲେ କରୁଥିଲା କରୁଥିଲି କରୁଛି କରୁଛୁ କରୁଛନ୍ତି କରିଛି କଲା କଲେ କଲି କରିବ କରିବି କରିବେ କରିଥାଏ କରିଥିଲେ କରିଥିଲା କରିଥିଲି କରିଛନ୍ତି କରନ୍ତି କରେ କରିବା କରି"),
    ("ବସ", "ବସିବା", "ବସୁଥିଲେ ବସୁଥିଲା ବସୁଥିଲି ବସୁଛି ବସୁଛୁ ବସୁଛନ୍ତି ବସିଛି ବସିଲା ବସିଲେ ବସିଲି ବସିବ ବସିବି ବସିବେ ବସିଥାଏ ବସିଥିଲେ ବସିଥିଲା ବସିଥିଲି ବସିଛନ୍ତି ବସନ୍ତି ବସେ ବସିବା ବସି"),
    ("ଶୁଣ", "ଶୁଣିବା", "ଶୁଣୁଥିଲେ ଶୁଣୁଥିଲା ଶୁଣୁଥିଲି ଶୁଣୁଛି ଶୁଣୁଛୁ ଶୁଣୁଛନ୍ତି ଶୁଣିଛି ଶୁଣିଲା ଶୁଣିଲେ ଶୁଣିଲି ଶୁଣିବ ଶୁଣିବି ଶୁଣିବେ ଶୁଣିଥାଏ ଶୁଣିଥିଲେ ଶୁଣିଥିଲା ଶୁଣିଥିଲି ଶୁଣିଛନ୍ତି ଶୁଣନ୍ତି ଶୁଣେ ଶୁଣିବା ଶୁଣି"),
    (
        "ଦେଖ",
        "ଦେଖିବା",
        "ଦେଖୁଥିଲେ ଦେଖୁଥିଲା ଦେଖୁଥିଲି ଦେଖୁଛି ଦେଖୁଛୁ ଦେଖୁଛନ୍ତି ଦେଖିଛି ଦେଖିଲା ଦେଖିଲେ ଦେଖିଲି ଦେଖିବ ଦେଖିବି ଦେଖିବେ ଦେଖିଥାଏ ଦେଖିଥିଲେ ଦେଖିଥିଲା ଦେଖିଥିଲି ଦେଖିଛନ୍ତି ଦେଖନ୍ତି ଦେଖେ ଦେଖିବା ଦେଖି",
    ),
    ("ରହ", "ରହିବା", "ରହୁଥିଲେ ରହୁଥିଲା ରହୁଥିଲି ରହୁଛି ରହୁଛୁ ରହୁଛନ୍ତି ରହିଛି ରହିଲା ରହିଲେ ରହିଲି ରହିବ ରହିବି ରହିବେ ରହିଥାଏ ରହିଥିଲେ ରହିଥିଲା ରହିଥିଲି ରହିଛନ୍ତି ରହନ୍ତି ରହେ ରହିବା ରହି"),
    ("କହ", "କହିବା", "କହୁଥିଲେ କହୁଥିଲା କହୁଥିଲି କହୁଛି କହୁଛୁ କହୁଛନ୍ତି କହିଛି କହିଲା କହିଲେ କହିଲି କହିବ କହିବି କହିବେ କହିଥାଏ କହିଥିଲେ କହିଥିଲା କହିଥିଲି କହିଛନ୍ତି କହନ୍ତି କହେ କହିବା କହି"),
    ("ଚାହ", "ଚାହିଁବା", "ଚାହୁଁଥିଲେ ଚାହୁଁଥିଲା ଚାହୁଁଥିଲି ଚାହୁଁଛି ଚାହୁଁଛୁ ଚାହୁଁଛନ୍ତି ଚାହିଁଛି ଚାହିଁଲା ଚାହିଁଲେ ଚାହିଁଲି ଚାହିଁବ ଚାହିଁବି ଚାହିଁବେ ଚାହିଁଥାଏ ଚାହିଁଥିଲେ ଚାହିଁଥିଲା ଚାହିଁଥିଲି ଚାହିଁଛନ୍ତି ଚାହାନ୍ତି ଚାହେଁ ଚାହିଁବା ଚାହିଁ"),
    ("ପଢ଼", "ପଢ଼ିବା", "ପଢ଼ୁଥିଲେ ପଢ଼ୁଥିଲା ପଢ଼ୁଥିଲି ପଢ଼ୁଛି ପଢ଼ୁଛୁ ପଢ଼ୁଛନ୍ତି ପଢ଼ିଛି ପଢ଼ିଲା ପଢ଼ିଲେ ପଢ଼ିଲି ପଢ଼ିବ ପଢ଼ିବି ପଢ଼ିବେ ପଢ଼ିଥାଏ ପଢ଼ିଥିଲେ ପଢ଼ିଥିଲା ପଢ଼ିଥିଲି ପଢ଼ିଛନ୍ତି ପଢ଼ନ୍ତି ପଢ଼େ ପଢ଼ିବା ପଢ଼ି"),
    ("ଜଳ", "ଜଳିବା", "ଜଳୁଥିଲେ ଜଳୁଥିଲା ଜଳୁଥିଲି ଜଳୁଛି ଜଳୁଛୁ ଜଳୁଛନ୍ତି ଜଳିଛି ଜଳିଲା ଜଳିଲେ ଜଳିଲି ଜଳିବ ଜଳିବି ଜଳିବେ ଜଳିଥାଏ ଜଳିଥିଲେ ଜଳିଥିଲା ଜଳିଥିଲି ଜଳିଛନ୍ତି ଜଳନ୍ତି - ଜଳିବା ଜଳି"),
    ("ଖା", "ଖାଇବା", "ଖାଉଥିଲେ ଖାଉଥିଲା ଖାଉଥିଲି ଖାଉଛି ଖାଉଛୁ ଖାଉଛନ୍ତି ଖାଇଛି ଖାଇଲା ଖାଇଲେ ଖାଇଲି ଖାଇବ ଖାଇବି ଖାଇବେ ଖାଇଥାଏ ଖାଇଥିଲେ ଖାଇଥିଲା ଖାଇଥିଲି ଖାଇଛନ୍ତି ଖାଆନ୍ତି ଖାଏ ଖାଇବା ଖାଇ"),
    ("ପା", "ପାଇବା", "ପାଉଥିଲେ ପାଉଥିଲା ପାଉଥିଲି ପାଉଛି ପାଉଛୁ ପାଉଛନ୍ତି ପାଇଛି ପାଇଲା ପାଇଲେ ପାଇଲି ପାଇବ ପାଇବି ପାଇବେ ପାଇଥାଏ ପାଇଥିଲେ ପାଇଥିଲା ପାଇଥିଲି ପାଇଛନ୍ତି ପାଆନ୍ତି ପାଏ ପାଇବା ପାଇ"),
    ("ଗା", "ଗାଇବା", "ଗାଉଥିଲେ ଗାଉଥିଲା ଗାଉଥିଲି ଗାଉଛି ଗାଉଛୁ ଗାଉଛନ୍ତି ଗାଇଛି ଗାଇଲା ଗାଇଲେ ଗାଇଲି ଗାଇବ ଗାଇବି ଗାଇବେ ଗାଇଥାଏ ଗାଇଥିଲେ ଗାଇଥିଲା ଗାଇଥିଲି ଗାଇଛନ୍ତି ଗାଆନ୍ତି ଗାଏ ଗାଇବା ଗାଇ"),
    ("ଯା", "ଯିବା", "ଯାଉଥିଲେ ଯାଉଥିଲା ଯାଉଥିଲି ଯାଉଛି ଯାଉଛୁ ଯାଉଛନ୍ତି ଯାଇଛି ଗଲା ଗଲେ ଗଲି ଯିବ ଯିବି ଯିବେ ଯାଇଥାଏ ଯାଇଥିଲେ ଯାଇଥିଲା ଯାଇଥିଲି ଯାଇଛନ୍ତି ଯାଆନ୍ତି ଯାଏ ଯିବା ଯାଇ"),
    (
        "ଦେ",
        "ଦେବା",
        "ଦେଉଥିଲେ ଦେଉଥିଲା ଦେଉଥିଲି ଦେଉଛି ଦେଉଛୁ ଦେଉଛନ୍ତି ଦେଇଛି ଦେଲା ଦେଲେ ଦେଲି ଦେବ ଦେବି ଦେବେ ଦେଇଥାଏ ଦେଇଥିଲେ ଦେଇଥିଲା ଦେଇଥିଲି ଦେଇଛନ୍ତି ଦିଅନ୍ତି ଦିଏ ଦେବା ଦେଇ",
    ),
    (
        "ନେ",
        "ନେବା",
        "ନେଉଥିଲେ ନେଉଥିଲା ନେଉଥିଲି ନେଉଛି ନେଉଛୁ ନେଉଛନ୍ତି ନେଇଛି ନେଲା ନେଲେ ନେଲି ନେବ ନେବି ନେବେ ନେଇଥାଏ ନେଇଥିଲେ ନେଇଥିଲା ନେଇଥିଲି ନେଇଛନ୍ତି ନିଅନ୍ତି ନିଏ ନେବା ନେଇ",
    ),
    (
        "ହେ",
        "ହେବା",
        "ହେଉଥିଲେ ହେଉଥିଲା ହେଉଥିଲି ହେଉଛି ହେଉଛୁ ହେଉଛନ୍ତି ହୋଇଛି ହେଲା ହେଲେ ହେଲି ହେବ ହେବି ହେବେ ହୋଇଥାଏ ହୋଇଥିଲେ ହୋଇଥିଲା ହୋଇଥିଲି ହୋଇଛନ୍ତି ହୁଅନ୍ତି ହୁଏ ହେବା ହୋଇ",
    ),
    ("ଥା", "ଥିବା", "ଥାଉଥିଲେ ଥାଉଥିଲା ଥାଉଥିଲି ଥାଉଛି ଥାଉଛୁ ଥାଉଛନ୍ତି - ଥିଲା ଥିଲେ ଥିଲି ଥିବ ଥିବି ଥିବେ - - - - - ଥାଆନ୍ତି ଥାଏ ଥିବା ଥାଇ"),
)
_CELLS = [
    (root, infinitive, citation, features, surface)
    for root, infinitive, row in _PARADIGMS
    for citation, features, surface in zip(_CITATIONS, _FEATURES, row.split(), strict=True)
    if surface != "-"
]
_LISTED_ROOTS = "ଆସ କର ବସ ଶୁଣ ଦେଖ ରହ କହ ଚାହ ପଢ଼ ଖା ପା ଗା ଯା ଥା ଦେ ନେ ହେ ଜଳ".split()


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


def test_every_listed_root_has_a_cell_for_every_verbal_citation() -> None:
    verbal = {item.citation for item in suffixes() if item.kind == "verbal"}
    assert set(_CITATIONS) == verbal
    assert len(_CITATIONS) == len(_FEATURES) == len(verbal)
    assert sorted(root for root, _, _ in _PARADIGMS) == sorted(_LISTED_ROOTS)
    for _, _, row in _PARADIGMS:
        assert len(row.split()) == len(_CITATIONS)
    assert len(_CELLS) == 389


@pytest.mark.parametrize(("root", "infinitive", "citation", "features", "surface"), _CELLS)
def test_paradigm_cell_stems_to_its_root_and_lemma(
    root: str, infinitive: str, citation: str, features: FiniteVerb | NonfiniteVerb, surface: str
) -> None:
    assert stem(surface) == _nfc(root)
    assert lemma(surface) == Lemma(_nfc(infinitive), "VERB", features)
    assert stem(stem(surface)) == _nfc(root)
    nfd = unicodedata.normalize("NFD", surface)
    assert (stem(nfd), lemma(nfd)) == (stem(surface), lemma(surface))


def test_no_chah_form_stems_inside_its_ending() -> None:
    chah = [surface for root, _, _, _, surface in _CELLS if root == "ଚାହ"]
    assert len(chah) == len(_CITATIONS)
    for surface in chah:
        assert stem(surface) == _nfc("ଚାହ")
        assert not stem(surface).endswith(("ଛ", "ଁ"))


def test_jala_e_keeps_the_listed_noun_locative_reading() -> None:
    assert lemma("ଜଳେ") == Lemma("ଜଳ", "NOUN", NounFeatures("singular", "locative", False))


def test_a_candrabindu_after_a_non_vowel_sign_is_not_part_of_the_nasal_stem() -> None:
    assert lemma("ଚାହଇଁବ").pos == "UNKNOWN"
    assert lemma("ଚାହଇବ") == Lemma(_nfc("ଚାହିଁବା"), "VERB", FiniteVerb("future", "simple", 3, "singular"))
