import random
import re
import unicodedata

import pytest

from openodia import roman
from openodia.roman._roman import Scheme

REVERSIBLE_SCHEMES: list[Scheme] = ["ISO15919", "ITRANS"]
ALL_SCHEMES: list[Scheme] = ["ISO15919", "ITRANS", "Hunterian"]
ODIA_BLOCK = [chr(c) for c in range(0x0B00, 0x0B80)]
JOINERS = ["\u200d", "\u200c"]
ODIA_RUN = re.compile("[\u0b00-\u0b7f]+")
STRAY_SIGNS = [chr(c) for c in (*range(0x0B3E, 0x0B45), 0x0B47, 0x0B48, 0x0B4B, 0x0B4C, 0x0B4D, 0x0B62, 0x0B63)]


def code_points(text: str) -> list[str]:
    return [f"U+{ord(c):04X}" for c in text]


def nfc_odia_runs(text: str) -> str:
    return ODIA_RUN.sub(lambda m: unicodedata.normalize("NFC", m.group()), text)


def round_trip(text: str, scheme: Scheme) -> str:
    return roman.from_roman(roman.to_roman(text, scheme, reversible=True), scheme)


def odia_runs_are_nfc(text: str) -> bool:
    return all(unicodedata.is_normalized("NFC", m.group()) for m in ODIA_RUN.finditer(text))


class TestStraySignsRoundTrip:
    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize("sign", STRAY_SIGNS)
    def test_lone_sign_comes_back(self, scheme: Scheme, sign: str) -> None:
        assert code_points(round_trip(sign, scheme)) == code_points(sign)

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    @pytest.mark.parametrize("text", ["ଓା", "କ୍୍", "କ\u200dା", "କ\u200c୍ଷ", "କାା", "କା୍", "ଂ୍"])
    def test_sign_without_a_consonant_comes_back(self, scheme: Scheme, text: str) -> None:
        assert code_points(round_trip(text, scheme)) == code_points(text)

    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [
            ("ISO15919", "ା", "ା"),
            ("ITRANS", "ା", "ା"),
            ("ISO15919", "କ୍୍", "k:{୍:}"),
            ("ITRANS", "କ୍୍", "k_{୍_}"),
            ("ISO15919", "କ\u200c୍ଷ", "ka:{\u200c୍:}ṣa"),
            ("ITRANS", "ଓା", "oା"),
        ],
    )
    def test_stray_sign_is_written_as_itself(self, scheme: Scheme, text: str, expected: str) -> None:
        assert roman.to_roman(text, scheme, reversible=True) == expected

    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [("ISO15919", "ା", "ā"), ("ITRANS", "ା", "A"), ("Hunterian", "ା", "a"), ("ISO15919", "କ୍୍", "k")],
    )
    def test_default_output_still_spells_stray_signs(self, scheme: Scheme, text: str, expected: str) -> None:
        assert roman.to_roman(text, scheme) == expected

    def test_hunterian_ignores_reversible_for_stray_signs(self) -> None:
        assert roman.to_roman("ା", "Hunterian", reversible=True) == "a"

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    def test_every_short_odia_sequence_comes_back(self, scheme: Scheme) -> None:
        failures = []
        for a in ODIA_BLOCK:
            for text in [a, a + a, "କ" + a + a] + ["କ" + j + a for j in JOINERS]:
                if round_trip(text, scheme) != unicodedata.normalize("NFC", text):
                    failures.append(text)
            for b in ODIA_BLOCK:
                for text in [a + b] + [a + j + b for j in JOINERS] + ["କ" + j + a + b for j in JOINERS]:
                    if round_trip(text, scheme) != unicodedata.normalize("NFC", text):
                        failures.append(text)
        assert [code_points(t) for t in failures] == []

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    def test_decomposed_input_comes_back_in_nfc(self, scheme: Scheme) -> None:
        for text in ["\u0b47\u0b3e", "କ\u0b47\u0b57", "\u0b47\u0b56\u0b47\u0b56"]:
            assert code_points(round_trip(text, scheme)) == code_points(unicodedata.normalize("NFC", text))

    @pytest.mark.parametrize("scheme", REVERSIBLE_SCHEMES)
    def test_mixed_text_fuzz(self, scheme: Scheme) -> None:
        pool = ODIA_BLOCK + JOINERS + list("akhī:_{}`·.^ '\u0301\u0323\u0304\u00c5\u212b\u2000\n")
        rnd = random.Random(227)
        for _ in range(3000):
            text = "".join(rnd.choice(pool) for _ in range(rnd.randint(1, 7)))
            assert code_points(round_trip(text, scheme)) == code_points(nfc_odia_runs(text))


class TestFromRomanOutputIsNfc:
    @pytest.mark.parametrize("scheme", ALL_SCHEMES)
    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            ("\u0b5c", "\u0b21\u0b3c"),
            ("\u0b5d", "\u0b22\u0b3c"),
            ("ka\u0b5c", "\u0b15\u0b21\u0b3c"),
            ("\u0b47\u0b3e", "\u0b4b"),
            ("\u0b4b", "\u0b4b"),
            ("ka\u0b47\u0b3e", "\u0b15\u0b4b"),
        ],
    )
    def test_passed_through_odia_is_nfc(self, scheme: Scheme, text: str, expected: str) -> None:
        assert code_points(roman.from_roman(text, scheme)) == code_points(expected)

    @pytest.mark.parametrize(("scheme", "text"), [("ISO15919", ":{\u0b5c:}"), ("ITRANS", "_{\u0b5c_}")])
    def test_quoted_odia_is_nfc(self, scheme: Scheme, text: str) -> None:
        assert code_points(roman.from_roman(text, scheme)) == code_points("\u0b21\u0b3c")

    @pytest.mark.parametrize(
        ("scheme", "text", "expected"),
        [
            ("ITRANS", "_{\u212b_}", ["U+212B"]),
            ("ITRANS", "\u212b", ["U+212B"]),
            ("Hunterian", "\u212b", ["U+212B"]),
            ("ISO15919", ":{\u212b:}", ["U+212B"]),
            ("ISO15919", "\u212b", ["U+00C5"]),
        ],
    )
    def test_non_odia_text_is_normalised_only_by_iso_outside_quotes(
        self, scheme: Scheme, text: str, expected: list[str]
    ) -> None:
        assert code_points(roman.from_roman(text, scheme)) == expected

    @pytest.mark.parametrize("scheme", ALL_SCHEMES)
    def test_output_fuzz(self, scheme: Scheme) -> None:
        pool = ODIA_BLOCK + JOINERS + list("akAhīṛ:_{}`·.^~ D'\u0301\u0323\u0304")
        rnd = random.Random(244)
        for _ in range(3000):
            text = "".join(rnd.choice(pool) for _ in range(rnd.randint(1, 7)))
            assert odia_runs_are_nfc(roman.from_roman(text, scheme)), code_points(text)

    @pytest.mark.parametrize("scheme", ALL_SCHEMES)
    def test_every_odia_pair_decodes_to_nfc(self, scheme: Scheme) -> None:
        failures = [a + b for a in ODIA_BLOCK for b in ODIA_BLOCK if not odia_runs_are_nfc(roman.from_roman(a + b, scheme))]
        assert [code_points(t) for t in failures] == []


class TestSeparatorBeforeNukta:
    def test_nukta_after_separator_attaches_to_the_consonant(self) -> None:
        assert code_points(roman.from_roman("k_`", "ITRANS")) == ["U+0B15", "U+0B3C", "U+0B4D"]

    @pytest.mark.parametrize(("scheme", "text"), [("ITRANS", "k_`a"), ("ISO15919", "k:·a")])
    def test_vowel_after_separated_nukta_is_the_inherent_vowel(self, scheme: Scheme, text: str) -> None:
        assert code_points(roman.from_roman(text, scheme)) == ["U+0B15", "U+0B3C"]

    def test_encoder_writes_latin_text_and_the_nukta_mark(self) -> None:
        assert roman.to_roman("k_଼", "ITRANS") == "k_`"
