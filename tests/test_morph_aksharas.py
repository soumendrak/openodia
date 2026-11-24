from __future__ import annotations

import unicodedata

import pytest

from openodia.morph import Lemma, NounFeatures, UnknownFeatures, lemma, stem
from openodia.morph import _engine

_ONE_AKSHARA_CONJUNCTS = ("ସ୍ତ", "ସ୍ଥି", "କ୍ଷେ", "ପ୍ରୀ", "ସ୍ୱ", "ତ୍ରୁ", "ଦ୍ୱି", "ଷ୍ଟ", "ୱେ")
_TWO_AKSHARA_STEMS = ("ସ୍କୁଲ", "କ୍ଷେତ", "ପ୍ରକାଶ", "ବସ୍ତ୍ର", "ସ୍ତମ୍ଭ", "ୱେବ", "ୱେଲ୍ସ")
_COUNTED_RULES = [tail for tail in _engine._TAILS if isinstance(tail, _engine._Nominal) and tail.min_aksharas > 1]


def _nfc(text: str) -> str:
    return unicodedata.normalize("NFC", text)


@pytest.mark.parametrize("word", ("ସ୍ତର", "ସ୍ଥିର", "ଫେର"))
def test_a_one_akshara_remainder_keeps_its_final_ra(word: str) -> None:
    assert stem(word) == word
    assert lemma(word) == Lemma(word, "UNKNOWN", UnknownFeatures())


def test_the_akshara_counted_rules_are_the_ones_this_file_covers() -> None:
    assert [(tail.text, tail.case, tail.min_aksharas) for tail in _COUNTED_RULES] == [(_nfc("ର"), "genitive", 2)]


@pytest.mark.parametrize("tail", _COUNTED_RULES, ids=lambda tail: tail.text)
@pytest.mark.parametrize("base", _ONE_AKSHARA_CONJUNCTS)
def test_a_conjunct_initial_one_akshara_remainder_is_not_peeled(tail: _engine._Nominal, base: str) -> None:
    word = _nfc(base + tail.text)
    assert stem(word) == word
    assert lemma(word).pos == "UNKNOWN"


@pytest.mark.parametrize("tail", _COUNTED_RULES, ids=lambda tail: tail.text)
@pytest.mark.parametrize("base", _TWO_AKSHARA_STEMS)
def test_a_two_akshara_remainder_is_still_peeled(tail: _engine._Nominal, base: str) -> None:
    word = _nfc(base + tail.text)
    assert stem(word) == _nfc(base)
    assert lemma(word) == Lemma(_nfc(base), "NOUN", NounFeatures("singular", tail.case or "nominative", False))
