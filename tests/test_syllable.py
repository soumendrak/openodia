import pytest

from openodia import syllable


class TestSplit:
    @pytest.mark.parametrize(
        "word, expected",
        [
            ("ନମସ୍କାର", ["ନ", "ମ", "ସ୍କା", "ର"]),
            ("ଓଡ଼ିଆ", ["ଓ", "ଡ଼ି", "ଆ"]),
            ("ବିଦ୍ୟାଳୟ", ["ବି", "ଦ୍ୟା", "ଳ", "ୟ"]),
            ("ରାମ", ["ରା", "ମ"]),
            ("ସୀତା", ["ସୀ", "ତା"]),
        ],
    )
    def test_basic_words(self, word: str, expected: list[str]) -> None:
        assert syllable.split(word) == expected

    def test_independent_vowel_only(self) -> None:
        assert syllable.split("ଆ") == ["ଆ"]

    def test_consonant_only(self) -> None:
        # Bare consonant with implicit schwa.
        assert syllable.split("କ") == ["କ"]

    def test_conjunct_cluster(self) -> None:
        # ସ + ୍ + କ + ୍ + ର = ସ୍କ୍ର
        assert syllable.split("ସ୍କ୍ର") == ["ସ୍କ୍ର"]

    def test_modifiers_cling_to_akshara(self) -> None:
        # ଅଁ should be a single akshara.
        assert syllable.split("ଅଁ") == ["ଅଁ"]

    def test_anusvara_after_consonant(self) -> None:
        assert syllable.split("ରଂ") == ["ରଂ"]

    def test_visarga_after_consonant(self) -> None:
        assert syllable.split("ରଃ") == ["ରଃ"]

    def test_nukta_attaches(self) -> None:
        # ଡ + ଼ + ି should produce one akshara: ଡ଼ି
        assert syllable.split("ଡ଼ି") == ["ଡ଼ି"]

    def test_independent_vowel_breaks_akshara(self) -> None:
        # "କଆ" should be two aksharas: ['କ', 'ଆ']
        assert syllable.split("କଆ") == ["କ", "ଆ"]

    def test_empty_string(self) -> None:
        assert syllable.split("") == []

    def test_non_odia_chars_emitted_individually(self) -> None:
        assert syllable.split("ର ର") == ["ର", " ", "ର"]
        assert syllable.split("ର!") == ["ର", "!"]

    def test_digits_emitted_individually(self) -> None:
        # Odia digits are not aksharas — they are emitted as own units.
        assert syllable.split("୨୩") == ["୨", "୩"]


class TestCount:
    @pytest.mark.parametrize(
        "word, expected",
        [
            ("ନମସ୍କାର", 4),
            ("ଓଡ଼ିଆ", 3),
            ("ବିଦ୍ୟାଳୟ", 4),
            ("ରାମ", 2),
            ("", 0),
        ],
    )
    def test_count_matches_split_excluding_non_odia(self, word: str, expected: int) -> None:
        assert syllable.count(word) == expected

    def test_count_ignores_whitespace_and_punctuation(self) -> None:
        # 2 aksharas + space + ! → still 2.
        assert syllable.count("ର ର!") == 2

    def test_count_ignores_digits(self) -> None:
        assert syllable.count("ର୨") == 1


class TestHyphenate:
    def test_basic(self) -> None:
        assert syllable.hyphenate("ବିଦ୍ୟାଳୟ") == "ବି-ଦ୍ୟା-ଳ-ୟ"

    def test_custom_separator(self) -> None:
        assert syllable.hyphenate("ବିଦ୍ୟାଳୟ", separator="·") == "ବି·ଦ୍ୟା·ଳ·ୟ"

    def test_preserves_inter_word_whitespace(self) -> None:
        assert syllable.hyphenate("ନମସ୍କାର ଓଡ଼ିଆ") == "ନ-ମ-ସ୍କା-ର ଓ-ଡ଼ି-ଆ"

    def test_single_akshara_word(self) -> None:
        assert syllable.hyphenate("ଆ") == "ଆ"

    def test_empty_string(self) -> None:
        assert syllable.hyphenate("") == ""

    def test_punctuation_breaks_hyphenation(self) -> None:
        # "ର!" → 'ର' + '!' — they shouldn't be joined with a hyphen.
        assert syllable.hyphenate("ର!") == "ର!"


class TestIdempotenceProperty:
    """``"".join(split(w))`` recovers the original word."""

    @pytest.mark.parametrize(
        "word",
        ["ନମସ୍କାର", "ଓଡ଼ିଆ", "ବିଦ୍ୟାଳୟ", "ରାମ", "ସୀତା"],
    )
    def test_split_then_join(self, word: str) -> None:
        assert "".join(syllable.split(word)) == word


class TestPublicAPI:
    def test_submodule_accessible(self) -> None:
        import openodia

        assert openodia.syllable is syllable
        assert callable(openodia.syllable.split)
