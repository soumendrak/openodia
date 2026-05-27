import pytest

from openodia import roman
from openodia.roman import SCHEMES


class TestSchemesConstant:
    def test_three_schemes_listed(self) -> None:
        assert set(SCHEMES) == {"ISO15919", "Hunterian", "ITRANS"}


class TestToRomanISO15919:
    def test_independent_vowel(self) -> None:
        assert roman.to_roman("ଆ", "ISO15919") == "ā"

    def test_consonant_with_inherent_schwa(self) -> None:
        # ନ → na (inherent schwa)
        assert roman.to_roman("ନ", "ISO15919") == "na"

    def test_consonant_with_matra(self) -> None:
        # ନା → nā (matra replaces schwa)
        assert roman.to_roman("ନା", "ISO15919") == "nā"

    def test_consonant_with_halant(self) -> None:
        # କ + halant → "k" (schwa suppressed)
        assert roman.to_roman("କ୍", "ISO15919") == "k"

    def test_conjunct(self) -> None:
        # ସ୍କ + ā → "skā"
        assert roman.to_roman("ସ୍କା", "ISO15919") == "skā"

    def test_modifier_attaches(self) -> None:
        # କଂ → "kaṁ"
        assert roman.to_roman("କଂ", "ISO15919") == "kaṁ"

    def test_basic_word(self) -> None:
        assert roman.to_roman("ନମସ୍କାର", "ISO15919") == "namaskāra"


class TestToRomanHunterian:
    def test_basic_word(self) -> None:
        # ନମସ୍କାର — Hunterian keeps schwa: 'namaskara'
        assert roman.to_roman("ନମସ୍କାର", "Hunterian") == "namaskara"

    def test_diacritic_free(self) -> None:
        out = roman.to_roman("ସୋମେନ୍ଦ୍ର", "Hunterian")
        # Must be ASCII (no diacritics).
        assert out.isascii()


class TestToRomanITRANS:
    def test_basic_word(self) -> None:
        # ITRANS is ASCII; uppercase distinguishes retroflex.
        out = roman.to_roman("ଓଡ଼ିଆ", "ITRANS")
        assert out.isascii()
        # ଓ → "o"; ଡ଼ → ".D"; ି → "i"; ଆ → "A"
        assert out == "o.DiA"

    def test_consonant_no_inherent_for_aa(self) -> None:
        # ଆ as independent vowel → "A" (capital in ITRANS)
        assert roman.to_roman("ଆ", "ITRANS") == "A"


class TestToRomanErrors:
    def test_unknown_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown scheme"):
            roman.to_roman("ନ", "Velthuis")  # type: ignore[arg-type]


class TestToRomanEdgeCases:
    def test_empty(self) -> None:
        assert roman.to_roman("", "ISO15919") == ""

    def test_non_odia_passes_through(self) -> None:
        assert roman.to_roman("hello", "ISO15919") == "hello"
        assert roman.to_roman("123", "ISO15919") == "123"

    def test_whitespace_preserved(self) -> None:
        assert roman.to_roman("ନ ମ", "ISO15919") == "na ma"


class TestFromRomanRoundTrip:
    @pytest.mark.parametrize(
        "word",
        ["ନ", "ନା", "ନମ", "ନମସ୍କାର", "ଆ", "ଓଡ଼ିଆ"],
    )
    def test_iso15919_round_trip(self, word: str) -> None:
        roman_text = roman.to_roman(word, "ISO15919")
        decoded = roman.from_roman(roman_text, "ISO15919")
        # Re-encoding the decoded string should produce the same roman.
        assert roman.to_roman(decoded, "ISO15919") == roman_text

    @pytest.mark.parametrize(
        "word",
        ["ନ", "ନା", "ନମ", "ନମସ୍କାର", "ଆ"],
    )
    def test_itrans_round_trip(self, word: str) -> None:
        roman_text = roman.to_roman(word, "ITRANS")
        decoded = roman.from_roman(roman_text, "ITRANS")
        assert roman.to_roman(decoded, "ITRANS") == roman_text


class TestFromRomanUnknownChars:
    def test_unknown_chars_pass_through(self) -> None:
        # Punctuation isn't in any roman table → emitted verbatim.
        out = roman.from_roman("namaskara!", "Hunterian")
        assert out.endswith("!")

    def test_empty(self) -> None:
        assert roman.from_roman("", "ISO15919") == ""


class TestPublicAPI:
    def test_submodule_accessible(self) -> None:
        import openodia

        assert openodia.roman is roman
        assert callable(openodia.roman.to_roman)
        assert callable(openodia.roman.from_roman)
