import unicodedata
from typing import cast

import pytest

from openodia import indic
from openodia.indic import SCRIPTS
from openodia.indic._indic import _SCRIPT_OFFSETS, Script


class TestScriptsConstant:
    def test_contains_all_supported(self) -> None:
        for s in [
            "devanagari",
            "bengali",
            "assamese",
            "gurmukhi",
            "gujarati",
            "odia",
            "tamil",
            "telugu",
            "kannada",
            "malayalam",
        ]:
            assert s in SCRIPTS


class TestOdiaToDevanagari:
    def test_basic_consonant(self) -> None:
        assert indic.transliterate("କ", "odia", "devanagari") == "क"

    def test_basic_word(self) -> None:
        assert indic.transliterate("ଭାରତ", "odia", "devanagari") == "भारत"

    def test_digits(self) -> None:
        assert indic.transliterate("୦୧୨", "odia", "devanagari") == "०१२"


class TestDevanagariToOdia:
    def test_basic_word(self) -> None:
        assert indic.transliterate("भारत", "devanagari", "odia") == "ଭାରତ"

    def test_namaste(self) -> None:
        assert indic.transliterate("नमस्ते", "devanagari", "odia") == "ନମସ୍ତେ"


class TestRoundTrip:
    @pytest.mark.parametrize(
        "scripts",
        [
            ("odia", "devanagari"),
            ("odia", "bengali"),
            ("odia", "telugu"),
            ("odia", "kannada"),
            ("odia", "malayalam"),
            ("odia", "gujarati"),
            ("odia", "gurmukhi"),
            ("devanagari", "bengali"),
        ],
    )
    def test_round_trip(self, scripts: tuple[Script, Script]) -> None:
        a, b = scripts
        word = "ଭାରତ" if a == "odia" else "भारत"
        once = indic.transliterate(word, a, b)
        twice = indic.transliterate(once, b, a)
        assert twice == word


class TestIdempotenceWhenSameScript:
    def test_same_script_returns_input(self) -> None:
        assert indic.transliterate("କ", "odia", "odia") == "କ"
        assert indic.transliterate("\u0b15\u0b47\u0b56", "odia", "odia") == "\u0b15\u0b47\u0b56"
        assert indic.transliterate("\u0b5c", "odia", "odia") == "\u0b5c"

    def test_assamese_is_bengali_block(self) -> None:
        assert indic.transliterate("কখগ", "bengali", "assamese") == indic.transliterate("কখগ", "assamese", "bengali") == "কখগ"


class TestNonIndicPassThrough:
    def test_latin_unchanged(self) -> None:
        assert indic.transliterate("hello", "odia", "devanagari") == "hello"

    def test_mixed_input(self) -> None:
        out = indic.transliterate("hello କ world", "odia", "devanagari")
        assert "hello" in out
        assert "world" in out
        assert "क" in out

    def test_whitespace_preserved(self) -> None:
        assert indic.transliterate("କ ଖ", "odia", "devanagari") == "क ख"


class TestUnknownScripts:
    def test_unknown_from_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown from_script"):
            indic.transliterate("क", cast(Script, "sanskrit"), "odia")

    def test_unknown_to_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown to_script"):
            indic.transliterate("କ", "odia", cast(Script, "sanskrit"))


class TestEmpty:
    def test_empty_input(self) -> None:
        assert indic.transliterate("", "odia", "devanagari") == ""


class TestNfcRoundTrip:
    def test_nfc_nukta_word_round_trips(self) -> None:
        source = "ଓଡ଼ିଆ"
        devanagari = indic.transliterate(source, from_script="odia", to_script="devanagari")
        assert devanagari == "ओड़िआ"
        assert unicodedata.normalize("NFC", devanagari) == devanagari
        assert indic.transliterate(devanagari, from_script="devanagari", to_script="odia") == source

    @pytest.mark.parametrize(
        ("script", "expected"),
        [
            ("malayalam", "\u0d13\u0b21\u0b3c\u0d3f\u0d06"),
            ("tamil", "\u0b93\u0b21\u0b3c\u0bbf\u0b86"),
        ],
    )
    def test_nukta_word_keeps_its_spelling_when_the_target_has_no_nukta(self, script: Script, expected: str) -> None:
        source = "ଓଡ଼ିଆ"
        out = indic.transliterate(source, from_script="odia", to_script=script)
        assert out == expected
        assert unicodedata.normalize("NFC", out) == out
        assert indic.transliterate(out, from_script=script, to_script="odia") == source

    def test_precomposed_exclusion_keeps_the_letters_before_it(self) -> None:
        assert indic.transliterate("\u0b15\u0b5c", "odia", "devanagari") == "\u0915\u0921\u093c"
        assert indic.transliterate("\u0b13\u0b5c\u0b3f\u0b06", "odia", "devanagari") == "\u0913\u0921\u093c\u093f\u0906"
        assert indic.transliterate("\u0915\u0958", "devanagari", "odia") == "\u0b15\u0b15\u0b3c"


class TestLength:
    """A chillu grows by a virama. A nukta letter can shrink."""

    @pytest.mark.parametrize(
        "text, from_, to_",
        [
            ("କଖଗ", "odia", "devanagari"),
            ("ନମସ୍କାର ଓଡ଼ିଆ", "odia", "telugu"),
        ],
    )
    def test_length_unchanged(self, text: str, from_: Script, to_: Script) -> None:
        assert len(indic.transliterate(text, from_, to_)) == len(text)

    def test_chillu_expands(self) -> None:
        text = "ൻ"
        out = indic.transliterate(text, from_script="malayalam", to_script="devanagari")
        assert out == "न्"
        assert len(out) == len(text) + 1

    def test_nukta_letter_can_shrink(self) -> None:
        text = "ଓଡ଼ିଆ"
        out = indic.transliterate(text, from_script="odia", to_script="gurmukhi")
        assert out == "\u0a13\u0a5c\u0a3f\u0a06"
        assert len(text) == 5
        assert len(out) == 4


class TestPublicAPI:
    def test_submodule_accessible(self) -> None:
        import openodia

        assert openodia.indic is indic
        assert callable(openodia.indic.transliterate)

    def test_changelog_scopes_the_nukta_claim(self) -> None:
        from pathlib import Path

        changelog = Path(__file__).resolve().parents[1].joinpath("CHANGELOG.md").read_text(encoding="utf-8")
        bullet = next(line for line in changelog.splitlines() if line.startswith("- `openodia.indic`"))
        assert "composition-excluded" in bullet
        assert "precomposed nukta letter" not in bullet
        for name in ("Gurmukhi", "RRA", "LLA", "SHA", "YYA"):
            assert name in bullet
        assert indic.transliterate("\u095c", "devanagari", "gurmukhi") == "\u0a5c"
        assert indic.transliterate("\u0a33", "gurmukhi", "devanagari") == "\u0933"
        assert indic.transliterate("\u0958", "devanagari", "bengali") == "\u0995\u09bc"


class TestCharacterIdentity:
    def test_malayalam_chillu_expands_to_consonant_plus_virama(self) -> None:
        assert indic.transliterate("ൻ", from_script="malayalam", to_script="devanagari") == "न्"

    def test_malayalam_chillu_rr_is_ra(self) -> None:
        assert indic.transliterate("അവർ", from_script="malayalam", to_script="devanagari") == "अवर्"
        assert indic.transliterate("ർ", from_script="malayalam", to_script="odia") == "ର୍"

    def test_shared_danda_is_preserved(self) -> None:
        assert indic.transliterate("नमस्ते।", from_script="devanagari", to_script="odia") == "ନମସ୍ତେ।"

    def test_odia_flap_rra_is_dda_plus_nukta(self) -> None:
        assert indic.transliterate("\u0b5c", from_script="odia", to_script="devanagari") == "\u0921\u093c"
        assert indic.transliterate("\u095c", from_script="devanagari", to_script="odia") == "\u0b21\u0b3c"
        assert indic.transliterate("\u0931", from_script="devanagari", to_script="odia") == "\u0b30\u0b3c"
        assert indic.transliterate("\u09dc", from_script="bengali", to_script="devanagari") == "\u0921\u093c"
        assert indic.transliterate("\u095c", from_script="devanagari", to_script="gurmukhi") == "\u0a5c"

    def test_odia_wa_is_kept(self) -> None:
        text = "\u0b38\u0b4d\u0b71"
        for script in (
            "devanagari",
            "bengali",
            "assamese",
            "gurmukhi",
            "gujarati",
            "tamil",
            "telugu",
            "kannada",
            "malayalam",
        ):
            out = indic.transliterate(text, from_script="odia", to_script=script)
            assert "\u0b71" in out
            assert indic.transliterate(out, from_script=script, to_script="odia") == text

    def test_missing_tamil_letter_is_kept_not_offset(self) -> None:
        assert indic.transliterate("खक", from_script="devanagari", to_script="tamil") == "खக"
        assert indic.transliterate("\u0958", from_script="devanagari", to_script="tamil") == "\u0958"
        assert indic.transliterate("\u0934", from_script="devanagari", to_script="bengali") == "\u0934"

    def test_llla_to_gurmukhi_has_one_nukta(self) -> None:
        out = indic.transliterate("\u0934", from_script="devanagari", to_script="gurmukhi")
        assert out == "\u0a32\u0a3c"
        assert out != "\u0a32\u0a3c\u0a3c"
        nuktas = [c for c in out if "SIGN NUKTA" in unicodedata.name(c, "")]
        assert len(nuktas) < 2

    def test_no_assigned_character_emits_two_nuktas_in_a_row(self) -> None:
        for src in SCRIPTS:
            start = _SCRIPT_OFFSETS[src]
            for cp in range(start, start + 0x80):
                if not unicodedata.name(chr(cp), ""):
                    continue
                for dst in SCRIPTS:
                    if src == dst:
                        continue
                    out = indic.transliterate(chr(cp), from_script=src, to_script=dst)
                    marks = [c for c in out if "SIGN NUKTA" in unicodedata.name(c, "")]
                    consecutive = any(
                        "SIGN NUKTA" in unicodedata.name(a, "") and "SIGN NUKTA" in unicodedata.name(b, "")
                        for a, b in zip(out, out[1:])
                    )
                    assert not consecutive, (src, dst, hex(cp), out)
                    assert len(marks) < 2

    def test_unassigned_codepoint_passes_through(self) -> None:
        assert indic.transliterate("\u0984", from_script="bengali", to_script="devanagari") == "\u0984"

    def test_long_e_and_o_match_across_north_and_south(self) -> None:
        assert indic.transliterate("देव", from_script="devanagari", to_script="telugu") == "దేవ"
        assert indic.transliterate("ଓ", from_script="odia", to_script="telugu") == "ఓ"
        assert indic.transliterate("దేవ", from_script="telugu", to_script="devanagari") == "देव"
        assert indic.transliterate("ऎ", from_script="devanagari", to_script="kannada") == "ಎ"
        assert indic.transliterate("\u090f", from_script="devanagari", to_script="tamil") == "\u0b8f"
        assert indic.transliterate("\u090f", from_script="devanagari", to_script="malayalam") == "\u0d0f"

    def test_assamese_ra_and_wa(self) -> None:
        assert indic.transliterate("ৰাম", from_script="assamese", to_script="devanagari") == "राम"
        assert indic.transliterate("ৱ", from_script="assamese", to_script="devanagari") == "व"

    def test_nukta_letter_and_khanda_ta_expand(self) -> None:
        assert indic.transliterate("\u0958", from_script="devanagari", to_script="bengali") == "\u0995\u09bc"
        assert indic.transliterate("ৎ", from_script="bengali", to_script="devanagari") == "त्"


class TestCodexRound3:
    @pytest.mark.parametrize(
        ("text", "src", "dst", "expected"),
        [
            ("ਮੇਰਾ", "gurmukhi", "devanagari", "मेरा"),
            ("देव", "devanagari", "gurmukhi", "ਦੇਵ"),
            ("ਸੋਨਾ", "gurmukhi", "devanagari", "सोना"),
            ("ਪੰਜਾਬੀ", "gurmukhi", "devanagari", "पंजाबी"),
            ("ਹਾਂ", "gurmukhi", "devanagari", "हां"),
            ("ਪੱਤਾ", "gurmukhi", "devanagari", "पत्ता"),
            ("ਪੱਤਾ", "gurmukhi", "odia", "ପତ୍ତା"),
            ("राम", "devanagari", "assamese", "ৰাম"),
            ("वाणी", "devanagari", "assamese", "ৱাণী"),
            ("राम", "devanagari", "bengali", "রাম"),
            ("ઑક્ટોબર", "gujarati", "devanagari", "ऑक्टोबर"),
            ("ऑक्टोबर", "devanagari", "gujarati", "ઑક્ટોબર"),
            ("\u0901", "devanagari", "gurmukhi", "\u0a01"),
            ("\u090d", "devanagari", "gujarati", "\u0a8d"),
        ],
    )
    def test_script_specific_names(self, text: str, src: Script, dst: Script, expected: str) -> None:
        assert indic.transliterate(text, src, dst) == expected

    @pytest.mark.parametrize(
        ("decomposed", "src"),
        [("କ\u0b47\u0b57", "odia"), ("ক\u09c7\u09d7", "bengali"), ("ക\u0d46\u0d57", "malayalam")],
    )
    def test_decomposed_vowel_signs_compose(self, decomposed: str, src: Script) -> None:
        composed = unicodedata.normalize("NFC", decomposed)
        assert indic.transliterate(decomposed, src, "devanagari") == indic.transliterate(composed, src, "devanagari")
        assert all(0x0900 <= ord(c) < 0x0980 for c in indic.transliterate(decomposed, src, "devanagari"))

    def test_non_source_text_is_not_normalized(self) -> None:
        assert indic.transliterate("e\u0301 କ", "odia", "devanagari") == "e\u0301 क"

    def test_addak_without_following_consonant_is_kept(self) -> None:
        assert indic.transliterate("ੱ", "gurmukhi", "devanagari") == "ੱ"

    def test_addak_before_a_sign_is_kept(self) -> None:
        assert indic.transliterate("\u0a71\u0a01", "gurmukhi", "devanagari") == "\u0a71\u0901"

    def test_addak_before_an_unmapped_letter_is_kept(self) -> None:
        assert indic.transliterate("\u0a71\u0a16", "gurmukhi", "tamil") == "\u0a71\u0a16"

    def test_bengali_writes_va_as_ba_and_keeps_wa(self) -> None:
        assert indic.transliterate("विश्वास", "devanagari", "bengali") == "বিশ্বাস"
        assert indic.transliterate("ଵ", "odia", "bengali") == "ব"
        wa = "\u0b38\u0b4d\u0b71"
        out = indic.transliterate(wa, "odia", "bengali")
        assert out == "\u09b8\u09cd\u0b71"
        assert indic.transliterate(out, "bengali", "odia") == wa

    def test_assamese_keeps_its_own_va(self) -> None:
        assert indic.transliterate("विश्वास", "devanagari", "assamese") == "ৱিশ্ৱাস"

    def test_malayalam_au_length_mark_is_the_au_sign(self) -> None:
        assert indic.transliterate("പൗരൻ", "malayalam", "devanagari") == "पौरन्"

    def test_malayalam_target_keeps_precomposed_au(self) -> None:
        assert indic.transliterate("पौ", "devanagari", "malayalam") == "പൌ"


class TestCodexRound4:
    @pytest.mark.parametrize(
        ("text", "src", "expected"),
        [
            ("पंजाबी", "devanagari", "\u0a2a\u0a70\u0a1c\u0a3e\u0a2c\u0a40"),
            ("हां", "devanagari", "\u0a39\u0a3e\u0a02"),
            ("में", "devanagari", "\u0a2e\u0a47\u0a02"),
            ("सिं", "devanagari", "\u0a38\u0a3f\u0a70"),
            ("सीं", "devanagari", "\u0a38\u0a40\u0a02"),
            ("कुं", "devanagari", "\u0a15\u0a41\u0a70"),
            ("कूं", "devanagari", "\u0a15\u0a42\u0a70"),
            ("उं", "devanagari", "\u0a09\u0a02"),
            ("ऊं", "devanagari", "\u0a0a\u0a02"),
            ("अं", "devanagari", "\u0a05\u0a70"),
            ("आं", "devanagari", "\u0a06\u0a02"),
            ("ं", "devanagari", "\u0a70"),
            ("\u09b9\u09be\u0982", "bengali", "\u0a39\u0a3e\u0a02"),
            ("\u0939\u093e\u093c\u0902", "devanagari", "\u0a39\u0a3e\u0a3c\u0a02"),
        ],
    )
    def test_gurmukhi_tippi_follows_the_vowel(self, text: str, src: Script, expected: str) -> None:
        assert indic.transliterate(text, src, "gurmukhi") == expected

    def test_decomposed_gurmukhi_consonants_match_precomposed(self) -> None:
        assert indic.transliterate("\u0a36\u0a2c\u0a26", "gurmukhi", "devanagari") == "शबद"
        assert indic.transliterate("\u0a38\u0a3c\u0a2c\u0a26", "gurmukhi", "devanagari") == "शबद"
        assert indic.transliterate("\u0a33", "gurmukhi", "devanagari") == "ळ"
        assert indic.transliterate("\u0a32\u0a3c", "gurmukhi", "devanagari") == "ळ"

    def test_tamil_aytham_is_not_visarga(self) -> None:
        assert indic.transliterate("\u0b83", "tamil", "devanagari") == "\u0b83"
        assert indic.transliterate("\u0903", "devanagari", "tamil") == "\u0903"
        assert indic.transliterate("\u0915\u0903", "devanagari", "tamil") == "\u0b95\u0903"

    def test_kannada_fa_name_is_llla(self) -> None:
        assert indic.transliterate("\u0cde", "kannada", "devanagari") == "\u0934"
        assert indic.transliterate("\u0934", "devanagari", "kannada") == "\u0cde"
        assert indic.transliterate("\u0cde", "kannada", "tamil") == "\u0bb4"
        assert indic.transliterate("\u095e", "devanagari", "kannada") == "\u0cab\u0cbc"

    def test_malayalam_dot_reph_is_dead_ra(self) -> None:
        assert indic.transliterate("\u0d4e\u0d15", "malayalam", "devanagari") == "\u0930\u094d\u0915"

    def test_gurmukhi_yakash_is_subjoined_ya(self) -> None:
        assert (
            indic.transliterate("\u0a38\u0a3f\u0a16\u0a75\u0a3e", "gurmukhi", "devanagari")
            == "\u0938\u093f\u0916\u094d\u092f\u093e"
        )


_ALL_PAIRS: list[tuple[Script, Script]] = [
    (src, dst) for src in SCRIPTS for dst in SCRIPTS if _SCRIPT_OFFSETS[src] != _SCRIPT_OFFSETS[dst]
]


def _block_text(script: Script) -> str:
    start = _SCRIPT_OFFSETS[script]
    letters = [chr(cp) for cp in range(start, start + 0x80) if unicodedata.name(chr(cp), "")]
    return " ".join(letters[0] + ch for ch in letters)


class TestNormalization:
    @pytest.mark.parametrize(("src", "dst"), _ALL_PAIRS)
    def test_nfc_and_nfd_input_agree(self, src: Script, dst: Script) -> None:
        text = _block_text(src)
        nfc = indic.transliterate(unicodedata.normalize("NFC", text), src, dst)
        nfd = indic.transliterate(unicodedata.normalize("NFD", text), src, dst)
        assert nfc == nfd

    def test_kannada_two_level_oo(self) -> None:
        decomposed = unicodedata.normalize("NFD", "\u0c95\u0ccb")
        assert indic.transliterate(decomposed, "kannada", "devanagari") == "\u0915\u094b"

    def test_tamil_decomposed_au_letter(self) -> None:
        assert indic.transliterate("\u0b92\u0bd7\u0bb5\u0bc8", "tamil", "devanagari") == "\u0914\u0935\u0948"

    @pytest.mark.parametrize(("letter", "expected"), [("\u0931", "\u0bb1"), ("\u0929", "\u0ba9"), ("\u0934", "\u0bb4")])
    def test_decomposed_devanagari_nukta_letters(self, letter: str, expected: str) -> None:
        decomposed = unicodedata.normalize("NFD", letter)
        assert indic.transliterate(decomposed, "devanagari", "tamil") == expected

    def test_excluded_nukta_letter_is_nfc(self) -> None:
        nfc = "\u0921\u093c"
        assert indic.transliterate("\u0b21\u0b3c", "odia", "devanagari") == nfc
        assert indic.transliterate("\u0b5c", "odia", "devanagari") == nfc


_DEVANAGARI_BINDI = [
    ("\u0906", "\u0a06"),
    ("\u0915\u093e", "\u0a15\u0a3e"),
    ("\u0908", "\u0a08"),
    ("\u0915\u0940", "\u0a15\u0a40"),
    ("\u090f", "\u0a0f"),
    ("\u0915\u0947", "\u0a15\u0a47"),
    ("\u0910", "\u0a10"),
    ("\u0915\u0948", "\u0a15\u0a48"),
    ("\u0913", "\u0a13"),
    ("\u0915\u094b", "\u0a15\u0a4b"),
    ("\u0914", "\u0a14"),
    ("\u0915\u094c", "\u0a15\u0a4c"),
    ("\u0909", "\u0a09"),
    ("\u090a", "\u0a0a"),
]


@pytest.mark.parametrize(("vowel", "expected"), _DEVANAGARI_BINDI)
def test_every_bindi_vowel(vowel: str, expected: str) -> None:
    assert indic.transliterate(vowel + "\u0902", "devanagari", "gurmukhi") == expected + "\u0a02"


class TestAssameseBengaliDirect:
    @pytest.mark.parametrize(
        ("text", "src", "dst", "expected"),
        [
            ("ৰাম", "assamese", "bengali", "রাম"),
            ("ৱ", "assamese", "bengali", "ব"),
            ("রাম", "bengali", "assamese", "ৰাম"),
            ("ৰ", "assamese", "assamese", "ৰ"),
            ("রাম", "bengali", "bengali", "রাম"),
        ],
    )
    def test_direct_conversion_applies_the_script_specific_letters(
        self, text: str, src: Script, dst: Script, expected: str
    ) -> None:
        assert indic.transliterate(text, src, dst) == expected

    def test_direct_conversion_matches_the_route_through_devanagari(self) -> None:
        text = "ৰাম ৱাহ কৃষ্ণ"
        direct = indic.transliterate(text, "assamese", "bengali")
        via = indic.transliterate(indic.transliterate(text, "assamese", "devanagari"), "devanagari", "bengali")
        assert direct == via


class TestUnicodeEdgeCases:
    @pytest.mark.parametrize(
        ("text", "src"),
        [("\u0c5d", "telugu"), ("\u0cdd", "kannada")],
    )
    def test_nakaara_pollu_is_dead_na(self, text: str, src: Script) -> None:
        assert indic.transliterate(text, src, "devanagari") == "\u0928\u094d"

    @pytest.mark.parametrize("virama", ["\u0d3b", "\u0d3c"])
    def test_malayalam_variant_viramas_are_the_virama(self, virama: str) -> None:
        assert indic.transliterate("\u0d15" + virama + "\u0d37", "malayalam", "devanagari") == "\u0915\u094d\u0937"
