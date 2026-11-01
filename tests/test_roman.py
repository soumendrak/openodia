from typing import cast

import pytest

from openodia import roman
from openodia.roman import SCHEMES
from openodia.roman._roman import Scheme


class TestSchemesConstant:
    def test_three_schemes_listed(self) -> None:
        assert set(SCHEMES) == {"ISO15919", "Hunterian", "ITRANS"}


class TestToRomanISO15919:
    def test_independent_vowel(self) -> None:
        assert roman.to_roman("ଆ", "ISO15919") == "ā"

    def test_consonant_with_inherent_schwa(self) -> None:
        assert roman.to_roman("ନ", "ISO15919") == "na"

    def test_consonant_with_matra(self) -> None:
        assert roman.to_roman("ନା", "ISO15919") == "nā"

    def test_consonant_with_halant(self) -> None:
        assert roman.to_roman("କ୍", "ISO15919") == "k"

    def test_conjunct(self) -> None:
        assert roman.to_roman("ସ୍କା", "ISO15919") == "skā"

    def test_modifier_attaches(self) -> None:
        assert roman.to_roman("କଂ", "ISO15919") == "kaṁ"

    def test_basic_word(self) -> None:
        assert roman.to_roman("ନମସ୍କାର", "ISO15919") == "namaskāra"


class TestToRomanHunterian:
    def test_basic_word(self) -> None:
        assert roman.to_roman("ନମସ୍କାର", "Hunterian") == "namaskara"

    def test_diacritic_free(self) -> None:
        out = roman.to_roman("ସୋମେନ୍ଦ୍ର", "Hunterian")
        assert out.isascii()


class TestToRomanITRANS:
    def test_basic_word(self) -> None:
        out = roman.to_roman("ଓଡ଼ିଆ", "ITRANS")
        assert out.isascii()
        assert out == "o.DiA"

    def test_consonant_no_inherent_for_aa(self) -> None:
        assert roman.to_roman("ଆ", "ITRANS") == "A"


class TestToRomanErrors:
    def test_unknown_scheme_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown scheme"):
            roman.to_roman("ନ", cast(Scheme, "Velthuis"))


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
        assert roman.from_roman(roman_text, "ISO15919") == word

    @pytest.mark.parametrize(
        "word",
        ["ନ", "ନା", "ନମ", "ନମସ୍କାର", "ଆ", "ଓଡ଼ିଆ"],
    )
    def test_itrans_round_trip(self, word: str) -> None:
        roman_text = roman.to_roman(word, "ITRANS")
        assert roman.from_roman(roman_text, "ITRANS") == word


class TestFromRomanUnknownChars:
    def test_unknown_chars_pass_through(self) -> None:
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
    def test_round_trip_with_vowel_context(self, scheme: Scheme, word: str) -> None:
        back = roman.from_roman(roman.to_roman(word, scheme), scheme)
        assert back == word

    def test_independent_vowel_vs_matra(self) -> None:
        assert roman.from_roman("ā") == "ଆ"
        assert roman.from_roman("nā") == "ନା"

    def test_hunterian_prefers_common_letters(self) -> None:
        assert roman.from_roman("namaskara", "Hunterian") == "ନମସ୍କର"
        assert roman.from_roman("ta", "Hunterian") == "ତ"

    @pytest.mark.parametrize("scheme", ["Hunterian", "ITRANS"])
    def test_wa_and_vocalic_forms_are_ascii(self, scheme: Scheme) -> None:
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
    def test_pass_through_latin_unchanged(self, text: str, scheme: Scheme) -> None:
        assert roman.to_roman(text, scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", ["ଅ:ଇ", "ଅ_ଇ", "କ::ଖ", "ରାମ_ସୀତା"])
    def test_literal_separator_round_trips(self, text: str, scheme: Scheme) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", ["କ୍ଅ", "କ୍ଆ", "ସ୍ଇ", "ନମସ୍କାର"])
    def test_halant_before_independent_vowel_round_trips(self, text: str, scheme: Scheme) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme), scheme) == text

    def test_halant_mark_examples(self) -> None:
        assert roman.to_roman("କ୍ଅ") == "k:a"
        assert roman.to_roman("କ୍ଅ", "ITRANS") == "k_a"
        assert roman.to_roman("କ୍ଅ", "Hunterian") == "ka"
        assert roman.to_roman("ଅ:ଇ", reversible=True) == "a::i"

    def test_escaped_separator_after_bare_consonant(self) -> None:
        assert roman.from_roman("k::a") == "କ୍:ଅ"


class TestCodexRound4:
    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", ["କi", "କ୍h", "iକ", "ନମସ୍କାର hello", "ରାମ {x} ସୀତା", "କa:b", "କ{a}"])
    def test_mixed_script_round_trips(self, text: str, scheme: Scheme) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme) == text

    def test_mixed_script_quoting_examples(self) -> None:
        assert roman.to_roman("କi", reversible=True) == "ka:{i:}"
        assert roman.to_roman("କ୍h", "ITRANS", reversible=True) == "k_{h_}"
        assert roman.to_roman("ନମସ୍କାର hello", reversible=True) == "namaskāra :{hello:}"


class TestNonOdiaRunsUnchanged:
    """Non-Odia runs come back exactly as given unless reversible=True."""

    @pytest.mark.parametrize(
        ("text", "scheme"),
        [
            ("https://example.test", "ISO15919"),
            ("1:2", "ISO15919"),
            ("file_name", "ITRANS"),
            ("e\u0301", "ISO15919"),
        ],
    )
    def test_pure_non_odia_unchanged(self, text: str, scheme: Scheme) -> None:
        assert roman.to_roman(text, scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS", "Hunterian"])
    def test_latin_run_in_mixed_text_unquoted(self, scheme: Scheme) -> None:
        out = roman.to_roman("ନମସ୍କାର hello 1:2 file_name e\u0301", scheme)
        assert out.endswith(" hello 1:2 file_name e\u0301")
        assert "{" not in out

    def test_mixed_text_default_examples(self) -> None:
        assert roman.to_roman("କi") == "kai"
        assert roman.to_roman("ଅ:ଇ") == "a:i"

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS", "Hunterian"])
    def test_decomposed_odia_is_nfc_normalised(self, scheme: Scheme) -> None:
        assert roman.to_roman("କ\u0b47\u0b56", scheme) == roman.to_roman("କ\u0b48", scheme)
        assert roman.to_roman("କ\u0b47\u0b57", scheme) == roman.to_roman("କ\u0b4c", scheme)


class TestReversibleExact:
    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", ["hello", "hello world", "1:2", "file_name", "kha", "e\u0301"])
    def test_pure_non_odia_round_trips(self, text: str, scheme: Scheme) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme) == text

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("text", ["କt\u0323", "କ e\u0301", "t\u0323"])
    def test_quoted_literals_are_not_normalised(self, text: str, scheme: Scheme) -> None:
        assert roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme) == text

    def test_decoder_keeps_quoted_text_verbatim(self) -> None:
        assert roman.from_roman("ka:{t\u0323:}") == "କt\u0323"


class TestHunterianConsonantNH:
    @pytest.mark.parametrize(
        ("spelling", "word"),
        [
            ("jesan", "ଜେସନ୍"),
            ("an", "ଅନ୍"),
            ("duh", "ଦୁହ୍"),
            ("anka", "ଅନ୍କ"),
            ("ahka", "ଅହ୍କ"),
            ("ahpa", "ଅହ୍ପ"),
            ("ansa", "ଅନ୍ସ"),
            ("ansha", "ଅନ୍ଶ"),
            ("anha", "ଅନ୍ହ"),
            ("angga", "ଅଙ୍ଗ"),
            ("anka.", "ଅନ୍କ."),
            ("anx", "ଅନ୍x"),
            ("ahx", "ଅହ୍x"),
            ("anna", "ଅନ୍ନ"),
            ("brahma", "ବ୍ରହ୍ମ"),
            ("kna", "କ୍ନ"),
            ("nga", "ଙ"),
            ("ngka", "ଙ୍କ"),
            ("angka", "ଅଙ୍କ"),
            ("namaskara", "ନମସ୍କର"),
        ],
    )
    def test_decodes_as_consonant(self, spelling: str, word: str) -> None:
        assert roman.from_roman(spelling, "Hunterian") == word

    @pytest.mark.parametrize("word", ["ଜେସନ୍", "ଅନ୍କ", "ଅନ୍ସ", "ଅନ୍ଶ", "ଅନ୍ହ", "ଅଙ୍କ", "ଅଙ୍ଗ", "ଶଙ୍କର", "ମନ୍"])
    def test_round_trip(self, word: str) -> None:
        assert roman.from_roman(roman.to_roman(word, "Hunterian"), "Hunterian") == word

    def test_no_ascii_spelling_decodes_as_a_modifier(self) -> None:
        printable = [chr(c) for c in range(0x20, 0x7F)]
        spellings = printable + [a + b for a in printable for b in printable]
        decoded = "".join(roman.from_roman(s, "Hunterian") for s in spellings)
        assert sorted({c for c in decoded if c in "\u0b01\u0b02\u0b03"}) == []
        assert len(spellings) == 9120

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("\u0b02", ["U+0B02"]),
            ("\u0b01", ["U+0B01"]),
            ("\u0b03", ["U+0B03"]),
            ("\u0b15\u0b02", ["U+0B15", "U+0B02"]),
            ("an\u0b03", ["U+0B05", "U+0B28", "U+0B4D", "U+0B03"]),
        ],
    )
    def test_odia_modifiers_in_the_input_pass_through(self, text: str, expected: list[str]) -> None:
        assert [f"U+{ord(c):04X}" for c in roman.from_roman(text, "Hunterian")] == expected

    @pytest.mark.parametrize("spelling", ["ri", "li", "kri", "kli", "ari", "ali", "rii", "lii", "riti", "rhi"])
    def test_ri_and_li_are_not_vocalic(self, spelling: str) -> None:
        decoded = roman.from_roman(spelling, "Hunterian")
        assert sorted({f"U+{ord(c):04X}" for c in decoded if c in "\u0b0b\u0b0c\u0b60\u0b61\u0b43\u0b44\u0b62\u0b63"}) == []

    @pytest.mark.parametrize("scheme", ["ISO15919", "ITRANS"])
    @pytest.mark.parametrize("word", ["ସଂସ୍କୃତ", "ଦୁଃଖ", "ଏବଂ", "ସଂଗୀତ", "ସିଂହ", "ଅଁ", "ଜେସନ୍", "ଅଙ୍କ"])
    def test_marked_modifiers_round_trip(self, word: str, scheme: Scheme) -> None:
        assert roman.from_roman(roman.to_roman(word, scheme), scheme) == word
