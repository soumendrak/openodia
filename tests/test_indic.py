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
