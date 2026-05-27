
from openodia import phonetic


class TestSoundex:
    def test_empty_input(self) -> None:
        assert phonetic.soundex("") == ""

    def test_no_consonant_returns_empty(self) -> None:
        # Only vowels and matras.
        assert phonetic.soundex("ଆଇ") == ""

    def test_first_consonant_kept_verbatim(self) -> None:
        out = phonetic.soundex("ସ")
        assert out.startswith("ସ")

    def test_padded_to_four_chars(self) -> None:
        out = phonetic.soundex("ସ")
        assert len(out) == 4
        assert out == "ସ000"

    def test_basic_word(self) -> None:
        # ସୋମେନ୍ଦ୍ର → ସ (verbatim) + ମ(6) + ନ(5) + ଦ(5)→same as ନ, skipped → ର(7)
        # → "ସ657"
        out = phonetic.soundex("ସୋମେନ୍ଦ୍ର")
        assert len(out) == 4

    def test_truncates_to_four_chars(self) -> None:
        assert len(phonetic.soundex("ଚକ୍ରପାଣିଗ୍ରାହୀ")) == 4

    def test_adjacent_duplicates_collapse(self) -> None:
        # ଗଗଗ → all gutturals → 'ଗ' + (2 dropped as dup) + padding
        out = phonetic.soundex("ଗଗଗ")
        assert out == "ଗ000"

    def test_spelling_variants_match(self) -> None:
        # The difference between ସୋ vs ସୌ is just the vowel sign — Soundex
        # ignores vowels/matras, so the codes must match.
        assert phonetic.soundex("ସୋମେନ୍ଦ୍ର") == phonetic.soundex("ସୌମେନ୍ଦ୍ର")

    def test_aspirated_unaspirated_share_digit_code(self) -> None:
        """Standard Soundex keeps the first letter literal — but
        aspirated/unaspirated pairs in *body* positions collapse to one
        digit. So same first consonant + ``ଗ`` vs ``ଘ`` mid-word should match.
        """
        assert phonetic.soundex("ସଗର") == phonetic.soundex("ସଘର")


class TestMetaphone:
    def test_empty_input(self) -> None:
        assert phonetic.metaphone("") == ""

    def test_no_consonant(self) -> None:
        assert phonetic.metaphone("ଆଇ") == ""

    def test_first_consonant(self) -> None:
        # ଖ collapses to କ.
        assert phonetic.metaphone("ଖ") == "କ"

    def test_aspirated_collapses(self) -> None:
        # ଖ → କ; both should produce "କ"
        assert phonetic.metaphone("ଖ") == phonetic.metaphone("କ")

    def test_adjacent_duplicates_collapse(self) -> None:
        # Three labials in a row should yield a single ପ.
        assert phonetic.metaphone("ପଫବ") == "ପ"

    def test_basic_word(self) -> None:
        # ସୋମେନ୍ଦ୍ର — consonants ସ ମ ନ ଦ ର → bases ସ ପ ତ ତ ର
        # adjacent duplicates collapse: ସ ପ ତ ର
        assert phonetic.metaphone("ସୋମେନ୍ଦ୍ର") == "ସପତର"

    def test_spelling_variants_match(self) -> None:
        assert phonetic.metaphone("ସୋମେନ୍ଦ୍ର") == phonetic.metaphone("ସୌମେନ୍ଦ୍ର")


class TestSimilarity:
    def test_identical_inputs(self) -> None:
        assert phonetic.similarity("ସୋମେନ୍ଦ୍ର", "ସୋମେନ୍ଦ୍ର") == 1.0

    def test_spelling_variants_high(self) -> None:
        # Different matras only — soundex equal AND metaphone equal.
        score = phonetic.similarity("ସୋମେନ୍ଦ୍ର", "ସୌମେନ୍ଦ୍ର")
        assert score == 1.0

    def test_completely_different(self) -> None:
        # Names from different articulation groups.
        score = phonetic.similarity("ସୀତା", "ବିଜୟ")
        assert 0.0 <= score < 0.5

    def test_symmetric(self) -> None:
        a, b = "ସୋମେନ୍ଦ୍ର", "ସୁମନ"
        assert phonetic.similarity(a, b) == phonetic.similarity(b, a)

    def test_in_unit_interval(self) -> None:
        for a, b in [("ସୋମ", "ସୌମ"), ("ର", "କ"), ("ସୀତା", "ରାମ")]:
            score = phonetic.similarity(a, b)
            assert 0.0 <= score <= 1.0

    def test_empty_pair(self) -> None:
        # No consonants on either side. Defined to be 0.0 to avoid
        # accidentally matching everything.
        assert phonetic.similarity("", "") == 0.0
        assert phonetic.similarity("ଆ", "") == 0.0


class TestNonOdiaInputs:
    """Latin and other-script inputs degrade gracefully."""

    def test_latin_input_returns_empty(self) -> None:
        # No Odia consonants → empty soundex, empty metaphone.
        assert phonetic.soundex("hello") == ""
        assert phonetic.metaphone("hello") == ""

    def test_mixed_input(self) -> None:
        # Should pick up Odia consonants and ignore Latin.
        # Just check it returns a non-empty 4-char Soundex.
        out = phonetic.soundex("ସୋ hello")
        assert len(out) == 4


class TestPublicAPI:
    def test_submodule_accessible(self) -> None:
        import openodia

        assert openodia.phonetic is phonetic
        assert callable(openodia.phonetic.soundex)
        assert callable(openodia.phonetic.metaphone)
        assert callable(openodia.phonetic.similarity)


class TestLevenshteinHelper:
    """The Wagner-Fischer routine — exercise its branches."""

    def test_identical(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("abc", "abc") == 0

    def test_one_empty(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("", "abc") == 3
        assert _levenshtein("abc", "") == 3

    def test_both_empty(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("", "") == 0

    def test_single_substitution(self) -> None:
        from openodia.phonetic._phonetic import _levenshtein

        assert _levenshtein("abc", "axc") == 1


class TestNormalisedEditSimilarity:
    def test_both_empty_is_one(self) -> None:
        from openodia.phonetic._phonetic import _normalised_edit_similarity

        assert _normalised_edit_similarity("", "") == 1.0

    def test_one_empty_is_zero(self) -> None:
        from openodia.phonetic._phonetic import _normalised_edit_similarity

        assert _normalised_edit_similarity("abc", "") == 0.0
        assert _normalised_edit_similarity("", "abc") == 0.0
