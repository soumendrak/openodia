import unicodedata

import pytest

from openodia import roman
from openodia.roman._roman import Scheme
from openodia.roman._tables import ISO15919

NUKTA = "\u0b3c"
HALANT = "\u0b4d"
DDA_NUKTA = "\u0b21" + NUKTA
DDHA_NUKTA = "\u0b22" + NUKTA
REVERSIBLE_SCHEMES: list[Scheme] = ["ISO15919", "ITRANS"]

PLAIN_CONSONANTS = [c for c in ISO15919["consonants"] if c not in "\u0b5c\u0b5d"]
CONSONANTS = PLAIN_CONSONANTS + [c + NUKTA for c in PLAIN_CONSONANTS]
VOWELS = list(ISO15919["vowels"])
VOWEL_SIGNS = list(ISO15919["matras"])
MODIFIERS = list(ISO15919["modifiers"])
OTHER_SIGNS = [chr(c) for c in range(0x0B66, 0x0B71)] + [chr(c) for c in range(0x0B72, 0x0B78)]
TAILS = [""] + VOWEL_SIGNS + [HALANT] + [HALANT + c for c in ("ଷ", "ର", DDA_NUKTA, DDHA_NUKTA)]
NEIGHBOURS = ["କ", DDA_NUKTA, DDHA_NUKTA + "ା", "ଆ", "ଂ", "୧", "ଽ", " ଓ"]


def code_points(text: str) -> list[str]:
    return [f"U+{ord(c):04X}" for c in text]


def round_trip(text: str, scheme: Scheme) -> str:
    return roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme)


def assert_exact_nfc_round_trip(text: str, scheme: Scheme) -> None:
    assert unicodedata.is_normalized("NFC", text)
    back = round_trip(text, scheme)
    assert code_points(back) == code_points(text)
    assert unicodedata.is_normalized("NFC", back)
    nfd_back = round_trip(unicodedata.normalize("NFD", text), scheme)
    assert code_points(nfd_back) == code_points(text)


class TestDdaAndDdhaWithNukta:
    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize("letter", [DDA_NUKTA, DDHA_NUKTA])
    def test_two_character_form_round_trips_exactly(self, scheme: Scheme, letter: str) -> None:
        back = round_trip(letter, scheme)
        assert code_points(back) == code_points(letter)
        assert unicodedata.is_normalized("NFC", back)

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    def test_odia_word_round_trips_exactly(self, scheme: Scheme) -> None:
        word = "ଓ" + DDA_NUKTA + "ିଆ"
        assert code_points(round_trip(word, scheme)) == ["U+0B13", "U+0B21", "U+0B3C", "U+0B3F", "U+0B06"]

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize(("precomposed", "nfc"), [("\u0b5c", DDA_NUKTA), ("\u0b5d", DDHA_NUKTA)])
    def test_precomposed_input_comes_back_in_nfc(self, scheme: Scheme, precomposed: str, nfc: str) -> None:
        assert unicodedata.normalize("NFC", precomposed) == nfc
        assert code_points(round_trip(precomposed, scheme)) == code_points(nfc)

    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [
            ("ISO15919", "ṛā", DDA_NUKTA + "ା"),
            ("ISO15919", "ṛhā", DDHA_NUKTA + "ା"),
            ("ITRANS", ".DA", DDA_NUKTA + "ା"),
            ("ITRANS", ".DhA", DDHA_NUKTA + "ା"),
            ("Hunterian", "rha", DDHA_NUKTA),
        ],
    )
    def test_from_roman_writes_the_nfc_letters(self, scheme: Scheme, text: str, expected: str) -> None:
        back = roman.from_roman(text, scheme)
        assert code_points(back) == code_points(expected)
        assert unicodedata.is_normalized("NFC", back)


class TestEveryOdiaInputClassRoundTrips:
    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize("consonant", CONSONANTS)
    def test_consonant_syllables(self, scheme: Scheme, consonant: str) -> None:
        for tail in TAILS:
            syllable = consonant + tail
            for modifier in MODIFIERS:
                assert_exact_nfc_round_trip(syllable + modifier, scheme)
            for neighbour in ["", *NEIGHBOURS]:
                assert_exact_nfc_round_trip(syllable + neighbour, scheme)
                assert_exact_nfc_round_trip(neighbour + syllable, scheme)

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize("vowel", VOWELS)
    def test_independent_vowels(self, scheme: Scheme, vowel: str) -> None:
        for modifier in ["", *MODIFIERS]:
            for neighbour in ["", *NEIGHBOURS]:
                assert_exact_nfc_round_trip(vowel + modifier + neighbour, scheme)
                assert_exact_nfc_round_trip(neighbour + vowel + modifier, scheme)

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize("sign", OTHER_SIGNS)
    def test_digits_and_other_signs(self, scheme: Scheme, sign: str) -> None:
        for neighbour in ["", *NEIGHBOURS]:
            assert_exact_nfc_round_trip(sign + neighbour, scheme)
            assert_exact_nfc_round_trip(neighbour + sign, scheme)

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize(
        "other",
        [
            "hello",
            "1:2",
            "file_name",
            "e\u0301",
            "\u00b7",
            "`",
            "ṛ",
            "\u212b",
            "\u2000",
            "\u2001",
            "x\u2000y",
            ":{x:}",
            "_{x_}",
            ".D",
            "k",
            " ",
        ],
    )
    def test_odia_mixed_with_other_text(self, scheme: Scheme, other: str) -> None:
        for word in [*NEIGHBOURS, "ଓ" + DDA_NUKTA + "ିଆ", "ନମସ୍କାର", "କ" + NUKTA + HALANT]:
            for text in (word + other + word, other + word + other):
                assert round_trip(text, scheme) == text


class TestWhitespaceThatNfcChanges:
    @pytest.mark.parametrize("space", ["\u2000", "\u2001"])
    def test_space_is_quoted_and_kept(self, space: str) -> None:
        text = "କ" + space + "ଖ"
        assert roman.to_roman(text, reversible=True) == "ka:{" + space + ":}kha"
        assert code_points(round_trip(text, "ISO15919")) == code_points(text)

    def test_ordinary_whitespace_is_not_quoted(self) -> None:
        assert roman.to_roman("କ \u2002\tଖ", reversible=True) == "ka \u2002\tkha"


class TestSeparatorBeforeNonRomanText:
    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [("ISO15919", "ka:!", "କ:!"), ("ISO15919", "k:!", "କ୍:!"), ("ITRANS", "ka_!", "କ_!"), ("ISO15919", "ka:", "କ:")],
    )
    def test_separator_stays_literal(self, scheme: Scheme, text: str, expected: str) -> None:
        assert roman.from_roman(text, scheme) == expected

    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [("ISO15919", "ka:{ā", "କ:{ଆ"), ("ISO15919", "ka:{a\u0304", "କ:{ଆ"), ("ITRANS", "ka_{A", "କ_{ଆ")],
    )
    def test_unclosed_quote_is_decoded_as_plain_text(self, scheme: Scheme, text: str, expected: str) -> None:
        assert roman.from_roman(text, scheme) == expected

    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [
            ("ISO15919", "!:a", "!:ଅ"),
            ("ISO15919", "ka!:a", "କ!:ଅ"),
            ("ISO15919", "ka:::a", "କ::ଅ"),
            ("ISO15919", "ka:{!:}:a", "କ!:ଅ"),
            ("ITRANS", "ka!_A", "କ!_ଆ"),
        ],
    )
    def test_separator_after_non_roman_text_stays_literal(self, scheme: Scheme, text: str, expected: str) -> None:
        assert roman.from_roman(text, scheme) == expected


class TestIsoDecoderNormalizesOutsideQuotes:
    @pytest.mark.parametrize(
        ("text", "expected"),
        [("ka\u0304:{!:}", "କା!"), ("ka\u0304:{!:}ka\u0304", "କା!କା"), (":{e\u0301:}ka\u0304", "e\u0301କା")],
    )
    def test_decomposed_roman_letters_decode_like_precomposed(self, text: str, expected: str) -> None:
        assert roman.from_roman(text) == expected


class TestEncoderMarks:
    @pytest.mark.parametrize(("scheme", "expected"), [("ISO15919", "ṛha"), ("ITRANS", ".Dha"), ("Hunterian", "rha")])
    def test_ddha_with_nukta_keeps_its_own_letter(self, scheme: Scheme, expected: str) -> None:
        assert roman.to_roman(DDHA_NUKTA, scheme) == expected
        assert roman.to_roman(DDA_NUKTA, scheme) == expected.replace("h", "")

    def test_halant_after_a_sign_writes_no_boundary_mark(self) -> None:
        assert roman.to_roman("ଂ୍ଇ") == "ṁi"
