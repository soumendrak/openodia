import unicodedata

import pytest

from openodia import indic
from openodia.indic import SCRIPTS


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
        # Odia କ (U+0B15) → Devanagari क (U+0915)
        assert indic.transliterate("କ", "odia", "devanagari") == "क"

    def test_basic_word(self) -> None:
        # ଭାରତ → भारत
        assert indic.transliterate("ଭାରତ", "odia", "devanagari") == "भारत"

    def test_digits(self) -> None:
        # ୦ (U+0B66) → ० (U+0966)
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
    def test_round_trip(self, scripts: tuple[str, str]) -> None:
        a, b = scripts
        word = "ଭାରତ" if a == "odia" else "भारत"
        once = indic.transliterate(word, a, b)
        twice = indic.transliterate(once, b, a)
        assert twice == word


class TestIdempotenceWhenSameScript:
    def test_same_script_returns_input(self) -> None:
        assert indic.transliterate("କ", "odia", "odia") == "କ"

    def test_assamese_is_bengali_block(self) -> None:
        # They alias — transliterating from one to the other should be a no-op.
        assert indic.transliterate("কখগ", "bengali", "assamese") == indic.transliterate("কখগ", "assamese", "bengali") == "কখগ"


class TestNonIndicPassThrough:
    def test_latin_unchanged(self) -> None:
        assert indic.transliterate("hello", "odia", "devanagari") == "hello"

    def test_mixed_input(self) -> None:
        out = indic.transliterate("hello କ world", "odia", "devanagari")
        assert "hello" in out
        assert "world" in out
        assert "क" in out  # Devanagari ka

    def test_whitespace_preserved(self) -> None:
        assert indic.transliterate("କ ଖ", "odia", "devanagari") == "क ख"


class TestUnknownScripts:
    def test_unknown_from_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown from_script"):
            indic.transliterate("क", "sanskrit", "odia")  # type: ignore[arg-type]

    def test_unknown_to_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown to_script"):
            indic.transliterate("କ", "odia", "sanskrit")  # type: ignore[arg-type]


class TestEmpty:
    def test_empty_input(self) -> None:
        assert indic.transliterate("", "odia", "devanagari") == ""


class TestLength:
    """Codepoint count must be preserved."""

    @pytest.mark.parametrize(
        "text, from_, to_",
        [
            ("କଖଗ", "odia", "devanagari"),
            ("ନମସ୍କାର ଓଡ଼ିଆ", "odia", "telugu"),
        ],
    )
    def test_length_unchanged(self, text: str, from_: str, to_: str) -> None:
        assert len(indic.transliterate(text, from_, to_)) == len(text)


class TestPublicAPI:
    def test_submodule_accessible(self) -> None:
        import openodia

        assert openodia.indic is indic
        assert callable(openodia.indic.transliterate)


class TestCharacterIdentity:
    """Characters outside the parallel core must not be offset blindly."""

    def test_malayalam_chillu_expands_to_consonant_plus_virama(self) -> None:
        assert indic.transliterate("ൻ", from_script="malayalam", to_script="devanagari") == "न्"

    def test_shared_danda_is_preserved(self) -> None:
        assert indic.transliterate("नमस्ते।", from_script="devanagari", to_script="odia") == "ନମସ୍ତେ।"

    def test_odia_flap_rra_maps_to_devanagari_dddha(self) -> None:
        assert indic.transliterate("\u0b5c", from_script="odia", to_script="devanagari") == "\u095c"
        assert indic.transliterate("\u095c", from_script="devanagari", to_script="odia") == "\u0b5c"
        # Devanagari alveolar RRA (ऱ) has no Odia letter; it is canonically
        # र + nukta, so it maps part by part (never to the flap ଡ଼).
        assert indic.transliterate("\u0931", from_script="devanagari", to_script="odia") == "\u0b30\u0b3c"

    def test_odia_wa_maps_to_va(self) -> None:
        assert indic.transliterate("ସ୍ୱ", from_script="odia", to_script="devanagari") == "स्व"

    def test_missing_tamil_letter_is_kept_not_offset(self) -> None:
        assert indic.transliterate("खक", from_script="devanagari", to_script="tamil") == "खக"

    def test_long_e_and_o_match_across_north_and_south(self) -> None:
        assert indic.transliterate("देव", from_script="devanagari", to_script="telugu") == "దేవ"
        assert indic.transliterate("ଓ", from_script="odia", to_script="telugu") == "ఓ"
        assert indic.transliterate("దేవ", from_script="telugu", to_script="devanagari") == "देव"
        assert indic.transliterate("ऎ", from_script="devanagari", to_script="kannada") == "ಎ"

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
        ],
    )
    def test_script_specific_names(self, text: str, src: str, dst: str, expected: str) -> None:
        assert indic.transliterate(text, src, dst) == expected

    @pytest.mark.parametrize(
        ("decomposed", "src"),
        [("କ\u0b47\u0b57", "odia"), ("ক\u09c7\u09d7", "bengali"), ("ക\u0d46\u0d57", "malayalam")],
    )
    def test_decomposed_vowel_signs_compose(self, decomposed: str, src: str) -> None:
        composed = unicodedata.normalize("NFC", decomposed)
        assert indic.transliterate(decomposed, src, "devanagari") == indic.transliterate(composed, src, "devanagari")
        assert all(0x0900 <= ord(c) < 0x0980 for c in indic.transliterate(decomposed, src, "devanagari"))

    def test_non_source_text_is_not_normalized(self) -> None:
        assert indic.transliterate("e\u0301 କ", "odia", "devanagari") == "e\u0301 क"

    def test_addak_without_following_consonant_is_kept(self) -> None:
        assert indic.transliterate("ੱ", "gurmukhi", "devanagari") == "ੱ"
