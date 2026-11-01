import pytest

from openodia import roman
from openodia.roman._roman import Scheme


NUKTA = "\u0b3c"
NUKTA_CONSONANTS = "କଖଗଘଙଚଛଜଝଞଟଠଣତଥଦଧନପଫବଭମଯରଲଳଵଶଷସହ"


class TestNuktaConsonants:
    @pytest.mark.parametrize(
        ("scheme", "expected"),
        [("ISO15919", "khōj\u00b7a"), ("ITRANS", "khoj`a"), ("Hunterian", "khoja")],
    )
    def test_nukta_after_a_consonant_leaves_no_odia_script(self, scheme: Scheme, expected: str) -> None:
        assert roman.to_roman("ଖୋଜ" + NUKTA, scheme) == expected

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("consonant", list(NUKTA_CONSONANTS))
    @pytest.mark.parametrize("tail", ["", "ା", "ି", "୍କ", "୍", "ଅ", "ଂ"])
    def test_every_consonant_with_nukta_round_trips(self, scheme: Scheme, consonant: str, tail: str) -> None:
        text = consonant + NUKTA + tail
        romanised = roman.to_roman(text, scheme)
        assert NUKTA not in romanised
        assert roman.from_roman(romanised, scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", [NUKTA, "ଅ" + NUKTA, "କ" + NUKTA + NUKTA])
    def test_stray_nukta_round_trips(self, scheme: Scheme, text: str) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme), scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    def test_precomposed_dda_and_ddha_keep_their_spellings(self, scheme: Scheme) -> None:
        assert roman.to_roman("ଡ" + NUKTA, scheme) == roman.to_roman("\u0b5c", scheme)
        assert roman.to_roman("ଢ" + NUKTA, scheme) == roman.to_roman("\u0b5d", scheme)

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("run", ["\u00b7", "`", "k\u00b7"])
    def test_reversible_quotes_the_nukta_mark_written_by_the_user(self, scheme: Scheme, run: str) -> None:
        text = "କ" + run
        assert roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme) == text
