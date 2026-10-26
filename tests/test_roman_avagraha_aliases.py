import pytest

from openodia import roman
from openodia.roman._roman import Scheme


class TestAvagraha:
    @pytest.mark.parametrize(
        ("scheme", "expected"),
        [("ISO15919", "a\u2019"), ("Hunterian", "a'"), ("ITRANS", "a.a")],
    )
    def test_every_scheme_maps_the_avagraha(self, scheme: Scheme, expected: str) -> None:
        assert roman.to_roman("ଅଽ", scheme) == expected

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("word", ["ଽ", "କଽ", "ଅଽ", "ଆଽଆ", "ଽକ୍"])
    def test_round_trip(self, scheme: Scheme, word: str) -> None:
        assert roman.from_roman(roman.to_roman(word, scheme), scheme) == word

    def test_hunterian_decodes_apostrophe(self) -> None:
        assert roman.from_roman("ka'", "Hunterian") == "କଽ"


class TestHunterianRiLi:
    @pytest.mark.parametrize(
        ("spelling", "word"),
        [("oria", "ଓରିଅ"), ("ria", "ରିଅ"), ("oli", "ଓଲି"), ("kri", "କ୍ରି"), ("pali", "ପଲି")],
    )
    def test_prefers_consonant_and_vowel_sign(self, spelling: str, word: str) -> None:
        assert roman.from_roman(spelling, "Hunterian") == word


class TestItransAliases:
    @pytest.mark.parametrize(
        ("spelling", "word"),
        [
            ("kaa", "କା"),
            ("kii", "କୀ"),
            ("kuu", "କୂ"),
            ("aa", "ଆ"),
            ("ii", "ଈ"),
            ("uu", "ଊ"),
            ("kR^i", "କୃ"),
            ("kR^I", "କୄ"),
            ("R^i", "ଋ"),
            ("R^I", "ୠ"),
            ("kL^i", "କୢ"),
            ("L^I", "ୡ"),
            ("kRRi", "କୃ"),
        ],
    )
    def test_decoder_accepts_standard_aliases(self, spelling: str, word: str) -> None:
        assert roman.from_roman(spelling, "ITRANS") == word

    @pytest.mark.parametrize("word", ["ଅଅ", "କଅ", "ଇଇ", "ଉଉ", "କଇଇ", "ଅକଅଅ"])
    def test_encoder_keeps_doubled_vowels_apart(self, word: str) -> None:
        assert roman.from_roman(roman.to_roman(word, "ITRANS"), "ITRANS") == word

    def test_encoder_still_writes_canonical_spellings(self) -> None:
        assert roman.to_roman("କା", "ITRANS") == "kA"
        assert roman.to_roman("କୃ", "ITRANS") == "kRRi"
