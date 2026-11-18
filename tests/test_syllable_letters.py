from __future__ import annotations

import unicodedata

import pytest

from openodia import syllable

_ODIA_LETTERS = [
    chr(code)
    for code in range(0x0B00, 0x0B80)
    if unicodedata.name(chr(code), "").startswith("ORIYA LETTER ") and unicodedata.normalize("NFC", chr(code)) == chr(code)
]


@pytest.mark.parametrize("letter", _ODIA_LETTERS, ids=lambda letter: unicodedata.name(letter))
def test_every_odia_letter_is_one_akshara(letter: str) -> None:
    assert syllable.split(letter) == [letter]
    assert syllable.count(letter) == 1


_CONSONANT_LETTERS = [letter for letter in _ODIA_LETTERS if letter not in "ଅଆଇଈଉଊଋଌଏଐଓଔୠୡ"]


@pytest.mark.parametrize("letter", _CONSONANT_LETTERS, ids=lambda letter: unicodedata.name(letter))
def test_every_odia_consonant_takes_a_vowel_sign_and_a_conjunct(letter: str) -> None:
    assert syllable.split(letter + "େ" + "ବ") == [letter + "େ", "ବ"]
    assert syllable.split("ସ୍" + letter + "ର") == ["ସ୍" + letter, "ର"]


@pytest.mark.parametrize(
    ("word", "aksharas"),
    (("ୱେବ", ["ୱେ", "ବ"]), ("ୱେଲ୍ସ", ["ୱେ", "ଲ୍ସ"]), ("କୁୱ", ["କୁ", "ୱ"]), ("ସ୍ୱର", ["ସ୍ୱ", "ର"])),
)
def test_wa_is_a_consonant(word: str, aksharas: list[str]) -> None:
    assert syllable.split(word) == aksharas
    assert syllable.count(word) == len(aksharas)
