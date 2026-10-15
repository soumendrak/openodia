import unicodedata

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


class TestReviewFixes:
    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("word", ["ଆ", "ନା", "ନମସ୍କାର", "ସ୍ୱାଗତ", "ଦ୍ୱିତୀୟ", "କୢ", "ମଁ", "କଇ", "କ୍ହ", "ଅଉ", "କ୍"])
    def test_round_trip_with_vowel_context(self, scheme: str, word: str) -> None:
        back = roman.from_roman(roman.to_roman(word, scheme), scheme)
        assert unicodedata.normalize("NFD", back) == unicodedata.normalize("NFD", word)

    def test_independent_vowel_vs_matra(self) -> None:
        assert roman.from_roman("ā") == "ଆ"
        assert roman.from_roman("nā") == "ନା"

    def test_hunterian_prefers_common_letters(self) -> None:
        assert roman.from_roman("namaskara", "Hunterian") == "ନମସ୍କର"
        assert roman.from_roman("ta", "Hunterian") == "ତ"

    @pytest.mark.parametrize("scheme", ["Hunterian", "ITRANS"])
    def test_wa_and_vocalic_forms_are_ascii(self, scheme: str) -> None:
        out = roman.to_roman("ସ୍ୱାଗତ ଦ୍ୱିତୀୟ କୢ ୠ ୡ କୄ କୣ", scheme)
        assert out.isascii(), out

    def test_iso_accepts_decomposed_input(self) -> None:
        assert roman.from_roman("t\u0323a") == roman.from_roman("ṭa") == "ଟ"

    def test_documented_examples(self) -> None:
        assert roman.to_roman("ଓଡ଼ିଆ", "ISO15919") == "ōṛiā"
        assert roman.to_roman("ଓଡ଼ିଆ", "Hunterian") == "oria"

    def test_boundary_separators(self) -> None:
        assert roman.to_roman("କଇ") == "ka:i"
        assert roman.to_roman("କ୍ହ") == "k:ha"
        assert roman.to_roman("କଇ", "ITRANS") == "ka_i"
        assert roman.to_roman("କଇ", "Hunterian") == "kai"

    def test_plain_punctuation_is_kept(self) -> None:
        assert roman.from_roman("k-a: b") == "କ୍-ଅ: ବ୍"


class TestCodexRound3:
    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS", "Hunterian"])
    @pytest.mark.parametrize("text", ["plain", "ai", "kha", "hello world"])
    def test_pass_through_latin_unchanged(self, text: str, scheme: str) -> None:
        assert roman.to_roman(text, scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", ["ଅ:ଇ", "ଅ_ଇ", "କ::ଖ", "ରାମ_ସୀତା"])
    def test_literal_separator_round_trips(self, text: str, scheme: str) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme), scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", ["କ୍ଅ", "କ୍ଆ", "ସ୍ଇ", "ନମସ୍କାର"])
    def test_halant_before_independent_vowel_round_trips(self, text: str, scheme: str) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme), scheme) == text

    def test_halant_mark_examples(self) -> None:
        assert roman.to_roman("କ୍ଅ") == "k:a"
        assert roman.to_roman("କ୍ଅ", "ITRANS") == "k_a"
        assert roman.to_roman("କ୍ଅ", "Hunterian") == "ka"
        assert roman.to_roman("ଅ:ଇ") == "a::i"

    def test_escaped_separator_after_bare_consonant(self) -> None:
        assert roman.from_roman("k::a") == "କ୍:ଅ"
